#!/usr/bin/env python3
"""GD 原始导出第二轮扫描：挂接与目录覆盖。只输出计数、列名和遮蔽后的写法，不输出病例内容。

1. 挂接：编号列之间除了完全相等，再试"一个是另一个的一段"（如 8 位编号是 11 位编号的后 8 位）；同一工作簿里行数相同的表能否按行对上；
   名单表的（病案号, 入院日期, 出院日期）能否按时间窗对上各表的住院编号；
2. 目录覆盖：体征项目、检验名称、医嘱名称、检查项目按目标数据项的关键词计数（行数、住院数、命中几种名称、数值占比、单位）；
   名单表诊断编码按 ICD-10 前三位计数，基础病 / 并发症按候选编码范围计数；
3. 低基数列（≤40 种取值、列名与人和编号无关、不是数字列）的取值分布，取值按路径名规则严格遮蔽（词表外的汉字、长英文、≥3 位数字都遮）。

所有按病人数据分类的计数：1–4 写成 "<5"。

用法：python gd_raw_probe.py <目录> [--out 报告.md]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gd_raw_scan as S  # noqa: E402

K = 5
PERSON = re.compile(r"姓名|名字|医生|医师|护士|签名|书写人|记录人|操作员|审核|报告人|申请人|执行人|录入|联系人|电话|地址|身份证|住址|籍贯|"
                    r"工作单位|职业|婚姻|民族|患者|病人|助手|术者|主刀|麻醉医|麻醉师|医师")
IDLIKE = re.compile(r"ID|UUID|号|编号|编码|码$|JZH", re.I)
KEYNAMES = {"ENCT_ID", "ENCT_UUID", "住院号", "病案号", "JZH", "编号", "条码号", "病历号", "就诊号", "流水号", "患者ID", "病人ID", "登记号"}
TIME_HEAD = re.compile(r"时间|日期")
# 取值、正文类列：不管有几种取值都不列（只列编码表一样的列：类别、标本、单位、医嘱类型、病历名称……）
VALUE_HEAD = re.compile(r"结果|^值|内容|正文|所见|影像诊断|备注|医嘱名称|通用名|^名称$|^项目$|其他诊断|规格|剂量|总量|参考")
# “日”前不能用 \s*：会把日期和时间之间的空格先吃掉，后面可选的时间部分就配不上了（文字写的“2023-12-02 14:49:04.0”只剩日期）
DT_RE = re.compile(r"^\s*(\d{4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})(?:\s*日)?(?:[\sT]+(\d{1,2})\s*[:：时]\s*(\d{1,2}))?")


def c5(n: int) -> str:
    return "0" if n == 0 else (str(n) if n >= K else "<5")


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "—"


def to_dt(v) -> dt.datetime | None:
    if isinstance(v, dt.datetime):
        return v
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    s = S.as_text(v)
    if not s:
        return None
    m = DT_RE.match(s)
    if not m:
        return None
    y, mo, d, h, mi = m.groups()
    try:
        return dt.datetime(int(y), int(mo), int(d), int(h or 0), int(mi or 0))
    except ValueError:
        return None


def canon(s: str) -> str:
    return re.sub(r"[^0-9A-Z]", "", S.canon_id(s))


def strict(v: str) -> str:
    return S.render_label(v, strict=True)


def quant(xs: list[float]) -> str:
    if not xs:
        return "—"
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1)))]  # noqa: E731
    return f"p1 {q(.01):g} / p50 {q(.5):g} / p99 {q(.99):g}"


def num(s: str | None) -> float | None:
    m = re.match(r"^\s*[<>＜＞≤≥]?=?\s*([-+]?\d+(?:\.\d+)?)\s*$", s or "")
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------- 目标数据项的关键词（只用来计数）
VITAL = [("体温", r"体温|腋温|耳温|肛温|口温", None), ("脉搏/心率", r"脉搏|心率", None), ("呼吸频率", r"^\s*呼吸\s*(频率|次数)?\s*$|^R$|^RR$", None),
         ("血压", r"血压|收缩压|舒张压", None), ("血氧饱和度", r"血氧|SPO2|氧饱和|指脉氧", None),
         ("吸氧 / 氧流量 / 氧浓度", r"吸氧|氧流量|给氧|氧疗|氧浓度|FIO2|氧气|吸氧方式", None), ("意识", r"意识|神志|GCS|格拉斯哥", None),
         ("身高 / 体重", r"身高|体重|BMI", None), ("出入量", r"尿量|入量|出量|引流", None), ("疼痛", r"疼痛", None), ("大便", r"大便", None)]
LAB = [("LAB001 白细胞", r"白细胞(计数)?|WBC", r"尿|介素|酯酶|镜检|粪|脑脊液|胸水|腹水|分类|形态"),
       ("LAB002 中性粒细胞绝对值", r"中性粒细胞.*(绝对值|计数|数)|NEUT?#|NEU#|GRAN#", r"百分|比|%"),
       ("中性粒细胞百分比", r"中性粒细胞.*(百分|比)|NEUT?%|NEU%", None),
       ("LAB003 淋巴细胞绝对值", r"淋巴细胞.*(绝对值|计数|数)|LYMPH?#|LYM#|LY#", r"百分|比|%|亚群|CD"),
       ("淋巴细胞百分比", r"淋巴细胞.*(百分|比)|LYMPH?%|LYM%|LY%", r"亚群|CD"),
       ("LAB004 血红蛋白", r"血红蛋白|HGB|\bHB\b", r"糖化|尿|平均|浓度|含量|MCH|游离"),
       ("LAB005 血小板", r"血小板(计数)?|PLT", r"压积|分布|平均|体积|大型|聚集|抗体|PCT|MPV|PDW"),
       ("LAB006 C反应蛋白", r"C.?反应蛋白|CRP", None), ("LAB007 降钙素原", r"降钙素原|PROCALCITONIN", None),
       ("LAB008 白介素6", r"白细胞介素.?6|白介素.?6|IL.?6", None), ("LAB009 ALT", r"丙氨酸.*转[氨移]酶|谷丙|\bALT\b|GPT", r"比"),
       ("LAB010 AST", r"天[门冬]+氨酸.*转[氨移]酶|谷草|\bAST\b|GOT", r"比|线粒体"),
       ("LAB011 肌酐", r"肌酐|CREA|\bCR\b|\bSCR\b", r"清除|尿|比|胱抑素"), ("LAB012 尿素", r"尿素|BUN|UREA", r"酶|比|尿液"),
       ("LAB013 D-二聚体", r"D.?二聚体|D.?DIMER|\bDD\b", None), ("LAB014 铁蛋白", r"铁蛋白|FERRITIN", None),
       ("LAB015 乳酸脱氢酶", r"乳酸脱氢酶|\bLDH\b|\bLD\b", r"同工酶"),
       ("钾", r"^钾|\(K\+?\)|\bK\+?\b|血钾", None), ("钠", r"^钠|\(NA\+?\)|\bNA\+?\b|血钠", None),
       ("白蛋白", r"白蛋白|\bALB\b", r"前白蛋白|球蛋白比|尿|微量|比值"), ("血气 氧分压", r"氧分压|PO2|PAO2", r"肺泡|差|比|/"),
       ("血气 二氧化碳分压", r"二氧化碳分压|PCO2|PACO2", None), ("氧合指数", r"氧合指数|PO2/FIO2|P/F", None),
       ("吸入氧浓度（检验单）", r"吸入氧|FIO2", r"/"), ("乳酸", r"^乳酸$|乳酸\(|\bLAC\b|\bLA\b", r"脱氢酶"),
       ("BNP / NT-proBNP", r"BNP|脑钠肽|利钠肽", None), ("肌钙蛋白", r"肌钙蛋白|TNI|TNT|CTN", None),
       ("肌酸激酶", r"肌酸激酶|\bCK\b", r"同工酶|MB"), ("总胆红素", r"总胆红素|TBIL", None),
       ("凝血酶原时间", r"凝血酶原时间|\bPT\b", r"活动度|比值|INR|部分"), ("纤维蛋白原", r"纤维蛋白原|FIB", r"降解"),
       ("流感病毒检测", r"流感|INFLUENZA|FLU", r"副流感|嗜血"), ("新冠病毒检测", r"新型冠状|SARS|COV", None),
       ("其他呼吸道病原", r"合胞|腺病毒|支原体|衣原体|鼻病毒|偏肺|副流感", None)]
ORD = [("TRT001 奥司他韦", r"奥司他韦|达菲|可威", None), ("TRT002 玛巴洛沙韦", r"巴洛沙韦|速福达", None), ("帕拉米韦", r"帕拉米韦", None),
       ("扎那米韦", r"扎那米韦", None), ("法维拉韦 / 阿比多尔", r"法[维匹]拉韦|阿比多尔", None), ("TRT003 金银花（全部）", r"金银花", None),
       ("　其中金银花口服液", r"金银花口服液", None), ("TRT004 痰热清", r"痰热清", None), ("TRT005 化湿败毒", r"化湿败毒", None),
       ("连花清瘟", r"连花清瘟", None), ("TRT006 无创通气", r"无创|BIPAP|CPAP|双水平", None),
       ("TRT007 有创 / 机械通气", r"有创|机械通气|呼吸机辅助|呼吸机", r"无创"), ("气管插管 / 切开", r"气管插管|气管切开|经口插管", None),
       ("高流量氧疗", r"高流量|HFNC", None), ("吸氧", r"吸氧|氧疗|给氧|鼻导管|面罩", r"高流量"), ("TRT009 ECMO", r"ECMO|体外膜", None),
       ("CRRT / 血液净化", r"CRRT|血液净化|血滤|血液透析|连续性肾", None),
       ("升压药", r"去甲肾上腺素|多巴胺|间羟胺|血管加压素|垂体后叶素|肾上腺素", r"多巴酚丁胺"),
       ("糖皮质激素", r"甲泼尼龙|甲强龙|地塞米松|氢化可的松|泼尼松|强的松", None), ("病危 / 病重", r"病危|病重", None),
       ("转科 / 转ICU", r"转科|转入|转.{0,3}(ICU|重症|监护)", None), ("死亡", r"死亡|尸体", None), ("出院", r"出院", None)]
IMG_ITEM = [("胸部 CT", r"(胸|肺).*CT|CT.*(胸|肺)", None), ("胸片 / DR", r"DR|X线|胸片|摄片|平片", r"CT"), ("头颅", r"头|颅", None),
            ("腹部", r"腹", None), ("心脏超声", r"心脏|超声心动", None)]
IMG_WORDS = ["肺炎", "炎症", "炎性", "感染", "渗出", "磨玻璃", "实变", "胸腔积液", "气胸", "纵隔气肿", "间质", "结节"]
ICD_COM = {"COM001 COPD": ["J44"], "COM002 哮喘": ["J45", "J46"], "COM003 支气管扩张": ["J47"], "COM004 冠心病": [f"I2{i}" for i in range(6)],
           "COM005 心力衰竭": ["I50"], "COM006 糖尿病": [f"E1{i}" for i in range(5)], "COM007 CKD": ["N18", "N19"],
           "COM008 肿瘤": [f"C{i:02d}" for i in range(98)], "COM009 脑卒中": [f"I6{i}" for i in range(10)],
           "COM010 免疫抑制": ["D80", "D81", "D82", "D83", "D84", "B20", "B21", "B22", "B23", "B24", "Z94"],
           "（参考）高血压": ["I10", "I11", "I12", "I13", "I15"], "（参考）慢性肺心病": ["I27"]}
ICD_CLP = {"CLP001 病毒性肺炎": ["J12", "J10.0", "J11.0"], "CLP002 细菌性 / 混合性肺炎": ["J13", "J14", "J15", "J16", "J17", "J18"],
           "CLP003/004 呼吸衰竭": ["J96"], "CLP005 ARDS": ["J80"], "CLP006 胸腔积液": ["J90", "J91", "J94.8"], "CLP007 气胸 / 纵隔气肿": ["J93", "J98.2"],
           "CLP008 （急性）心衰": ["I50"], "CLP009 心肌损伤 / 心肌炎": ["I40", "I41", "I51.4"], "CLP010 心律失常": ["I44", "I45", "I46", "I47", "I48", "I49"],
           "CLP011 急性冠脉综合征": ["I20.0", "I21", "I22", "I24"], "CLP012 脓毒症": ["A40", "A41"], "CLP013 感染性休克": ["R57", "R65.2"],
           "CLP014 急性肾损伤": ["N17"], "CLP015 急性肝损伤": ["K72", "K71", "R74.0"], "CLP016 脑病 / 脑炎": ["G04", "G05", "G93.4"],
           "CLP017 意识障碍 / 谵妄": ["F05", "R40", "R41.0"], "CLP018 DIC": ["D65"], "CLP019 横纹肌溶解": ["M62.8", "T79.6"],
           "CLP020 MODS": ["R65.3", "R68.8"], "CLP021 低钾血症": ["E87.6"], "CLP022 低钠血症": ["E87.1"], "CLP023 低蛋白血症": ["E88.0", "E77"]}
ICD_CODE = re.compile(r"[A-Z]\d{2}(?:\.[0-9A-Za-z]+)?[+*]?")


def compile_concepts(lst):
    return [(n, re.compile(a, re.I), re.compile(b, re.I) if b else None) for n, a, b in lst]


VITAL_C, LAB_C, ORD_C, IMG_C = (compile_concepts(x) for x in (VITAL, LAB, ORD, IMG_ITEM))


def hits(concepts, text: str) -> list[str]:
    return [n for n, a, b in concepts if a.search(text) and not (b and b.search(text))]


# ---------------------------------------------------------------- 一张表
def role_of(h: set[str]) -> str:
    if {"病案号", "入院日期", "出院日期"} <= h:
        return "名单"
    if "医嘱名称" in h:
        return "医嘱"
    if "项目" in h and "值1" in h:
        return "体征"
    if "名称" in h and "结果" in h:
        return "检验"
    if "影像所见" in h or "影像诊断" in h:
        return "检查"
    return "其他"


class T:
    def __init__(self, label: str, header: list[str]):
        self.label, self.header = label, header
        self.ix = {h.strip(): j for j, h in enumerate(header) if h and h.strip()}
        self.role = role_of(set(self.ix))
        self.n = 0
        self.low: dict[int, Counter] = {j: Counter() for j, h in enumerate(header)
                                        if not (h and (PERSON.search(h) or IDLIKE.search(h) or TIME_HEAD.search(h) or VALUE_HEAD.search(h)))
                                        and h}
        self.numeric: Counter = Counter()
        self.keys: dict[str, set[str]] = {h: set() for h in self.ix if h in KEYNAMES}
        self.rowkeys: list[dict[str, str]] = []
        self.pairs: dict[tuple[str, str], dict[str, Counter]] = {}
        ks = sorted(self.keys)
        for a in range(len(ks)):
            for b in range(len(ks)):
                if a != b:
                    self.pairs[(ks[a], ks[b])] = defaultdict(Counter)
        self.tcol = next((h for h in ("开始时间", "记录时间", "报告时间", "采集时间", "报告日期", "书写时间") if h in self.ix), None)
        self.pcol = next((h for h in ("住院号", "病案号") if h in self.ix), None)
        self.enc: dict[str, dict] = {}
        self.c: dict = defaultdict(lambda: {"rows": 0, "enc": set(), "names": set(), "num": 0, "v2": 0, "u": Counter(), "sp": Counter(),
                                            "vals": [], "vals2": [], "t1": Counter(), "t2": Counter(), "stop": 0, "icu": 0, "res": Counter()})
        self.unmatched_rows, self.unmatched_names = 0, set()
        self.cohort: dict = defaultdict(list)
        self.icu_enc: set[str] = set()
        self.icu_depts: set[str] = set()
        self.img_words: Counter = Counter()

    def g(self, row, h):
        j = self.ix.get(h)
        return S.as_text(row[j]) if j is not None and j < len(row) else None

    def add(self, row: list) -> None:
        self.n += 1
        for j, ctr in self.low.items():
            if ctr is None or j >= len(row):
                continue
            s = S.as_text(row[j])
            if s is None:
                continue
            if num(s) is not None or isinstance(row[j], (int, float)):
                self.numeric[j] += 1
            ctr[s] += 1
            if len(ctr) > 40:
                self.low[j] = None
        rk = {}
        for h, st in self.keys.items():
            s = self.g(row, h)
            if s:
                cs = canon(s)
                if len(st) < 50000:
                    st.add(cs)
                rk[h] = cs
        if self.n <= 5000:
            self.rowkeys.append(rk)
        for (a, b), m in self.pairs.items():
            if a in rk and b in rk and len(m) < 50000:
                m[rk[a]][rk[b]] += 1
        if "ENCT_ID" in rk and self.pcol and self.tcol:
            e = self.enc.setdefault(rk["ENCT_ID"], {"p": Counter(), "t": None})
            if self.pcol in rk:
                e["p"][rk[self.pcol]] += 1
            t = to_dt(row[self.ix[self.tcol]] if self.ix[self.tcol] < len(row) else None)
            if t and (e["t"] is None or t < e["t"]):
                e["t"] = t
        getattr(self, "_" + {"名单": "cohort_row", "医嘱": "order", "体征": "vital", "检验": "lab", "检查": "img"}.get(self.role, "noop"))(row, rk)

    def _noop(self, row, rk):
        pass

    def _vital(self, row, rk):
        item = (self.g(row, "项目") or "").upper()
        hs = hits(VITAL_C, item)
        if not hs:
            self.unmatched_rows += 1
            self.unmatched_names.add(item)
        v1, v2 = self.g(row, "值1"), self.g(row, "值2")
        for h in hs:
            c = self.c[h]
            c["rows"] += 1
            c["enc"].add(rk.get("ENCT_ID"))
            c["names"].add(item)
            n1 = num(v1)
            if n1 is not None:
                c["num"] += 1
                if len(c["vals"]) < 20000:
                    c["vals"].append(n1)
            if v2:
                c["v2"] += 1
                n2 = num(v2)
                if n2 is not None and len(c["vals2"]) < 20000:
                    c["vals2"].append(n2)
            u = self.g(row, "单位")
            c["u"][strict(u) if u else "（空）"] += 1
            for k in ("值3", "值4", "值5"):
                if self.g(row, k):
                    c["t1"][k] += 1

    def _lab(self, row, rk):
        name = (self.g(row, "名称") or "").upper()
        hs = hits(LAB_C, name)
        if not hs:
            self.unmatched_rows += 1
            self.unmatched_names.add(name)
        res = self.g(row, "结果")
        for h in hs:
            c = self.c[h]
            c["rows"] += 1
            c["enc"].add(rk.get("JZH") or rk.get("ENCT_ID"))
            c["names"].add(name)
            if num(res) is not None:
                c["num"] += 1
            elif res and h.startswith(("流感", "新冠", "其他呼吸道")):
                c["res"][strict(res)] += 1
            u, sp = self.g(row, "结果单位"), self.g(row, "标本类型")
            c["u"][strict(u) if u else "（空）"] += 1
            c["sp"][strict(sp) if sp else "（空）"] += 1

    def _order(self, row, rk):
        name = (self.g(row, "医嘱名称") or "") + " " + (self.g(row, "通用名") or "")
        dept = self.g(row, "科室") or ""
        icu = bool(re.search(r"ICU|重症|监护", dept, re.I))
        if icu:
            self.icu_enc.add(rk.get("ENCT_ID"))
            self.icu_depts.add(dept)
        for h in hits(ORD_C, name.upper()):
            c = self.c[h]
            c["rows"] += 1
            c["enc"].add(rk.get("ENCT_ID"))
            c["names"].add(name)
            t1, t2 = self.g(row, "医嘱类型"), self.g(row, "普通或出院")
            c["t1"][strict(t1) if t1 else "（空）"] += 1
            c["t2"][strict(t2) if t2 else "（空）"] += 1
            c["stop"] += bool(self.g(row, "停止时间"))
            c["icu"] += icu

    def _img(self, row, rk):
        item = (self.g(row, "项目") or "").upper()
        for h in hits(IMG_C, item) or ["（其他项目）"]:
            c = self.c[h]
            c["rows"] += 1
            c["enc"].add(rk.get("ENCT_ID"))
            c["names"].add(item)
        text = (self.g(row, "影像所见") or "") + "\n" + (self.g(row, "影像诊断") or "")
        for w in IMG_WORDS:
            if w in text:
                self.img_words[w] += 1

    def _cohort_row(self, row, rk):
        co = self.cohort
        a = to_dt(row[self.ix["入院日期"]]) if self.ix["入院日期"] < len(row) else None
        d = to_dt(row[self.ix["出院日期"]]) if self.ix["出院日期"] < len(row) else None
        co["rows"].append((rk.get("病案号"), a, d))
        for h in ("年龄", "天数"):
            v = num(self.g(row, h))
            if v is not None:
                co[h].append(v)
        if a:
            co["month"].append(f"{a:%Y-%m}")
        for h in ("ICD码", "主要诊断ICD码"):
            co[h].append((self.g(row, h) or "").upper())
        other = (self.g(row, "其他诊断ICD码") or "").upper()
        co["other"].append(other)
        names = self.g(row, "其他诊断疾病名称") or ""
        codes = ICD_CODE.findall(other)
        seps = re.sub(r"[A-Z0-9.+*]", "", other)
        co["sep"].append(seps)
        nsplit = len([x for x in re.split(r"[,，;；|、\s]+", names) if x]) if names else 0
        co["pair"].append((len(codes), nsplit))


def read_tables(scan: S.Scan):
    from openpyxl import load_workbook
    for f in scan.files:
        fid = scan.fid[f]
        kind = S.sniff(f)
        sheets = []
        try:
            if kind == "xlsx":
                wb = load_workbook(f, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    ws.reset_dimensions()
                    sheets.append((ws.title, ws.iter_rows(values_only=True)))
            elif kind == "xls":
                sheets = list(S.iter_xls(f))
            elif kind == "html":
                sheets = list(S.iter_html_tables(f))
            elif kind == "文本":
                enc, got = S.iter_delimited(f)
                if got:
                    sheets = [("文本表", got[1])]
        except Exception as e:  # noqa: BLE001
            print(f"{fid} 读不了：{type(e).__name__}", file=sys.stderr)
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
            header = [S.as_text(v) or "" for v in head[h]]
            t = T(f"{fid}“{S.render_label(name, ascii_strict=True)}”", header)
            print(f"…{t.label}（{t.role}）", file=sys.stderr)
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
            yield f, t


# ---------------------------------------------------------------- 报告
def concept_table(t: T, cols: list[str], fmt) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for name, *_ in {"体征": VITAL, "检验": LAB, "医嘱": ORD, "检查": IMG_ITEM + [("（其他项目）",)]}[t.role]:
        c = t.c.get(name)
        out.append(fmt(name, c) if c else "| " + name + " | 0 |" + " |" * (len(cols) - 2))
    return out


def report(scan: S.Scan, tables: list[tuple[Path, T]]) -> str:
    L: list[str] = []
    w = L.append
    w("# GD 原始导出第二轮扫描：挂接与目录覆盖（只含计数、列名和遮蔽后的写法）\n")
    w("计数 1–4 写成 <5；“住院数”按各表自己的住院编号去重。\n")
    w("## 1 读到的表\n")
    w("| 表 | 认成 | 数据行 | 编号列 |")
    w("|---|---|---|---|")
    for _, t in tables:
        w(f"| {t.label} | {t.role} | {t.n} | {'、'.join(f'{k}（{len(v)}）' for k, v in t.keys.items()) or '—'} |")
    w("")
    # ---- 挂接
    w("## 2 编号挂接\n")
    w("### 2.1 不同表的编号列：完全相等之外，试“一个是另一个的一段”\n")
    w("| A | B | A 不同值 | B 不同值 | 完全相等 | A 是 B 的一段 | B 是 A 的一段 | 常见位置 |")
    w("|---|---|---|---|---|---|---|---|")
    cols = [(t, k, v) for _, t in tables for k, v in t.keys.items() if v and len(v) <= 30000]
    seen_rows = 0
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            ta, ka, va = cols[i]
            tb, kb, vb = cols[j]
            if ta is tb:
                continue
            eq = len(va & vb)

            def sub(x: set[str], y: set[str]) -> tuple[int, Counter]:
                lens = {len(s) for s in x}
                where: dict[str, tuple[int, int]] = {}
                for s in y:
                    for L_ in lens:
                        for o in range(0, len(s) - L_ + 1):
                            where.setdefault(s[o:o + L_], (len(s), o))
                pos = Counter()
                n = 0
                for s in x:
                    if s in where and where[s][0] != len(s):
                        n += 1
                        ln, o = where[s]
                        pos[f"长 {ln} 位里的第 {o + 1}–{o + len(s)} 位"] += 1
                return n, pos

            na, pa = sub(va, vb)
            nb, pb = sub(vb, va)
            m = min(len(va), len(vb))
            if max(eq, na, nb) < 0.05 * m:
                continue
            pos = (pa + pb).most_common(2)
            w(f"| {ta.label}[{ka}] | {tb.label}[{kb}] | {len(va)} | {len(vb)} | {eq} | {na} | {nb} | {'；'.join(f'{p}×{c5(n)}' for p, n in pos) or '—'} |")
            seen_rows += 1
    if not seen_rows:
        w("| — | — | — | — | — | — | — | 没有重合 ≥5% 的 |")
    w("")
    # 同一工作簿里行数相同的表按行对
    w("### 2.2 同一工作簿里行数相同的表能否按行对上\n")
    by_file: dict[Path, list[T]] = defaultdict(list)
    for f, t in tables:
        by_file[f].append(t)
    maps = [(t, a, b, m) for _, t in tables for (a, b), m in t.pairs.items() if m]
    any_row = False
    for f, ts in by_file.items():
        for i in range(len(ts)):
            for j in range(len(ts)):
                t1, t2 = ts[i], ts[j]
                if i == j or t1.n != t2.n or t1.n > 5000:
                    continue
                for x in t1.keys:
                    for y in t2.keys:
                        xs = [r.get(x) for r in t1.rowkeys]
                        ys = [r.get(y) for r in t2.rowkeys]
                        best = ("直接相等", sum(1 for a, b in zip(xs, ys) if a and a == b))
                        for tm, a, b, m in maps:
                            if tm in (t1, t2):
                                continue
                            agree = sum(1 for xv, yv in zip(xs, ys) if yv in m and m[yv].most_common(1)[0][0] == xv)
                            if agree > best[1]:
                                best = (f"经 {tm.label} 的 [{a}]→[{b}]", agree)
                        if best[1]:
                            any_row = True
                            w(f"- {t2.label}[{y}] 第 i 行 ↔ {t1.label}[{x}] 第 i 行：{best[0]}，{best[1]}/{t1.n} 行一致")
    if not any_row:
        w("- 没有能按行对上的表")
    w("")
    # 名单按时间窗对住院编号
    co_t = next((t for _, t in tables if t.role == "名单"), None)
    w("### 2.3 名单表（病案号 + 入院 / 出院日期）按时间窗对各表的住院编号\n")
    if co_t is None:
        w("- 没有认出名单表\n")
    else:
        w("| 来源表 | 住院编号数 | 名单行：唯一对上 | 对上多个 | 没对上 | 来源表里没被名单对上的住院 |")
        w("|---|---|---|---|---|---|")
        for _, t in tables:
            if not t.enc:
                continue
            by_p: dict[str, list[tuple[str, dt.datetime | None]]] = defaultdict(list)
            for e, d in t.enc.items():
                if d["p"]:
                    by_p[d["p"].most_common(1)[0][0]].append((e, d["t"]))
            uni = mul = none = 0
            used = set()
            for p, a, d in co_t.cohort["rows"]:
                cand = [e for e, t0 in by_p.get(p, []) if t0 and a and (a - dt.timedelta(days=2)) <= t0 <= ((d or a) + dt.timedelta(days=2))]
                if len(cand) == 1:
                    uni += 1
                    used.add(cand[0])
                elif cand:
                    mul += 1
                    used.update(cand)
                else:
                    none += 1
            w(f"| {t.label}（{t.role}，时间取[{t.tcol}]、病人取[{t.pcol}]） | {len(t.enc)} | {uni} | {c5(mul)} | {c5(none)} | {c5(len(set(t.enc) - used))} |")
        w("")
    # ---- 目录覆盖
    w("## 3 目录覆盖（按目标数据项的关键词计数）\n")
    order = {"体征": 0, "检验": 1, "医嘱": 2, "检查": 3}
    for _, t in sorted(tables, key=lambda x: order.get(x[1].role, 9)):
        if t.role == "体征":
            w(f"### 3.1 体征 {t.label}：数据行 {t.n}；没命中任何关键词的 {t.unmatched_rows} 行、{len(t.unmatched_names)} 种项目名\n")
            L.extend(concept_table(t, ["数据项", "行数", "住院数", "命中几种项目名", "值1 是数字", "值2 有值", "值1 分布", "值2 分布", "单位（遮蔽）", "值3–5 有值"],
                                   lambda n, c: f"| {n} | {c['rows']} | {c5(len(c['enc']))} | {len(c['names'])} | {pct(c['num'], c['rows'])} | "
                                                f"{pct(c['v2'], c['rows'])} | {quant(c['vals'])} | {quant(c['vals2'])} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['u'].most_common(3))} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['t1'].most_common(3)) or '—'} |"))
            w("")
        if t.role == "检验":
            w(f"### 3.2 检验 {t.label}：数据行 {t.n}；没命中任何关键词的 {t.unmatched_rows} 行、{len(t.unmatched_names)} 种名称\n")
            L.extend(concept_table(t, ["数据项", "行数", "住院数", "命中几种名称", "结果是数字", "单位（遮蔽）", "标本（遮蔽）", "非数字结果（遮蔽）"],
                                   lambda n, c: f"| {n} | {c['rows']} | {c5(len(c['enc']))} | {len(c['names'])} | {pct(c['num'], c['rows'])} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['u'].most_common(3))} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['sp'].most_common(3))} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['res'].most_common(4)) or '—'} |"))
            w("")
        if t.role == "医嘱":
            w(f"### 3.3 医嘱 {t.label}：数据行 {t.n}；科室名含 ICU / 重症 / 监护的科室 {len(t.icu_depts)} 个，在这些科室有医嘱的住院 {c5(len(t.icu_enc))} 次\n")
            L.extend(concept_table(t, ["数据项", "行数", "住院数", "命中几种医嘱名", "医嘱类型（遮蔽）", "普通或出院（遮蔽）", "有停止时间", "在 ICU 类科室"],
                                   lambda n, c: f"| {n} | {c['rows']} | {c5(len(c['enc']))} | {len(c['names'])} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['t1'].most_common(3))} | "
                                                f"{'、'.join(f'{u}×{c5(k)}' for u, k in c['t2'].most_common(3))} | {pct(c['stop'], c['rows'])} | {pct(c['icu'], c['rows'])} |"))
            w("")
        if t.role == "检查":
            w(f"### 3.4 检查 {t.label}：数据行 {t.n}\n")
            L.extend(concept_table(t, ["检查项目", "行数", "住院数", "命中几种项目名"],
                                   lambda n, c: f"| {n} | {c['rows']} | {c5(len(c['enc']))} | {len(c['names'])} |"))
            w("")
            w("所见 + 诊断里出现这些词的报告数：" + "、".join(f"{k} {c5(v)}" for k, v in t.img_words.most_common()) + "\n")
    if co_t is not None:
        co = co_t.cohort
        w(f"### 3.5 名单表 {co_t.label}：{co_t.n} 行\n")
        w(f"- 年龄：{quant(co['年龄'])}；最小 {min(co['年龄']) if co['年龄'] else '—':g}、最大 {max(co['年龄']) if co['年龄'] else '—':g}" if co["年龄"] else "- 年龄：—")
        w(f"- 住院天数：{quant(co['天数'])}")
        months = Counter(co["month"])
        w("- 入院月份：" + "、".join(f"{m} {c5(n)}" for m, n in sorted(months.items())))

        def pref(codes: list[str], n: int, top: int) -> str:
            ctr = Counter(c[:n] for c in codes if c)
            big = [(k, v) for k, v in ctr.most_common() if v >= K]
            small = sum(v for k, v in ctr.items() if v < K)
            return "、".join(f"{k} {v}" for k, v in big[:top]) + (f"；其他 {len(ctr) - len(big[:top])} 种共 {small + sum(v for k, v in big[top:])} 次" if len(ctr) > len(big[:top]) else "")
        w(f"- 流感诊断编码（ICD码）前 5 位：{pref(co['ICD码'], 5, 15)}")
        w(f"- 主要诊断编码前 3 位：{pref(co['主要诊断ICD码'], 3, 20)}")
        w(f"- 主要诊断是流感（J09–J11）的：{c5(sum(1 for c in co['主要诊断ICD码'] if c[:3] in ('J09', 'J10', 'J11')))} / {co_t.n}")
        allcodes = [c for s in co["other"] for c in ICD_CODE.findall(s)]
        per_row = [len(ICD_CODE.findall(s)) for s in co["other"]]
        sep = Counter(ch for s in co["sep"] for ch in s)
        w(f"- 其他诊断编码：每行 {quant(per_row)} 个；编码之间的分隔符 " + "、".join(f"{ch!r}×{n}" for ch, n in sep.most_common(5)))
        eqn = sum(1 for a, b in co["pair"] if a == b)
        w(f"- 其他诊断：编码个数与名称个数（按逗号、分号、顿号、空白切）相同的行 {eqn}/{len(co['pair'])}")
        w(f"- 其他诊断编码前 3 位（≥5 次的）：{pref(allcodes, 3, 60)}")
        w("")
        w("候选基础病 / 并发症编码范围在名单表里能找到的住院数（主要诊断 + 其他诊断；只是可行性计数，编码范围待研究者定）：\n")
        w("| 数据项 | 编码范围 | 住院数 |")
        w("|---|---|---|")
        rows_codes = [set(ICD_CODE.findall(o)) | ({m} if m else set()) for o, m in zip(co["other"], co["主要诊断ICD码"])]
        for d in (ICD_COM, ICD_CLP):
            for name, prefs in d.items():
                n = sum(1 for cs in rows_codes if any(c.startswith(p) for c in cs for p in prefs))
                w(f"| {name} | {'、'.join(prefs[:6])}{' 等' if len(prefs) > 6 else ''} | {c5(n)} |")
        j96 = Counter(c[:5] for cs in rows_codes for c in cs if c.startswith("J96"))
        w(f"\nJ96 细分（前 5 位）：" + ("、".join(f"{k} {c5(v)}" for k, v in j96.most_common()) or "—") + "\n")
    # ---- 低基数列
    w("## 4 低基数列的取值（≤40 种、列名与人和编号无关、不是数字列；取值严格遮蔽，<5 行的合并）\n")
    for _, t in tables:
        for j, ctr in t.low.items():
            if not ctr or t.numeric[j] >= 0.9 * sum(ctr.values()):
                continue
            big = [(k, v) for k, v in ctr.most_common() if v >= K]
            small = [(k, v) for k, v in ctr.items() if v < K]
            vals = "、".join(f"{strict(k)}×{v}" for k, v in big[:25])
            if small:
                vals += f"；另 {len(small)} 种各 <5 行"
            w(f"- {t.label}[{S.render_label(t.header[j]) or S.col_letter(j)}]（{len(ctr)} 种）：{vals}")
    w("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    scan = S.Scan(a.root.resolve(), False)
    import os
    for dp, dns, fns in os.walk(scan.root):
        dns[:] = sorted(d for d in dns if not d.startswith("."))
        for fn in sorted(fns):
            if fn.startswith(".") or fn.startswith("~$") or fn == "Thumbs.db":
                continue
            scan.files.append(Path(dp) / fn)
    scan.build_keep()
    for i, f in enumerate(scan.files):
        scan.fid[f] = f"F{i + 1:03d}"
    tables = list(read_tables(scan))
    rep = report(scan, tables)
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
        print(f"报告已写到 {a.out}", file=sys.stderr)
    print(rep)


if __name__ == "__main__":
    main()
