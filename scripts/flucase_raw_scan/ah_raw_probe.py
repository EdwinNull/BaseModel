#!/usr/bin/env python3
"""新中心 AH（呼吸内二科数据统计）的结构扫描：只输出结构与计数，不输出病例内容。

AH 的导出长什么样事先不知道。这个脚本把 GD（gd_raw_scan / gd_raw_probe）、GAM（gam_raw_probe）两轮扫描要回答的问题一次问完，
供 BaseModel plans/数据工程与flucase/AH接入_执行计划_20261111.md 的对齐与特征分析、flucase 的 AH 读取器使用：

1. flucase 现有格式认不认得：单文件格式（GD式 CRF、GAM式住院 / 门诊、门急诊导出模板、统一格式 Excel）逐个文件认，
   成套格式（GD式、GAM式原始导出）整套认；给状态、得分、认出的表与差异；
2. 每张表：猜的角色、表头、行数；编号列（不同值、每个编号几行、覆盖几天）；时间列（能解析的比例、精度、年月范围；就诊类时间按月计数）；
   每列的填充、类型、数值分布、短取值的写法形状；目录列的名称目录；长表（项目 + 值）的项目目录；长文字列的小节标题与关键词命中行数；
3. 统一数据项覆盖（特征分析用）：按表头（宽表一列一项）和按名称目录（长表、医嘱、检验、诊断）数 flucase 的每个数据项在多少个编号上能取到；
   诊断编码按 ICD-10 前缀数流感、基础病、并发症；
4. 低基数列（≤40 种取值、不是数字列）的取值分布，取值严格遮蔽；
5. 编号重合（加盐哈希，只给计数），同一工作簿里不同工作表之间也算；
6. 附：通用结构扫描（gd_raw_scan.py 的报告：文件类型、目录形状、文书类文件的长度与小节标题）。

不输出：任何单元格原文。目录类名称（检验项目、医嘱名称、体征项目等）例外，只列在 ≥10 个编号里出现、没有 ≥6 位连续数字、没有人称或联系方式类的词、
不像日期、≤60 字的名称，名称里像人名的 2–3 个字（常见姓开头、在目录里出现不到 3 次的词）再遮蔽；其余只计数。编号、姓名、时间原值、
病历和护理记录正文的任何片段都不输出。按编号分类的计数 1–4 写成 "<5"。文件名、目录名默认遮蔽。编号重合用本次随机加盐的哈希，盐不落盘。
压缩包解到它旁边的临时文件夹（真实数据不离开 data/），扫完删掉。

用法（BaseModel 根目录，用 flucase 的 venv；Windows 上是 flucase/backend/.venv/Scripts/python.exe）：
  flucase/backend/.venv/bin/python scripts/flucase_raw_scan/ah_raw_probe.py "data/AH-呼吸内二科数据统计" --out tmp/ah_scan_20261111/ah_raw_probe.md
给的路径可以是文件夹、单个文件或压缩包。
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gam_raw_probe as G  # noqa: E402
import gd_raw_probe as P  # noqa: E402
import gd_raw_scan as S  # noqa: E402

K = 5                      # 计数 1–4 写成 "<5"
K_NAME = 10                # 名称目录只列在这么多个编号里出现的名称（低频写法可能是手写的自由文本）
LOW_MAX = 40
EXTRA_CATALOG = re.compile(r"子项|明细|医嘱|药品|药名|诊断名称|疾病名称|检验名称|检查名称")
ITEM_HEAD = re.compile(r"项目|名称|子项|明细")
VISIT_TIME = re.compile(r"入院|就诊|挂号|来院|到院|收治|入科|发病|起病")
ICD_HEAD = re.compile(r"ICD|编码|代码|码$|诊断", re.I)
ICD_CODE = re.compile(r"(?<![A-Z0-9])[A-Z]\d{2}(?:\.[0-9A-Z]+)?[+*]?")
TEXT_MIN = 50              # 长文字：数小节标题的门槛
# 自由文字类的列：低基数也不列取值（小样本里主诉、诊断写法可能只有几十种）
TEXT_LIKE = re.compile(r"主诉|现病史|既往史|病史|诊断|记录|内容|描述|备注|小结|意见|建议|所见|结论|印象|病情|观察|措施|体格|经过|说明|原因|其他|其它")
# 低基数列取值严格遮蔽时照常显示的分类词（不是人名、不是自由文本）
LOW_KEEP = set("是 否 有 无 已 未 弱 阳 阴 轻 中 重 甲 乙 丙 可疑 待查 未检 未查 未做 未测 不详 未知 缺失 不适用 拒绝 放弃 放弃治疗 好转 治愈 "
               "未愈 自动 轻症 轻度 中度 重度 轻型 中型 重型 普通型 危重型 腋温 口温 肛温 耳温 双侧 单侧 左 右".split())

# ---------------------------------------------------------------- 统一数据项（表头和名称目录共用的关键词，只用来计数）
ITEMS: list[tuple[str, list[tuple[str, str, str | None]]]] = [
    ("基本信息", [
        ("年龄", r"年龄", None), ("性别", r"性别", None), ("出生日期", r"出生", None),
        ("身高 / 体重 / BMI", r"身高|体重|BMI", None),
        ("入院时间", r"入院(时间|日期)|入科(时间|日期)|收治(时间|日期)", None),
        ("出院时间", r"出院(时间|日期)|离院(时间|日期)", None),
        ("就诊 / 挂号时间", r"就诊(时间|日期)|挂号(时间|日期)|来院|到院|急诊(时间|日期)|门诊(时间|日期)", None),
        ("发病 / 起病时间", r"发病|起病|病程(天数)?$", r"病程记录"),
        ("住院天数", r"住院天数|住院日|在院天数", None), ("科室 / 病区", r"科室|科别|病区", r"会诊"),
        ("流感疫苗", r"疫苗|接种", None), ("吸烟 / 饮酒", r"吸烟|饮酒", None), ("院内发病", r"院内(发病|感染)", None)]),
    ("症状", [
        ("SYM001 发热", r"发热|发烧|最高体温|体温最高|热峰", r"退热|无发热"), ("SYM002 咳嗽", r"咳嗽", None), ("SYM003 咳痰", r"咳痰|痰", r"痰培养|痰涂片|吸痰"),
        ("SYM004 咽痛", r"咽痛|咽喉痛|咽干", None), ("SYM005 肌痛", r"肌痛|肌肉酸痛|全身酸痛|四肢酸痛|关节痛", None), ("SYM006 乏力", r"乏力|疲乏", None),
        ("SYM007 呼吸困难", r"呼吸困难|气促|气短|气喘|喘息|胸闷", None), ("头痛", r"头痛", None), ("鼻塞 / 流涕", r"鼻塞|流涕", None),
        ("纳差 / 厌食", r"纳差|食欲|厌食", None), ("意识 / 精神状态", r"意识|神志|嗜睡|谵妄|精神", None), ("呕吐 / 腹泻", r"腹泻|呕吐|恶心", None)]),
    ("基础病", [
        ("COM001 COPD", r"COPD|慢阻肺|慢性阻塞", None), ("COM002 哮喘", r"哮喘", None), ("COM003 支气管扩张", r"支气管扩张|支扩", None),
        ("COM004 冠心病", r"冠心病|冠状动脉", None), ("COM005 心力衰竭", r"心衰|心力衰竭|心功能不全", r"急性"),
        ("COM006 糖尿病", r"糖尿病", None), ("COM007 慢性肾病", r"慢性肾|肾功能不全|CKD|尿毒症|透析", r"急性"),
        ("COM008 肿瘤", r"肿瘤|癌|恶性", None), ("COM009 脑卒中", r"卒中|脑梗|脑出血|脑血管", None),
        ("COM010 免疫抑制", r"免疫抑制|免疫缺陷|器官移植|HIV|艾滋", None), ("COM012 肝病", r"肝硬化|慢性肝|肝炎", None),
        ("COM020 间质性肺病", r"间质性肺|肺间质|肺纤维化", None), ("（参考）高血压", r"高血压", None),
        ("基础病（汇总列）", r"基础病|基础疾病|合并症|既往史|慢性病|伴随疾病", None)]),
    ("体征", [(n, a, b) for n, a, b in P.VITAL]),
    ("检验", [(n, a, b) for n, a, b in P.LAB]),
    ("流感病原学", [
        ("流感检测（全部）", r"流感|FLU|INFLUENZA", r"副流感|嗜血|疫苗"), ("甲型", r"甲型|甲流|FLU.?A|H1N1|H3N2", r"甲型肝炎"),
        ("乙型", r"乙型流|乙流|FLU.?B", None), ("抗原", r"抗原", None), ("核酸 / PCR", r"核酸|RNA|PCR", None),
        ("NGS", r"NGS|宏基因|高通量测序", None), ("其他呼吸道病原", r"新冠|新型冠状|COVID|合胞|腺病毒|支原体|衣原体|鼻病毒|偏肺", None)]),
    ("治疗", [(n, a, b) for n, a, b in P.ORD if n not in ("死亡", "出院")]),
    ("结局与去向", [
        ("死亡", r"死亡|病故|死因", None), ("转归 / 离院方式", r"转归|离院方式|出院方式|去向|结局", None),
        ("ICU", r"ICU|重症监护|监护室|重症医学", None), ("重症 / 危重 / 病情分级", r"重症|危重|重型|病情分级|严重程度|转重|分级", None),
        ("再入院", r"再入院|再住院", None)]),
    ("并发症", [
        ("肺炎（全部）", r"肺炎", None), ("CLP001 病毒性肺炎", r"病毒性肺炎", None), ("CLP003/004 呼吸衰竭", r"呼吸衰竭|呼衰", None),
        ("CLP005 ARDS", r"ARDS|呼吸窘迫", None), ("CLP006 胸腔积液", r"胸腔积液|胸水", None), ("CLP007 气胸 / 纵隔气肿", r"气胸|纵隔气肿", None),
        ("CLP008 急性心衰", r"急性心(力)?衰", None), ("CLP009 心肌损伤 / 心肌炎", r"心肌炎|心肌损伤", None),
        ("CLP010 心律失常", r"心律失常|房颤|心房颤动|心动过速", None), ("CLP012 脓毒症", r"脓毒|败血", None), ("CLP013 休克", r"休克", None),
        ("CLP014 急性肾损伤", r"急性肾损伤|AKI|急性肾衰", None), ("CLP015 肝损伤 / 肝衰竭", r"肝损伤|肝功能异常|肝衰", None),
        ("CLP016 脑病 / 脑炎", r"脑病|脑炎", None), ("CLP018 DIC", r"DIC|弥散性血管内凝血", None), ("CLP020 MODS", r"MODS|多器官", None),
        ("CLP021–023 低钾 / 低钠 / 低蛋白", r"低钾|低钠|低蛋白", None)]),
    ("影像", [(n, a, b) for n, a, b in P.IMG_ITEM] + [("影像所见 / 结论", r"所见|影像|检查结论|报告结论|印象", None)]),
    ("中医", [("证型 / 证候", r"证型|证候|辨证", None), ("舌脉", r"舌|脉象", None), ("中医诊断 / 治法 / 方药", r"中医诊断|中医病名|治法|方药|中药|汤剂|颗粒", None)]),
    ("老年评估", [("Barthel / ADL", r"BARTHEL|ADL|日常生活", None), ("Morse / 跌倒", r"MORSE|跌倒", None), ("Braden / 压疮", r"BRADEN|压疮|压力性损伤", None),
                ("衰弱 / 营养 / 认知", r"衰弱|CFS|FRAIL|营养|NRS|MNA|MMSE|认知", None)]),
]
ITEMS_C = [(g, [(n, re.compile(a, re.I), re.compile(b, re.I) if b else None) for n, a, b in lst]) for g, lst in ITEMS]
ALL_C = [(f"{g}·{n}", a, b) for g, lst in ITEMS_C for n, a, b in lst]
# 这些列的取值是诊断、病史、结论一类的文字：按关键词数每个数据项在多少个编号的文字里出现（不判否定）
TEXTSCAN_HEAD = re.compile(G.TEXT_HEAD.pattern + r"|疾病|并发症|合并症|基础|病史|结论|印象|所见|转归|影像|CT|胸片", re.I)


def item_hits(text: str) -> list[str]:
    return [n for n, a, b in ALL_C if a.search(text) and not (b and b.search(text))]


# 表头里的临床词照常显示：取数据项关键词里的汉字词（如“奥司他韦”“最高体温”），其余按 gd_raw_scan 的规则遮蔽
HEAD_KEEP = {w for _, lst in ITEMS for n, a, b in lst for s in (n, a) for w in re.findall(r"[一-鿿]{2,}", s)}
HEAD_KEEP |= set("最高 最低 首次 末次 入院时 出院时 使用 情况 结果 方式 天数 时长 程度 分级 类型 是否 有无 胸部 双肺 肺部 病原 病原学 抗病毒 "
                 "检测 阳性 阴性 弱阳性".split())
MAXK = max(len(x) for x in HEAD_KEEP)


def render_head(h: str) -> str:
    """表头显示：词表和临床词照常显示；剩下的汉字串里像人名的（2–3 个字、常见姓开头）遮蔽；数字、日期、长文字同 render_label。"""
    h = str(h or "").strip()
    if not h or len(h) > 60 or "\n" in h or S.DATE_ANY.search(h):
        return S.render_label(h)
    out = []
    for m in S.TOKEN.finditer(h):
        if not m.group(1):
            out.append(S.render_label(m.group(0)))
            continue
        for iv, t in S.segment(m.group(1)):
            if iv:
                out.append(t)
                continue
            i, rest = 0, []
            while i < len(t):                          # 词表外的串再按临床词最长匹配
                hit = next((t[i:i + k] for k in range(min(MAXK, len(t) - i), 1, -1) if t[i:i + k] in HEAD_KEEP), None)
                if hit:
                    rest.append((True, hit))
                    i += len(hit)
                else:
                    if rest and not rest[-1][0]:
                        rest[-1] = (False, rest[-1][1] + t[i])
                    else:
                        rest.append((False, t[i]))
                    i += 1
            out += [x if ok or not (2 <= len(x) <= 3 and x[0] in S.SURNAMES) else f"〔汉{len(x)}〕" for ok, x in rest]
    return "".join(out)


c5, pct, quant = G.c5, G.pct, G.quant


def k10(n: int) -> bool:
    return n >= K_NAME


# ---------------------------------------------------------------- 名称遮蔽：safe_name 之外，像人名的 2–3 个字再遮
def mask_catalog(names: list[str]) -> dict[str, str]:
    """名称 → 显示文字。名称里词表外的 2–3 个汉字、首字是常见姓、而且在这个目录的不同名称里出现不到 3 次的，当作人名遮蔽。"""
    runs: dict[str, Counter] = {}
    seen: Counter = Counter()
    for n in names:
        segs = []
        for m in S.TOKEN.finditer(n):
            if m.group(1):
                segs += [(iv, t) for iv, t in S.segment(m.group(1))]
            else:
                segs.append((True, m.group(0)))
        runs[n] = segs
        for iv, t in set(segs):
            if not iv:
                seen[t] += 1
    out = {}
    for n, segs in runs.items():
        out[n] = "".join(f"〔汉{len(t)}〕" if (not iv and 2 <= len(t) <= 3 and t[0] in S.SURNAMES and seen[t] < 3) else t for iv, t in segs)
    return out


# ---------------------------------------------------------------- 一张表（在 gam_raw_probe.Tab 上加：低基数取值、表头数据项、ICD、小节标题、按月计数）
class Tab(G.Tab):
    def __init__(self, fid: str, sheet: str, header: list[str]):
        super().__init__(fid, sheet, header)
        for c in self.cols:
            plain = not (c.is_id or c.is_time or c.is_person)
            if plain and not c.is_catalog and EXTRA_CATALOG.search(c.head):
                c.is_catalog = True
            c.low = Counter() if plain else None
            c.items = item_hits(c.head) if not (c.is_id or c.is_person) else []
            c.idset = set() if c.items else None
            c.icd = plain and bool(ICD_HEAD.search(c.head))
            c.n_icd = 0
            c.heads = Counter()
            c.n_long = 0
            c.months = Counter() if c.is_time and VISIT_TIME.search(c.head) else None
            c.text_hits = defaultdict(set) if plain and not c.is_catalog and TEXTSCAN_HEAD.search(c.head) else None
        self.item = next((c for c in self.cols if ITEM_HEAD.search(c.head) and c.is_catalog), None)
        # 宽表里“某某名称”“某某结果”两列碰巧都在时不当长表
        self.long = self.item is not None and self.value is not None and len(self.cols) <= 25
        self.icd_by_id: dict[int, set[str]] = defaultdict(set)
        self.ids_seen: set[int] = set()

    def add(self, row: list) -> None:
        super().add(row)
        kid = None
        if self.key is not None and self.key.j < len(row):
            s = S.as_text(row[self.key.j])
            if s:
                kid = S.h64(S.canon_id(s))
        unit = kid if kid is not None else -self.n          # 没有编号列时按行计
        if len(self.ids_seen) < G.CAP:
            self.ids_seen.add(unit)
        for c in self.cols:
            v = row[c.j] if c.j < len(row) else None
            s = S.as_text(v)
            if s is None:
                continue
            if c.low is not None:
                c.low[s] += 1
                if len(c.low) > LOW_MAX:
                    c.low = None
            if c.idset is not None and len(c.idset) < G.CAP:
                c.idset.add(unit)
            if c.months is not None:
                t, _ = G.dt_of(v)
                if t is not None:
                    c.months[f"{t:%Y-%m}"] += 1
            if c.icd:
                codes = ICD_CODE.findall(s.upper())
                if codes:
                    c.n_icd += 1
                    if len(self.icd_by_id) < G.CAP:
                        self.icd_by_id[unit].update(codes)
            if c.text_hits is not None:
                for x in item_hits(s):
                    if len(c.text_hits[x]) < G.CAP:
                        c.text_hits[x].add(unit)
            if len(s) > TEXT_MIN and not (c.is_id or c.is_person):
                c.n_long += 1
                for h in S.HEADINGS:
                    if h in s:
                        c.heads[h] += 1

    @property
    def per_id_median(self) -> float | None:
        return statistics.median(self.key.per_id.values()) if self.key is not None and self.key.per_id else None

    def role(self) -> str:
        """角色猜测（只看表头和每个编号的行数）。"""
        h = "|".join(self.header)
        one = self.per_id_median is not None and self.per_id_median <= 1.2
        n_items = sum(1 for c in self.cols if c.items)
        if len(self.cols) >= 30 and one and n_items >= 10:
            return "CRF 宽表（一次就诊一行、一项一列）"
        if re.search(r"医嘱|药品|药名", h) and re.search(r"开始|频次|剂量|用法", h):
            return "医嘱 / 处方"
        if re.search(r"结果", h) and re.search(r"项目|名称|子项|明细", h) and re.search(r"单位|参考|范围", h):
            return "检验"
        if re.search(r"所见|影像|检查结论|报告结论", h):
            return "检查"
        if self.long and any(c is self.item for c in self.cols):
            return "长表（项目 + 值：体征 / 护理 / 评估）"
        if re.search(r"体温|脉搏|心率|血压", h) and sum(1 for c in self.cols if c.is_time):
            return "体征宽表（一个体征一列）"
        if re.search(r"诊断", h) and not one and len(self.cols) <= 12:
            return "诊断"
        if re.search(r"入院", h) and re.search(r"出院", h) and one:
            return "就诊主表 / 名单"
        if any(c.n_long and c.lens and statistics.median(c.lens) > 100 for c in self.cols):
            return "病历文书"
        return "其他"


# ---------------------------------------------------------------- 读表
def read_tables(scan: S.Scan, unread: list[str]):
    from openpyxl import load_workbook
    for f in scan.files:
        fid = scan.fid[f]
        kind = S.sniff(f)
        sheets = []
        try:
            if kind == "xlsx":
                wb = load_workbook(f, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    ws.reset_dimensions()               # 有些导出的表尺寸写坏，不重置只能读到第一格
                    sheets.append((ws.title, ws.iter_rows(values_only=True)))
            elif kind == "xls":
                sheets = list(S.iter_xls(f))
            elif kind == "html":
                sheets = list(S.iter_html_tables(f))
            elif kind == "文本" and f.suffix.lower() in (".csv", ".txt", ".tsv"):
                enc, got = S.iter_delimited(f)
                if got:
                    sheets = [("文本表", got[1])]
        except Exception as e:  # noqa: BLE001 —— 医院给的文件可能加密或损坏：记进报告，别的文件照常扫
            unread.append(f"{fid}（{kind}）：{type(e).__name__}")
            continue
        for name, rows in sheets:
            head: list = []
            it = iter(rows)
            for r in it:
                head.append(list(r))
                if len(head) >= 15:
                    break
            h = S.pick_header(head)
            if h is None:
                continue
            t = Tab(fid, name, [(S.as_text(v) or "").strip() for v in head[h]])
            print(f"…{t.label}", file=sys.stderr)
            for r in head[h + 1:]:
                if any(S.as_text(v) for v in r):
                    t.add(list(r))
            empty = 0
            for r in it:
                r = list(r)
                if not any(S.as_text(v) for v in r):
                    empty += 1
                    if empty >= S.EMPTY_STOP:
                        break
                    continue
                empty = 0
                t.add(r)
            yield t


# ---------------------------------------------------------------- flucase 现有格式
def flucase_match(scan: S.Scan) -> list[str]:
    from flucase.repo.formats import builtin_readers, bundle_readers
    lab = lambda x: S.render_label(x, ascii_strict=True)  # noqa: E731
    xl = [f for f in scan.files if f.suffix.lower() in (".xlsx", ".xlsm", ".xls")]
    out = ["### 1.1 单文件格式（逐个文件认）\n", "| 文件 | 格式 | 认定 | 得分 | 认出的 / 差异 |", "|---|---|---|---|---|"]
    n_none = 0
    for f in xl:
        for r in builtin_readers():
            try:
                m = r.match(f)
            except Exception as e:  # noqa: BLE001 —— 一个格式出错照常认别的，报告里写出错类型
                out.append(f"| {scan.fid[f]} | {r.name} | 出错 {type(e).__name__} | — | — |")
                continue
            if m.status == "none" and m.score == 0:
                n_none += 1
                continue
            parts = [lab(x) for x in (m.evidence or [])]
            diffs = "；".join(lab(d.get("detail", "")) for d in (m.differences or [])[:15])
            if len(m.differences or []) > 15:
                diffs += f"；…共 {len(m.differences)} 处"
            parts += [f"差异：{diffs}"] if diffs else []
            out.append(f"| {scan.fid[f]} | {r.name} | {m.status} | {m.score:g} | {'；'.join(parts) or '—'} |")
    out.append(f"\n（另有 {n_none} 个“文件 × 格式”得分为 0，不列。状态：exact 完全符合；similar 相似；none 认不出。）\n")
    out += ["### 1.2 成套格式（整套文件一起认）\n", "| 格式 | 认定 | 得分 | 各文件认成的表 | 缺的表 / 差异 |", "|---|---|---|---|---|"]
    paths = [f for f in xl if f.suffix.lower() != ".xls"]
    for r in bundle_readers():
        try:
            m = r.match_bundle(paths)
        except Exception as e:  # noqa: BLE001
            out.append(f"| {r.name} | 出错 {type(e).__name__} | — | — | — |")
            continue
        roles = "；".join(f"{scan.fid[paths[i]]} {lab(v)}" for i, v in sorted(m.roles.items())[:40]) or "—"
        if len(m.roles) > 40:
            roles += f"；…共 {len(m.roles)} 个文件"
        miss = "、".join(lab(x) for x in m.missing) or "—"
        out.append(f"| {r.name} | {m.status} | {m.score:g} | {roles} | {miss} |")
    return out


# ---------------------------------------------------------------- 报告
def table_section(t: Tab, w) -> None:
    w(f"\n## 表 {t.label}（{t.role()}）\n")
    w("表头：" + " · ".join(render_head(h) or "（空）" for h in t.header) + "\n")
    w("| 列 | 填充 | 类别 | 数值占比 | 数值分布 | 长度 p50 / p90 | 短取值的写法形状 | 对应数据项（按表头） |")
    w("|---|---|---|---|---|---|---|---|")
    for c in t.cols:
        kind = "编号" if c.is_id else ("时间" if c.is_time else ("人员（不看）" if c.is_person else ("目录" if c.is_catalog else "取值")))
        dist = quant(c.nums) if c.nums and not c.is_id and (G.VITAL_HEAD.search(c.head) or c.n_num / max(c.n, 1) > .8 or "年龄" in c.head) else "—"
        ln = f"{statistics.median(c.lens):g} / {sorted(c.lens)[int(.9 * (len(c.lens) - 1))]}" if c.lens else "—"
        shp = "、".join(f"{k}（{pct(v, c.n)}）" for k, v in c.shapes.most_common(3)) if c.shapes and not c.is_catalog else "—"
        items = "、".join(x.split("·", 1)[1] for x in c.items[:3]) or "—"
        w(f"| {render_head(c.head)} | {pct(c.n, t.n)} | {kind} | {pct(c.n_num, c.n) if not (c.is_id or c.is_time) else '—'} | {dist} | {ln} "
          f"| {shp} | {items} |")
    if t.key is not None and t.key.per_id:
        per = sorted(t.key.per_id.values())
        line = f"\n编号列 {render_head(t.key.head)}：{c5(len(per))} 个不同值；每个编号的行数 {quant([float(x) for x in per])}"
        if t.span:
            days = [round((b - a).total_seconds() / 86400, 1) for a, b in t.span.values()]
            line += f"；按 {render_head(t.tcol.head)}，每个编号覆盖的天数 {quant(days)}"
        w(line)
    else:
        w("\n没有认出编号列（下面“编号数”都按行数计）。")
    for c in t.cols:
        if c.is_time and (c.prec or c.t_bad):
            tot = sum(c.prec.values()) + c.t_bad
            w(f"\n时间列 {render_head(c.head)}：能解析 {pct(sum(c.prec.values()), tot)}；精度 " +
              "、".join(f"{p} {pct(n, tot)}" for p, n in c.prec.most_common()) +
              (f"；范围 {c.tmin:%Y-%m} 至 {c.tmax:%Y-%m}" if c.tmin and c.tmax else ""))
            if c.months:
                w("按月行数：" + "、".join(f"{m} {c5(n)}" for m, n in sorted(c.months.items())))
    for c in [c for c in t.cols if c.is_catalog and c.names]:
        if c.lens and statistics.median(c.lens) > 20:
            w(f"\n目录列 {render_head(c.head)}：取值多为长文字（长度中位数 {statistics.median(c.lens):g}），不列写法；{len(c.names)} 种")
            continue
        ok = [(n, len(ids), c.name_rows[n]) for n, ids in c.names.items() if k10(len(ids)) and G.safe_name(n)]
        ok.sort(key=lambda x: -x[2])
        shown = mask_catalog([n for n, _, _ in ok])
        w(f"\n目录列 {render_head(c.head)}：{len(c.names)} 种写法；列出 {len(ok)} 种（≥{K_NAME} 个编号）" +
          (f"，另 {len(c.names) - len(ok)} 种只计数" if len(c.names) > len(ok) else ""))
        if ok:
            w("\n| 写法 | 编号数 | 行数 |")
            w("|---|---|---|")
            for n, k, r in ok[:120]:
                w(f"| {shown[n]} | {k} | {r} |")
            if len(ok) > 120:
                w(f"| …另 {len(ok) - 120} 种 | | |")
    if t.long and t.items:
        ok = [(n, d) for n, d in t.items.items() if k10(len(d["ids"])) and G.safe_name(n)]
        ok.sort(key=lambda x: -x[1]["rows"])
        shown = mask_catalog([n for n, _ in ok])
        w(f"\n长表项目目录（{render_head(t.item.head)} + {render_head(t.value.head)}；{len(t.items)} 种项目，列出 {len(ok)} 种）：\n")
        w("| 项目 | 行数 | 编号数 | 数值占比 | 数值分布 | 常见单位 |")
        w("|---|---|---|---|---|---|")
        for n, d in ok[:200]:
            u = "、".join(f"{k}（{v}）" for k, v in d["u"].most_common(3)) or "—"
            w(f"| {shown[n]} | {d['rows']} | {c5(len(d['ids']))} | {pct(d['num'], d['rows'])} | {quant(d['vals'])} | {u} |")
    kws = [c for c in t.cols if c.kw]
    if kws:
        w("\n文字列关键词（命中的行数，只数不摘）：\n")
        w("| 列 | " + " | ".join(G.KEYWORDS) + " |")
        w("|---|" + "---|" * len(G.KEYWORDS))
        for c in kws:
            w(f"| {render_head(c.head)} | " + " | ".join(str(c.kw.get(k, 0)) for k in G.KEYWORDS) + " |")
    longs = [c for c in t.cols if c.n_long >= K]
    if longs:
        w(f"\n长文字列（>{TEXT_MIN} 字）里出现小节标题 / 词的行数占比：\n")
        for c in longs:
            hs = "、".join(f"{h} {pct(n, c.n_long)}" for h, n in c.heads.most_common(30) if n >= K) or "—"
            w(f"- {render_head(c.head)}（{c.n_long} 行）：{hs}")
    lows = [c for c in t.cols if c.low and c.n_num < .9 * c.n and not c.is_catalog and statistics.median(c.lens) <= 20]
    texty = [c for c in lows if TEXT_LIKE.search(c.head)]
    lows = [c for c in lows if c not in texty]
    if texty:
        w("\n文字类列（主诉、诊断、备注等）即使取值种类少也不列取值，只给种数：" + "、".join(f"{render_head(c.head)} {len(c.low)} 种" for c in texty))
    if lows:
        w("\n低基数列的取值（≤40 种、不是数字列、不是长文字；严格遮蔽后相同的合并，<5 行的和像编号 / 日期的只计数）：\n")
        for c in lows:
            shown: Counter = Counter()
            other = []
            for k, v in c.low.items():
                if v >= K and not S.value_like(k):
                    shown[S.render_label(k, strict=True, keep=LOW_KEEP)] += v
                else:
                    other.append(v)
            vals = "、".join(f"{k}×{v}" for k, v in shown.most_common(25))
            if other:
                vals += f"{'；' if vals else ''}另 {len(other)} 种共 {c5(sum(other))} 行"
            w(f"- {render_head(c.head)}（{len(c.low)} 种）：{vals}")


def coverage_section(tabs: list[Tab], w) -> None:
    w("\n## 3 统一数据项覆盖（特征分析用）\n")
    w("按表头：列名对上这个数据项、有值的编号数（宽表里“否 / 0”也算有值，取值分布看各表的低基数列）。按名称目录：目录列（体征项目、检验名称、医嘱名称、诊断名称等）"
      "里对上这个数据项的名称所覆盖的编号数和名称种数。按文字：诊断、病史、结论、病程一类的文字列里出现这个数据项关键词的编号数（只数关键词，"
      "不判否定，“无发热”也算发热）。编号数按各表自己的编号列；表没有编号列时按行数。\n")
    head_hits: dict[str, list] = defaultdict(list)
    for t in tabs:
        for c in t.cols:
            for x in c.items:
                head_hits[x].append((len(c.idset), t, c))
    cat_hits: dict[str, list] = defaultdict(list)
    for t in tabs:
        cols = [c for c in t.cols if c.is_catalog and c.names]
        for c in cols:
            agg: dict[str, tuple[set, int]] = {}
            for name, ids in c.names.items():
                for x in item_hits(name):
                    s, k = agg.get(x, (set(), 0))
                    agg[x] = (s | ids, k + 1)
            for x, (s, k) in agg.items():
                cat_hits[x].append((len(s), k, t, c))
    text_hits: dict[str, list] = defaultdict(list)
    for t in tabs:
        for c in t.cols:
            for x, s in (c.text_hits or {}).items():
                text_hits[x].append((len(s), t, c))

    def cell(hits: list, fmt) -> str:
        hits = sorted(hits, key=lambda z: -z[0])
        return ("；".join(fmt(*z) for z in hits[:4]) + (f"；…共 {len(hits)} 列" if len(hits) > 4 else "")) or "—"

    for g, lst in ITEMS_C:
        w(f"\n### {g}\n")
        w("| 数据项 | 按表头（表.列：有值的编号数） | 按名称目录（表.列：编号数 / 名称种数） | 按文字（表.列：编号数） |")
        w("|---|---|---|---|")
        for n, _, _ in lst:
            x = f"{g}·{n}"
            hs = cell(head_hits.get(x, []), lambda k, t, c: f"{t.fid}.{render_head(c.head)}：{c5(k)}")
            cs = cell(cat_hits.get(x, []), lambda k, m, t, c: f"{t.fid}.{render_head(c.head)}：{c5(k)} / {m}")
            ts = cell(text_hits.get(x, []), lambda k, t, c: f"{t.fid}.{render_head(c.head)}：{c5(k)}")
            w(f"| {n} | {hs} | {cs} | {ts} |")


def icd_section(tabs: list[Tab], w) -> None:
    have = [t for t in tabs if t.icd_by_id]
    w("\n## 4 诊断编码（ICD-10 写法，按编号计）\n")
    if not have:
        w("没有哪一列的取值像 ICD-10 编码（字母 + 两位数字）。诊断只能按名称（见第 3 节“按名称目录”和各表的目录列）。\n")
        return
    for t in have:
        cols = "、".join(f"{render_head(c.head)}（{c.n_icd} 行）" for c in t.cols if c.n_icd)
        ids = t.icd_by_id
        w(f"\n### {t.label}：{c5(len(ids))} 个编号有编码；列：{cols}\n")
        pref = lambda ps: c5(sum(1 for cs in ids.values() if any(c.startswith(p) for c in cs for p in ps)))  # noqa: E731
        w(f"流感 J09 / J10 / J11：{pref(['J09'])} / {pref(['J10'])} / {pref(['J11'])}；任一 {pref(['J09', 'J10', 'J11'])}\n")
        w("| 类 | 前缀 | 编号数 |")
        w("|---|---|---|")
        for name, ps in list(P.ICD_COM.items()) + list(P.ICD_CLP.items()):
            w(f"| {name} | {'、'.join(ps[:6])}{' 等' if len(ps) > 6 else ''} | {pref(ps)} |")
        j96 = Counter(c[:5] for cs in ids.values() for c in set(cs) if c.startswith("J96"))
        w("\nJ96 细分（前 5 位，按编号）：" + ("、".join(f"{k} {c5(v)}" for k, v in j96.most_common()) or "—"))
        top = Counter(p for cs in ids.values() for p in {c[:3] for c in cs})
        w(f"\n前三位编码（≥{K_NAME} 个编号，前 40 种）：" + ("、".join(f"{k} {v}" for k, v in top.most_common(40) if v >= K_NAME) or "—") + "\n")


def overlap_section(tabs: list[Tab], w) -> None:
    w("\n## 5 编号重合（加盐哈希，只给计数）\n")
    w("每行两列编号（同一工作簿的不同工作表、同一张表的不同编号列也算）：各自有多少个不同值、有多少个相同，相同的占各自的多少。重合 <5 时不给占比。"
      "按重合数从大到小，最多 300 行。\n")
    w("| 表.列 A | A 不同值 | 表.列 B | B 不同值 | 重合 | 占 A / 占 B |")
    w("|---|---|---|---|---|---|")
    idcols = [(t, c) for t in tabs for c in t.cols if c.is_id and c.ids]
    rows = []
    for i, (t, c) in enumerate(idcols):
        for u, d in idcols[i + 1:]:
            k = len(c.ids & d.ids)
            if k:
                rows.append((k, t, c, u, d))
    rows.sort(key=lambda x: -x[0])
    for k, t, c, u, d in rows[:300]:
        share = f"{pct(k, len(c.ids))} / {pct(k, len(d.ids))}" if k >= K else "—"
        w(f"| {t.label}.{render_head(c.head)} | {c5(len(c.ids))} | {u.label}.{render_head(d.head)} | {c5(len(d.ids))} | {c5(k)} | {share} |")
    if not rows:
        w("| （没有重合的编号列） | | | | | |")


def report(scan: S.Scan, tabs: list[Tab], unread: list[str]) -> str:
    L: list[str] = []
    w = L.append
    w("# AH 原始数据扫描（只含结构与计数）\n")
    w(f"- 扫描时间：{dt.datetime.now():%Y-%m-%d %H:%M}；文件 {len(scan.files)} 个，表 {len(tabs)} 张；名字{'未遮蔽' if scan.show else '已遮蔽'}")
    w(f"- 名称目录只列在 ≥{K_NAME} 个编号里出现、无长数字、无人称词、≤60 字的名称，像人名的字再遮蔽；按编号分类的计数 1–4 写成 \"<5\"")
    w("- 表格按文件编号 F001… 引用；文件与编号的对应见文末附录的目录形状（名字遮蔽）" + (f"\n- **读不了的表格文件**：{'；'.join(unread)}" if unread else "") + "\n")
    w("## 1 flucase 现有格式认不认得\n")
    L.extend(flucase_match(scan))
    w("\n## 2 各表概况\n")
    w("| 表 | 角色（猜） | 行数 | 列数 | 编号列（不同值） | 每个编号的行数 p50 | 时间列 | 长表（项目 + 值） |")
    w("|---|---|---|---|---|---|---|---|")
    for t in tabs:
        ids = "、".join(f"{render_head(c.head)}（{c5(len(c.ids))}）" for c in t.cols if c.is_id) or "—"
        tms = "、".join(render_head(c.head) for c in t.cols if c.is_time) or "—"
        lg = f"{render_head(t.item.head)} + {render_head(t.value.head)}" if t.long else "—"
        med = f"{t.per_id_median:g}" if t.per_id_median is not None else "—"
        w(f"| {t.label} | {t.role()} | {t.n} | {len(t.cols)} | {ids} | {med} | {tms} | {lg} |")
    for t in tabs:
        table_section(t, w)
    coverage_section(tabs, w)
    icd_section(tabs, w)
    overlap_section(tabs, w)
    return "\n".join(L)


# ---------------------------------------------------------------- 输入：文件夹、单个文件或压缩包
def name_like(token: str) -> bool:
    """文件名里每次都出现的词会被当成结构词照常显示；导出人、申请人的姓名也每次都出现（11-11 的 AH 报告就漏了一个），所以含姓氏开头的非词表片段的词不当结构词。"""
    return any(not iv and len(x) >= 2 and x[0] in S.SURNAMES for iv, x in S.segment(token)) if S.CJK.match(token) else False


class Scan(S.Scan):
    """单个文件时目录形状只列这个文件：基准目录是它所在的 data/，不能把旁边别的数据也列出来。"""

    def __init__(self, root: Path, show_names: bool, single: bool):
        super().__init__(root, show_names)
        self.single = single

    def tree(self) -> list[str]:
        if not self.single:
            return super().tree()
        return ["（单个文件）", *(f"  {self.name(f.name)}" for f in self.files)]


def collect(root: Path) -> tuple[Path, list[Path], list[Path]]:
    """→ (显示路径的基准目录, 要扫的文件, 临时解包目录)。压缩包解到它旁边的临时文件夹；给的是压缩包时基准目录就是解出来的文件夹。"""
    from flucase.repo.archive import JUNK, expand, is_archive
    tmp: list[Path] = []

    def unpack(arc: Path) -> tuple[Path, list[Path]]:
        d = Path(tempfile.mkdtemp(prefix="_扫描解包_", dir=arc.parent))
        tmp.append(d)
        return d / "x", [p for _, p in expand(arc, d / "x")]

    if root.is_file():
        if is_archive(root.name):
            base, files = unpack(root)
            return base, files, tmp
        return root.parent, [root], tmp
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or JUNK.search(p.relative_to(root).as_posix()):
            continue
        files += unpack(p)[1] if is_archive(p.name) else [p]
    return root, files, tmp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path, help="文件夹、单个文件或压缩包")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--show-names", action="store_true", help="文件名、目录名不遮蔽（研究者确认名字里没有病人信息时才用）")
    ap.add_argument("--no-structure", action="store_true", help="不附通用结构扫描（gd_raw_scan.py）")
    a = ap.parse_args()
    root = a.root.resolve()
    if not root.exists():
        sys.exit(f"路径不存在：{a.root}（路径里有空格要加引号）")
    base, files, tmp = collect(root)
    try:
        single = root.is_file() and base == root.parent
        scan = Scan(base, a.show_names, single)
        scan.files = files
        if single:
            scan.n_units = 0                       # 不看同目录的其他文件，结构词为空
        else:
            scan.build_keep()
            scan.keep = {t for t in scan.keep if not name_like(t)}
        for i, f in enumerate(scan.files):
            scan.fid[f] = f"F{i + 1:03d}"
        tail = ""
        if not a.no_structure:
            t0 = time.time()
            for i, f in enumerate(scan.files):
                if i % 25 == 0:
                    print(f"…结构扫描第 {i + 1}/{len(scan.files)} 个文件（{time.time() - t0:.0f} 秒）", file=sys.stderr)
                scan.one(f)
            tail = "\n\n---\n\n" + "\n".join(("#" + x if x.startswith("#") else x) for x in scan.report().splitlines()).replace(
                "# 原始导出结构扫描", "# 附：通用结构扫描", 1)
        unread: list[str] = []
        tabs = list(read_tables(scan, unread))
        rep = report(scan, tabs, unread) + tail
    finally:
        for d in tmp:
            shutil.rmtree(d)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(rep, encoding="utf-8")
    print(f"报告已写到 {a.out}（{len(tabs)} 张表）", file=sys.stderr)


if __name__ == "__main__":
    main()
