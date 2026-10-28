"""证型对应表拆分（10-26 汇报第 12 页“证型对应”一线）：拆开“¤”、去重，定每个证候的对应证型。

输入：docs/数据对齐/证型对应.xlsx（GD 临床 10-25 交回：355 种证候写法、两院就诊次数、GD 填的方案证型；只含写法与次数）。
150 种写法是“¤”连起来的多个证候（多半是同一证候重复，如“痰热阻肺证¤痰热阻肺证”）。这里先拆开、去重成单个证候：

- 单个证候的证型：取 GD 在“只由这一个证候组成”的写法上填的（如“A”“A¤A”）→ 已对应；这些写法填的不一样 → 按写法对应：GD 确认
  （研究者 10-27）不同写法代表的原因不同，就是这样填的，所以这几个证候不拆到单个证候上，按写法各记各的证型；
- 其余没填的（含只在多证候写法如“A¤B”里出现、那条写法填了的）→ 不对应（原发病证候）。研究者 10-27 定（D84）：这些病人多不是因为流感
  住院，证候按原发病写，流感的证型定不了，不再请 GD 补；
- 多证候写法 GD 填了的，那个证型按写法记（不拆到单个证候上）；
- 就诊次数按写法累加（一次就诊写了几种写法会重复计），只作排序参考。

输出一个 Excel：
1 单个证候：证候、两院就诊次数、对应证型、状态（已对应 / 按写法对应 / 不对应（原发病证候））、来自几种写法；
2 按写法对应：同一证候不同写法填了不同证型的，列出每种写法和它的证型（GD 已确认：不同写法原因不同）；
3 多证候写法：由 ≥2 种不同证候组成的写法和 GD 填的证型（“一次就诊对到多个证型时怎么取”另定口径时用）。

用法（BaseModel 根目录）：python scripts/tcm_mapping/split_tcm_mapping.py [--input docs/数据对齐/证型对应.xlsx] [--out 输出.xlsx]
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

SEP = "¤"
MAPPED, CONFLICT, NONE = "已对应", "按写法对应", "不对应（原发病证候）"


def atoms(writing: str) -> list[str]:
    """一种写法拆成单个证候（去空白、按出现顺序去重）。"""
    out: list[str] = []
    for x in str(writing).split(SEP):
        x = x.strip()
        if x and x not in out:
            out.append(x)
    return out


def split(rows: list[tuple]) -> tuple[list[dict], list[dict], list[dict]]:
    """rows：(写法, 已对到方案证型, GD 就诊, GAM 就诊, GD 填的证型)。返回（单个证候, 冲突明细, 多证候写法）。"""
    acc: dict[str, dict] = defaultdict(lambda: {"gd": 0, "gam": 0, "pure": defaultdict(list), "n": 0})
    multi = []
    for w, _, gd, gam, ty in rows:
        if not w:
            continue
        ty = (str(ty).strip() or None) if ty is not None else None
        a = atoms(w)
        for x in a:
            d = acc[x]
            d["gd"] += int(gd or 0)
            d["gam"] += int(gam or 0)
            d["n"] += 1
            if ty and len(a) == 1:
                d["pure"][ty].append((w, int(gd or 0), int(gam or 0)))
        if len(a) >= 2:
            multi.append({"写法": w, "证候": "、".join(a), "GD 就诊": int(gd or 0), "GAM 就诊": int(gam or 0), "GD 填的证型": ty or ""})
    single, conflicts = [], []
    for x, d in acc.items():
        types = sorted(d["pure"])
        if len(types) == 1:
            ty, st = types[0], MAPPED
        elif len(types) > 1:
            ty, st = " / ".join(types), CONFLICT
            for t in types:
                for w, gd, gam in d["pure"][t]:
                    conflicts.append({"证候": x, "写法": w, "GD 就诊": gd, "GAM 就诊": gam, "GD 填的证型": t})
        else:
            ty, st = "", NONE
        single.append({"证候": x, "GD 就诊": d["gd"], "GAM 就诊": d["gam"], "对应证型": ty, "状态": st, "来自几种写法": d["n"]})
    order = {CONFLICT: 0, NONE: 1, MAPPED: 2}
    single.sort(key=lambda r: (order[r["状态"]], -(r["GD 就诊"] + r["GAM 就诊"]), r["证候"]))
    multi.sort(key=lambda r: -(r["GD 就诊"] + r["GAM 就诊"]))
    return single, conflicts, multi


def _sheet(wb: Workbook, title: str, cols: list[str], recs: list[dict], widths: dict[str, int], note: str):
    ws = wb.create_sheet(title)
    ws.append([note])
    ws["A1"].font = Font(italic=True, color="666666")
    ws.append(cols)
    for c in ws[2]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDEBF7")
    for r in recs:
        ws.append([r.get(c, "") for c in cols])
    for i, c in enumerate(cols):
        ws.column_dimensions[chr(65 + i)].width = widths.get(c, 12)
    ws.freeze_panes = "A3"
    for row in ws.iter_rows(min_row=3):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=True)
    return ws


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("docs/数据对齐/证型对应.xlsx"))
    ap.add_argument("--out", type=Path, default=Path("docs/数据对齐/证型对应_拆分_20261027.xlsx"))
    a = ap.parse_args()
    rows = list(load_workbook(a.input, read_only=True).active.iter_rows(values_only=True))[1:]
    single, conflicts, multi = split([tuple(r[:5]) for r in rows])
    wb = Workbook()
    wb.remove(wb.active)
    _sheet(wb, "单个证候", ["证候", "GD 就诊", "GAM 就诊", "对应证型", "状态", "来自几种写法"], single,
           {"证候": 22, "对应证型": 26, "状态": 22},
           f"由 {len(rows)} 种写法拆开“¤”、去重得到 {len(single)} 种证候；没填的按原发病证候、不对应；同一证候不同写法填得不同的按写法对应（研究者 10-27，D84）；就诊次数按写法累加，只作排序参考")
    _sheet(wb, "按写法对应", ["证候", "写法", "GD 就诊", "GAM 就诊", "GD 填的证型"], conflicts,
           {"证候": 18, "写法": 34, "GD 填的证型": 20},
           "同一个证候在不同写法里填了不同证型：GD 确认（研究者 10-27）不同写法代表的原因不同，按写法各记各的证型")
    _sheet(wb, "多证候写法", ["写法", "证候", "GD 就诊", "GAM 就诊", "GD 填的证型"], multi, {"写法": 40, "证候": 32, "GD 填的证型": 22},
           "由 ≥2 种不同证候组成的写法：GD 填了的按写法记那个证型；一次就诊对到多个证型时怎么取，要另定口径")
    wb.save(a.out)
    st = defaultdict(int)
    for r in single:
        st[r["状态"]] += 1
    print(f"{len(rows)} 种写法 → {len(single)} 种证候（" + "、".join(f"{k} {v}" for k, v in st.items())
          + f"）；按写法对应 {len({c['证候'] for c in conflicts})} 种（{len(conflicts)} 种写法）；多证候写法 {len(multi)} 种；写到 {a.out}")


if __name__ == "__main__":
    main()
