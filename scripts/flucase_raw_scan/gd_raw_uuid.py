#!/usr/bin/env python3
"""ENCT_ID 与 ENCT_UUID 能不能互相推算。只输出计数和按段描述的写法（每段是数字 / 十六进制 / 字母数字、几位），
不输出编号和病例内容；按住院分类的计数 1–4 写成 "<5"。

取同时有 ENCT_ID、ENCT_UUID 的表（入院记录、标注名单等；医嘱、体征、检验这类大表跳过），逐对看：
1. 写法：长度、大小写、分隔符切开后每段的长度、每段是不是十六进制；有没有标准 UUID（8-4-4-4-12）及其版本号；
2. ENCT_UUID 里有没有原样带着 ENCT_ID / 住院号 / JZH / 入院日期（也试 ENCT_ID 倒序、ENCT_ID 的十六进制）；
3. ENCT_UUID 里有没有这些编号（及 住院号+住院次数）的 MD5 / SHA-1 / SHA-256（前 16 位即算），或标准的名字型 UUID（v3 / v5）；
4. 版本 1 的 UUID 带生成时间：和入院时间差多少；
5. 每段（十六进制数值）的大小顺序与 ENCT_ID、入院时间的顺序是否一致。

用法：python gd_raw_uuid.py <原始导出目录> [--out 报告.md]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import uuid
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gd_raw_jzh as J  # noqa: E402

c5, pct, cid, RAW = J.c5, J.pct, J.cid, J.RAW
STD = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-([0-9a-f])[0-9a-f]{3}-([0-9a-f])[0-9a-f]{3}-[0-9a-f]{12}")
SEP = re.compile(r"[-_|:.{}\s]")
BIG = ("医嘱名称", "项目编码", "结果")


def seg_desc(u: str) -> str:
    """按分隔符切开，每段只写类别和位数（不逐字给形状：随机串逐字的数字 / 字母分布本身就近乎是这个编号）。"""
    parts = []
    for x in SEP.split(u):
        cls = "数字" if x.isdigit() else "十六进制" if re.fullmatch(r"[0-9a-fA-F]+", x) else "字母数字" if x.isalnum() else "其他"
        parts.append(f"{cls}{len(x)}")
    seps = "".join(dict.fromkeys(SEP.findall(u)))
    return " + ".join(parts) + (f"（分隔符 {seps}）" if seps else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    enc: dict[str, dict] = {}
    used = []
    files = [f for f in J.all_files(a.root) if f.suffix.lower() in J.SHEET_EXT]
    for k, f, sheet, head, hrow, _rh, rows in J.sheets(files):
        ix: dict[str, int] = {}
        for j, h in enumerate(head):
            if h:
                ix.setdefault(J.norm(h), j)
        if not ("ENCT_ID" in ix and "ENCT_UUID" in ix) or any(b in ix for b in BIG):
            continue
        g = lambda row, c: J.S.as_text(row[ix[c]]) if c in ix and ix[c] < len(row) else None  # noqa: E731
        n = 0
        for row in rows:
            e, u = cid(g(row, "ENCT_ID")), (g(row, "ENCT_UUID") or "").strip()
            if not e or not u:
                continue
            n += 1
            d = enc.setdefault(e, {"u": set()})
            d["u"].add(u)
            for key, col in (("p", "住院号"), ("j", "JZH"), ("n", "住院次数")):
                if g(row, col) and key not in d:
                    d[key] = cid(g(row, col))
            t = J.P.to_dt(row[ix["入院时间"]]) if "入院时间" in ix and ix["入院时间"] < len(row) else None
            if t and "t" not in d:
                d["t"] = t
        used.append(f"{J.S.render_label(sheet, strict=True)}（F{k:03d}，{n} 行）")

    u2e: dict[str, set] = {}
    for e, d in enc.items():
        for u in d["u"]:
            u2e.setdefault(u, set()).add(e)
    one = {e: next(iter(d["u"])) for e, d in enc.items() if len(d["u"]) == 1}
    L = ["# ENCT_ID 与 ENCT_UUID 能不能互相推算（只含计数和遮蔽后的写法）\n", "计数 1–4 写成 <5；写法只按段给类别和位数。\n",
         "用到的表：" + ("、".join(used) or "（没有同时带 ENCT_ID 和 ENCT_UUID 的表）") + "\n", "## 1 对应关系与写法\n",
         f"- 住院（ENCT_ID）{c5(len(enc))} 个、ENCT_UUID {c5(len(u2e))} 个；一个 ENCT_ID 对多个 UUID：{c5(sum(len(d['u']) > 1 for d in enc.values()))}；"
         f"一个 UUID 对多个 ENCT_ID：{c5(sum(len(v) > 1 for v in u2e.values()))}"]
    us = list(one.values())
    L.append("- 长度：" + "、".join(f"{k} 位×{c5(m)}" for k, m in sorted(Counter(len(u) for u in us).items())))
    L.append(f"- 大小写：含大写字母 {c5(sum(any(c.isupper() for c in u) for u in us))}、含小写字母 {c5(sum(any(c.islower() for c in u) for u in us))}")
    segs = Counter(seg_desc(u) for u in us)
    L.append("- 按段的写法（≥5 个的前 3 种）：" + ("、".join(f"{s_}×{m}" for s_, m in segs.most_common(3) if m >= 5) or "—")
             + f"；不到 5 个的写法 {sum(m for m in segs.values() if m < 5)} 个")
    std = Counter()
    for u in us:
        m = STD.search(u.lower())
        std[(m.group(1), m.group(2)) if m else None] += 1
    L.append("- 含标准 UUID（8-4-4-4-12）：" + ("、".join(f"版本 {v}、变体位 {w}×{c5(m)}" for (v, w), m in
                                                 sorted(((k, m) for k, m in std.items() if k), key=lambda x: -x[1])) or "没有")
             + f"；不含的 {c5(std[None])}（版本 4 = 随机生成，推不出；版本 1 = 带时间；版本 3 / 5 = 由名字算出）\n")

    # ---- 2 原样包含
    L.append("## 2 ENCT_UUID 里有没有原样带着别的编号\n")
    tests = {
        "ENCT_ID": lambda e, d: [RAW.get(e, e)],
        "ENCT_ID 倒序": lambda e, d: [RAW.get(e, e)[::-1]],
        "ENCT_ID 的十六进制": lambda e, d: [format(int(e), "x")] if e.isdigit() else [],
        "住院号": lambda e, d: [RAW.get(d["p"], d["p"])] if d.get("p") else [],
        "JZH": lambda e, d: [RAW.get(d["j"], d["j"])] if d.get("j") else [],
        "入院日期": lambda e, d: [d["t"].strftime("%Y%m%d"), d["t"].strftime("%y%m%d"), d["t"].strftime("%Y-%m-%d")] if d.get("t") else [],
    }
    for name, fn in tests.items():
        n = hit = 0
        pos = Counter()
        for e, u in one.items():
            cands = [c for c in fn(e, enc[e]) if c and len(c) >= 4]
            if not cands:
                continue
            n += 1
            ul, flat = u.lower(), SEP.sub("", u.lower())
            for c in cands:
                c = c.lower()
                if c in ul or c in flat:
                    hit += 1
                    i = ul.find(c)
                    pos[f"第 {i + 1}–{i + len(c)} 位" if i >= 0 else "去掉分隔符后"] += 1
                    break
        L.append(f"- {name}：{c5(hit)} / {c5(n)}" + (f"（{'、'.join(f'{p}×{c5(m)}' for p, m in pos.most_common(3))}）" if pos else ""))
    L.append("")

    # ---- 3 哈希 / 名字型 UUID
    L.append("## 3 ENCT_UUID 是不是由编号算出来的（哈希、名字型 UUID）\n")
    nss = {"DNS": uuid.NAMESPACE_DNS, "URL": uuid.NAMESPACE_URL, "OID": uuid.NAMESPACE_OID, "X500": uuid.NAMESPACE_X500}

    def keys(e, d):
        out = {"ENCT_ID": RAW.get(e, e)}
        if d.get("p"):
            p = RAW.get(d["p"], d["p"])
            out["住院号"] = p
            if d.get("n"):
                n = RAW.get(d["n"], d["n"])
                for sep in ("", "_", "-"):
                    out[f"住院号{sep or '直接'}接住院次数"] = f"{p}{sep}{n}"
        if d.get("j"):
            out["JZH"] = RAW.get(d["j"], d["j"])
        return out
    hits: Counter = Counter()
    tried: Counter = Counter()
    for e, u in one.items():
        ul, flat = u.lower(), SEP.sub("", u.lower())
        for kn, kv in keys(e, enc[e]).items():
            for an in ("md5", "sha1", "sha256"):
                tried[f"{kn} 的 {an.upper()}"] += 1
                h = hashlib.new(an, kv.encode()).hexdigest()
                if h[:16] in flat:
                    hits[f"{kn} 的 {an.upper()}"] += 1
            for nn, ns in nss.items():
                for ver, fn in (("v3", uuid.uuid3), ("v5", uuid.uuid5)):
                    tried[f"{kn} 的 {ver}（{nn}）"] += 1
                    if fn(ns, kv).hex[:16] in flat:
                        hits[f"{kn} 的 {ver}（{nn}）"] += 1
    L.append(f"- 试了 {len(tried)} 种算法 × 编号组合；对上的：" + ("、".join(f"{k} {c5(m)} / {c5(tried[k])}" for k, m in hits.most_common()) or "没有") + "\n")

    # ---- 4 版本 1 的时间
    diffs = []
    for e, u in one.items():
        m = STD.search(u.lower())
        if m and m.group(1) == "1" and enc[e].get("t"):
            ut = uuid.UUID(m.group(0))
            sec = (ut.time - 0x01B21DD213814000) / 1e7
            diffs.append((sec - enc[e]["t"].timestamp()) / 3600)
    L.append("## 4 版本 1 UUID 里的生成时间 − 入院时间（小时）\n")
    L.append(f"- {c5(len(diffs))} 个：{J.quant(diffs)}\n" if diffs else "- 没有版本 1 的 UUID，或没有入院时间\n")

    # ---- 5 顺序
    L.append("## 5 各段的大小顺序和 ENCT_ID、入院时间是否一致（等级相关，接近 1 = 一致）\n")
    rows = [(int(e), enc[e].get("t"), SEP.split(u)) for e, u in one.items() if e.isdigit()]
    width = max((len(s) for _, _, s in rows), default=0)
    for i in range(width):
        xs = [(n_, t, s[i]) for n_, t, s in rows if i < len(s) and s[i] and re.fullmatch(r"[0-9a-fA-F]+", s[i])]
        if len(xs) < max(5, len(rows) // 2):
            continue
        r_e = J.spearman([x[0] for x in xs], [int(x[2], 16) for x in xs])
        tx = [x for x in xs if x[1]]
        r_t = J.spearman([x[1].timestamp() for x in tx], [int(x[2], 16) for x in tx]) if len(tx) >= 3 else None
        L.append(f"- 第 {i + 1} 段（{c5(len(xs))} 个十六进制值）：与 ENCT_ID {r_e:.3f}" if r_e is not None else f"- 第 {i + 1} 段：算不出")
        if r_t is not None:
            L[-1] += f"、与入院时间 {r_t:.3f}"
    L.append("\n读法：第 2、3 节都没对上、标准 UUID 是版本 4、第 5 节接近 0 → ENCT_UUID 是随机生成的，和 ENCT_ID 推算不了，只能靠同时带两列的表"
             "（入院记录、医嘱）对照；有对上的再看是哪一种。")
    rep = "\n".join(L)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
    print(rep)


if __name__ == "__main__":
    main()
