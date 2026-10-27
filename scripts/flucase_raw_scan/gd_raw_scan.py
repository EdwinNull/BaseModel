#!/usr/bin/env python3
"""医院原始导出的结构扫描：只输出结构与计数，不输出任何病例内容。

输出：文件类型与数量；目录形状（名字遮蔽：〔汉N〕〔数N〕〔字母N〕）；每类表格的工作表名、表头（列名）、行数，
每列的填充数、取值类型、长度、写法形状（汉字→汉、字母→a、数字→9）；编号列每个值占几行；不同表的编号列重合多少（只给计数）；
文书类文件的数量、长度与固定小节标题出现的比例。

不输出：任何单元格取值、文件名原文（除非 --show-names）、病历正文的任何片段。编号重合用本次随机加盐的哈希计算，盐不落盘。

用法：python3 gd_raw_scan.py <目录> [--out 报告.md] [--show-names]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import math
import os
import re
import secrets
import statistics
import subprocess
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

SALT = secrets.token_bytes(16)
SAMPLE = 20000            # 每列最多留这么多个值做长度、形状统计（蓄水池抽样）
KEY_CAP = 300000          # 编号列最多记这么多个不同值
BUFFER = 2000             # 先看这么多行再决定哪些列是编号候选
EMPTY_STOP = 5000         # 连续这么多空行就认为表结束（有些导出的表尺寸写错）
DOC_CAP = 200             # 同类文书最多解析这么多个（其余只计数）

# ---------------------------------------------------------------- 遮蔽
SURNAMES = set(
    "王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范"
    "金石廖贾夏韦付傅方白邹孟熊秦邱江尹薛闫阎段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤常温康施文牛樊葛邢安齐易乔伍庞"
    "颜倪庄聂章鲁岳翟殷詹申欧耿关兰焦俞左柳甘祝包宁尚符舒阮柯纪梅童凌毕单季裴霍涂成苗谷盛曲翁冉骆蓝路游辛靳管柴蒙鲍华喻祁"
    "蒲房滕屈饶解牟艾尤阳时穆农司卓古吉缪简车项连芦麦褚娄窦戚岑景党宫费卜冷晏席卫米柏宗瞿桂全佟应臧闵苟邬边卞姬师和仇栾隋"
    "商刁沙荣巫寇桑郎甄丛仲虞敖巩明佘池查麻苑迟邝区练利钮蔺凤谈")
# 表名、列名、文书名里常见的词（遮蔽时这些词照常显示，其余汉字按规则遮蔽）
VOCAB = set("""
住院 门诊 急诊 留观 病人 患者 病案 病历 首页 医嘱 长期 临时 检验 检查 化验 结果 报告 明细 项目 子项 名称 代码 编码 诊断 主要 次要
其他 其它 出院 入院 转科 转入 转出 转院 手术 麻醉 护理 记录 体温 体征 生命 测量 时间 日期 开始 结束 停止 执行 开立 下达 开嘱 停嘱
医生 医师 护士 科室 病区 床号 床位 姓名 性别 年龄 出生 民族 职业 婚姻 籍贯 地址 电话 身份证 证件 号码 编号 序号 住院号 病案号
病历号 门诊号 急诊号 登记号 就诊 流水号 流水 关联 字段 标识 类型 类别 分类 状态 内容 文书 正文 标题 描述 所见 结论 意见 印象 部位
方法 标本 样本 单位 参考 范围 参考值 异常 标志 标记 提示 危急值 危急 药品 药物 剂量 规格 频次 频率 用法 途径 给药 数量 金额 费用
费别 价格 处方 草药 中药 西药 成药 中成药 饮片 治疗 用药 首次 病程 日常 查房 会诊 讨论 抢救 死亡 转归 离院 方式 情况 天数 主诉
现病史 既往史 个人史 家族史 婚育史 月经史 过敏史 体格 辅助 专科 初步 修正 补充 确定 最后 最终 签名 书写 创建 修改 审核 确认 申请
采集 采样 接收 报告人 操作员 操作 录入 导出 数据 信息 汇总 列表 统计 清单 主表 子表 详情 基本 人口学 汇总表 附表 说明 字典 变量
结构化 非结构化 原始 全部 合并症 并发症 既往 病史 症状 体检 影像 放射 超声 心电图 心电 内镜 病理 核酸 抗原 抗体 流感 病毒 甲型
乙型 新冠 呼吸 呼吸科 重症 监护 危重 医学科 内科 外科 中医 西医 证候 证型 舌象 脉象 治法 方药 疗效 随访 复诊 初诊 挂号 收费
结算 医保 自费 费用 总费用 药费 床位费 检验费 检查费 护理费 入科 出科 在院 离科 一般 特级 一级 二级 三级 等级 级别 病情 病重
病危 通知 通知书 同意书 知情 委托 告知 协议 评估 评分 量表 风险 跌倒 压疮 营养 疼痛 出入量 入量 出量 尿量 血压 收缩压 舒张压
脉搏 心率 血氧 饱和度 氧饱和度 吸氧 氧疗 呼吸机 无创 有创 通气 插管 气管 机械 体重 身高 指数 白细胞 中性粒细胞 淋巴细胞 血红蛋白
血小板 反应蛋白 降钙素原 白介素 肌酐 尿素 尿素氮 转氨酶 胆红素 白蛋白 乳酸 血气 分压 氧分压 二氧化碳 钾 钠 氯 钙 血糖 凝血 二聚体
铁蛋白 肌钙蛋白 脑钠肽 计数 百分比 绝对值 比率 浓度 含量 定量 定性 阳性 阴性 正常 偏高 偏低 男 女 年 月 日 时 分 秒 岁 天 次 号 名 码
值 人 期 级 表 单 页 栏 列 行 份 套 版 号码 编码 院区 本部 分院 医院 中医院 人民医院 广东省 省 市 区 县 广州 大学 附属 第一 第二
批次 来源 系统 平台 接口 视图 查询 结果表 主索引 索引 首页表 医技 申请单 报告单 检验单 检查单 条码 样本号 标本号 医嘱号 处方号
疫苗 接种 基础病 模块 合并 吸烟 饮酒 嗜好 职业史 生化 血常规 尿常规 便常规 肝功能 肾功能 电解质 心肌酶 炎症 指标 免疫 微生物 培养 药敏
细菌 真菌 涂片 痰 咽拭子 鼻拭子 拭子 胸片 胸部 平扫 增强 肺部 肺炎 感染 发热 咳嗽 咳痰 咽痛 肌痛 乏力 气促 胸闷 呼吸困难 症状体征
入院途径 入院病情 出院方式 离院方式 主要诊断 其他诊断 诊断编码 疾病编码 手术编码 操作编码 住院天数 实际住院 总天数 次数 住院次数 入院次数
就诊次数 就诊时间 就诊日期 挂号时间 接诊 接诊时间 首诊 分诊 预检 分级 生命征 意识 神志 格拉斯哥 吸入 氧浓度 流量 鼻导管 面罩 高流量
血清 血浆 全血 尿液 痰液 粪便 胸水 腹水 脑脊液 咽拭子 鼻咽拭子 肺泡灌洗液 灌洗液 引流液 分泌物 动脉血 静脉血 末梢血 骨髓 脓液 穿刺液 血液
流行性感冒 甲型流感 乙型流感 流感病毒 病毒性肺炎 细菌性肺炎 社区获得性肺炎 肺部感染 呼吸衰竭 心力衰竭 慢性 急性 阻塞性 支气管 哮喘 扩张
高血压 糖尿病 冠心病 冠状动脉 动脉 粥样硬化 心脏病 脑梗死 脑梗塞 脑出血 肾病 肾衰竭 肿瘤 恶性 癌 型 病毒性 细菌性 肺 心 脑 肝 肾
口服 静滴 静注 静脉 滴注 注射 皮下 肌注 雾化 吸入 外用 鼻饲 泵入 微泵 每日 一次 两次 三次 四次 每晚 必要时 立即 持续 隔日 每周 早 晚
长期医嘱 临时医嘱 普通 带药 出院带药 平扫 增强 胸部 头颅 腹部 盆腔 床旁 床边 摄片 正位 侧位 彩超 心脏 超声心动图 数字 X线 片
""".split())
ID_WORDS = ["住院号", "病案号", "病历号", "门诊号", "急诊号", "登记号", "就诊号", "流水号", "关联字段", "患者ID", "病人ID", "患者编号",
            "病人编号", "档案号", "卡号", "就诊卡", "医保号", "申请单号", "报告单号", "检验单号", "医嘱号", "处方号", "标本号", "条码",
            "ID", "编号", "流水", "主索引", "PATIENT", "VISIT", "INPATIENT", "ENCOUNTER", "MRN", "HIS"]
ASCII_OK = set("""xls xlsx xlsm csv txt doc docx pdf xml html htm json sql rar zip 7z his emr lis pacs ris data export sheet report gd gam
icu ct mr mri dr pet ecg lab labs result results order orders note notes patient patients inpatient outpatient admission discharge diag
diagnosis drug drugs med meds vital vitals temp info list detail details all total new old copy final dict readme table tables view
mmol umol mmhg kpa mg ml ug ng pg iu kg cm bpm null none nan ivgtt ivvp qid tid bid qd qn qod prn stat once st po im iv ih sc wbc rbc hgb plt
crp pct neut lymph mono crea urea alt ast ldh bnp tni ferritin dimer flua flub influenza rna dna igm igg hfnc bipap cpap ecmo crrt ricu eicu
sicu micu nicu ccu mri spect sars cov""".split())
DATE_ANY = re.compile(r"(19|20)\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}")
DIGIT_RUN = re.compile(r"\d{4,}")
CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
TOKEN = re.compile(r"([㐀-䶿一-鿿豈-﫿]+)|([A-Za-z]+)|(\d+)|([^㐀-䶿一-鿿豈-﫿A-Za-z\d]+)")
MAXW = max(len(w) for w in VOCAB)


def segment(run: str) -> list[tuple[bool, str]]:
    """汉字串按词表做最长匹配：[(是不是词表里的词, 片段)]，连续的词表外汉字合成一段。"""
    out: list[tuple[bool, str]] = []
    i = 0
    while i < len(run):
        hit = next((run[i:i + k] for k in range(min(MAXW, len(run) - i), 0, -1) if run[i:i + k] in VOCAB), None)
        if hit:
            out.append((True, hit))
            i += len(hit)
        else:
            if out and not out[-1][0]:
                out[-1] = (False, out[-1][1] + run[i])
            else:
                out.append((False, run[i]))
            i += 1
    return out


def render_cjk(run: str, strict: bool, keep: set[str] = frozenset()) -> str:
    if run in keep:
        return run
    out = []
    for in_vocab, t in segment(run):
        if in_vocab or t in keep:
            out.append(t)
        elif strict or (len(t) >= 2 and any(ch in SURNAMES for ch in t[:2])):
            out.append(f"〔汉{len(t)}〕")
        else:
            out.append(t)
    return "".join(out)


def value_like(s: str) -> bool:
    return bool(DATE_ANY.search(s) or DIGIT_RUN.search(s) or "\n" in s or len(s) > 60)


def render_label(s, strict: bool = False, keep: set[str] = frozenset(), ascii_strict: bool | None = None) -> str:
    """工作表名、表头、路径名的显示：日期、≥4 位数字、长文字一律只给形状；词表外的疑似姓名（2–4 个汉字、首字是常见姓）遮蔽；
    strict（路径名）时词表外的汉字全部遮蔽、≥5 个字母的英文串除非常见词也遮蔽。"""
    s = str(s if s is not None else "").strip()
    if not s:
        return ""
    if len(s) > 60 or "\n" in s:
        return f"〔长文字{len(s)}字〕"
    if DATE_ANY.search(s):
        return "〔日期〕"
    out = []
    for m in TOKEN.finditer(s):
        cjk, alpha, digit, other = m.groups()
        if cjk:
            out.append(render_cjk(cjk, strict, keep))
        elif alpha:
            ok = alpha in keep or alpha.lower() in ASCII_OK or len(alpha) <= (3 if (strict if ascii_strict is None else ascii_strict) else 12)
            out.append(alpha if ok else f"〔字母{len(alpha)}〕")
        elif digit:
            out.append(digit if len(digit) <= (2 if strict else 3) else f"〔数{len(digit)}〕")
        else:
            out.append(other)
    return "".join(out)


def shape(s: str) -> str:
    """写法形状：汉字串→汉，字母串→a，数字逐位→9，空白→空格，其余符号原样。"""
    out, prev = [], None
    for ch in s:
        if CJK.match(ch):
            c = "汉"
        elif ch.isascii() and ch.isalpha():
            c = "a"
        elif ch.isdigit():
            c = "9"
        elif ch.isspace():
            c = " "
        else:
            c = ch
        if c in ("汉", "a", " ") and c == prev:
            continue
        out.append(c)
        prev = c
    return "".join(out)


MASK_LEN = re.compile(r"〔(汉|字母)\d+〕")


def loose(name: str) -> str:
    """分组用：〔汉2〕〔汉3〕都记成〔汉*〕（姓名长短不同的同类文件归到一起）；数字位数保留。"""
    return MASK_LEN.sub(lambda m: f"〔{m.group(1)}*〕", name)


def h64(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8, key=SALT).digest(), "big")


def canon_id(s: str) -> str:
    s = s.strip().upper()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s.lstrip("0") or s


# ---------------------------------------------------------------- 取值分类
DT_TXT = re.compile(r"^\s*(19|20)\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}\s*日?\s*$")
DTT_TXT = re.compile(r"^\s*(19|20)\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}\s*日?[\sT]+\d{1,2}\s*[:：时]\s*\d{1,2}")
NUM_TXT = re.compile(r"^\s*[<>＜＞≤≥]?=?\s*[-+]?\d+(\.\d+)?\s*$")
ID_TXT = re.compile(r"^[A-Za-z0-9_\-]{4,30}$")


def as_text(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, (dt.date, dt.time)):
        return v.isoformat()
    s = str(v).replace("_x000D_", "\n").strip()
    return s or None


def classify(v, s: str) -> str:
    if isinstance(v, dt.datetime):
        return "Excel日期时间" if (v.hour, v.minute, v.second) != (0, 0, 0) else "Excel日期"
    if isinstance(v, dt.date):
        return "Excel日期"
    if isinstance(v, dt.time):
        return "Excel时刻"
    if isinstance(v, bool):
        return "布尔"
    if isinstance(v, int):
        return "整数"
    if isinstance(v, float):
        return "整数" if v.is_integer() else "小数"
    if DTT_TXT.match(s):
        return "日期时间文字"
    if DT_TXT.match(s):
        return "日期文字"
    if NUM_TXT.match(s):
        return "数字文字"
    if "\n" in s:
        return "多行文字"
    return "长文字" if len(s) > 20 else "短文字"


# 长文字里数一数这些小节标题 / 词出现的比例（只给比例，不给原文）
HEADINGS = ["主诉", "现病史", "既往史", "个人史", "婚育史", "家族史", "过敏史", "体格检查", "专科检查", "辅助检查", "初步诊断", "入院诊断",
            "出院诊断", "修正诊断", "补充诊断", "诊疗经过", "出院情况", "出院医嘱", "入院时间", "入院日期", "出院时间", "出院日期", "记录时间",
            "住院天数", "病例特点", "鉴别诊断", "诊疗计划", "查房", "首次病程", "死亡时间", "死亡原因", "体温", "脉搏", "呼吸", "血压", "SpO2",
            "血氧饱和度", "姓名", "性别", "年龄", "流感", "奥司他韦", "玛巴洛沙韦", "呼吸机", "无创", "插管", "ECMO", "ICU", "转入", "吸氧",
            "医师签名", "<", "{\\rtf", "&nbsp;"]
LEAD_DT = re.compile(r"^\s*((?:19|20)\d{2}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}(?:\s*日)?(?:[\sT]+\d{1,2}\s*[:：时]\s*\d{1,2}(?:\s*[:：分]\s*\d{1,2})?)?)")


class ColStat:
    def __init__(self) -> None:
        self.n = 0
        self.types: Counter = Counter()
        self.sample: list[str] = []
        self.seen = 0
        self.distinct: set[int] = set()
        self.distinct_capped = False

    def add(self, v, s: str) -> None:
        self.n += 1
        self.types[classify(v, s)] += 1
        if not self.distinct_capped:
            self.distinct.add(h64(s))
            if len(self.distinct) > KEY_CAP:
                self.distinct_capped = True
                self.distinct.clear()
        self.seen += 1
        if len(self.sample) < SAMPLE:
            self.sample.append(s)
        else:
            j = secrets.randbelow(self.seen)
            if j < SAMPLE:
                self.sample[j] = s

    def merge(self, o: "ColStat") -> None:
        self.n += o.n
        self.types.update(o.types)
        if self.distinct_capped or o.distinct_capped:
            self.distinct_capped, self.distinct = True, set()
        else:
            self.distinct |= o.distinct
            if len(self.distinct) > KEY_CAP:
                self.distinct_capped, self.distinct = True, set()
        for s in o.sample:
            self.seen += 1
            if len(self.sample) < SAMPLE:
                self.sample.append(s)
            else:
                j = secrets.randbelow(self.seen)
                if j < SAMPLE:
                    self.sample[j] = s


# ---------------------------------------------------------------- 一张表
def label_like(c: str) -> bool:
    return not value_like(c) and len(c) <= 40 and not NUM_TXT.match(c) and not DT_TXT.match(c)


def pick_header(rows: list[list]) -> int | None:
    best, best_n = None, 0
    for i, row in enumerate(rows[:10]):
        cells = [as_text(v) for v in row]
        ne = [c for c in cells if c]
        if not ne:
            continue
        lab = [c for c in ne if label_like(c)]
        if len(lab) / len(ne) >= 0.7 and len(set(ne)) / len(ne) >= 0.5 and len(lab) > best_n:
            best, best_n = i, len(lab)
    return best


class Table:
    """一张工作表（或一个 CSV / HTML 表）的结构统计。"""

    def __init__(self, where: str) -> None:
        self.where = where
        self.rows_total = 0
        self.rows_nonempty = 0
        self.width = 0
        self.header_idx: int | None = None
        self.header: list[str] = []
        self.header_doubt = False
        self.module_row: list[str] | None = None
        self.cols: dict[int, ColStat] = defaultdict(ColStat)
        self.keys: dict[int, Counter] = {}
        self.pairs: dict[tuple[int, int], set[int]] = {}
        self.stopped_early = False

    def signature(self) -> tuple:
        if self.header_idx is None:
            return ("<无表头>", self.width)
        return tuple(self.header)

    def feed(self, it) -> None:
        head: list[list] = []
        body_buf: list[list] = []
        empty_run = 0
        decided = False
        for row in it:
            row = list(row)
            self.rows_total += 1
            if not any(as_text(v) for v in row):
                empty_run += 1
                if empty_run >= EMPTY_STOP and self.rows_nonempty:
                    self.stopped_early = True
                    break
                continue
            empty_run = 0
            self.rows_nonempty += 1
            self.width = max(self.width, max((i + 1 for i, v in enumerate(row) if as_text(v)), default=0))
            if len(head) < 15:
                head.append(row)
                if len(head) < 15:
                    continue
                self._decide_header(head, body_buf)
                decided = True
                continue
            if not decided:
                continue
            if len(body_buf) < BUFFER:
                body_buf.append(row)
                if len(body_buf) == BUFFER:
                    self._pick_keys(body_buf)
                    for r in body_buf:
                        self._row(r)
                continue
            self._row(row)
        if not decided:
            self._decide_header(head, body_buf)
        if len(body_buf) < BUFFER or not self.keys and not decided:
            self._pick_keys(body_buf)
            for r in body_buf:
                self._row(r)

    def _decide_header(self, head: list[list], body_buf: list[list]) -> None:
        h = pick_header(head)
        self.header_idx = h
        if h is not None:
            raw = [as_text(v) or "" for v in head[h]]
            self.header = raw
            if h > 0:
                prev = [as_text(v) or "" for v in head[h - 1]]
                ne = [c for c in prev if c]
                if ne and all(label_like(c) for c in ne):
                    self.module_row = prev
            rest = head[h + 1:]
            body_buf.extend(rest)
            # 表头里的字在下面的数据里反复出现：表头行可能认错了
            hits = sum(1 for j, c in enumerate(raw) if c and any(as_text(r[j]) == c for r in rest if j < len(r)))
            if raw and hits >= max(2, 0.3 * sum(1 for c in raw if c)):
                self.header_doubt = True
        else:
            body_buf.extend(head)

    def _pick_keys(self, buf: list[list]) -> None:
        for j in range(self.width):
            name = self.header[j] if j < len(self.header) else ""
            nu = name.replace(" ", "").upper()
            vals = [as_text(r[j]) for r in buf if j < len(r) and as_text(r[j])]
            by_name = any(w.upper() in nu for w in ID_WORDS) and not any(x in nu for x in ("时间", "日期", "名称"))
            by_shape = bool(vals) and sum(1 for v in vals if ID_TXT.match(v)) / len(vals) >= 0.95 and \
                statistics.median(len(v) for v in vals) >= 5 and not all(DT_TXT.match(v) for v in vals)
            if by_name or by_shape:
                self.keys[j] = Counter()
        ks = sorted(self.keys)[:8]
        for a in range(len(ks)):
            for b in range(a + 1, len(ks)):
                self.pairs[(ks[a], ks[b])] = set()

    def _row(self, row: list) -> None:
        for j, v in enumerate(row):
            s = as_text(v)
            if s is None:
                continue
            self.cols[j].add(v, s)
            if j in self.keys and len(self.keys[j]) < KEY_CAP:
                self.keys[j][h64(canon_id(s))] += 1
        for (a, b), st in self.pairs.items():
            if len(st) >= KEY_CAP:
                continue
            sa = as_text(row[a]) if a < len(row) else None
            sb = as_text(row[b]) if b < len(row) else None
            if sa and sb:
                st.add(h64(canon_id(sa) + "\x00" + canon_id(sb)))


# ---------------------------------------------------------------- 各种文件
def sniff(p: Path) -> str:
    try:
        with open(p, "rb") as fh:
            head = fh.read(4096)
    except OSError:
        return "打不开"
    ext = p.suffix.lower()
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(p) as z:
                names = set(z.namelist())
        except zipfile.BadZipFile:
            return "坏的zip"
        if "xl/workbook.xml" in names:
            return "xlsx"
        if "word/document.xml" in names:
            return "docx"
        return "zip"
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return {".xls": "xls", ".doc": "doc", ".ppt": "ppt", ".msg": "msg"}.get(ext, "ole")
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"Rar!"):
        return "rar"
    if head.startswith(b"7z\xbc\xaf"):
        return "7z"
    if head.startswith(b"{\\rtf"):
        return "rtf"
    if head.startswith(b"\xff\xd8") or head.startswith(b"\x89PNG") or head.startswith(b"GIF8") or head[:4] in (b"II*\x00", b"MM\x00*") \
            or head.startswith(b"BM"):
        return "图片"
    if len(head) > 132 and head[128:132] == b"DICM":
        return "DICOM"
    if not head:
        return "空文件"
    txt = None
    for enc in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            txt = head.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if txt is None or sum(1 for ch in txt[:2000] if ch == "\x00") > 10:
        return "二进制"
    t = txt.lstrip().lower()
    if t.startswith("<"):
        if "urn:schemas-microsoft-com:office:spreadsheet" in t or "<workbook" in t:
            return "xml表格"
        if "<html" in t or "<table" in t or "<!doctype html" in t or "<meta" in t:
            return "html"
        return "xml"
    if t.startswith("mime-version") or "multipart/related" in t[:500]:
        return "mht"
    if t.startswith("{") or t.startswith("["):
        return "json"
    return "文本"


def read_text(p: Path, limit: int | None = None) -> tuple[str, str]:
    raw = p.read_bytes() if limit is None else open(p, "rb").read(limit)
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("gb18030", errors="replace"), "gb18030(有坏字节)"


def iter_xlsx(p: Path):
    from openpyxl import load_workbook
    wb = load_workbook(p, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            ws.reset_dimensions()          # 有些导出把表尺寸写成 A1，只读模式会只读到第一格（pandas 读 Excel 时也先重置）
            yield ws.title, ws.iter_rows(values_only=True)
    finally:
        wb.close()


def iter_xls(p: Path):
    import xlrd  # noqa: F401  —— 没装时由调用方记"需要 xlrd"
    book = xlrd.open_workbook(p, on_demand=True)
    for sh in book.sheets():
        def rows(sh=sh):
            for i in range(sh.nrows):
                out = []
                for c in sh.row(i):
                    if c.ctype == xlrd.XL_CELL_DATE:
                        try:
                            out.append(xlrd.xldate.xldate_as_datetime(c.value, book.datemode))
                        except Exception:  # noqa: BLE001
                            out.append(c.value)
                    else:
                        out.append(c.value if c.value != "" else None)
                yield out
        yield sh.name, rows()


def iter_delimited(p: Path):
    text, enc = read_text(p)
    sample = text[:65536]
    lines = [ln for ln in sample.splitlines()[:50] if ln.strip()]
    best, best_score = None, 0.0
    for d in (",", "\t", "|", ";"):
        counts = [ln.count(d) for ln in lines]
        if counts and min(counts) > 0:
            score = statistics.mean(counts) / (1 + statistics.pstdev(counts))
            if score > best_score:
                best, best_score = d, score
    if best is None:
        return enc, None
    return enc, (best, csv.reader(io.StringIO(text), delimiter=best))


def iter_html_tables(p: Path):
    import lxml.html
    text, _ = read_text(p)
    doc = lxml.html.fromstring(text)
    for k, t in enumerate(doc.iter("table")):
        rows = []
        for tr in t.iter("tr"):
            rows.append([c.text_content() for c in tr if c.tag in ("td", "th")])
        yield f"表{k + 1}", iter(rows)


def iter_xml_sheets(p: Path):
    from lxml import etree
    ns = "{urn:schemas-microsoft-com:office:spreadsheet}"
    tree = etree.parse(str(p))
    for ws in tree.iter(ns + "Worksheet"):
        name = ws.get(ns + "Name") or "Sheet"
        rows = []
        for row in ws.iter(ns + "Row"):
            cells = []
            for c in row.iter(ns + "Cell"):
                idx = c.get(ns + "Index")
                if idx:
                    while len(cells) < int(idx) - 1:
                        cells.append(None)
                d = c.find(ns + "Data")
                cells.append("".join(d.itertext()) if d is not None else None)
            rows.append(cells)
        yield name, iter(rows)


def doc_text(p: Path, kind: str) -> str | None:
    try:
        if kind == "docx":
            import docx
            d = docx.Document(str(p))
            parts = [para.text for para in d.paragraphs]
            for t in d.tables:
                for r in t.rows:
                    parts.append("\t".join(c.text for c in r.cells))
            return "\n".join(parts)
        if kind in ("doc", "rtf", "mht") and sys.platform == "darwin":
            r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(p)], capture_output=True, timeout=60)
            return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None
        if kind == "pdf":
            from pypdf import PdfReader
            rd = PdfReader(str(p))
            return "\n".join((pg.extract_text() or "") for pg in rd.pages[:50])
        if kind in ("html", "xml", "文本", "json"):
            text, _ = read_text(p, 20_000_000)
            if kind == "html":
                import lxml.html
                return lxml.html.fromstring(text).text_content()
            return text
    except Exception:  # noqa: BLE001
        return None
    return None


# ---------------------------------------------------------------- 扫描
class Scan:
    def __init__(self, root: Path, show_names: bool) -> None:
        self.root = root
        self.show = show_names
        self.files: list[Path] = []
        self.kinds: Counter = Counter()
        self.size_by: Counter = Counter()
        self.ext_kind: Counter = Counter()
        self.tables: list[tuple[str, Table]] = []        # (文件编号, 表)
        self.docs: dict[str, dict] = {}
        self.unread: list[tuple[str, str]] = []
        self.notes: list[str] = []
        self.fid: dict[Path, str] = {}
        self.keep: set[str] = set()

    # ---- 名字遮蔽：在 ≥20% 的"单元"（分叉处的子目录或文件）里重复出现的词当作结构词，照常显示
    def build_keep(self) -> None:
        base = self.root
        while True:
            kids = [k for k in base.iterdir() if not k.name.startswith(".")]
            dirs = [k for k in kids if k.is_dir()]
            if len(dirs) == 1 and len(kids) == 1:
                base = dirs[0]
                continue
            break
        self.unit_base = base
        units = [k for k in base.iterdir() if not k.name.startswith(".")]
        n = max(len(units), 1)
        per_token: dict[str, set[str]] = defaultdict(set)
        for f in self.files:
            try:
                rel = f.relative_to(base)
            except ValueError:
                continue
            unit = rel.parts[0]
            for part in rel.parts:
                stem = part
                for m in TOKEN.finditer(stem):
                    cjk, alpha = m.group(1), m.group(2)
                    if cjk:
                        per_token[cjk].add(unit)
                    if alpha:
                        per_token[alpha].add(unit)
        need = max(3, math.ceil(0.2 * n))
        self.keep = {t for t, us in per_token.items() if len(us) >= need}
        self.n_units = len(units)

    def name(self, part: str) -> str:
        if self.show:
            return part
        stem, ext = os.path.splitext(part)
        ext_ok = ext if re.fullmatch(r"\.[A-Za-z0-9]{1,5}", ext or "") else ""
        return render_label(stem if ext_ok else part, strict=True, keep=self.keep) + ext_ok.lower()

    def rel_name(self, p: Path) -> str:
        return "/".join(self.name(x) for x in p.relative_to(self.root).parts)

    def run(self) -> None:
        for dp, dns, fns in os.walk(self.root):
            dns[:] = sorted(d for d in dns if not d.startswith("."))
            for fn in sorted(fns):
                if fn.startswith(".") or fn.startswith("~$") or fn == "Thumbs.db":
                    continue
                self.files.append(Path(dp) / fn)
        self.build_keep()
        for i, f in enumerate(self.files):
            self.fid[f] = f"F{i + 1:03d}"
        t0 = time.time()
        for i, f in enumerate(self.files):
            if i % 25 == 0:
                print(f"…扫描第 {i + 1}/{len(self.files)} 个文件（{time.time() - t0:.0f} 秒）", file=sys.stderr)
            self.one(f)

    def one(self, f: Path) -> None:
        kind = sniff(f)
        try:
            size = f.stat().st_size
        except OSError:
            size = 0
        ext = f.suffix.lower() or "（无扩展名）"
        self.kinds[kind] += 1
        self.size_by[kind] += size
        self.ext_kind[(ext, kind)] += 1
        fid = self.fid[f]
        try:
            if kind == "xlsx":
                for sheet, rows in iter_xlsx(f):
                    self._table(fid, f"工作表“{render_label(sheet, ascii_strict=True)}”", rows)
            elif kind == "xls":
                try:
                    import xlrd  # noqa: F401
                except ImportError:
                    self.unread.append((fid, "老式 .xls（需要 xlrd 才能读结构）"))
                    return
                for sheet, rows in iter_xls(f):
                    self._table(fid, f"工作表“{render_label(sheet, ascii_strict=True)}”", rows)
            elif kind == "xml表格":
                for sheet, rows in iter_xml_sheets(f):
                    self._table(fid, f"工作表“{render_label(sheet, ascii_strict=True)}”（XML 表格）", rows)
            elif kind == "html" and (b"<table" in open(f, "rb").read(2_000_000).lower()):
                n = 0
                for sheet, rows in iter_html_tables(f):
                    self._table(fid, f"HTML {sheet}", rows)
                    n += 1
                if n == 0:
                    self._doc(f, fid, kind)
            elif kind == "文本" and ext in (".csv", ".txt", ".tsv", ".dat", ".xls", "（无扩展名）"):
                enc, got = iter_delimited(f)
                if got is None:
                    self._doc(f, fid, kind)
                else:
                    d, reader = got
                    self._table(fid, f"文本表（编码 {enc}，分隔符 {'TAB' if d == chr(9) else d}）", reader)
            elif kind in ("docx", "doc", "rtf", "pdf", "html", "xml", "文本", "json", "mht"):
                self._doc(f, fid, kind)
            else:
                self.unread.append((fid, kind))
        except Exception as e:  # noqa: BLE001
            self.unread.append((fid, f"{kind}：读结构出错 {type(e).__name__}"))

    def _table(self, fid: str, where: str, rows) -> None:
        t = Table(where)
        t.feed(rows)
        if t.rows_nonempty == 0:
            self.notes.append(f"{fid} {where}：空表")
            return
        self.tables.append((fid, t))

    def _doc(self, f: Path, fid: str, kind: str) -> None:
        key = (kind, loose(self.name(f.name)) if not self.show else re.sub(r"\d", "9", f.name))
        d = self.docs.setdefault(key, {"n": 0, "lens": [], "lines": [], "heads": Counter(), "lead": Counter(), "fail": 0, "files": [],
                                       "skipped": 0})
        d["n"] += 1
        d["files"].append(fid)
        if d["n"] - d["skipped"] > DOC_CAP:          # 同类文书只解析前 DOC_CAP 个，其余只计数
            d["skipped"] += 1
            return
        text = doc_text(f, kind)
        if text is None:
            d["fail"] += 1
            return
        d["lens"].append(len(text))
        d["lines"].append(text.count("\n") + 1)
        for h in HEADINGS:
            if h in text:
                d["heads"][h] += 1
        m = LEAD_DT.match(text)
        if m:
            d["lead"][shape(m.group(1))] += 1

    # ---------------------------------------------------------------- 报告
    def report(self) -> str:
        L: list[str] = []
        w = L.append
        w("# 原始导出结构扫描（只含结构与计数）\n")
        w(f"- 扫描时间：{dt.datetime.now():%Y-%m-%d %H:%M}；文件 {len(self.files)} 个，"
          f"共 {sum(self.size_by.values()) / 1048576:.1f} MB；名字{'未遮蔽（--show-names）' if self.show else '已遮蔽'}")
        w("- 遮蔽记号：〔汉N〕N 个汉字、〔数N〕N 位数字、〔字母N〕N 个字母、〔日期〕；形状里 汉 = 一串汉字、a = 一串字母、9 = 一位数字")
        w(f"- 结构词：在分叉处 {getattr(self, 'n_units', 0)} 个单元里 ≥20% 出现的词照常显示（{len(self.keep)} 个）\n")
        w("## 1 文件类型\n")
        w("| 扩展名 | 实际类型（按文件头判断） | 文件数 |")
        w("|---|---|---|")
        for (ext, kind), n in sorted(self.ext_kind.items(), key=lambda x: -x[1]):
            w(f"| {ext} | {kind} | {n} |")
        w("")
        w("## 2 目录形状\n")
        w("```")
        L.extend(self.tree())
        w("```\n")
        w("## 3 表格（表头完全相同的归为一类）\n")
        L.extend(self.table_report())
        if self.docs:
            w("## 5 文书类文件（按遮蔽后的文件名归类；只给数量、长度和固定词出现的比例）\n")
            w("| 类型 | 文件名形状 | 个数 | 解析并读出文字的 | 字数（中位 / 最大） | 行数中位 | 开头是日期时间的 | 出现比例最高的固定词 |")
            w("|---|---|---|---|---|---|---|---|")
            for (kind, nm), d in sorted(self.docs.items(), key=lambda x: -x[1]["n"]):
                ok = d["n"] - d["fail"] - d["skipped"]
                lens = d["lens"] or [0]
                heads = "、".join(f"{h} {100 * c / max(ok, 1):.0f}%" for h, c in d["heads"].most_common(12))
                lead = "、".join(f"{s}×{c}" for s, c in d["lead"].most_common(3))
                w(f"| {kind} | {nm} | {d['n']} | {ok} | {int(statistics.median(lens))} / {max(lens)} | "
                  f"{int(statistics.median(d['lines'] or [0]))} | {lead or '—'} | {heads or '—'} |")
            w("")
        if self.unread or self.notes:
            w("## 6 没读结构的文件与其他说明\n")
            for fid, why in self.unread:
                w(f"- {fid}：{why}")
            for n in self.notes:
                w(f"- {n}")
            w("")
        w("## 附 文件编号对照（遮蔽后的路径）\n")
        w("```")
        for f in self.files[:400]:
            w(f"{self.fid[f]}  {self.rel_name(f)}")
        if len(self.files) > 400:
            w(f"…… 另有 {len(self.files) - 400} 个文件")
        w("```")
        return "\n".join(L)

    def tree(self) -> list[str]:
        out: list[str] = []

        def sig(d: Path) -> tuple:
            kids = sorted(k for k in d.iterdir() if not k.name.startswith("."))
            return tuple(sorted(Counter((loose(self.name(k.name)), k.is_dir()) for k in kids).items()))

        def walk(d: Path, depth: int) -> None:
            kids = sorted(k for k in d.iterdir() if not k.name.startswith(".") and not k.name.startswith("~$"))
            files = [k for k in kids if k.is_file()]
            dirs = [k for k in kids if k.is_dir()]
            fc = Counter(loose(self.name(k.name)) for k in files)
            for nm, c in sorted(fc.items(), key=lambda x: (-x[1], x[0]))[:40]:
                out.append("  " * depth + f"{nm}" + (f"  ×{c}" if c > 1 else ""))
            if len(fc) > 40:
                out.append("  " * depth + f"…… 另有 {len(fc) - 40} 种文件名")
            groups: dict[tuple, list[Path]] = defaultdict(list)
            for k in dirs:
                groups[(loose(self.name(k.name)), sig(k))].append(k)
            for (nm, _), ds in sorted(groups.items(), key=lambda x: -len(x[1]))[:40]:
                n_files = sum(1 for _ in ds[0].rglob("*") if _.is_file())
                out.append("  " * depth + f"{nm}/" + (f"  ×{len(ds)}（结构相同）" if len(ds) > 1 else "") + f"  [首个含 {n_files} 个文件]")
                if depth < 5:
                    walk(ds[0], depth + 1)
            if len(groups) > 40:
                out.append("  " * depth + f"…… 另有 {len(groups) - 40} 组目录")

        out.append(f"{'（扫描根目录）'}/")
        walk(self.root, 1)
        return out

    def table_report(self) -> list[str]:
        L: list[str] = []
        w = L.append
        groups: dict[tuple, list[tuple[str, Table]]] = defaultdict(list)
        for fid, t in self.tables:
            groups[t.signature()].append((fid, t))
        ordered = sorted(groups.values(), key=lambda g: -sum(t.rows_nonempty for _, t in g))
        self.type_of: dict[int, str] = {}
        key_sets: list[tuple[str, str, Counter]] = []
        for k, g in enumerate(ordered, start=1):
            tid = f"T{k:02d}"
            t0 = g[0][1]
            rows = sum(t.rows_nonempty for _, t in g)
            w(f"### {tid}：{len(g)} 张表，非空行共 {rows}（含表头行）\n")
            wh = Counter(t.where for _, t in g)
            w("- 出现在：" + "；".join(f"{x}×{c}" if c > 1 else x for x, c in wh.most_common(6))
              + (f" 等 {len(wh)} 种" if len(wh) > 6 else "") + "；文件 " + "、".join(sorted({fid for fid, _ in g})[:12])
              + (" 等" if len({fid for fid, _ in g}) > 12 else ""))
            if t0.header_idx is None:
                w(f"- 没有认出表头行（前 10 行里像列名的格不够多）；列数 {t0.width}")
            else:
                w(f"- 表头在第 {t0.header_idx + 1} 行" + ("；**表头行可能认错了**（表头里的字在下面的数据里反复出现），列名只给形状" if t0.header_doubt else "")
                  + (f"；上一行像模块行：{'、'.join(render_label(c) for c in t0.module_row if c)}" if t0.module_row else ""))
            if any(t.stopped_early for _, t in g):
                w(f"- 有表在连续 {EMPTY_STOP} 个空行后停止（表尺寸可能写错）")
            cols: dict[int, ColStat] = defaultdict(ColStat)
            keys: dict[int, Counter] = defaultdict(Counter)
            pairs: dict[tuple[int, int], set[int]] = defaultdict(set)
            for _, t in g:
                for j, c in t.cols.items():
                    cols[j].merge(c)
                for j, c in t.keys.items():
                    keys[j].update(c)
                for p, s in t.pairs.items():
                    pairs[p] |= s
            width = max(t.width for _, t in g)
            w("")
            w("| 列 | 列名 | 非空 | 取值类型（占比） | 不同值 | 字数（最短 / 中位 / 最长） | 常见写法形状（只给形状） |")
            w("|---|---|---|---|---|---|---|")
            for j in range(width):
                c = cols.get(j)
                hdr = t0.header[j] if j < len(t0.header) else ""
                label = (shape(hdr) if t0.header_doubt else render_label(hdr)) if hdr else "（空）"
                if c is None or c.n == 0:
                    w(f"| {col_letter(j)} | {label} | 0 | — | — | — | — |")
                    continue
                types = "、".join(f"{k} {100 * v / c.n:.0f}%" for k, v in c.types.most_common(3))
                lens = [len(s) for s in c.sample]
                lens.sort()
                med = lens[len(lens) // 2] if lens else 0
                distinct = "≥30万" if c.distinct_capped else str(len(c.distinct))
                shapes = Counter(shape(s) for s in c.sample if len(s) <= 40)
                long_text = med > 40 or c.types.get("多行文字", 0) > 0.2 * c.n
                sh = "（长文字，不给形状）" if long_text else "、".join(f"`{s}`×{n}" for s, n in shapes.most_common(4))
                w(f"| {col_letter(j)} | {label} | {c.n} | {types} | {distinct} | {lens[0] if lens else 0} / {med} / {lens[-1] if lens else 0} | {sh} |")
                if long_text:
                    heads = Counter()
                    lead = Counter()
                    for s in c.sample:
                        for hd in HEADINGS:
                            if hd in s:
                                heads[hd] += 1
                        m = LEAD_DT.match(s)
                        if m:
                            lead[shape(m.group(1))] += 1
                    n = len(c.sample)
                    w(f"|  | ↳ 长文字（抽样 {n} 条）：开头是日期时间的 {100 * sum(lead.values()) / n:.0f}%"
                      + (f"（{'、'.join(f'`{s}`' for s, _ in lead.most_common(3))}）" if lead else "")
                      + "；固定词出现比例：" + ("、".join(f"{h} {100 * v / n:.0f}%" for h, v in heads.most_common(14)) or "—") + " |  |  |  |  |  |")
            w("")
            for j, cnt in sorted(keys.items()):
                if not cnt:
                    continue
                per = sorted(cnt.values())
                hdr = t0.header[j] if j < len(t0.header) else ""
                nm = f"{col_letter(j)}[{render_label(hdr) if hdr and not t0.header_doubt else '第' + col_letter(j) + '列'}]"
                w(f"- 编号候选 {nm}：不同值 {len(cnt)}{'（达到上限）' if len(cnt) >= KEY_CAP else ''}，每个值占 {per[0]}–{per[-1]} 行（中位 {per[len(per) // 2]}）")
                key_sets.append((tid, nm, cnt))
            shown = 0
            for (a, b), s in sorted(pairs.items(), key=lambda x: -len(x[1])):
                if not s or len(keys.get(a) or ()) < 2 or len(keys.get(b) or ()) < 2 or shown >= 10:
                    continue
                shown += 1
                na, nb = len(keys[a]), len(keys[b])
                ha = t0.header[a] if a < len(t0.header) else ""
                hb = t0.header[b] if b < len(t0.header) else ""
                la, lb = render_label(ha) or col_letter(a), render_label(hb) or col_letter(b)
                rel = ("一一对应" if len(s) == na == nb else f"一个[{lb}]只对应一个[{la}]" if len(s) == nb else
                       f"一个[{la}]只对应一个[{lb}]" if len(s) == na else "多对多")
                w(f"- 编号组合 [{la}]×[{lb}]：组合 {len(s)} 个（[{la}] {na} 个、[{lb}] {nb} 个）→ {rel}")
            w("")
        if len(key_sets) > 1:
            w("## 4 不同表之间的编号重合（只给计数；编号已去空白、转大写、去前导零）\n")
            w("| 表与列 A | 表与列 B | A 不同值 | B 不同值 | 重合 |")
            w("|---|---|---|---|---|")
            rows = []
            for i in range(len(key_sets)):
                for k in range(i + 1, len(key_sets)):
                    ta, na, ca = key_sets[i]
                    tb, nb, cb = key_sets[k]
                    if ta == tb:
                        continue
                    inter = len(ca.keys() & cb.keys())
                    if inter and inter >= 0.05 * min(len(ca), len(cb)):
                        rows.append((inter, f"| {ta} {na} | {tb} {nb} | {len(ca)} | {len(cb)} | {inter} |"))
            for _, r in sorted(rows, key=lambda x: -x[0])[:60]:
                w(r)
            if not rows:
                w("| — | — | — | — | 没有重合 ≥5% 的编号列 |")
            w("")
        return L


def col_letter(idx: int) -> str:
    s, n = "", idx + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="报告另存一份（Markdown）")
    ap.add_argument("--show-names", action="store_true", help="文件名、目录名不遮蔽（研究者确认名字里没有病人信息时才用）")
    a = ap.parse_args()
    if not a.root.is_dir():
        sys.exit(f"不是目录：{a.root}")
    s = Scan(a.root.resolve(), a.show_names)
    s.run()
    rep = s.report()
    if a.out:
        a.out.write_text(rep, encoding="utf-8")
        print(f"报告已写到 {a.out}", file=sys.stderr)
    print(rep)


if __name__ == "__main__":
    main()
