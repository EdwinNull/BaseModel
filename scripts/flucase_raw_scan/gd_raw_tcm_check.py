#!/usr/bin/env python3
"""核对 GD 原始导出里的中医诊断编码是不是《中医病证分类与代码》（修订版，国中医药医政发〔2020〕3号；与 GB/T 15657-2021
同一套编码体系）。只输出计数和编码目录（≥5 次住院出现的编码与名称），不输出病例内容。

做法：从官方附件 docx 读出全部疾病码（A 开头）、证候码（B 开头）及正名、异名；再读原始导出里所有“…中医…码 / …编码”列和
对应的名称列，逐个看：编码在不在官方表里（原样、或去掉末尾的点）、名称是不是这个编码的正名或异名。

用法：python gd_raw_tcm_check.py <原始导出目录> <官方 docx> [--out 报告.md]
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
CODE = re.compile(r"^[AB]\d{2}(\.\d{2})*\.?$")


def official(docx_path: Path) -> dict[str, list[str]]:
    import docx
    d = docx.Document(str(docx_path))
    out: dict[str, list[str]] = {}
    for t in d.tables:
        for r in t.rows:
            cells = [c.text.strip() for c in r.cells]
            for j, c in enumerate(cells[:-1]):
                if CODE.match(c):
                    names = [x.strip() for x in cells[j + 1].splitlines() if x.strip()]
                    out.setdefault(c, names)
    return out


def split(s: str | None) -> list[str]:
    return [x.strip() for x in re.split(r"[,，¤;；]", s or "") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("docx", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    off = official(a.docx)
    off_nodot = {k.rstrip("."): k for k in off}
    from openpyxl import load_workbook
    stats: dict[str, Counter] = defaultdict(Counter)
    seen: dict[tuple[str, str], set] = defaultdict(set)          # (编码, 名称) → 住院
    bad: dict[tuple[str, str, str], set] = defaultdict(set)      # (列, 编码, 名称) → 住院
    files = []
    for dp, dns, fns in os.walk(a.root):
        dns[:] = sorted(x for x in dns if not x.startswith("."))
        files += [Path(dp) / f for f in sorted(fns) if f.lower().endswith(".xlsx") and not f.startswith(("~$", "."))]
    for f in files:
        wb = load_workbook(f, read_only=True, data_only=True)
        for ws in wb.worksheets:
            ws.reset_dimensions()
            it = ws.iter_rows(values_only=True)
            head = next(it, None)
            if not head:
                continue
            hdr = [(S.as_text(v) or "").strip() for v in head]
            pairs = []
            for j, h in enumerate(hdr):
                if "中医" in h and (h.endswith("码") or h.endswith("编码")):
                    nm = h[:-2] + "名称" if h.endswith("编码") else h[:-1] + "疾病名称"
                    nm = nm if nm in hdr else next((x for x in hdr if x.startswith(h.replace("编码", "").replace("码", "")) and x.endswith("名称")), None)
                    pairs.append((h, j, hdr.index(nm) if nm in hdr else None))
            if not pairs:
                continue
            key_j = next((hdr.index(c) for c in ("ENCT_ID", "ENCT_UUID", "病案号", "住院号") if c in hdr), None)
            for row in it:
                enc = S.as_text(row[key_j]) if key_j is not None and key_j < len(row) else None
                for h, j, nj in pairs:
                    codes = split(S.as_text(row[j]) if j < len(row) else None)
                    names = split(S.as_text(row[nj]) if nj is not None and nj < len(row) else None)
                    if len(names) != len(codes):
                        stats[h]["名称个数对不上的行"] += 1
                        names = [None] * len(codes)
                    for c, n in zip(codes, names):
                        stats[h]["编码"] += 1
                        hit = c if c in off else off_nodot.get(c.rstrip("."))
                        if hit is None:
                            stats[h]["不在官方表里"] += 1
                            bad[(h, c, n or "")].add(enc)
                            continue
                        stats[h]["在官方表里" + ("（原样）" if hit == c else "（末尾的点不同）")] += 1
                        if n is None:
                            continue
                        if n in off[hit]:
                            stats[h]["名称是正名或异名"] += 1
                        else:
                            stats[h]["名称不是这个码的正名或异名"] += 1
                            bad[(h, c, n)].add(enc)
                        seen[(c, n)].add(enc)
        wb.close()
    L = ["# GD 原始导出的中医编码核对（只含计数和编码目录）\n",
         f"官方表：疾病码 {sum(k.startswith('A') for k in off)} 个、证候码 {sum(k.startswith('B') for k in off)} 个。\n",
         "| 列 | 编码个数 | 在官方表里（原样） | 在官方表里（末尾的点不同） | 不在官方表里 | 名称是正名或异名 | 名称不对 | 名称个数对不上的行 |",
         "|---|---|---|---|---|---|---|---|"]
    for h, c in stats.items():
        L.append(f"| {h} | {c['编码']} | {c['在官方表里（原样）']} | {c['在官方表里（末尾的点不同）']} | {c['不在官方表里']} | {c['名称是正名或异名']} | "
                 f"{c['名称不是这个码的正名或异名']} | {c['名称个数对不上的行']} |")
    L.append("\n## 对不上的编码与名称（≥5 次住院出现的；更少的只计数）\n")
    L.append("| 列 | 编码 | 数据里的名称 | 官方表里这个码的名称 | 住院数 |")
    L.append("|---|---|---|---|---|")
    small = 0
    for (h, c, n), encs in sorted(bad.items(), key=lambda x: -len(x[1])):
        if len(encs) < K:
            small += 1
            continue
        hit = c if c in off else off_nodot.get(c.rstrip("."))
        L.append(f"| {h} | {c} | {n or '—'} | {'、'.join(off[hit][:3]) if hit else '（无此码）'} | {len(encs)} |")
    L.append(f"\n另有 {small} 种对不上的编码 / 名称组合各不到 5 次住院，只计数。")
    rep = "\n".join(L)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
    print(rep)


if __name__ == "__main__":
    main()
