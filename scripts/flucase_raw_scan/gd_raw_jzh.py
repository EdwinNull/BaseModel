#!/usr/bin/env python3
"""JZH（检验表里的就诊号）怎么挂到住院：用研究者标注的对照表核对、找规律，再试不用对照表能不能推出来。
只输出计数、列名和遮蔽后的写法，不输出编号、姓名和病例内容；按病人数据分类的计数 1–4 写成 "<5"。

1. 认表：带 JZH 列的表；对照表每列的非空、不同值、写法形状；flucase 读取器会把它认成哪类表；
2. 对照表：JZH 与住院编号是不是一对一；同一病人两次住院的 JZH 是否不同；
3. 覆盖：对照表的住院有多少在这一套导出里；检验表的 JZH 有多少在对照表里、覆盖多少行检验；
4. 编码规律：JZH 与 ENCT_ID / 住院号 / 条码号是否相等、是否是其中一段、数值差是否固定；是否随入院时间递增（全院流水号）；
5. 时间核对：按对照表挂上的检验，采集时间是否落在那次住院里（入院到最后一条医嘱，前后各放宽 1 天）；
6. 不用对照表：每个 JZH 的检验时间落在哪几次住院的时间窗里；落在多次住院里时，看哪次住院的医嘱开始时间与检验采集时间吻合得多；
   与对照表比一致率。

用法：python gd_raw_jzh.py <原始导出目录> [--extra 另放的表.xlsx ...] [--out 报告.md]
用 flucase 的 venv（flucase/backend/.venv/bin/python）运行时，会额外报告 flucase 读取器把每张带 JZH 的表认成什么。
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import io
import itertools
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gd_raw_probe as P  # noqa: E402
import gd_raw_scan as S  # noqa: E402

c5, pct, canon = P.c5, P.pct, P.canon
DAY = 86400.0
KEYS = ["ENCT_ID", "ENCT_UUID", "住院号", "病案号"]
# 标注列里常见的短词：严格遮蔽时保留（其余汉字照旧遮成〔汉n〕）
KEEP = {"是", "否", "有", "无", "轻", "重", "轻症", "重症", "危重", "转重", "未转重", "不转重", "普通", "待核", "待定", "不确定", "排除", "纳入",
        "阳性", "阴性", "流感", "甲流", "乙流", "肺炎", "死亡", "存活", "好转", "治愈", "未愈", "院内", "院外", "社区", "医院获得"}


RAW: dict[str, str] = {}          # 去前导零后的编号 → 原样（去空白、去 Excel 的 ".0"），比较“是不是一段”时用原样


def cid(s: str | None) -> str:
    """编号：挂接用去前导零的写法（两边一个存成数字、一个存成文字也能对上），同时记下原样。"""
    if not s:
        return ""
    r = "".join(s.split()).upper()
    r = r[:-2] if r.endswith(".0") and r[:-2].isdigit() else r
    c = canon(r)
    RAW.setdefault(c, r)
    return c


# 列名变体归成标准名：“JZH（检验）”“就诊号”“enct id”这类写法也认（报告里写明认到的是哪一列）
ALIAS = [("JZH", re.compile(r"JZH|就诊号")), ("ENCT_UUID", re.compile(r"ENCTUUID")), ("ENCT_ID", re.compile(r"ENCTID"))]
SHEET_EXT = (".xlsx", ".xlsm", ".csv")


def norm(h: str) -> str:
    h = (h or "").strip()
    u = re.sub(r"[\s_\-（）()【】\[\]:：]", "", h).upper()
    for name, rx in ALIAS:
        if rx.search(u):
            return name
    return h.upper() if h.isascii() else h


def ts(v) -> float | None:
    d = P.to_dt(v)
    return d.timestamp() if d else None


def all_files(root: Path) -> list[Path]:
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(x for x in dns if not x.startswith("."))
        out += [Path(dp) / f for f in sorted(fns) if not f.startswith(("~$", "."))]
    return out


def csv_sheet(f: Path):
    raw = f.read_bytes()
    for enc in ("utf-8-sig", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return
    yield "CSV", csv.reader(io.StringIO(text))


def sheets(files: list[Path]):
    """(文件序号, 文件, 工作表名, 表头, 表头行号, 读取器用的表头, 其余行)。表头：前 10 行里有 JZH 类列名的那一行；没有就取第一行至少 2 格有值的。
    flucase 读取器取第一个非空行当表头，另外返回。"""
    for k, f in enumerate(files, 1):
        for name, rows in (csv_sheet(f) if f.suffix.lower() == ".csv" else S.iter_xlsx(f)):
            it = iter(rows)
            buf = [list(r) for r in itertools.islice(it, 10)]
            texts = [[(S.as_text(v) or "").strip() for v in r] for r in buf]
            i = next((i for i, r in enumerate(texts) if any(v and norm(v) == "JZH" for v in r)), None)
            if i is None:
                i = next((i for i, r in enumerate(texts) if sum(1 for v in r if v) >= 2), None)
            rh = next((r for r in texts if any(r)), [])
            if i is not None:
                yield k, f, name, texts[i], i + 1, rh, itertools.chain(buf[i + 1:], it)


def ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3:
        return None
    ra, rb = ranks(a), ranks(b)
    ma, mb = statistics.fmean(ra), statistics.fmean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else None


def quant(xs: list[float], fmt=lambda v: f"{v:.0f}") -> str:
    if not xs:
        return "—"
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1)))]  # noqa: E731
    return f"p5 {fmt(q(.05))} / p50 {fmt(q(.5))} / p95 {fmt(q(.95))}"


class Col:
    def __init__(self, h: str):
        self.h, self.n, self.vals, self.shapes = h, 0, Counter(), Counter()

    def add(self, s: str | None):
        if not s:
            return
        self.n += 1
        self.vals[s] += 1
        self.shapes["（长文字）" if len(s) > 30 else S.shape(s)] += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--extra", type=Path, nargs="*", default=[], help="不在导出目录里的表（如标注后的名单）")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "flucase" / "backend"))
        from flucase.repo.readers.gd_raw import GdRawReader
        _r = GdRawReader()
        roles_of, role_label = _r.roles_of, _r.role_label
    except Exception:  # noqa: BLE001 —— 没用 flucase 的 venv 时只是少一列
        roles_of = role_label = None

    found = []                                   # (表名, 行数, JZH 非空, 认成, 用途)
    maps: list[tuple[str, list[Col], list[dict]]] = []
    lab_t: dict[str, list[float]] = defaultdict(list)      # JZH → 检验时间（采集，没有用报告）
    lab_c: dict[str, set[float]] = defaultdict(set)        # JZH → 不同的采集时间
    lab_rows = lab_bar_hit = lab_bar_n = 0
    o_t: dict[str, list[float]] = defaultdict(list)        # ENCT_ID → 医嘱开始时间
    e_pid: dict[str, str] = {}
    uuid2e: dict[str, str] = {}
    adm_t: dict[str, float] = {}                           # ENCT_UUID → 入院时间

    files = all_files(a.root) + [f for f in a.extra if f.is_file()]
    missing = [f for f in a.extra if not f.is_file()]
    readable = [f for f in files if f.suffix.lower() in SHEET_EXT]
    now = time.time()
    inv_files = []
    for f in files:
        ext = f.suffix.lower()
        how = "读" if ext in SHEET_EXT else "读不了（.xls 请另存为 .xlsx）" if ext == ".xls" else "不是表格，跳过"
        fid = f"F{readable.index(f) + 1:03d}" if f in readable else "—"
        rel = f.relative_to(a.root).as_posix() if f.is_relative_to(a.root) else "（另给）" + f.name
        inv_files.append(f"| {fid} | {S.render_label(rel, strict=True)} | {ext or '（无）'} | "
                         f"{f.stat().st_size // 1024} KB | {'是' if now - f.stat().st_mtime < 3 * DAY else ''} | {how} |")
    inv_sheets = []
    for k, f, sheet, head, hrow, rhead, rows in sheets(readable):
        ix: dict[str, int] = {}
        for j, h in enumerate(head):
            if h:
                ix.setdefault(norm(h), j)
        g = lambda row, c: S.as_text(row[ix[c]]) if c in ix and ix[c] < len(row) else None  # noqa: E731
        tname = f"F{k:03d}“{S.render_label(sheet, strict=True)}”"
        idc = [h for h in head if h and (norm(h) in ("JZH", "ENCT_ID", "ENCT_UUID") or P.IDLIKE.search(h) or re.search(r"住院|病案|就诊|入院", h))]
        alias = [f"{c} ← “{S.render_label(head[ix[c]])}”" for c in ("JZH", "ENCT_ID", "ENCT_UUID") if c in ix and norm(head[ix[c]]) == c
                 and head[ix[c]].strip().upper() != c]
        inv_sheets.append(f"| {tname} | {hrow} | {sum(1 for h in head if h)} | {'、'.join(S.render_label(h) for h in idc) or '—'} | "
                          f"{'；'.join(alias) or '—'} |")
        is_lab = "JZH" in ix and "名称" in ix and "结果" in ix
        is_order = all(c in ix for c in ("ENCT_ID", "医嘱名称", "开始时间"))
        is_adm = all(c in ix for c in ("ENCT_UUID", "住院号", "入院时间", "主诉", "现病史"))
        is_map = "JZH" in ix and not is_lab and any(c in ix for c in KEYS)
        if not (is_lab or is_order or is_adm or is_map):
            continue
        cols = [Col(h) for h in head] if is_map else []
        recs, n, nj = [], 0, 0
        for row in rows:
            if not any(v is not None and S.as_text(v) for v in row):
                continue
            n += 1
            if is_lab:
                j = cid(g(row, "JZH"))
                if not j:
                    continue
                nj += 1
                lab_rows += 1
                tc = ts(row[ix["采集时间"]]) if "采集时间" in ix and ix["采集时间"] < len(row) else None
                t = tc or (ts(row[ix["报告日期"]]) if "报告日期" in ix and ix["报告日期"] < len(row) else None)
                if t:
                    lab_t[j].append(t)
                if tc:
                    lab_c[j].add(tc)
                bar = cid(g(row, "条码号"))
                if bar:
                    lab_bar_n += 1
                    lab_bar_hit += RAW.get(j, j) in RAW.get(bar, bar)
            if is_order:
                e = cid(g(row, "ENCT_ID"))
                t = ts(row[ix["开始时间"]]) if ix["开始时间"] < len(row) else None
                if e and t:
                    o_t[e].append(t)
                if e and g(row, "住院号"):
                    e_pid.setdefault(e, cid(g(row, "住院号")))
                if e and g(row, "ENCT_UUID"):
                    uuid2e.setdefault(g(row, "ENCT_UUID").strip(), e)
            if is_adm:
                u = (g(row, "ENCT_UUID") or "").strip()
                t = ts(row[ix["入院时间"]]) if ix["入院时间"] < len(row) else None
                if u and t:
                    adm_t[u] = t
            if is_map:
                for j, c in enumerate(cols):
                    c.add(S.as_text(row[j]) if j < len(row) else None)
                r = {c: cid(g(row, c)) for c in ["JZH"] + KEYS if c in ix}
                r["ENCT_UUID"] = (g(row, "ENCT_UUID") or "").strip() if "ENCT_UUID" in ix else ""
                if r.get("JZH"):
                    nj += 1
                    recs.append(r)
        if roles_of:
            rs = roles_of(rhead)
            role = "、".join(role_label(x) for x in rs) or "（认不出）"
            if f.suffix.lower() == ".csv":
                role += "（读取器只读 .xlsx）"
            elif rhead != head:
                role += f"（读取器把第 1 个非空行当表头，不是第 {hrow} 行）"
        else:
            role = "—"
        use = "检验" if is_lab else "对照表候选" if is_map else "医嘱" if is_order else "入院记录"
        if "JZH" in ix:
            found.append((tname, n, nj, role, use))
        if is_map and nj:
            maps.append((tname, cols, recs))

    # ---- 住院：入院时间（入院记录，没有就用最早医嘱）、时间窗（入院 − 1 天 到 最后一条医嘱 + 1 天）
    e_adm: dict[str, float] = {}
    for u, t in adm_t.items():
        if u in uuid2e:
            e_adm[uuid2e[u]] = t
    win: dict[str, tuple[float, float]] = {}
    for e, xs in o_t.items():
        xs.sort()
        s0 = min(e_adm.get(e, xs[0]), xs[0])
        e_adm.setdefault(e, xs[0])
        win[e] = (s0 - DAY, xs[-1] + DAY)
    for j in lab_t:
        lab_t[j].sort()
    pid_encs: dict[str, list[str]] = defaultdict(list)
    for e, p in e_pid.items():
        pid_encs[p].append(e)

    L = ["# JZH 怎么挂到住院（只含计数、列名和遮蔽后的写法）\n", "计数 1–4 写成 <5。\n", "## 0 目录里的文件\n",
         "| 表 | 路径（遮蔽） | 类型 | 大小 | 最近 3 天改过 | 读法 |", "|---|---|---|---|---|---|", *inv_files,
         *([f"\n**--extra 给的文件有 {len(missing)} 个不存在。**"] if missing else []),
         "\n每张表的表头行、列数和像编号的列名（列名变体归成标准名的另外写出）：\n",
         "| 表 | 表头在第几行 | 列数 | 像编号的列 | 归成标准名的列 |", "|---|---|---|---|---|", *inv_sheets, "", "## 1 带 JZH 列的表\n",
         "| 表 | 数据行 | JZH 有值的行 | flucase 读取器认成 | 本脚本当作 |", "|---|---|---|---|---|"]
    L += [f"| {t} | {n} | {nj} | {r} | {u} |" for t, n, nj, r, u in found]
    L.append(f"\n这一套导出：医嘱里的住院 {c5(len(win))} 次、病人 {c5(len(pid_encs))} 位；检验表的 JZH {c5(len(lab_t))} 个、{lab_rows} 行。\n")

    # ---- 对照表各列
    for tname, cols, recs in maps:
        L += [f"### {tname} 的列\n", "| 列 | 列名 | 非空 | 不同值 | 常见写法形状 | 取值（≤12 种、列名与人和编号无关时；严格遮蔽） |", "|---|---|---|---|---|---|"]
        for j, c in enumerate(cols):
            hh = S.render_label(c.h) or "（空）"
            person = bool(P.PERSON.search(c.h or ""))
            shp = "（人名类列，不给）" if person else "、".join(f"`{s}`×{c5(m)}" for s, m in c.shapes.most_common(3)) or "—"
            vals = "—"
            if not person and not P.IDLIKE.search(c.h or "") and 0 < len(c.vals) <= 12 and all(len(v) <= 20 for v in c.vals):
                merged = Counter()
                for v, m in c.vals.items():
                    merged[S.render_label(v, strict=True, keep=KEEP)] += m
                vals = "、".join(f"{v}×{c5(m)}" for v, m in merged.most_common())
            L.append(f"| {j + 1} | {hh} | {c.n} | {c5(len(c.vals))} | {shp} | {vals} |")
        L.append("")

    if not maps:
        L.append("**没有找到对照表**（带 JZH 列、又带 ENCT_ID / ENCT_UUID / 住院号 / 病案号之一、且 JZH 有值的表）。\n")
    recs = [r for _, _, rs in maps for r in rs]

    # ---- 2 对照表：一对一吗
    pairs: set[tuple[str, str]] = set()                     # (JZH, ENCT_ID)
    how = Counter()
    for r in recs:
        e = None
        if r.get("ENCT_ID"):
            e, h = r["ENCT_ID"], "ENCT_ID"
        elif r.get("ENCT_UUID") and r["ENCT_UUID"] in uuid2e:
            e, h = uuid2e[r["ENCT_UUID"]], "ENCT_UUID"
        else:
            p = r.get("住院号") or r.get("病案号")
            if p and len(pid_encs.get(p, [])) == 1:
                e, h = pid_encs[p][0], "住院号（病人只有一次住院）"
            else:
                h = "挂不上住院（没有编号，或病人有多次住院）"
        how[h] += 1
        if e:
            pairs.add((r["JZH"], e))
    j2e, e2j = defaultdict(set), defaultdict(set)
    for j, e in pairs:
        j2e[j].add(e)
        e2j[e].add(j)
    L += ["## 2 对照表：JZH 与住院是不是一对一\n", f"- 对照表 JZH 有值的行 {len(recs)}；按哪一列挂住院：" + "、".join(f"{h} {c5(m)}" for h, m in how.most_common()),
          f"- 不同的 JZH {c5(len(j2e))} 个、住院 {c5(len(e2j))} 次",
          f"- 一个 JZH 对应多次住院：{c5(sum(len(v) > 1 for v in j2e.values()))}；一次住院对应多个 JZH：{c5(sum(len(v) > 1 for v in e2j.values()))}"]
    multi = [p for p, es in pid_encs.items() if len(es) > 1 and sum(e in e2j for e in es) > 1]
    diff = sum(1 for p in multi if len({j for e in pid_encs[p] for j in e2j.get(e, ())}) > 1)
    L.append(f"- 有两次以上住院、且都在对照表里的病人 {c5(len(multi))} 位：各次住院 JZH 不同的 {c5(diff)} 位、相同的 {c5(len(multi) - diff)} 位"
             "（不同 → JZH 是一次住院一个号；相同 → 一个病人一个号）\n")

    # ---- 3 覆盖
    in_exp = sum(1 for e in e2j if e in win)
    lab_in = [j for j in lab_t if j in j2e]
    L += ["## 3 覆盖\n", f"- 对照表的住院在这一套导出里：{c5(in_exp)} / {c5(len(e2j))}；导出里没有出现在对照表的住院 {c5(sum(1 for e in win if e not in e2j))} 次",
          f"- 检验表的 JZH 在对照表里：{c5(len(lab_in))} / {c5(len(lab_t))}，覆盖检验 {sum(len(lab_t[j]) for j in lab_in)} / {sum(len(v) for v in lab_t.values())} 行（有时间的行）",
          f"- 对照表里有、检验表里没有的 JZH {c5(sum(1 for j in j2e if j not in lab_t))} 个\n"]

    # ---- 4 编码规律
    L.append("## 4 JZH 的编码规律\n")
    one = [(j, next(iter(es))) for j, es in j2e.items() if len(es) == 1]
    for name, other in (("ENCT_ID", lambda e: e), ("住院号", lambda e: e_pid.get(e, ""))):
        eq = sub = sup = 0
        pos = Counter()
        dif = Counter()
        n = 0
        for j0, e in one:
            o0 = other(e)
            if not o0:
                continue
            j, o = RAW.get(j0, j0), RAW.get(o0, o0)
            n += 1
            if j == o:
                eq += 1
            elif j in o:
                sub += 1
                i = o.find(j)
                pos[f"长 {len(o)} 位里的第 {i + 1}–{i + len(j)} 位"] += 1
            elif o in j:
                sup += 1
            if j.isdigit() and o.isdigit():
                dif[int(o) - int(j)] += 1
        top = dif.most_common(1)
        tops = f"最常见的差占 {pct(top[0][1], n)}" + (f"（差 = {top[0][0]}）" if top and top[0][1] >= max(5, n // 5) else "") if top else "—"
        L.append(f"- JZH 与 {name}（{c5(n)} 对）：相等 {c5(eq)}、JZH 是 {name} 的一段 {c5(sub)}"
                 + (f"（{'、'.join(f'{p}×{c5(m)}' for p, m in pos.most_common(3))}）" if pos else "")
                 + f"、{name} 是 JZH 的一段 {c5(sup)}；数值差 {name} − JZH 有 {c5(len(dif))} 种，{tops}")
    L.append(f"- 检验表里条码号含 JZH 的行：{lab_bar_hit} / {lab_bar_n}")
    lens = Counter(len(RAW.get(j, j)) for j in j2e)
    L.append("- JZH 位数：" + "、".join(f"{k} 位×{c5(m)}" for k, m in sorted(lens.items())))
    seq = sorted(((e_adm[e], int(j), int(e) if e.isdigit() else None) for j, e in one if e in e_adm and j.isdigit()))
    if len(seq) >= 3:
        rho = spearman([x[0] for x in seq], [x[1] for x in seq])
        rho_e = spearman([x[0] for x in seq if x[2] is not None], [x[2] for x in seq if x[2] is not None])
        up = sum(1 for x, y in zip(seq, seq[1:]) if y[1] > x[1])
        span = (seq[-1][0] - seq[0][0]) / DAY
        slope = (statistics.median([x[1] for x in seq[-max(1, len(seq) // 10):]]) - statistics.median([x[1] for x in seq[:max(1, len(seq) // 10)]])) / max(span * 0.9, 1)
        yr2 = sum(1 for t, j, _ in seq if str(j)[:2] == dt.datetime.fromtimestamp(t).strftime("%y"))
        L += [f"- 按入院时间排序（{c5(len(seq))} 次住院）：JZH 与入院时间的等级相关 {rho:.3f}；ENCT_ID 与入院时间 {rho_e:.3f}" if rho is not None and rho_e is not None
              else f"- 按入院时间排序（{c5(len(seq))} 次住院）：等级相关算不出",
              f"- 相邻两次住院（按入院时间）JZH 变大的比例 {pct(up, len(seq) - 1)}；入院时间跨度 {span:.0f} 天，JZH 大约每天增加 {slope:.0f}",
              f"- JZH 前 2 位等于入院年份后 2 位的 {c5(yr2)} / {c5(len(seq))}",
              "\n读法：等级相关接近 1、相邻变大的比例接近 100%、每天增加数和全院每天的就诊量相当 → JZH 是全院按就诊先后发的流水号，"
              "和病案号、ENCT_ID 没有算术关系，只能靠对照表或病历系统里的字段挂；前 2 位等于年份 → 号里带年份。"]
    L.append("")

    # ---- 5 时间核对
    inn = before = after = 0
    allin = most = few = 0
    first_h = []
    for j in lab_in:
        e = next(iter(j2e[j])) if len(j2e[j]) == 1 else None
        if e is None or e not in win:
            continue
        s0, s1 = win[e]
        xs = lab_t[j]
        k_in = bisect.bisect_right(xs, s1) - bisect.bisect_left(xs, s0)
        k_b = bisect.bisect_left(xs, s0)
        inn, before, after = inn + k_in, before + k_b, after + len(xs) - k_in - k_b
        fr = k_in / len(xs) if xs else 0
        allin += fr == 1
        most += 0.9 <= fr < 1
        few += fr < 0.5
        if xs and e in e_adm:
            first_h.append((xs[0] - e_adm[e]) / 3600)
    tot = inn + before + after
    L += ["## 5 按对照表挂上的检验：时间对得上吗\n", "住院时间窗 = 入院前 1 天 到 最后一条医嘱后 1 天。\n",
          f"- 检验行：在窗内 {inn}（{pct(inn, tot)}）、早于窗 {before}、晚于窗 {after}",
          f"- 按 JZH：全部在窗内 {c5(allin)}、90% 以上 {c5(most)}、不到一半 {c5(few)}（不到一半的多半是对照写错，或 JZH 不是这次住院的）",
          f"- 每个 JZH 第一条检验距入院（小时）：{quant(first_h)}\n"]

    # ---- 6 不用对照表
    encs = list(win)
    uniq = mult = none = 0
    u_ok = u_bad = u_unk = 0
    r_ok = r_bad = r_unk = amb = 0
    sc_true, sc_other = [], []
    for j, xs in lab_t.items():
        if not xs:
            continue
        cand = []
        for e in encs:
            s0, s1 = win[e]
            k_in = bisect.bisect_right(xs, s1) - bisect.bisect_left(xs, s0)
            if k_in / len(xs) >= 0.9:
                cand.append(e)
        truth = next(iter(j2e[j])) if len(j2e.get(j, ())) == 1 else None
        if not cand:
            none += 1
            continue
        if len(cand) == 1:
            uniq += 1
            pick = cand[0]
            if truth is None:
                u_unk += 1
            elif pick == truth:
                u_ok += 1
            else:
                u_bad += 1
            continue
        mult += 1
        cs = sorted(lab_c.get(j, ()))
        scores = []
        for e in cand:
            ot = o_t[e]
            hit = sum(1 for t in cs if bisect.bisect_right(ot, t + 1800) > bisect.bisect_left(ot, t - 12 * 3600))
            scores.append((hit / len(cs) if cs else 0, e))
            if truth is not None:
                (sc_true if e == truth else sc_other).append(scores[-1][0])
        scores.sort(reverse=True)
        if len(scores) > 1 and scores[0][0] - scores[1][0] < 0.1:
            amb += 1
            continue
        pick = scores[0][1]
        if truth is None:
            r_unk += 1
        elif pick == truth:
            r_ok += 1
        else:
            r_bad += 1
    L += ["## 6 不用对照表，能不能推出 JZH 属于哪次住院\n",
          "第一步：JZH 的检验时间有 90% 以上落在某次住院的时间窗里，算候选；第二步（候选不止一次住院时）：看检验采集时间前 12 小时到后半小时内"
          "有没有这次住院的医嘱开始，吻合比例最高、且比第二名高 0.1 以上的算推出。\n",
          f"- 检验表的 JZH {c5(len(lab_t))} 个：只落在一次住院 {c5(uniq)}、落在多次住院 {c5(mult)}、一次都没落上 {c5(none)}",
          f"- 只落在一次住院的：与对照表一致 {c5(u_ok)}、不一致 {c5(u_bad)}、对照表里没有 {c5(u_unk)}",
          f"- 落在多次住院的：按医嘱吻合推出后与对照表一致 {c5(r_ok)}、不一致 {c5(r_bad)}、对照表里没有 {c5(r_unk)}、分不出 {c5(amb)}",
          f"- 医嘱吻合比例：对照表认定的那次住院 {quant(sc_true, lambda v: f'{v:.2f}')}；其他候选住院 {quant(sc_other, lambda v: f'{v:.2f}')}",
          f"- 合计不用对照表推出且与对照表一致：{c5(u_ok + r_ok)} / {c5(len(lab_in))}（对照表里有的 JZH）\n"]
    rep = "\n".join(L)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
    print(rep)


if __name__ == "__main__":
    main()
