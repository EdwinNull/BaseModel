#!/usr/bin/env python3
"""AH式住院表用 flucase 的读取器 ah_crf 读一遍，只输出计数、名称目录和写法形状，不输出病例内容。

用来在导入之前核对读取器（BaseModel plans/数据工程与flucase/AH中心接入_执行计划_20261111.md）：
1. 每个文件认成什么（exact / similar / none 与差异）；
2. 读出的就诊、记录、病历份数，问题代码计数（不输出说明原文，说明里有编号）；
3. 年龄分段；
4. 检验：每列每格几条、拆不开的格子数；条目名称目录（≥10 次住院出现）与对应的统一编码、数值分布、小数位形状、* ◇ △ 标记、
   “<x”比例、相对入院的时间分段——用来定单位、补别名；
5. 流感核酸：每列结果判成阳性 / 阴性 / 认不出的条数，认不出的写法只给形状；按住院的甲 / 乙阳性；首次检测相对入院的时间；
6. 同一住院号多行：几组、哪些列不同；
7. 出院记录各段（入院时情况、诊疗经过、出院诊断、出院医嘱）的有无组合；
8. 病历规则抽出的治疗、并发症、结局：按住院计数，并按证据所在的病历类型分；
9. 流感诊断、流感阳性、年龄 ≥60 的交叉计数；按入院月份的住院、阳性、出院记录有无；
   诊断名称配 ICD 的比例与没配上的名称目录（≥10 次住院）；中医证候目录。

按住院计数 1–4 写成 "<5"；名称目录只列 ≥10 次住院出现、无长数字、无人称词的名称，像人名的字再遮蔽。
在 BaseModel 根目录运行（路径可以是文件夹、单个 xlsx 或压缩包；Windows 上 Python 换成 flucase/backend/.venv/Scripts/python.exe）：
  flucase/backend/.venv/bin/python scripts/flucase_raw_scan/ah_check.py "data/AH-呼吸内二科数据统计" --out tmp/ah_scan_20261111/ah_check.md
"""
from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ah_raw_probe as A  # noqa: E402
import gam_raw_probe as G  # noqa: E402
import gd_raw_scan as S  # noqa: E402
from bundle_files import bundle_files  # noqa: E402

c5, pct, quant, K_NAME = G.c5, G.pct, G.quant, A.K_NAME
FLU_WORDS = ("阳性", "阴性", "弱阳性", "检出", "未检出", "可疑", "灰区", "待复查", "无效", "不合格", "未做", "未查", "+", "-")
OUTCOME_CODES = ["TRT011", "TRT014", "TRT006", "TRT007", "TRT008", "TRT009", "TRT012", "DEATH", "CLP003", "CLP004", "CLP005", "CLPX_RF",
                 "CLP001", "CLP002", "CLPX_PNEU", "CLP008", "CLP009", "CLP012", "CLP013", "CLP014", "CLP017", "TRT001", "TRT002",
                 # 基础病：扫描的关键词计数没去否定，既往史里“否认冠心病、脑卒中、肝病”一类模板句几乎每份都命中
                 "COM001", "COM002", "COM003", "COM004", "COM005", "COM006", "COM007", "COM008", "COM009", "COM010", "COM012", "COM020"]


def hours(t: str | None, t0: str | None) -> float | None:
    if not t or not t0:
        return None
    f = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M" if len(s) > 10 else "%Y-%m-%d")  # noqa: E731
    return (f(t) - f(t0)).total_seconds() / 3600


def band(h: float | None) -> str:
    if h is None:
        return "无时间"
    for lim, lab in ((-24 * 7, "入院前 >7 天"), (-24, "入院前 1–7 天"), (0, "入院前 24 小时内"), (24, "入院后 24 小时内"), (72, "入院后 1–3 天"),
                     (24 * 14, "入院后 3–14 天"), (24 * 60, "入院后 14–60 天")):
        if h < lim:
            return lab
    return "入院后 >60 天"


BANDS = ["入院前 >7 天", "入院前 1–7 天", "入院前 24 小时内", "入院后 24 小时内", "入院后 1–3 天", "入院后 3–14 天", "入院后 14–60 天", "入院后 >60 天", "无时间"]


def dec_shape(v: float, raw: str) -> str:
    return S.shape(raw.lstrip("<>＜＞≤≥ "))[:12]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    from flucase.repo.reader import ReadContext
    from flucase.repo.readers.ah_crf import AhCrfReader, parse_entries
    r = AhCrfReader()
    L: list[str] = []
    w = L.append
    w("# AH式住院表：读取核对（只含计数、名称目录与写法形状）\n")
    w(f"- 读取器 {r.reader_version}；扫描时间 {datetime.now():%Y-%m-%d %H:%M}")
    w("- 按住院计数 1–4 写成 \"<5\"；名称目录只列在 ≥10 次住院里出现的名称\n")
    results = []
    with bundle_files(a.paths) as files:
        w("## 1 认格式\n")
        w("| 文件 | 认定 | 得分 | 差异 |")
        w("|---|---|---|---|")
        for i, (p, _) in enumerate(files, 1):
            m = r.match(p)
            diffs = "；".join(f"{d['kind']}：{A.render_head(d['what'])}" for d in m.differences[:12]) or "—"
            w(f"| F{i:03d} | {m.status} | {m.score:g} | {diffs} |")
            if m.status != "none":
                print(f"…读 F{i:03d}", file=sys.stderr)
                res = r.read(p, f"F{i:03d}", ReadContext())
                results.append((f"F{i:03d}", p, res))
    if not results:
        w("\n没有认成 AH式住院表的文件。\n")
    for fid, p, res in results:
        section(w, fid, res, parse_entries)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"报告已写到 {a.out}", file=sys.stderr)


def section(w, fid: str, res, parse_entries) -> None:
    encs = res.encounters
    n = len(encs)
    t0 = {e.key: e.t0 for e in encs}
    by_enc: dict[str, list] = defaultdict(list)
    for x in res.records:
        by_enc[x.encounter_key].append(x)
    note_type = {nt.key: nt.type for nt in res.notes}
    w(f"\n## {fid}：读取结果\n")
    w(f"- 表里 {res.stats['rows']} 行 → 住院 {n} 次、住院号 {len({e.patient_key for e in encs})} 个；检验列 {res.stats['lab_columns']} 列")
    w(f"- 记录：" + "、".join(f"{k} {v}" for k, v in sorted(res.stats["records"].items())))
    w(f"- 病历：" + "、".join(f"{k} {v}" for k, v in Counter(nt.type for nt in res.notes).most_common()))
    w(f"- 入院时间精度：" + "、".join(f"{k} {c5(v)}" for k, v in Counter(e.t0_precision for e in encs).most_common()))
    w("\n问题代码（条数，说明原文不列）：" + "、".join(f"{c}·{lv} {k}" for (c, lv), k in Counter((i.code, i.level) for i in res.issues).most_common()) + "\n")

    # ---- 年龄
    ages = Counter()
    for e in encs:
        g = e.age
        ages["缺"] += g is None
        if g is not None:
            ages["<18" if g < 18 else "18–59" if g < 60 else "60–64" if g < 65 else "65–79" if g < 80 else "≥80"] += 1
    w("### 年龄（按住院）\n")
    w("、".join(f"{k} {c5(ages[k])}" for k in ("<18", "18–59", "60–64", "65–79", "≥80", "缺")) + "\n")

    # ---- 检验条目
    w("### 检验条目（按条目名称；按住院计数 ≥10 的才列）\n")
    labs = [x for x in res.records if x.kind == "lab" and x.code not in ("FLU_TEST", "FLU_TYPE")]
    per_name: dict[str, dict] = {}
    for x in labs:
        raw = x.sources[0].raw or ""
        nm = x.label if x.code.startswith("LABX:") else (parse_entries(raw)[0][0].name if parse_entries(raw)[0] else x.code)
        d = per_name.setdefault((nm, x.code), {"code": x.code, "encs": set(), "n": 0, "nums": [], "shapes": Counter(), "flags": Counter(),
                                               "lt": 0, "bands": Counter(), "cols": Counter()})
        d["encs"].add(x.encounter_key)
        d["n"] += 1
        d["cols"][x.sources[0].header] += 1
        if x.value_num is not None:
            d["nums"].append(x.value_num)
            ent = parse_entries(raw)[0]
            if ent:
                d["shapes"][dec_shape(x.value_num, ent[0].value)] += 1
        mark = (x.remark or "").split("原表标记 ", 1)                # 备注里还可能有别的说明（如“不当作白细胞计数”），只数标记
        for f in (mark[1] if len(mark) == 2 else ""):
            d["flags"][f] += 1
        d["lt"] += bool(set(x.marks) & {"lt", "gt"})
        d["first"] = d.get("first", {})
        k = x.encounter_key
        h = hours(x.time, t0.get(k))
        if k not in d["first"] or (h is not None and (d["first"][k] is None or h < d["first"][k])):
            d["first"][k] = h
    shown = {k: d for k, d in per_name.items() if len(d["encs"]) >= K_NAME and G.safe_name(k[0])}
    disp = A.mask_catalog(sorted({nm for nm, _ in shown}))
    w("| 条目名称 | 统一编码 | 所在列 | 住院 | 条数 | 数值占比 | 数值分布 | 小数位形状 | 标记 | <x / >x | 首次检测相对入院（按住院） |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for (nm, _), d in sorted(shown.items(), key=lambda kv: -len(kv[1]["encs"])):
        fb = Counter(band(h) for h in d["first"].values())
        w(f"| {disp[nm]} | {d['code'] if not d['code'].startswith('LABX:') else '（未对应）'} | {'、'.join(A.render_head(c) for c, _ in d['cols'].most_common(2))} "
          f"| {c5(len(d['encs']))} | {d['n']} | {pct(len(d['nums']), d['n'])} | {quant(d['nums'])} "
          f"| {'、'.join(f'`{s}`×{k}' for s, k in d['shapes'].most_common(3))} | {'、'.join(f'{f}×{k}' for f, k in d['flags'].most_common()) or '—'} "
          f"| {pct(d['lt'], d['n'])} | {'、'.join(f'{b} {c5(fb[b])}' for b in BANDS if fb[b])} |")
    hidden = [d for k, d in per_name.items() if k not in shown]
    w(f"\n另有 {len(hidden)} 种条目名称（共 {sum(d['n'] for d in hidden)} 条）在不到 10 次住院里出现或像自由文本，不列名称。\n")

    # ---- 流感核酸
    w("### 流感核酸\n")
    flu = [x for x in res.records if x.code == "FLU_TEST" and x.method == "table"]
    for head in sorted({x.sources[0].header for x in flu}):
        xs = [x for x in flu if x.sources[0].header == head]
        st = Counter(x.state for x in xs)
        words = Counter()
        for x in xs:
            v = (x.value_text or "").split("：", 1)[-1]
            words[v if v in FLU_WORDS or v.rstrip("()+-（）") in FLU_WORDS else f"形状 {S.shape(v)[:12]}"] += 1
        w(f"- {A.render_head(head)}：{len(xs)} 条，阳性 {st['pos']}、阴性 {st['neg']}、认不出 {st['none']}；写法：" +
          "、".join(f"“{k}”×{v}" for k, v in words.most_common(10)))
        names = Counter((x.value_text or "").split("：", 1)[0] for x in xs)
        nm = [k for k, v in names.items() if v >= K_NAME and G.safe_name(k)]
        dm = A.mask_catalog(nm)
        w(f"  条目名称：" + ("、".join(f"{dm[k]}×{names[k]}" for k in nm) or "—") + f"（另有 {len(names) - len(nm)} 种不列）")
    pos = defaultdict(set)
    for x in flu:
        if x.state == "pos":
            pos[x.encounter_key].add("甲" if "甲" in x.sources[0].header else "乙")
    tested = {x.encounter_key for x in flu}
    w(f"- 按住院：有核酸结果 {c5(len(tested))}；甲阳性 {c5(sum('甲' in s for s in pos.values()))}、乙阳性 {c5(sum('乙' in s for s in pos.values()))}、"
      f"甲乙都阳性 {c5(sum(len(s) == 2 for s in pos.values()))}；没有阳性结果 {c5(len(tested) - len(pos))}；没有核酸结果 {c5(n - len(tested))}")
    first = {}
    for x in flu:
        h = hours(x.time, t0.get(x.encounter_key))
        if x.encounter_key not in first or (h is not None and (first[x.encounter_key] is None or h < first[x.encounter_key])):
            first[x.encounter_key] = h
    fb = Counter(band(h) for h in first.values())
    w("- 首次核酸相对入院（按住院）：" + "、".join(f"{b} {c5(fb[b])}" for b in BANDS if fb[b]) + "\n")

    # ---- 重复行
    w("### 同一住院号、同一天入院的多行\n")
    dups = [i for i in res.issues if i.code == "DUP_ROWS"]
    for i in dups:
        if i.details:
            cols = Counter(c for row in i.details["rows"] for c in row[2].split("、") if c)
            w(f"- 取值不同的 {c5(len(i.details['rows']))} 组；不同的列（组数）：" + "、".join(f"{A.render_head(c)} {c5(k)}" for c, k in cols.most_common()))
        else:
            w(f"- 完全相同的重复：{c5(int(i.message.split(' ')[0]))} 组")
    if not dups:
        w("- 没有")
    w("")

    # ---- 出院记录各段
    w("### 出院记录各段的有无组合（按住院）\n")
    parts = ("入院时情况", "诊疗经过", "出院诊断", "出院医嘱")
    combo = Counter()
    dis = {nt.encounter_key: nt.text for nt in res.notes if nt.type == "出院记录"}
    for e in encs:
        t = dis.get(e.key, "")
        combo[" + ".join(p for p in parts if f"{p}：" in t) or "（都没有）"] += 1
    for k, v in combo.most_common():
        w(f"- {k}：{c5(v)}")
    w("")

    # ---- 治疗、并发症、结局
    w("### 病历规则与诊断名称读出的治疗、并发症、结局、基础病（按住院；状态 pos 才算）\n")
    w("| 编码 | 有（pos） | 其中证据在入院记录 | 首次病程记录 | 出院记录 | 检查报告 | 来自诊断名称 | 有时间 | 只有否定 / 未提及 / 假设 / 计划 |")
    w("|---|---|---|---|---|---|---|---|---|")
    for code in OUTCOME_CODES:
        pos_e, src, timed, other = set(), Counter(), set(), set()
        for k, xs in by_enc.items():
            ys = [x for x in xs if x.code == code]
            if not ys:
                continue
            ps = [x for x in ys if x.state == "pos"]
            if not ps:
                other.add(k)
                continue
            pos_e.add(k)
            kinds = {note_type.get(x.evidence[0]["note"], "?") if x.evidence else ("诊断名称" if x.rule_id == "AH-DX" else "表格") for x in ps}
            for kd in kinds:
                src[kd] += 1
            timed.add(k) if any(x.time for x in ps) else None
        from flucase.repo.query import label
        w(f"| {code} {label(code)} | {c5(len(pos_e))} | {c5(src['入院记录'])} | {c5(src['首次病程记录'])} | {c5(src['出院记录'])} | {c5(src['检查报告'])} | {c5(src['诊断名称'])} "
          f"| {c5(len(timed))} | {c5(len(other))} |")
    w("")

    # ---- 人群交叉
    w("### 流感诊断 × 核酸阳性 × 年龄（按住院）\n")
    flu_dx = {k for k, xs in by_enc.items() if any(x.code == "FLU_DX" for x in xs)}
    old = {e.key for e in encs if e.age is not None and e.age >= 60}
    w("| | 核酸阳性 | 核酸没有阳性 | 没有核酸结果 |")
    w("|---|---|---|---|")
    for lab, s in (("诊断有流感", flu_dx), ("诊断没有流感", {e.key for e in encs} - flu_dx)):
        for lab2, s2 in (("全部年龄", {e.key for e in encs}), ("≥60 岁", old)):
            ss = s & s2
            w(f"| {lab}·{lab2} | {c5(len(ss & set(pos)))} | {c5(len(ss & tested - set(pos)))} | {c5(len(ss - tested))} |")
    w("")

    # ---- 按月：夏季高峰是不是流感；出院记录缺的是不是集中在最近几个月（还没归档）
    w("### 按入院月份（按住院）\n")
    with_course = {nt.encounter_key for nt in res.notes if nt.type == "出院记录" and "诊疗经过：" in nt.text}
    with_ddx = {nt.encounter_key for nt in res.notes if nt.type == "出院记录" and "出院诊断：" in nt.text}
    months: dict[str, set] = defaultdict(set)
    for e in encs:
        months[e.t0[:7]].add(e.key)
    late = {k for k, h in first.items() if h is not None and h > 72}
    w("| 入院月份 | 住院 | ≥60 岁 | 核酸阳性 | 首次核酸在入院 72 小时后 | 诊断有流感 | 出院记录有诊疗经过 | 有出院诊断 |")
    w("|---|---|---|---|---|---|---|---|")
    for mo in sorted(months):
        s = months[mo]
        w(f"| {mo} | {c5(len(s))} | {c5(len(s & old))} | {c5(len(s & set(pos)))} | {c5(len(s & late))} | {c5(len(s & flu_dx))} "
          f"| {c5(len(s & with_course))} | {c5(len(s & with_ddx))} |")
    w("")

    # ---- 诊断名称配 ICD、中医证候
    dx = [x for x in res.records if x.code.startswith(("DX:", "DXN:"))]
    w("### 诊断名称配 ICD\n")
    w(f"- 诊断名称 {len(dx)} 条：配上 ICD {sum(x.code.startswith('DX:') for x in dx)} 条（{pct(sum(x.code.startswith('DX:') for x in dx), len(dx))}）；"
      f"入院初步诊断 {sum(bool(x.time) for x in dx)} 条、只在出院诊断 {sum(not x.time for x in dx)} 条")
    miss = Counter()
    miss_e: dict[str, set] = defaultdict(set)
    for x in dx:
        if x.code.startswith("DXN:"):
            miss[x.code[4:]] += 1
            miss_e[x.code[4:]].add(x.encounter_key)
    nm = [k for k in miss if len(miss_e[k]) >= K_NAME and G.safe_name(k)]
    dm = A.mask_catalog(nm)
    w("- 没配上的名称（≥10 次住院）：" + ("、".join(f"{dm[k]}（{c5(len(miss_e[k]))}）" for k in sorted(nm, key=lambda k: -len(miss_e[k]))[:40]) or "—")
      + f"；另有 {len(miss) - len(nm)} 种不列\n")
    syn = Counter()
    for x in res.records:
        if x.code == "TCM_SYN":
            syn[x.value_text] += 1
    nm = [k for k, v in syn.items() if v >= K_NAME and G.safe_name(k)]
    dm = A.mask_catalog(nm)
    w("### 中医主证\n")
    w("- " + ("、".join(f"{dm[k]}（{c5(syn[k])}）" for k in sorted(nm, key=lambda k: -syn[k])) or "—") + f"；另有 {len(syn) - len(nm)} 种不列；"
      f"与诊疗方案证型同名的住院 {c5(len({x.encounter_key for x in res.records if x.code == 'TCM_TYPE'}))}\n")

    # ---- 入院体征
    w("### 入院体征（按住院）\n")
    vs = {c: {x.encounter_key for x in res.records if x.code == c} for c in ("VS001", "VS002", "VS003", "VS004", "VS006")}
    src_vs = {c: Counter("表格" if x.method == "table" else "病历" for x in res.records if x.code == c) for c in vs}
    w("、".join(f"{c} {c5(len(s))}（{'、'.join(f'{k} {v}' for k, v in src_vs[c].items()) or '—'}）" for c, s in vs.items()) + "\n")
    stats_vals = [len(by_enc[e.key]) for e in encs]
    w(f"- 每次住院的记录数：p50 {statistics.median(stats_vals) if stats_vals else 0:g}")


if __name__ == "__main__":
    main()
