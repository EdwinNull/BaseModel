#!/usr/bin/env python3
"""GD 原始导出：规则集 v0.4 要核对的几件事（只输出名称目录与计数，不输出病例内容）。

研究者 10-27 定了 D76–D81（BaseModel plans/GAM三源格式与规则集v0.4_执行计划_20261027.md §2），其中三处要先在真实数据上看名称和覆盖：
1. D76 ICU：医嘱名称里带“监护 / 重症 / ICU”的名称目录（行数、住院数）；按医嘱的科室数有“重症监护”医嘱的住院——标黄的 12 个科室、
   EICU、芳村PCCM二科（没标黄，但批注说几个院区呼吸科都有监护室）以及其他科室；v0.4 读取器多认出的 ICU 住院数；
2. D80 NGS：检验名称、检查项目里像 NGS 的名称目录（行数、住院数、结果里提到流感的行数）；读取器认出的 NGS 流感检测（阳性 / 阴性住院数）；
3. D78 慢性低氧：COPD / 哮喘 / 心衰 / 间质性肺病各自的住院数，其中有动脉血 PaO2、PaO2 <60、吸空气 SpO2 ≤93 的住院数。

名称目录是医院的项目目录（医嘱、检验、检查、科室名称），不含病例；名称里有 ≥6 位连续数字或人称、联系方式类的词的整条不列。
住院数 1–4 写成 "<5"。

要用含 v0.4 读取器（gd_raw-6）的 flucase（flucase main 10-27 起）。路径给 GD 原始导出的文件夹或压缩包（导入 flucase 时用的那一套，
可以给几个）；压缩包解到旁边的临时文件夹，读完删掉。在 BaseModel 根目录运行：
  flucase/backend/.venv/Scripts/python.exe scripts/flucase_raw_scan/gd_v04_probe.py "data/GD原始导出.zip" --out tmp/gd_v04_probe.md
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

K = 5
PERSON = re.compile(r"主任|医生|医师|教授|护士|护师|家属|患者|病人|先生|女士|老师|同志|签字|签名|电话|手机|身份证|住址|地址")
LONG_DIGITS = re.compile(r"\d{6,}")
ICU_WORDS = re.compile(r"监护|重症|ICU", re.I)
NGS_WIDE = re.compile(r"NGS|宏基因组|测序|高通量|基因检测|病原.{0,6}(?:检测|鉴定)", re.I)
FLU = re.compile(r"流感|[Ii]nfluenza")
# NGS 报告里提到流感的那一句，同时写了什么（只数行数）：看“提到流感”是检出了，还是检测范围里列了一下
NGS_CUES = {"检出（不含未检出）": r"(?<!未)检出|阳性", "未检出 / 阴性": r"未检出|阴性|not\s*detected", "序列数 / reads": r"序列数|reads|读数|序列",
            "相对丰度": r"丰度", "检测范围 / 包括 / 覆盖": r"检测范围|包括|包含|覆盖|涵盖|病原谱", "疑似 / 背景 / 定植": r"疑似|背景|定植|污染"}


def flu_clause_cues(text: str) -> set[str]:
    clauses = [c for c in re.split(r"[。；;\n]", text or "") if FLU.search(c)]
    return {k for k, rx in NGS_CUES.items() if any(re.search(rx, c, re.I) for c in clauses)}


def c5(n: int) -> str:
    return "0" if n == 0 else (str(n) if n >= K else "<5")


def ok_name(s: str) -> bool:
    return bool(s) and len(s) <= 60 and not LONG_DIGITS.search(s) and not PERSON.search(s)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path, nargs="+", help="GD 原始导出的文件夹或压缩包（可以给几个）")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    from bundle_files import bundle_files
    from flucase.repo.readers.gd_raw import GdRawReader
    reader = GdRawReader()
    if reader.reader_version < "gd_raw-6":
        sys.exit(f"flucase 的 GD 读取器是 {reader.reader_version}，要 gd_raw-6 以上（合并 feat/v04-gam-20261027 后再跑）")
    with bundle_files(a.root) as files:
        rep = probe(reader, files)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
        print(f"报告已写到 {a.out}", file=sys.stderr)
    print(rep)


def probe(reader, files) -> str:
    from flucase.pipeline.extract.lexicon import ICU_WARD_DEPTS, is_icu_dept, is_icu_ward_dept
    from flucase.repo.reader import ReadContext
    from flucase.repo.readers.gd_raw import _rows
    print(f"…读取 {len(files)} 个 xlsx（和导入时一样，较慢）", file=sys.stderr)
    roles = Counter(reader.role_label(t.role) for p, d in files for t in reader.tables(p, d))
    res = reader.read_bundle(files, ReadContext())
    encs = {e.key: e for e in res.encounters}
    by_enct = {e.extra.get("enct_id"): e.key for e in res.encounters if e.extra.get("enct_id")}
    recs = defaultdict(list)
    for r in res.records:
        recs[r.encounter_key].append(r)

    # ---- 原表：医嘱、检验、检查的名称
    order_names: dict[str, dict] = defaultdict(lambda: {"rows": 0, "enc": set()})
    ward_order: dict[str, set] = defaultdict(set)          # 医嘱科室 → 有“重症监护”医嘱的住院
    ngs_names: dict[tuple[str, str], dict] = defaultdict(lambda: {"rows": 0, "enc": set(), "flu": 0})
    ngs_cues: Counter = Counter()
    ngs_where: Counter = Counter()
    for p, disp in files:
        for t in reader.tables(p, disp):
            if t.role not in ("order", "lab", "exam"):
                continue
            ix = t.ix
            g = lambda row, col: (str(row[ix[col]]).strip() if col in ix and ix[col] < len(row) and row[ix[col]] is not None else "")  # noqa: E731
            for _, row in _rows(t):
                if t.role == "order":
                    key = by_enct.get(re.sub(r"\.0$", "", g(row, "ENCT_ID")).lstrip("0") or "") or by_enct.get(g(row, "ENCT_ID"))
                    name, dept = g(row, "医嘱名称"), g(row, "科室")
                    if ICU_WORDS.search(name):
                        d = order_names[name]
                        d["rows"] += 1
                        d["enc"].add(key)
                    if "重症监护" in name and key:
                        ward_order[dept or "（医嘱没写科室）"].add(key)
                elif t.role == "lab":
                    name = g(row, "名称")
                    if NGS_WIDE.search(name):
                        d = ngs_names[("检验", name)]
                        d["rows"] += 1
                        d["enc"].add(g(row, "JZH") or g(row, "ENCT_ID"))
                        d["flu"] += bool(FLU.search(g(row, "结果")))
                        if FLU.search(g(row, "结果")):
                            ngs_where["检验结果"] += 1
                            ngs_cues.update(flu_clause_cues(g(row, "结果")))
                else:
                    name = f"{g(row, '类别')} {g(row, '项目')}".strip()
                    if NGS_WIDE.search(name):
                        d = ngs_names[("检查", name)]
                        d["rows"] += 1
                        d["enc"].add(g(row, "ENCT_ID"))
                        fi, co = g(row, "影像所见"), g(row, "影像诊断")
                        d["flu"] += bool(FLU.search(fi + co))
                        if FLU.search(fi + co):
                            ngs_where["影像所见" if FLU.search(fi) else "只在影像诊断"] += 1
                            ngs_cues.update(flu_clause_cues(fi + "\n" + co))

    L: list[str] = []
    w = L.append
    w("# GD 原始导出：规则集 v0.4 的核对（只含名称目录与计数）\n")
    w(f"- 读取器 {reader.reader_version}；xlsx {len(files)} 个；住院 {len(encs)} 次；住院数 1–4 写成 \"<5\"")
    w("- 认出的表：" + ("、".join(f"{k} {v}" for k, v in roles.most_common()) or "（没有）") + "\n")
    if not encs:
        w("**没有读到住院**：要有“入院记录”表（ENCT_UUID、住院号、入院时间、性别、主诉、现病史）。请确认给的是 GD 原始导出的文件夹或压缩包"
          "（导入 flucase 时用的那一套）。\n")
    w("## 1 ICU（D76）\n")
    w("### 1.1 名称里带“监护 / 重症 / ICU”的医嘱\n")
    w("| 医嘱名称 | 行数 | 住院数 |")
    w("|---|---|---|")
    hidden = 0
    for n, d in sorted(order_names.items(), key=lambda x: -x[1]["rows"]):
        if ok_name(n):
            w(f"| {n} | {d['rows']} | {c5(len(d['enc'] - {None}))} |")
        else:
            hidden += 1
    if hidden:
        w(f"| （另 {hidden} 种名称不合列出规则，只计数） | | |")
    w("\n### 1.2 有“重症监护”医嘱的住院，按医嘱的科室\n")
    w("| 医嘱的科室 | 标黄 | 名称算 ICU | 住院数 |")
    w("|---|---|---|---|")
    for dept, ks in sorted(ward_order.items(), key=lambda x: -len(x[1])):
        w(f"| {dept if ok_name(dept) else '（不列）'} | {'是' if is_icu_ward_dept(dept) else ''} | {'是' if is_icu_dept(dept) else ''} | {c5(len(ks))} |")
    for dept in ICU_WARD_DEPTS + ["芳村PCCM二科"]:
        if dept not in ward_order:
            w(f"| {dept} | {'是' if is_icu_ward_dept(dept) else ''} | | 0 |")
    plain = {k for k, rs in recs.items() if any(r.code == "TRT008" and r.state == "pos" and "icu_ward_order" not in r.marks for r in rs)}
    ward = {k for k, rs in recs.items() if any(r.code == "TRT008" and "icu_ward_order" in r.marks for r in rs)}
    w(f"\n读取器：v0.3 认的 ICU 住院（科室名、转 ICU 医嘱、病历文字）{c5(len(plain))}；标黄科室 + 重症监护医嘱 {c5(len(ward))}，"
      f"其中 v0.3 没认的（v0.4 新增）{c5(len(ward - plain))}。")
    eicu = {k for k, e in encs.items() if re.search(r"EICU", f"{e.ward or ''} {e.extra.get('出院科室') or ''}", re.I)}
    eicu_ord = set().union(*[ks for d, ks in ward_order.items() if re.search(r"EICU", d, re.I)]) if ward_order else set()
    w(f"EICU（入院或出院科室）住院 {c5(len(eicu))}；EICU 开过“重症监护”医嘱的住院 {c5(len(eicu_ord))}（GD 临床：EICU 也有普通床位，供参考）。")

    w("\n## 2 NGS（D80）\n")
    w("| 来源 | 名称 | 行数 | 编号数 | 结果里提到流感的行数 |")
    w("|---|---|---|---|---|")
    for (src, n), d in sorted(ngs_names.items(), key=lambda x: -x[1]["rows"]):
        w(f"| {src} | {n if ok_name(n) else '（不列）'} | {d['rows']} | {c5(len(d['enc'] - {''}))} | {d['flu']} |")
    if not ngs_names:
        w("| — | 没有找到像 NGS 的名称（关键词：NGS、宏基因组、测序、高通量、基因检测、病原…检测 / 鉴定） | | | |")
    ngs = [r for r in res.records if r.code == "FLU_TEST" and r.label == "流感检测（NGS）"]
    w(f"\n读取器认出的 NGS 流感检测：阳性住院 {c5(len({r.encounter_key for r in ngs if r.state == 'pos'}))}，"
      f"阴性住院 {c5(len({r.encounter_key for r in ngs if r.state == 'neg'}))}。"
      "名称没被认到的，请把上表里的名称告诉 Claude，写进格式配置 ngs_name。")
    n_flu = sum(d["flu"] for d in ngs_names.values())
    if n_flu:
        w(f"\n提到流感的 {n_flu} 行写在：" + "、".join(f"{k} {v}" for k, v in ngs_where.most_common())
          + "。提到流感的那一句里同时写了（行数，一行可算几类）：" + "、".join(f"{k} {ngs_cues.get(k, 0)}" for k in NGS_CUES)
          + "。读取器现在：这一句有“未检出 / 阴性”记阴性，否则记阳性；如果“检测范围 / 包括”多，说明有的只是列了检测范围，要改认法。")
    meth = Counter(r.label or "（没标方法）" for r in res.records if r.code == "FLU_TEST")
    w("流感检测按方法（记录条数）：" + "、".join(f"{k} {v}" for k, v in meth.most_common()))

    w("\n## 3 慢性低氧者的血气（D78）\n")
    w("| 病种 | 住院数 | 有动脉血 PaO2 | PaO2 <60 | 吸空气 SpO2 ≤93 |")
    w("|---|---|---|---|---|")
    for code, name in (("COM001", "COPD"), ("COM002", "支气管哮喘"), ("COM005", "心力衰竭"), ("COM020", "间质性肺病")):
        ks = {k for k, rs in recs.items() if any(r.code == code and r.state == "pos" for r in rs)}
        pa = {k for k in ks if any(r.code == "EXT_PAO2" and r.value_num is not None for r in recs[k])}
        lo = {k for k in ks if any(r.code == "EXT_PAO2" and r.value_num is not None and r.value_num < 60 for r in recs[k])}
        sp = {k for k in ks if any(r.code == "VS006" and r.o2 == "空气" and r.value_num is not None and r.value_num <= 93 for r in recs[k])}
        w(f"| {name} | {c5(len(ks))} | {c5(len(pa))} | {c5(len(lo))} | {c5(len(sp))} |")
    return "\n".join(L)


if __name__ == "__main__":
    main()
