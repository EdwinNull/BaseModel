#!/usr/bin/env python3
"""GD 原始导出的名称清单（项目目录），研究者 2026-10-18 同意给 Claude，用来写对应表。

只列医院的项目目录，不列病例：体征项目、检验名称、医嘱名称、科室、检查类别与项目、查房类型、操作名称、诊断编码与名称。
每个名称附出现的行数、住院数和取值的聚合量（数值的 p1 / p50 / p99、单位、标本）。

安全规则：
- 只列在 ≥5 次住院里出现的名称；
- 名称里有 ≥6 位连续数字，或有人称、联系方式一类的词（主任、医生、家属、电话……），整条不列，只计数；
- 长于 60 字的不列，只计数；
- 不列任何姓名、编号、时间、正文。

用法：python gd_raw_vocab.py <原始导出目录> --out <清单.md>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gd_raw_scan as S  # noqa: E402

K = 5
PERSON = re.compile(r"主任|医生|医师|教授|护士|护师|家属|患者|病人|先生|女士|老师|同志|签字|签名|电话|手机|身份证|住址|地址")
LONG_DIGITS = re.compile(r"\d{6,}")
NUM = re.compile(r"^\s*[<>＜＞≤≥]?=?\s*([-+]?\d+(?:\.\d+)?)\s*$")


def num(s):
    m = NUM.match(s or "")
    return float(m.group(1)) if m else None


def quant(xs):
    if not xs:
        return "—"
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1)))]  # noqa: E731
    return f"{q(.01):g} / {q(.5):g} / {q(.99):g}"


class Dropped:
    def __init__(self):
        self.n = Counter()

    def ok(self, kind: str, name: str | None) -> bool:
        if not name:
            return False
        if len(name) > 60:
            self.n[(kind, "长于 60 字")] += 1
            return False
        if LONG_DIGITS.search(name):
            self.n[(kind, "含 ≥6 位数字")] += 1
            return False
        if PERSON.search(name):
            self.n[(kind, "含人称或联系方式")] += 1
            return False
        return True


def top(c: Counter, n=3, k=K) -> str:
    items = [(v, x) for v, x in c.most_common() if x >= k]
    rest = len(c) - len(items[:n])
    return "、".join(f"{v}×{x}" for v, x in items[:n]) + (f"（另 {rest} 种）" if rest > 0 else "") if items else "—"


def cell(v):
    return S.as_text(v)


def sheets(root: Path):
    from openpyxl import load_workbook
    files = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if not d.startswith("."))
        files += [Path(dp) / f for f in sorted(fns) if not f.startswith((".", "~$"))]
    for f in files:
        kind = S.sniff(f)
        try:
            if kind == "xlsx":
                wb = load_workbook(f, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    ws.reset_dimensions()
                    yield ws.iter_rows(values_only=True)
            elif kind == "xls":
                for _, rows in S.iter_xls(f):
                    yield rows
        except Exception as e:  # noqa: BLE001
            print(f"读不了一个文件：{type(e).__name__}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    drop = Dropped()
    vit = defaultdict(lambda: {"enc": set(), "rows": 0, "u": Counter(), "cols": defaultdict(lambda: {"n": 0, "num": [], "txt": Counter()})})
    lab = defaultdict(lambda: {"enc": set(), "rows": 0, "u": Counter(), "sp": Counter(), "num": [], "txt": Counter()})
    ords = defaultdict(lambda: {"enc": set(), "rows": 0, "t": Counter(), "use": Counter(), "out": Counter(), "stop": 0, "freq": Counter()})
    dept = defaultdict(set)
    img = defaultdict(set)
    rounds = defaultdict(set)
    ops = defaultdict(set)
    dx = defaultdict(lambda: {"enc": set(), "names": Counter(), "src": Counter()})
    for rows in sheets(a.root.resolve()):
        it = iter(rows)
        head = []
        for r in it:
            head.append(list(r))
            if len(head) >= 15:
                break
        h = S.pick_header(head)
        if h is None:
            continue
        hdr = [(cell(v) or "").strip() for v in head[h]]
        ix = {x: j for j, x in enumerate(hdr) if x}
        hs = set(ix)

        def rows_after():
            for r in head[h + 1:]:
                yield list(r)
            for r in it:
                yield list(r)

        def g(r, col):
            j = ix.get(col)
            return cell(r[j]) if j is not None and j < len(r) else None

        enc_col = next((c for c in ("ENCT_ID", "ENCT_UUID", "enct_uuid", "JZH", "病案号", "住院号") if c in ix), None)
        for r in rows_after():
            enc = g(r, enc_col) if enc_col else None
            if not enc:
                continue
            if "项目" in hs and "值1" in hs:                                     # 生命体征
                name = f"{g(r, '项目编码') or ''} | {g(r, '项目') or ''}"
                d = vit[name]
                d["enc"].add(enc)
                d["rows"] += 1
                d["u"][g(r, "单位") or "（空）"] += 1
                for k in ("值1", "值2", "值3", "值4", "值5"):
                    v = g(r, k)
                    if v:
                        c = d["cols"][k]
                        c["n"] += 1
                        x = num(v)
                        if x is not None:
                            if len(c["num"]) < 20000:
                                c["num"].append(x)
                        elif len(c["txt"]) <= 30:
                            c["txt"][v] += 1
            elif "名称" in hs and "结果" in hs:                                   # 检验
                d = lab[g(r, "名称") or ""]
                d["enc"].add(enc)
                d["rows"] += 1
                d["u"][g(r, "结果单位") or "（空）"] += 1
                d["sp"][g(r, "标本类型") or "（空）"] += 1
                v = g(r, "结果")
                x = num(v)
                if x is not None:
                    if len(d["num"]) < 20000:
                        d["num"].append(x)
                elif v and len(d["txt"]) <= 30:
                    d["txt"][v] += 1
            elif "医嘱名称" in hs:                                               # 医嘱
                d = ords[(g(r, "医嘱名称") or "", g(r, "通用名") or "")]
                d["enc"].add(enc)
                d["rows"] += 1
                d["t"][g(r, "医嘱类型") or "（空）"] += 1
                d["use"][g(r, "用法") or "（空）"] += 1
                d["freq"][g(r, "频次名称") or "（空）"] += 1
                d["out"][g(r, "普通或出院") or "（空）"] += 1
                d["stop"] += bool(g(r, "停止时间"))
                if g(r, "科室"):
                    dept[("医嘱科室", g(r, "科室"))].add(enc)
            elif "影像所见" in hs or "影像诊断" in hs:                            # 检查
                img[(g(r, "类别") or "（空）", g(r, "项目") or "（空）")].add(enc)
            if "查房类型" in hs and g(r, "查房类型"):
                rounds[g(r, "查房类型")].add(enc)
            if "操作名称" in hs and g(r, "操作名称"):
                ops[("操作", g(r, "操作名称"))].add(enc)
            if "手术名称" in hs and g(r, "手术名称"):
                ops[("手术", g(r, "手术名称"))].add(enc)
            for c in ("入院科室", "出院科室", "入院科别", "出院科别", "当前科室"):
                if g(r, c):
                    dept[(c, g(r, c))].add(enc)
            # 诊断编码与名称：同一行里“…编码 / …名称”或“…ICD码 / …疾病名称”成对的列，按逗号切开后逐个配对
            for code_col in [c for c in hs if c.endswith("编码") or c.endswith("ICD码")]:
                if "中医" in code_col:
                    continue
                name_col = (code_col[:-2] + "名称") if code_col.endswith("编码") else code_col.replace("ICD码", "疾病名称")
                if code_col == "ICD码":
                    name_col = "疾病名称"
                if name_col not in ix:
                    continue
                codes = [x.strip() for x in re.split(r"[,，;；]", g(r, code_col) or "") if x.strip()]
                names = [x.strip() for x in re.split(r"[,，;；]", g(r, name_col) or "") if x.strip()]
                if not codes or len(codes) != len(names):
                    continue
                for c_, n_ in zip(codes, names):
                    d = dx[c_.upper()]
                    d["enc"].add(enc)
                    d["names"][n_] += 1
                    d["src"][code_col] += 1

    L = []
    w = L.append
    w("# GD 原始导出名称清单（只含项目目录与聚合量）\n")
    w(f"只列 ≥{K} 次住院出现的名称；含 ≥6 位数字、人称或联系方式、长于 60 字的名称不列（计数见文末）。数值写 p1 / p50 / p99。\n")
    w("## 1 生命体征项目（项目编码 | 项目）\n")
    w("| 项目编码 \\| 项目 | 行数 | 住院数 | 单位 | 值1：有值 / 数字分布 / 文字取值 | 值2 | 值3 | 值4 | 值5 |")
    w("|---|---|---|---|---|---|---|---|---|")
    for name, d in sorted(vit.items(), key=lambda x: -x[1]["rows"]):
        if len(d["enc"]) < K or not drop.ok("体征", name):
            continue
        cols = []
        for k in ("值1", "值2", "值3", "值4", "值5"):
            c = d["cols"].get(k)
            if not c:
                cols.append("—")
                continue
            txt = top(Counter({v: n for v, n in c["txt"].items() if drop.ok("体征取值", v)}), 4) if c["txt"] else ""
            cols.append(f"{100 * c['n'] / d['rows']:.0f}% / {quant(c['num'])}" + (f" / {txt}" if txt and txt != "—" else ""))
        w(f"| {name} | {d['rows']} | {len(d['enc'])} | {top(d['u'], 3, 1)} | " + " | ".join(cols) + " |")
    w("\n## 2 检验名称\n")
    w("| 名称 | 行数 | 住院数（按 JZH） | 标本 | 单位 | 数字结果分布 | 文字结果 |")
    w("|---|---|---|---|---|---|---|")
    for name, d in sorted(lab.items(), key=lambda x: -x[1]["rows"]):
        if len(d["enc"]) < K or not drop.ok("检验", name):
            continue
        txt = Counter({v: n for v, n in d["txt"].items() if drop.ok("检验取值", v)})
        w(f"| {name} | {d['rows']} | {len(d['enc'])} | {top(d['sp'], 3, 1)} | {top(d['u'], 3, 1)} | {quant(d['num'])} | {top(txt, 4)} |")
    w("\n## 3 医嘱名称（医嘱名称 | 通用名）\n")
    w("| 医嘱名称 | 通用名 | 行数 | 住院数 | 医嘱类型 | 用法 | 频次 | 普通或出院 | 有停止时间 |")
    w("|---|---|---|---|---|---|---|---|---|")
    for (n1, n2), d in sorted(ords.items(), key=lambda x: (-len(x[1]["enc"]), x[0])):
        if len(d["enc"]) < K or not drop.ok("医嘱", n1) or (n2 and not drop.ok("医嘱", n2)):
            continue
        w(f"| {n1} | {n2 or '—'} | {d['rows']} | {len(d['enc'])} | {top(d['t'], 2, 1)} | {top(d['use'], 2, 1)} | {top(d['freq'], 2, 1)} | "
          f"{top(d['out'], 2, 1)} | {100 * d['stop'] / d['rows']:.0f}% |")
    w("\n## 4 科室\n")
    w("| 出处 | 科室 | 住院数 |")
    w("|---|---|---|")
    for (src, name), encs in sorted(dept.items(), key=lambda x: (x[0][0], -len(x[1]))):
        if len(encs) >= K and drop.ok("科室", name):
            w(f"| {src} | {name} | {len(encs)} |")
    w("\n## 5 检查类别与项目\n")
    w("| 类别 | 项目 | 住院数 |")
    w("|---|---|---|")
    for (c, n), encs in sorted(img.items(), key=lambda x: -len(x[1])):
        if len(encs) >= K and drop.ok("检查", c) and drop.ok("检查", n):
            w(f"| {c} | {n} | {len(encs)} |")
    w("\n## 6 查房类型、有创操作、手术名称\n")
    for name, encs in sorted(rounds.items(), key=lambda x: -len(x[1])):
        if len(encs) >= K and drop.ok("查房类型", name):
            w(f"- 查房类型：{name}（{len(encs)} 次住院）")
    for (k, name), encs in sorted(ops.items(), key=lambda x: -len(x[1])):
        if len(encs) >= K and drop.ok(k, name):
            w(f"- {k}：{name}（{len(encs)} 次住院）")
    w("\n## 7 诊断编码与名称（西医；同一列表里编码与名称个数相同时逐个配对）\n")
    w("| 编码 | 名称（最常见的 2 种） | 住院数 | 出处 |")
    w("|---|---|---|---|")
    for code, d in sorted(dx.items()):
        if len(d["enc"]) < K or not drop.ok("诊断", code):
            continue
        names = [(n, c) for n, c in d["names"].most_common() if drop.ok("诊断名称", n)][:2]
        w(f"| {code} | {'；'.join(f'{n}×{c}' for n, c in names)} | {len(d['enc'])} | {'、'.join(s for s, _ in d['src'].most_common(3))} |")
    w("\n## 8 没列出来的名称（计数）\n")
    for (k, why), n in sorted(drop.n.items()):
        w(f"- {k}：{why} {n} 个")
    rep = "\n".join(L)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
        print(f"清单已写到 {a.out}", file=sys.stderr)
    print(rep)


if __name__ == "__main__":
    main()
