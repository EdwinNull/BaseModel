#!/usr/bin/env python3
"""GAM式原始导出（住院、门急诊工作簿 + 护理记录）用 flucase 的成套读取器 gam_raw 读一遍，只输出计数和项目目录，不输出病例内容。

用来在导入服务器之前核对（BaseModel plans/GAM三源格式与规则集v0.4_执行计划_20261027.md §3）：
1. 每个文件认成什么（住院工作簿 / 门急诊工作簿 / 护理记录 / 认不出）；
2. 护理记录挂到了哪类就诊、按什么挂上的（关联字段 / 病人ID + 时间），挂不上的份数，时间不在就诊里的份数；
3. 护理记录读出的记录：按数据项的条数与就诊数；体温单里没对应上的项目（名称目录：≥5 份护理记录里出现、无长数字、无人称词）；
3b. 评分表与血糖的时间（gam_raw-3 起，plans/数据集验收与数据底座_执行计划_20261029.md 第 2 项）：各评分项有时间的条数与精度、
    Barthel 的时间取自哪里；评分项里不是数字的写法只给“形状”（数字写 9、汉字写“汉”、字母写 a），不给原文；
4. 问题清单：按问题代码计数（不输出说明原文，说明里有文件名和编号）。

就诊数 1–4 写成 "<5"。要用含 gam_raw 读取器的 flucase（flucase main 10-27 起）。在 BaseModel 根目录运行，路径可以给几个
（护理记录的文件夹、住院 / 门诊 / 急诊工作簿，或它们的压缩包）：
  flucase/backend/.venv/Scripts/python.exe scripts/flucase_raw_scan/gam_raw_check.py "data/GAM- 护理记录" "data/GAM住院.xlsx" "data/GAM门诊.xlsx" --out tmp/gam_raw_check.md
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


def c5(n: int) -> str:
    return "0" if n == 0 else (str(n) if n >= K else "<5")


def ok_name(s: str) -> bool:
    return bool(s) and len(s) <= 60 and not LONG_DIGITS.search(s) and not PERSON.search(s)


SCORE = ("NURSE:日常生活能力", "NURSE:跌倒风险", "NURSE:压疮风险", "NURSE:血糖记录")


def shape(s: str) -> str:
    """写法的形状：数字 → 9、汉字 → 汉、字母 → a，其余符号照留；只看格式，不带内容。"""
    s = re.sub(r"\d", "9", str(s).strip())
    s = re.sub(r"[一-鿿]", "汉", s)
    return re.sub(r"[A-Za-z]", "a", s)[:30]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    from bundle_files import bundle_files
    from flucase.repo.reader import ReadContext
    from flucase.repo.readers.gam_raw import GamRawReader, cell_dt, nurse_tables
    r = GamRawReader()
    per_path: list[Counter] = []
    for p0 in a.paths:                                       # 每个路径各认出了什么（只给计数）
        with bundle_files([p0]) as fs:
            per_path.append(Counter(r.kind_of(p)[0] or "认不出" for p, _ in fs))
    with bundle_files(a.paths) as files:
        print(f"…认文件（{len(files)} 个 xlsx）", file=sys.stderr)
        kinds = Counter(r.kind_of(p)[0] or "认不出" for p, _ in files)
        m = r.match_bundle([p for p, _ in files])
        print("…读取（和导入时一样）", file=sys.stderr)
        res = r.read_bundle(files, ReadContext(progress=lambda s, f: print(f"…{s}", file=sys.stderr)))
        # 第 3b 节要再看护理记录的日期格子；压缩包解出的临时文件出了 with 就没了，先读好放着
        nurse_cache = [nurse_tables(p, r.spec) for p, _ in files if r.kind_of(p)[0] == "nurse"]
    L: list[str] = []
    w = L.append
    w("# GAM式原始导出：成套读取核对（只含计数与项目目录）\n")
    w(f"- 读取器 {r.reader_version}；xlsx {len(files)} 个：" + "、".join(f"{ {'ip': '住院工作簿', 'op': '门急诊工作簿', 'nurse': '护理记录'}.get(k, k)} {v}"
                                                             for k, v in kinds.most_common()))
    lab = {"ip": "住院工作簿", "op": "门急诊工作簿", "nurse": "护理记录"}
    for i, c in enumerate(per_path, 1):
        w(f"  - 第 {i} 个路径：" + ("、".join(f"{lab.get(k, k)} {v}" for k, v in c.most_common()) or "没有 xlsx"))
    w(f"- 成套认定：{m.status}（{'；'.join(m.evidence)}{'；缺 ' + '、'.join(m.missing) if m.missing else ''}）")
    if not (kinds["ip"] or kinds["op"]):
        w("\n**没有认出住院或门急诊工作簿**：护理记录要和它们一起读才能挂接。请把 GAM 的住院、门诊、急诊工作簿（以前导入 flucase 用的那几个 .xlsx）"
          "的路径也加在命令里；某个工作簿在上面显示“认不出”的，说明它的工作表或列名和 GAM式住院 / 门诊格式不同，把那一行告诉 Claude。\n")
    encs = res.encounters
    w(f"- 就诊：住院 {c5(sum(e.setting == 'inpatient' for e in encs))}、门急诊 {c5(sum(e.setting == 'ed' for e in encs))}；病人 {c5(len({e.patient_key for e in encs}))}\n")
    w("## 1 护理记录挂接\n")
    linked = [e for e in encs if e.extra.get("nurse_files")]
    n_files = res.stats.get("nurse_files", 0)
    un = next((i for i in res.issues if i.code == "NURSE_UNLINKED"), None)
    out = next((i for i in res.issues if i.code == "TIME_OUT_OF_WINDOW"), None)
    w(f"- 护理记录 {n_files} 份；挂上的就诊 {c5(len(linked))}（住院 {c5(sum(e.setting == 'inpatient' for e in linked))}、"
      f"门急诊 {c5(sum(e.setting == 'ed' for e in linked))}）；一次就诊挂了不止一份的 {c5(sum(e.extra['nurse_files'] > 1 for e in linked))}")
    w(f"- 挂不上的 {c5(len(un.details['rows']) if un and un.details else 0)} 份；挂上了、但一半以上的记录时间不在那次就诊里的 "
      f"{c5(len(out.details['rows']) if out and out.details else 0)} 份")
    w(f"- 就诊的年龄、性别取自护理记录的：年龄 {c5(sum(1 for e in encs if e.extra.get('age_from')))}、性别 {c5(sum(1 for e in encs if e.extra.get('sex_from')))}\n")
    w("## 2 护理记录读出的记录\n")
    w("| 数据项 | 条数 | 就诊数 |")
    w("|---|---|---|")
    by: dict[str, list] = defaultdict(lambda: [0, set()])
    for x in res.records:
        if x.rule_id == "GAM-NURSE" or "nursing_note" in (x.marks or []):
            k = x.code + ("（护理记录正文）" if "nursing_note" in (x.marks or []) else "")
            by[k][0] += 1
            by[k][1].add(x.encounter_key)
    hidden = 0
    for k, (n, es) in sorted(by.items(), key=lambda kv: -kv[1][0]):
        if len(es) >= K and ok_name(k):
            w(f"| {k} | {n} | {c5(len(es))} |")
        else:
            hidden += 1
    if hidden:
        w(f"| （另 {hidden} 种在 <5 次就诊里出现，只计数） | | |")
    w(f"\n护理记录正文 {sum(1 for n in res.notes if n.type == '护理记录')} 条；首次护理评估 {sum(1 for n in res.notes if n.type == '首次护理评估')} 份。")
    item = next((i for i in res.issues if i.code == "ITEM_IGNORED" and "体温单" in i.message), None)
    w("\n## 3 体温单里没对应上统一数据项的项目\n")
    if item and item.details:
        w("| 项目 | 行数 | 份数 |")
        w("|---|---|---|")
        hid = 0
        for name, rows, nf in item.details["rows"]:
            if nf >= K and ok_name(str(name)):
                w(f"| {name} | {rows} | {nf} |")
            else:
                hid += 1
        if hid:
            w(f"| （另 {hid} 种 <5 份或不合列出规则，只计数） | | |")
    else:
        w("（没有）")
    vu = next((i for i in res.issues if i.code == "VALUE_UNPARSED"), None)
    if vu and vu.details:
        w("\n体征值不是数字的写法（数据项、写法、次数；写法不合列出规则的只计数）：\n")
        w("| 数据项 | 写法 | 次数 |")
        w("|---|---|---|")
        for code, how, n in vu.details["rows"][:40]:
            w(f"| {code} | {how if ok_name(str(how)) and not re.search(r'\d{3,}', str(how)) else '（不列）'} | {n} |")
    w("\n## 3b 评分表与血糖的时间\n")
    sc = [x for x in res.records if x.rule_id == "GAM-NURSE" and x.code.startswith(SCORE)]
    if sc:
        w("| 数据项 | 条数 | 有时间 | 精确到分钟 | 只有日期 | 就诊数 |")
        w("|---|---|---|---|---|---|")
        g: dict[str, list] = defaultdict(list)
        for x in sc:
            g[x.code].append(x)
        for code, xs in sorted(g.items(), key=lambda kv: -len(kv[1])):
            es = {x.encounter_key for x in xs}
            if len(es) >= K and ok_name(code):
                w(f"| {code} | {len(xs)} | {sum(1 for x in xs if x.time)} | {sum(1 for x in xs if x.time and x.precision == 'minute')} | "
                  f"{sum(1 for x in xs if x.time and x.precision == 'day')} | {c5(len(es))} |")
        w("\nBarthel 表只有“总分 · 分级”两列、没有日期，表里的评分没有时间是正常的；带时间的 Barthel 在体温单的“生活能力评分”（第 2 节）。")
        odd = Counter(shape(x.value_text) for x in sc if x.value_num is None and x.value_text and x.code.endswith("·总分"))
        if odd:
            w("\n评分“总分”里不是数字的写法形状（形状、次数）：\n")
            w("| 形状 | 次数 |")
            w("|---|---|")
            for s, n in odd.most_common(10):
                w(f"| `{s}` | {c5(n)} |")
        bad = Counter()                                      # 评分表、血糖表的日期格子：读不出的按形状计数
        for ts in nurse_cache:
            times = sorted(tm for t in ts if t.role == "vitals" for _, row in t.rows if (tm := cell_dt(t.get(row, t.col(r"时间|日期时间")))))
            anchor = times[0] if times else None
            for t in ts:
                jd = t.col(r.spec["score_date"]) if t.role in ("adl", "fall", "pressure", "glucose") else None
                for _, row in (t.rows if jd is not None else []):
                    v = t.get(row, jd)
                    if v and cell_dt(v, anchor) is None and not re.fullmatch(r.spec["score_legend"], v):
                        bad[(r.spec["tables"][t.role]["label"], shape(v))] += 1
        if bad:
            w("\n评分表、血糖表里读不出的日期写法（表、形状、次数；形状只看格式）：\n")
            w("| 表 | 形状 | 次数 |")
            w("|---|---|---|")
            for (lab_, s), n in bad.most_common(12):
                w(f"| {lab_} | `{s}` | {c5(n)} |")
        else:
            w("\n评分表、血糖表的日期格子都读得出。")
    else:
        w("（没有读出评分或血糖）")
    w("\n## 4 问题清单（按代码计数，不输出说明原文）\n")
    w("| 问题代码 | 级别 | 条数 |")
    w("|---|---|---|")
    for (code, lv), n in Counter((i.code, i.level) for i in res.issues).most_common():
        w(f"| {code} | {lv} | {n} |")
    rep = "\n".join(L)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
        print(f"报告已写到 {a.out}", file=sys.stderr)
    print(rep)


if __name__ == "__main__":
    main()
