# -*- coding: utf-8 -*-
"""
生成《老年流感转重研究 · 近期工作与论文阅读汇报》v2（2026-10-26，按导师意见改版）。

相对 v1（build_progress_reading_report_20261026.py）的改动：
- 删去目录页（"四个问题与一句话回答"）；
- 已做工作压成一页；新增"目前的数据集设计"一页：左边仿 MIMIC-IV 图 1 画数据流与 std_v3 表结构，
  右边仿 ACES 图 4 画主结局 O3 的触发、起点窗与标签窗；
- 细讲 4 篇典型论文，每篇配论文原图：MIMIC-IV、CLIF、ACES（附 Lauritsen 2021 作旁证）、ISARIC 4C Deterioration；
- 四篇对照（优势 → 采用；局限 → 补足），再给后续安排；
- v1 的两院判据、GD 答复、证型、待定口径、34 篇路线图移到致谢之后作附录 A1–A5（内容不变，页码引用改成附录编号）。

10-27：第 9 页后续安排由按周的时间线改为三条（定口径、补数据底座、补门急诊样本），时间只留 12 月流感高峰一个节点。研究者 10-27 凌晨在
PowerPoint 里手改过封面、第 3 页并删去附录 A5，所以这次只用新的 build_plan 重建了 PPT 第 9 页，没有重跑本脚本；
重跑会冲掉那些手改。

输入：
- PPT/模板/hospital_优化版.pptx（模板，只读）；
- PPT/脚本/build_progress_reading_report_20261026.py（v1：复用样式工具与附录页）；
- PPT/素材/论文原图_20261026/*.png（论文原图裁图；由 PPT/脚本/extract_paper_figures_20261026.py 从本地 PDF 生成，
  PDF 在 paper/数据集构建调研_20261025/。裁图是第三方材料，幻灯片上逐张注明出处与页码；按仓库约定只放本地，
  是否入库由研究者定）。
输出：PPT/成品/周报与进展/近期工作与论文阅读汇报_20261026_v2.pptx

数字：项目数字都是聚合量（1–9 记为 <10），来源同 v1；论文数字出自原文，页码写在各页备注里
（MIMIC-IV、CLIF、ACES、Lauritsen 为 PDF 页；ISARIC 4C 为期刊页 349–359）。没有读任何真实病例。

运行（BaseModel 根目录）：python PPT/脚本/build_progress_reading_report_20261026_v2.py
依赖：python-pptx、lxml
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_progress_reading_report_20261026 as base  # noqa: E402  v1：样式与附录页
from build_progress_reading_report_20261026 import (  # noqa: E402
    AMBER, AMBER_BG, BODY, BORDER, CL, CW, CYAN, CYAN_BG, DARK, GREY, LIGHT, MID, MUTED, NAVY, PALE, RED,
    RED_BG, SW, WHITE, add_line, add_oval, add_rect, add_text, bullets, frame, num_badge, shape_text, small,
    text_width)
from pptx import Presentation  # noqa: E402
from pptx.enum.dml import MSO_LINE_DASH_STYLE  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.parts.image import Image as PptxImage  # noqa: E402
from pptx.util import Inches  # noqa: E402

FIG = HERE.parent / "素材" / "论文原图_20261026"
OUT = HERE.parent / "成品" / "周报与进展" / "近期工作与论文阅读汇报_20261026_v2.pptx"

# 仿 ACES 图 4 的窗口配色（只用在数据集设计页的时间轴上）
WIN_IN = "D6E9FB"      # 起点窗（ACES：输入窗，浅蓝）
WIN_IN_LINE = "6FA8DC"
WIN_OUT = "EADCF7"     # 标签窗（ACES：目标窗，浅紫）
WIN_OUT_LINE = "8E5BB5"
WIN_OUT_TEXT = "5E3A86"
RULE_BG = "E3F0DA"     # 约束标签（ACES：绿色标签）
RULE_TX = "3F6B23"
CLOCK_BG = "ECEFF3"    # 发病时钟
LEVEL = {"中型": "5B8FD0", "重型": AMBER, "危重型": RED}


# ---------------------------------------------------------------------------
# 演讲者备注（汇报人口吻；每页标了建议时长，合计约 16 分钟）
# ---------------------------------------------------------------------------
NOTES = {
    "cover": "封面，约 0.3 分钟。本次按导师意见改版：先用一页讲已做工作、一页讲目前的数据集设计，再细讲 4 篇典型论文"
             "（配论文原图），最后按这些论文的优势和局限给出后续安排。项目数字均为聚合统计（1–9 记为 <10）；论文数字出自"
             "原文，页码写在各页备注里。原来的两院判据、GD 答复、证型、待定口径等细节放在致谢后的附录 A1–A5。全程约 16 分钟。",
    "work": "约 1.5 分钟。上面是两周的时间线：10-17 部署；10-18 读 GD 病历系统原始导出；10-19 至 10-21 性能改造与医生端"
            "体征图；10-21、10-22 六模型实验（本人三个模型）；10-22、10-23 规则集 v0.3 与 std_v3 统一导出；10-24 在服务器"
            "导入两院真实数据、当天算出计数并发出问题单；10-25 GD 答复并交回证型对应表，同日读完 34 篇数据集构建论文。"
            "下面四张卡是结果。第二张卡的三个数是导入的就诊次数，主分析人群（确诊且 ≥60 岁）是 328、129、17。"
            "六模型实验：删 40% 观测时五个模型 AUPRC 降 0.016–0.036，个体预测翻转 6.2%–9.7%（5 个 seed 均值）。"
            "带到下一页的两个问题：门急诊样本太少；两院治疗类判据差异大（明细见附录 A1、A2）。",
    "design": "约 2.5 分钟。左图仿 MIMIC-IV 图 1：最左是数据来源，实线是已到的三个来源（GD 住院原始导出、GAM 住院、"
              "GAM 门急诊），虚线是待补的两院门急诊 / 发热门诊和前瞻表单；中间 flucase 按格式族和格式配置把各院 Excel "
              "读成统一病例记录，医生确认后入库，每个值都能追溯到原文件的表、行、列；规则集 v0.3 在病例库上派生分级时间线和"
              "候选结局；右边是 std_v3 统一导出，按就诊、事件、治疗区间、派生、元数据分组，两院同表同编码同取值，导出本身"
              "不定 t0、人群和标签（D68）。右图仿 ACES 图 4 画主结局 O3：触发是首次门急诊就诊（院内发病取首次阳性，D48）；"
              "起点窗 t0 前后 24 小时，基线不超过中型（D18）；标签窗 14 天（7 天作敏感性，D17），其间住院或达到重型及以上"
              "记为 1；当次收住院或基线已达重型的不进风险集；没关联到全院记录或转院的记“未知”、不记阴性。发病时钟（起病到"
              "就诊天数）同时作预测变量和分层变量（D12）。分级按 2025 年版方案，判据分生理、治疗、诊断三类分开派生，主口径"
              "是治疗类 + 诊断类（D21）。人群、索引、验证见左下要素框（D16、D70、D73、D19）。要点：结构上已能承载多中心，"
              "但 O3 风险集只有 17 次。",
    "mimic": "约 2 分钟。MIMIC-IV（Johnson 等，Scientific Data 2023;10:1）。图 1（p2）是构建流程，编号是我加的：① 采集——"
             "BIDMC 数据仓库、ICU 系统 MetaVision 和外部来源（ICD 等编码定义、州死亡登记）；② 格式转换——SQL 合到一个 schema；③ 去标识；④ 按 hosp、icu、"
             "note 模块发布；⑤ 用户在代码仓库提的问题回流修正构建。转换两条原则：向后兼容 MIMIC-III、尽量少加工（p3）。"
             "charttime 记测量时刻、storetime 记床旁人员核实时刻（p7）。技术验证（p7–8）：单一可复现构建脚本、版本控制、"
             "代码评审；单元测试分完整性（诊断码都在字典表里、每张表的患者都在 patients 表里）、一致性（≥99% 的 ICU 住段"
             "有计费诊断、有心率）和与上一版比对。规模见表 1（p4）：431,231 次住院、73,181 次 ICU 住段。局限是从我们的角度"
             "说的：单中心、只收进过急诊或 ICU 的患者（p2）；日期按患者平移，真实年份只给 3 年一档（p4–5）；官方文档"
             "《What's new in MIMIC-IV》写明不再发布星期和季节，改为发布大致年份——做流感季分析就不行；通气、升压药等派生概念放在 MIMIC Code Repository（p8）。",
    "clif": "约 2 分钟。CLIF（Rojas、Lyons 等；medRxiv 2024 预印本，期刊版 Intensive Care Med 2025）。左图是 23 张表的 ER 图"
            "（p13），橙框是呼吸支持表：device_name 存医院原文、device_category 存受控类别，模式、FiO2、PEEP 等设置值和观测值"
            "都有列。做法：2023 年 7 月起每周例会定流程、术语和质控（p3）；mCIDE 是每张表一组以 _category 结尾、取值受控的"
            "最小公共元素，_name 保留医院原名（p4）；联邦分析，同一脚本和模型对象发到各家本地跑、只回传聚合结果，不共享"
            "行级数据（p4–5）。结果：8 个医疗系统、33 家医院、94,356 次 ICU 入住；Rush 用 2019、2022、2023 年数据训练的 LightGBM，"
            "在 2020–2021 队列上于 8 家（含 Rush）评估，AUC 0.74–0.83（右上图 2A，p14；正文写 0.74–0.81，以图为准），校准也随站点变化。局限是论文自己写的（p7–8）：每家落地都要大量数据科学和重症"
            "专业投入；没接 FHIR；用 ADT（所在科室）定义重症人群，有选择偏倚和左删失；行级数据不公开。"
            "对我们：GD 第 9 题答复（科内监护室按医嘱区分）正是“不只看科室”。",
    "aces": "约 2 分钟。ACES（Xu、Gallifant、Johnson、McDermott，ICLR 2025）。动机（p1）：复现 MIMIC-III 研究时一半以上"
            "的队列重建不出来，人数差可达 25%。图 4（p7）是入院后 48 小时预测院内死亡：A 是数据集专用的谓词，把入院、出院、"
            "死亡映射到本库编码；C 触发是入院；B 输入窗到触发后 24 小时、至少 5 条事件；D 间隔窗 48 小时内不得出院或死亡，"
            "否则排除；E 目标窗到下一次出院或死亡，死亡记 1。换库只换 A。中间虚线框是把我们的 O3 按同样的写法拆开："
            "C 触发是首次门急诊就诊，B 起点窗 t0 前后 24 小时定基线，E 标签窗 14 天，另有两条排除。局限（§4.2，p9–10）："
            "配置语言还要扩，文本里的信息要用户先抽成谓词，病例对照匹配还不支持；数据要先是事件流（MEDS / ESGPT）；"
            "附录 B（p15–16）与 OMOP-learn、DPM360 的对比是初步的，作者自认可能有偏。右上是 Lauritsen 2021"
            "（npj Digital Medicine 4:158）图 2 作旁证：同一批 19,976 次普通病房住院、脓毒症 6.25%，“发病前固定时刻”取样"
            "AUROC 0.906、正负 1:15，全住院滑动窗口只有 0.756、1:750（p3–4）。对我们：规则集 v0.3 里判据映射和任务窗口"
            "写在同一个文件里，新中心接入时要整份改。",
    "isaric": "约 2 分钟。ISARIC 4C Deterioration（Gupta 等，Lancet Respir Med 2021;9:349–59）。英国 260 家医院前瞻队列，"
              "74,944 名住院成人。复合结局：开始通气支持（无创、有创、ECMO）、进 HDU/ICU 或死亡；作者说它接近 WHO 进展量表"
              " ≥6 分，并且不受各院呼吸支持习惯影响（p350）；43.2% 发生，中位 4 天（p354）。预测时点是入院时，院内感染取"
              "首次评估；只纳入 ≥60% 人群可得的预设变量，留下 11 个（p351、p354）。图 2（p355）是内-外交叉验证：8 个地区"
              "轮流留一，C 0.75–0.77、随机效应合并 0.76，校准斜率 0.95–1.06；伦敦整区留出（8,239 人）C 0.77、斜率 0.96。"
              "局限：只限住院成人和 2020 年英国 COVID；“≥60% 可得”让 LDH、D-二聚体进不了模型（p358）；作者观察到年长者"
              "恶化时更多直接死亡、较少升级到 HDU/ICU 或通气（p356）——对老年人，治疗类结局受升级决策影响。右下“请讨论”：O3 把“14 天内住院”也算结局，大致相当于 WHO 量表 ≥4 分的“住院”，"
              "ISARIC 取 ≥6 分正是为了避开各院习惯差异——O3 是否加“≥重型”的敏感性口径，请导师和临床定。"
              "底部“对我们”：O3 写清组成和理由；保留生理类口径、死亡单列；两个中心做不了有意义的地区间合并，要多收中心。",
    "compare": "约 1.5 分钟。每行：左边是论文解决的问题，中间两列是优势（我们采用）和局限（我们要补），右边是我们现在的"
               "状态和落到计划里的动作。共同点：四篇都把“原始记录可回溯”和“定义写成可复现的文件”放在前面。我们已有原值"
               "可追溯、两院同表、分级时间线；缺验收测试、呼吸支持表、任务配置化，以及门急诊样本和更多中心。",
    "plan": "约 1 分钟。三条，不按周排；时间只卡 12 月流感高峰前上线前瞻收集。1 定口径（规则集 v0.4，依据 GD 答复）："
            "讨论确定 ICU、慢性低氧、再住院、确诊、发热 5 处口径，登记为 v0.4、旧版保留，两院按 v0.3 / v0.4 重算对比——"
            "要讨论拍板。2 补数据底座：MIMIC-IV 的验收测试（完整性、一致性阈值、与上一版比对）、时间来源列、数据字典与"
            "Healthsheet 初稿；CLIF 的呼吸支持长表、允许取值清单、ICU 查找表（科室 + 医嘱），用新表重算两院吸氧、无创、ICU "
            "差异；ACES 的规则集拆两层、预测实例表。这些是技术项，可先在虚构数据上做。3 补门急诊样本（借鉴 ISARIC 4C）："
            "按 GD 第 3 题的检索条件申请两院门急诊、发热门诊导出（要协调信息科）；按 O3 结局率和候选变量数用 pmsampsize "
            "估算样本量；前瞻表单按固定时点定稿（ISARIC CCP：就诊日、第 3、6、9 天）后上线。原计划照常并行：GAM 补充数据、"
            "证型对应表进系统、六模型汇总（等合作同学的 OPL-MT-MNAR）、联系新中心接入。需要拍板的口径见附录 A4。",
    "closing": "结束页。附录 A1–A5 是 v1 的细节页：两院判据差异、GD 临床答复、中医证型、需要讨论确定的六件事、34 篇阅读路线。",
}


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def img_size(path):
    return PptxImage.from_file(str(path)).size


def figure(slide, path, x, y, w, h, name, pad=0.08):
    """白底卡片里放一张论文原图：按比例缩放，水平居中、顶端对齐。返回图片的 (x, y, w, h)。"""
    add_rect(slide, x, y, w, h, fill=WHITE, line=BORDER, shadow=True, name=f"{name}·底卡")
    pw, ph = img_size(path)
    bw, bh = w - 2 * pad, h - 2 * pad
    s = min(bw / pw, bh / ph)
    iw, ih = pw * s, ph * s
    ix, iy = x + pad + (bw - iw) / 2, y + pad + (bh - ih) / 2
    pic = slide.shapes.add_picture(str(path), Inches(ix), Inches(iy), Inches(iw), Inches(ih))
    pic.name = name
    return ix, iy, iw, ih


def fit_h(path, w, pad=0.08):
    """宽度定为 w 时，卡片需要的高度。"""
    pw, ph = img_size(path)
    return (w - 2 * pad) * ph / pw + 2 * pad


def mark(slide, box, fx0, fy0, fx1, fy1, color=AMBER, width=2.25):
    """在图上按相对坐标画一个圆角框（本页所加的标注）。"""
    ix, iy, iw, ih = box
    return add_rect(slide, ix + fx0 * iw, iy + fy0 * ih, (fx1 - fx0) * iw, (fy1 - fy0) * ih, line=color,
                    line_w=width, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04, name="标注框")


def tag(slide, box, fx, fy, text, fill=AMBER, d=0.3, size=11):
    """图上的编号圆点（本页所加的标注）。"""
    ix, iy, iw, ih = box
    return num_badge(slide, ix + fx * iw, iy + fy * ih, text, fill=fill, d=d, size=size)


def caption(slide, x, y, w, h, runs, size=10, align="l"):
    add_text(slide, x, y, w, h, [runs], size=size, color=MUTED, align=align, margins=(0, 0, 0, 0),
             line_spacing=1.05, name="图注")


def block(slide, x, y, w, h, label, items, kind="how", size=11.5, gap=3, fill=None, line=None):
    """一块说明：左上一个小标签，下面若干条项目符号。kind 决定标签颜色。"""
    colors = {"how": (DARK, WHITE), "pro": (CYAN, WHITE), "con": (AMBER, WHITE), "ours": (MID, WHITE),
              "note": (LIGHT, NAVY)}
    tf, tc = colors[kind]
    if fill or line:
        add_rect(slide, x, y, w, h, fill=fill, line=line)
    pad = 0.12 if (fill or line) else 0
    lw = text_width(label, 11.5) * 1.06 + 0.3
    lb = add_rect(slide, x + pad, y + pad, lw, 0.28, fill=tf, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    shape_text(lb, label, 11.5, tc, bold=True, wrap=False)
    bc = {"how": MID, "pro": CYAN, "con": AMBER, "ours": MID, "note": MID}[kind]
    add_text(slide, x + pad, y + pad + 0.34, w - 2 * pad, h - 0.34 - 2 * pad, bullets(items, gap=gap, color=bc),
             size=size, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.05)


def pill_at(slide, x, y, text, fill, color, size=10.5, h=0.28, line=None, bold=True):
    w = text_width(text, size) * 1.06 + 0.3
    s = add_rect(slide, x, y, w, h, fill=fill, line=line, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    shape_text(s, text, size, color, bold=bold, wrap=False)
    return w


def replace_text(slide, old, new):
    """把整页文字片段里的 old 换成 new（附录页改页码引用用）。"""
    for shp in slide.shapes:
        frames = []
        if shp.has_text_frame:
            frames.append(shp.text_frame)
        if getattr(shp, "has_table", False) and shp.has_table:
            for row in shp.table.rows:
                for cell in row.cells:
                    frames.append(cell.text_frame)
        for tf in frames:
            for p in tf.paragraphs:
                for r in p.runs:
                    if old in r.text:
                        r.text = r.text.replace(old, new)


# ---------------------------------------------------------------------------
# 第 2 页：已做工作（一页）
# ---------------------------------------------------------------------------
def build_work(slide):
    frame(slide, "已做工作", "近两周已做工作：数据系统跑上两院真实数据",
          "10-24 两院真实数据第一次按统一口径跑通；10-25 GD 答复全部 13 题；数据集构建论文 34 篇读完。",
          ask_lead="带出的问题：", ask="主结局 O3 可用的门急诊样本只有 17 次；两院治疗类判据可比性存疑（明细见附录 A1–A4）。",
          notes=NOTES["work"])
    # —— 时间线（两条泳道）——
    days = [("10-17", "六"), ("10-18", "日"), ("10-19", "一"), ("10-20", "二"), ("10-21", "三"), ("10-22", "四"),
            ("10-23", "五"), ("10-24", "六"), ("10-25", "日")]
    lw_ = 1.42
    x0 = CL + lw_ + 0.08
    dw = (CL + CW - x0) / len(days)
    lanes = [("系统与数据", 2.11), ("临床·文献·实验", 2.64)]
    lh = 0.49
    add_rect(slide, x0 + 7 * dw + 0.02, 1.76, 2 * dw - 0.04, lanes[-1][1] + lh + 0.04 - 1.76, fill=CYAN_BG,
             name="10-24/25 底色")
    for i, (d, wd) in enumerate(days):
        add_text(slide, x0 + i * dw, 1.76, dw, 0.3, [[(d, {"bold": True, "color": NAVY}),
                                                      (f" 周{wd}", {"size": 9.5, "color": MUTED})]],
                 size=11, align="c", anchor="m", margins=(0, 0, 0, 0))
    add_line(slide, x0, 2.07, CL + CW, 2.07, BORDER, 1)
    for name, y in lanes:
        b = add_rect(slide, CL, y, lw_, lh, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
        shape_text(b, name, 10.5, NAVY, bold=True, wrap=False)

    def ev(lane, d0, span, text, style="plain"):
        y = lanes[lane][1] + 0.03
        x = x0 + d0 * dw + 0.04
        w = span * dw - 0.08
        hh = lh - 0.06
        if style in ("key", "new"):
            s = add_rect(slide, x, y, w, hh, fill=DARK if style == "key" else CYAN,
                         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.18)
            shape_text(s, text, 10, WHITE, bold=True, margins=(0.03, 0.01, 0.03, 0.01))
        else:
            s = add_rect(slide, x, y, w, hh, fill=WHITE, line=MID, line_w=1.0,
                         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.18)
            shape_text(s, text, 10, NAVY, margins=(0.03, 0.01, 0.03, 0.01))

    ev(0, 0, 1, "部署到\n专用服务器")
    ev(0, 1, 1, "读 GD\n原始导出")
    ev(0, 2, 3, "性能改造 · 医生端体征图")
    ev(0, 5, 2, "规则集 v0.3 · std_v3 统一导出")
    ev(0, 7, 1, "两院真实\n数据首跑", "key")
    ev(1, 4, 2, "六模型实验\n本人 3 模型 × 5 seed")
    ev(1, 7, 1, "宽表计数\n问题单发 GD", "key")
    ev(1, 8, 1, "GD 答复\n34 篇读完", "new")

    # —— 四张成果卡 ——
    cards = [
        ("数据系统 flucase", DARK, DARK, "2 院", "两院真实导出都已读通", [
            "10-17 部署到专用服务器；\n10-23 发布含规则集 v0.3 的版本",
            "读通 GD 原始导出（20 个 xlsx）\n与 GAM 住院、门急诊；\n10-24 导入，207 个测试通过",
            "std_v3 统一导出：两院同表、\n同编码、同取值"]),
        ("真实数据首跑 · 10-24", DARK, DARK, "618 · 173 · 1,166", "GD 住院 · GAM 住院 · GAM 门急诊", [
            "主分析人群（确诊且 ≥60 岁）：\n328 · 129 · 17",
            "新开始吸氧 GD 84%、GAM 8%；\n差异集中在吸氧、无创、ICU",
            "诊断与检测不一致：GD 290 次\n诊断流感无阳性检测 → 以检测为准"]),
        ("临床对接 · GD", MID, MID, "13 题", "10-24 发出，10-25 全部答复", [
            "6 项同意现行；5 处改口径：\nICU 科室、慢性低氧、再住院、\n确诊、发热",
            "证型对应表：355 种写法\n已对到 7 型的 271 种",
            "第 3 题给出门急诊检索条件，\n可据此申请门急诊数据"]),
        ("文献与实验", CYAN, "0089AA", "34 篇", "数据集构建论文 · 7 站 · 13 篇必读", [
            "讲解页与逐篇笔记都标了页码\n或章节；下面细讲 4 篇典型论文",
            "六模型：本人 BRITS、mTAND、\nRaindrop 各 5 个 seed",
            "删 40% 观测：\nAUPRC 只降 ≤0.036；\n个体预测却翻转 6–10%"]),
    ]
    gap = 0.2
    w = (CW - 3 * gap) / 4
    y = 3.27
    h = 6.3 - y
    for i, (head, hc, bigc, big, sub, items) in enumerate(cards):
        x = CL + i * (w + gap)
        add_rect(slide, x, y, w, h, fill=WHITE, line=BORDER, shadow=True)
        add_rect(slide, x, y, w, 0.38, fill=hc)
        add_text(slide, x + 0.16, y, w - 0.3, 0.38, head, size=12.5, color=WHITE, bold=True, anchor="m",
                 margins=(0, 0, 0, 0))
        add_text(slide, x + 0.16, y + 0.42, w - 0.3, 0.44, big, size=20, color=bigc, bold=True, anchor="m",
                 margins=(0, 0, 0, 0))
        add_text(slide, x + 0.16, y + 0.86, w - 0.3, 0.26, sub, size=10.5, color=MUTED, anchor="m",
                 margins=(0, 0, 0, 0))
        add_line(slide, x + 0.16, y + 1.18, x + w - 0.16, y + 1.18, BORDER, 0.75)
        add_text(slide, x + 0.16, y + 1.26, w - 0.3, h - 1.3, bullets(items, gap=6, color=hc), size=10.5,
                 color=BODY, margins=(0, 0, 0, 0), line_spacing=1.05)


# ---------------------------------------------------------------------------
# 第 3 页：目前的数据集设计（仿 MIMIC-IV 图 1 + ACES 图 4）
# ---------------------------------------------------------------------------
def build_design(slide):
    frame(slide, "数据集设计", "目前的数据集设计：原始事件 → 分级 → 结局",
          "原始事件分层存放，规则集派生分级与结局；主结局 O3 是首次门急诊就诊触发的 14 天预测。",
          ask_lead="现状：", ask="主分析人群 GD 住院 328 · GAM 住院 129 · GAM 门急诊 17——O3 风险集太小，要靠新门急诊数据和前瞻收集补。",
          notes=NOTES["design"])
    # ===== 左：数据流与表结构 =====
    lx1 = 6.45
    add_text(slide, CL, 1.72, lx1 - CL, 0.3, [[("① 数据流与表结构", {"bold": True, "color": NAVY}),
                                               ("（仿 MIMIC-IV 图 1）", {"color": MUTED, "size": 10.5})]],
             size=13, anchor="m", margins=(0, 0, 0, 0))
    top, bot = 2.1, 5.62
    sx, sw_ = CL, 1.25
    srcs = [("GD 住院", "原始导出 · 618", True), ("GAM 住院", "173", True), ("GAM 门急诊", "1,166", True),
            ("两院门急诊", "发热门诊 · 待申请", False), ("前瞻表单", "12 月上线", False)]
    sh = 0.6
    sg = (bot - top - 5 * sh) / 4
    mids = []
    for i, (a, b, solid) in enumerate(srcs):
        yy = top + i * (sh + sg)
        if solid:
            s = add_rect(slide, sx, yy, sw_, sh, fill=LIGHT, line=MID, line_w=1.0, shape=MSO_SHAPE.CAN)
            s.adjustments[0] = 0.18
            shape_text(s, [{"runs": a, "bold": True, "size": 10.5, "color": NAVY},
                           {"runs": b, "size": 9, "color": MUTED}], 10.5, NAVY, margins=(0.02, 0.1, 0.02, 0.0))
        else:
            s = add_rect(slide, sx, yy, sw_, sh, fill=WHITE, line=GREY, line_w=1.25, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
                         radius=0.15, dash=MSO_LINE_DASH_STYLE.DASH)
            shape_text(s, [{"runs": a, "bold": True, "size": 10.5, "color": MUTED},
                           {"runs": b, "size": 9, "color": MUTED}], 10.5, MUTED)
        mids.append(yy + sh / 2)
    bx = sx + sw_ + 0.12
    for m in mids:
        add_line(slide, sx + sw_ + 0.02, m, bx, m, MID, 1.25)
    add_line(slide, bx, mids[0], bx, mids[-1], MID, 1.25)
    cy = (top + bot) / 2
    # flucase 病例库
    fx, fw = bx + 0.24, 1.5
    add_line(slide, bx, cy, fx - 0.03, cy, MID, 1.75, arrow_end=True)
    add_rect(slide, fx, top, fw, bot - top, fill=WHITE, line=MID, line_w=1.25, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
             radius=0.06, shadow=True)
    hb = add_rect(slide, fx, top, fw, 0.42, fill=DARK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
    shape_text(hb, "flucase 病例库", 11.5, WHITE, bold=True, wrap=False)
    add_text(slide, fx + 0.1, top + 0.52, fw - 0.16, 1.9, bullets([
        "按格式族 + 格式配置认表",
        "医生看过“读到了什么”再确认入库",
        "每个值可追溯到文件 · 表 · 行 · 列",
        "两院共用一套文字规则词表"], gap=4), size=10, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)
    rb = add_rect(slide, fx + 0.1, bot - 1.04, fw - 0.2, 0.92, fill=AMBER_BG, line=AMBER, line_w=1.0,
                  shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    shape_text(rb, [{"runs": "规则集 v0.3", "bold": True, "size": 11, "color": AMBER},
                    {"runs": "分级时间线", "size": 10, "color": BODY},
                    {"runs": "候选结局 · 按口径", "size": 10, "color": BODY}], 11, AMBER)
    # std_v3 统一导出
    tx = fx + fw + 0.32
    tw = lx1 - tx
    add_line(slide, fx + fw + 0.03, cy, tx - 0.03, cy, MID, 1.75, arrow_end=True)
    add_text(slide, fx + fw - 0.02, cy - 0.32, 0.36, 0.26, "导出", size=9.5, color=MID, bold=True, align="c",
             margins=(0, 0, 0, 0))
    add_rect(slide, tx, top, tw, bot - top, fill=WHITE, line=DARK, line_w=1.25, shadow=True)
    hb = add_rect(slide, tx, top, tw, 0.42, fill=DARK)
    shape_text(hb, "std_v3 统一导出", 11.5, WHITE, bold=True, wrap=False)
    groups = [("就诊", "encounters（根表）", ["人口学 · 流感证据 · 流感季"]),
              ("事件", "events + 分域视图", ["体征 · 检验 · 诊断 · 流感检测", "原值 · 来源 · 时间精度"]),
              ("治疗", "treatments（区间）", ["氧疗 · 通气 · ICU 的起止"]),
              ("派生", "severity_timeline", ["判据标“原文 / 代理”", "outcomes：每种口径都给出"]),
              ("元数据", "字典 · 映射表 · manifest", ["SHA256；报告只含聚合量"])]
    gy = top + 0.5
    gh = (bot - gy - 0.06) / len(groups)
    for i, (g, t1, t2) in enumerate(groups):
        yy = gy + i * gh
        if i:
            add_line(slide, tx + 0.08, yy - 0.01, tx + tw - 0.08, yy - 0.01, BORDER, 0.75)
        gl = add_rect(slide, tx + 0.08, yy + 0.07, 0.52, 0.25, fill=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
                      radius=0.3)
        shape_text(gl, g, 9, NAVY, bold=True, wrap=False, margins=(0, 0, 0, 0))
        add_text(slide, tx + 0.66, yy + 0.04, tw - 0.7, gh - 0.06,
                 [{"runs": t1, "bold": True, "size": 10, "color": NAVY}] +
                 [{"runs": t, "size": 9, "color": MUTED} for t in t2], size=10, margins=(0, 0, 0, 0),
                 line_spacing=1.0)
    add_text(slide, CL, bot + 0.08, lx1 - CL, 0.5,
             [[("两院同表、同列、同编码、同取值；", {"bold": True, "color": NAVY}),
               ("导出不定 t0、人群和标签，按列筛选（D68）。实线 = 已到数据，虚线 = 待补来源。", {})]],
             size=10, color=MUTED, margins=(0, 0, 0, 0))

    # ===== 右：一次预测怎么定义（O3） =====
    rx = 6.72
    rw = CL + CW - rx
    add_line(slide, rx - 0.14, 1.78, rx - 0.14, 6.28, BORDER, 1.0)
    add_text(slide, rx, 1.72, rw, 0.3, [[("② 一次预测怎么定义：主结局 O3", {"bold": True, "color": NAVY}),
                                        ("（仿 ACES 图 4；示意，未按比例）", {"color": MUTED, "size": 10.5})]],
             size=13, anchor="m", margins=(0, 0, 0, 0))
    ay = 3.12
    p_on, p_t0, p_end = rx + 0.4, rx + 1.9, rx + rw - 0.7
    h24 = 0.4
    # 起点窗（t0 ± 24 h）
    add_rect(slide, p_t0 - h24, 2.1, 2 * h24, 0.27, fill=WIN_IN, line=WIN_IN_LINE, line_w=1.0)
    add_text(slide, p_t0 + h24 + 0.1, 2.08, rw, 0.31,
             [[("起点窗 t0 ± 24 h：", {"bold": True, "color": "2F6EA8"}), ("基线不超过中型", {})]],
             size=11, color=BODY, anchor="m", margins=(0, 0, 0, 0))
    # 标签窗（14 天）
    add_rect(slide, p_t0, 2.47, p_end - p_t0, 0.34, fill=WIN_OUT, line=WIN_OUT_LINE, line_w=1.0)
    add_text(slide, p_t0 + 0.12, 2.47, p_end - p_t0 - 0.2, 0.34,
             [[("标签窗 14 天：", {"bold": True}), ("住院 或 达到重型及以上 → 1", {})]],
             size=11, color=WIN_OUT_TEXT, anchor="m", margins=(0, 0, 0, 0))
    # 起点窗的两条竖虚线：右边那条在标签窗处断开，不压字
    add_line(slide, p_t0 - h24, 2.37, p_t0 - h24, ay, WIN_IN_LINE, 0.75, dash=MSO_LINE_DASH_STYLE.DASH)
    add_line(slide, p_t0 + h24, 2.37, p_t0 + h24, 2.47, WIN_IN_LINE, 0.75, dash=MSO_LINE_DASH_STYLE.DASH)
    add_line(slide, p_t0 + h24, 2.81, p_t0 + h24, ay, WIN_IN_LINE, 0.75, dash=MSO_LINE_DASH_STYLE.DASH)
    add_line(slide, p_end, 2.81, p_end, ay, WIN_OUT_LINE, 0.75, dash=MSO_LINE_DASH_STYLE.DASH)
    add_line(slide, p_t0, 2.81, p_t0, ay, DARK, 0.75, dash=MSO_LINE_DASH_STYLE.DASH)
    # 时间轴与三个点
    add_line(slide, rx + 0.02, ay, rx + rw - 0.02, ay, NAVY, 2.25, arrow_end=True)
    add_text(slide, rx + rw - 0.55, ay - 0.27, 0.5, 0.22, "时间", size=9, color=MUTED, align="r", margins=(0, 0, 0, 0))
    for px, fill in ((p_on, WHITE), (p_t0, DARK), (p_end, WHITE)):
        add_oval(slide, px, ay, 0.2, fill=fill, line=NAVY, line_w=1.5)
    # 发病时钟
    add_rect(slide, p_on, ay + 0.17, p_t0 - p_on, 0.26, fill=CLOCK_BG, line=GREY, line_w=0.75)
    add_text(slide, p_on, ay + 0.17, p_t0 - p_on, 0.26, "发病时钟", size=9.5, color=NAVY, bold=True, align="c",
             anchor="m", margins=(0, 0, 0, 0))
    ly = ay + 0.5
    add_text(slide, p_on - 0.36, ly, 1.3, 0.46,
             [{"runs": "起病", "bold": True, "color": NAVY}, {"runs": "首个流感样症状", "size": 9, "color": MUTED}],
             size=10.5, margins=(0, 0, 0, 0))
    add_text(slide, p_t0 - 0.1, ly, 2.7, 0.46,
             [{"runs": "t0 = 首次门急诊就诊（触发）", "bold": True, "color": NAVY},
              {"runs": "院内发病取首次流感阳性", "size": 9, "color": MUTED}],
             size=10.5, margins=(0, 0, 0, 0))
    add_text(slide, p_end - 1.2, ly, 1.82, 0.46,
             [{"runs": "t0 + 14 天", "bold": True, "color": NAVY, "align": "r"},
              {"runs": "7 天窗作敏感性", "size": 9, "color": MUTED, "align": "r"}],
             size=10.5, margins=(0, 0, 0, 0))
    # 约束标签（仿 ACES 的绿色标签）
    cx = rx
    for t in ("当次收住院 → 排除", "基线已达重型 → 排除", "未关联全院记录 / 转院 → 记“未知”"):
        cx += pill_at(slide, cx, 4.13, t, RULE_BG, RULE_TX, size=10, h=0.29) + 0.12

    # 要素框 + 分级阶梯
    by = 4.56
    bh = 6.28 - by
    kw_ = 3.02
    add_rect(slide, rx, by, kw_, bh, fill=PALE, line=BORDER)
    rows = [("人群", "病原学确诊；≥60 岁（≥65 亚组）"),
            ("索引", "每人每个流感季第一次符合条件的就诊"),
            ("口径", "主：治疗类 + 诊断类；敏感性：生理类、只用方案原文"),
            ("验证", "GAM + GD 合并开发，按医院内-外交叉验证；新季节只评一次")]
    ry = by + 0.06
    rh = (bh - 0.12) / len(rows)
    for k, v in rows:
        add_text(slide, rx + 0.1, ry, 0.46, rh, k, size=10, color=NAVY, bold=True, anchor="m", margins=(0, 0, 0, 0))
        add_text(slide, rx + 0.55, ry, kw_ - 0.62, rh, v, size=9.5, color=BODY, anchor="m", margins=(0, 0, 0, 0),
                 line_spacing=1.0)
        ry += rh
    lx = rx + kw_ + 0.12
    lw2 = rx + rw - lx
    levels = [("危重型", "机械通气（含无创）· 休克 · ICU + 器官衰竭；代理：进 ICU、ECMO"),
              ("重型", "RR ≥30 · 吸空气 SpO2 ≤93% · PF ≤300；代理：新开始氧疗、高流量"),
              ("中型", "肺炎（影像 / 诊断）· 呼吸困难")]
    lg = 0.06
    lh2 = (bh - 2 * lg) / 3
    for i, (lv, desc) in enumerate(levels):
        yy = by + i * (lh2 + lg)
        c = add_rect(slide, lx, yy, 0.58, lh2, fill=LEVEL[lv])
        shape_text(c, lv, 10, WHITE, bold=True, wrap=False, margins=(0, 0, 0, 0))
        add_rect(slide, lx + 0.58, yy, lw2 - 0.58, lh2, fill=WHITE, line=BORDER)
        add_text(slide, lx + 0.66, yy, lw2 - 0.72, lh2, desc, size=9.5, color=BODY, anchor="m", margins=(0, 0, 0, 0),
                 line_spacing=1.0)


# ---------------------------------------------------------------------------
# 第 4–7 页：四篇典型论文（左：原图；右：怎么做 / 优势 / 局限；底部黄框：对我们）
# ---------------------------------------------------------------------------
def build_mimic(slide):
    frame(slide, "论文 ①", "MIMIC-IV：一个数据库怎么建",
          "Sci Data 2023：BIDMC 十年数据，按来源分模块、尽量少加工、版本化发布，并做技术验证。",
          ask_lead="对我们：", ask="std_v3 已有原值、来源与 manifest；补带阈值的验收测试和“时间来源”列，ICU 认定改成查找表。",
          notes=NOTES["mimic"])
    path = FIG / "MIMIC-IV_Fig1.png"
    fw = 6.75
    fh = fit_h(path, fw)
    box = figure(slide, path, CL, 1.76, fw, fh, "论文原图：MIMIC-IV Fig.1")
    for (fx, fy), t in zip([(0.05, 0.06), (0.21, 0.32), (0.45, 0.32), (0.60, 0.05), (0.30, 0.66)],
                           ["①", "②", "③", "④", "⑤"]):
        tag(slide, box, fx, fy, t)
    cy = 1.76 + fh + 0.05
    caption(slide, CL, cy, fw, 0.46,
            [("原图 ", {"bold": True, "color": NAVY}),
             ("Johnson AEW 等, Sci Data 2023;10:1, Fig. 1（p2，CC BY 4.0）。编号为本页所加：", {}),
             ("① 采集  ② 格式转换  ③ 去标识  ④ 分模块发布  ⑤ 用户反馈回流修正", {"color": AMBER, "bold": True})])
    ty = cy + 0.52
    th = 6.28 - ty
    tiles = [("431,231", "次住院（表 1，p4）"), ("73,181", "次 ICU 住段"), ("3 个模块", "hosp · icu · note")]
    tw = (fw - 2 * 0.15) / 3
    for i, (big, lab) in enumerate(tiles):
        x = CL + i * (tw + 0.15)
        add_rect(slide, x, ty, tw, th, fill=WHITE, line=BORDER, shadow=True)
        add_text(slide, x + 0.16, ty + 0.04, tw - 0.3, th - 0.08,
                 [{"runs": big, "bold": True, "size": 17, "color": DARK},
                  {"runs": lab, "size": 10, "color": MUTED}], size=17, anchor="m", margins=(0, 0, 0, 0),
                 line_spacing=1.0)
    rx = CL + fw + 0.25
    rw = CL + CW - rx
    block(slide, rx, 1.76, rw, 2.5, "怎么做", [
        "三步：采集（院内数据仓库、ICU 系统、外部来源）→ 格式转换 → 去标识（p2，图 1）",
        "两条原则：与 MIMIC-III 向后兼容；尽量少加工，贴近临床原始记录（p3）",
        "按来源分 hosp / icu / note 模块，用 subject_id、hadm_id 和平移后的时间联结（p3）",
        "技术验证：单一构建脚本 + 版本控制 + 代码评审；单元测试查完整性、一致性（≥99% ICU 住段有诊断、有心率）并与上一版比对（p7–8）"],
          kind="how", size=11, gap=4)
    hw = (rw - 0.15) / 2
    yy = 4.36
    block(slide, rx, yy, hw, 6.28 - yy, "优势", [
        "测量时刻 charttime 与核实时刻 storetime 分开存，时间语义清楚（p7）",
        "每版可复现、可比对；通气、升压药等派生概念用共享代码（p8）"], kind="pro", size=10.5, gap=3)
    block(slide, rx + hw + 0.15, yy, hw, 6.28 - yy, "局限（对本项目）", [
        "单中心，只收进过急诊或 ICU 的患者（p2）",
        "日期按患者平移，真实年份只给 3 年一档（p4–5），不给季节（官方文档）→ 做不了流感季分析"], kind="con", size=10.5, gap=3)


def build_clif(slide):
    frame(slide, "论文 ②", "CLIF：多家医院怎么合到一种格式",
          "8 个医疗系统、33 家医院、94,356 次 ICU 入住：23 张纵向表，标准类别 _category 与医院原名 _name 并列。",
          ask_lead="对我们：", ask="建呼吸支持长表（设备类别 + 起止 + 原文）；每个统一编码写允许取值清单；ICU 不只看科室名。",
          notes=NOTES["clif"])
    path = FIG / "CLIF_Fig1.png"
    fw = 4.5
    fh = fit_h(path, fw)
    box = figure(slide, path, CL, 1.76, fw, fh, "论文原图：CLIF Figure 1（ER 图）")
    mark(slide, box, 0.418, 0.004, 0.625, 0.49)
    ix, iy, iw, ih = box
    pill_at(slide, ix + 0.418 * iw - 0.05, iy + 0.49 * ih + 0.04, "呼吸支持表", AMBER, WHITE, size=10, h=0.26)
    caption(slide, CL, 1.76 + fh + 0.05, fw, 0.62,
            [("原图 ", {"bold": True, "color": NAVY}),
             ("Rojas JC, Lyons PG 等, medRxiv 2024（期刊版 Intensive Care Med 2025;51:556–69），Figure 1（p13，"
              "CC BY 4.0）；橙框为本页所加", {})])
    rx = CL + fw + 0.25
    rw = CL + CW - rx
    p2 = FIG / "CLIF_Fig2A.png"
    f2w = 3.55
    f2h = fit_h(p2, f2w)
    f2x = CL + CW - f2w
    figure(slide, p2, f2x, 1.76, f2w, f2h, "论文原图：CLIF Figure 2A（各站 ROC）")
    caption(slide, f2x, 1.76 + f2h + 0.04, f2w, 0.42,
            [("Figure 2A（p14）：", {"bold": True, "color": NAVY}),
             ("Rush 训练的死亡模型在 8 家（含 Rush 本院）验证，AUC 0.74–0.83", {})])
    hw_ = f2x - rx - 0.2
    block(slide, rx, 1.76, hw_, 2.6, "怎么做", [
        "2023-07 起每周例会，统一流程、术语与质控（p3）",
        "mCIDE：每张表一组 _category 元素，取值是受控清单；_name 存医院原名（p4）",
        "例：UCM_LAB HEMOGLOBIN - AUTOMATED → Hemoglobin",
        "23 张表按信息类型与器官系统组织；重症专用：呼吸支持、持续用药、透析、ECMO、体位（p3–4）",
        "联邦分析：脚本与模型发到各家本地跑，只回传聚合结果（p4–5）"], kind="how", size=10.5, gap=2)
    yy = 4.48
    hw = (rw - 0.15) / 2
    block(slide, rx, yy, hw, 6.28 - yy, "优势", [
        "临床可读；原名可回查",
        "呼吸支持细到设备、模式与设置",
        "格式统一后，多中心外部验证“自带”"], kind="pro", size=10.5, gap=3)
    block(slide, rx + hw + 0.15, yy, hw, 6.28 - yy, "局限（论文自述，p7–8）", [
        "每家落地都要大量数据科学与重症投入",
        "按所在科室（ADT）定义重症人群：选择偏倚、左删失",
        "未接 FHIR；行级数据不公开"], kind="con", size=10.5, gap=3)


def build_aces(slide):
    frame(slide, "论文 ③", "ACES：预测任务怎么写清楚",
          "ICLR 2025：任务 = 数据集专用的“谓词” + 与数据集无关的“窗口”；触发、输入、间隔、目标都写进配置文件。",
          ask_lead="对我们：", ask="规则集 v0.4 拆两层——中心专用的判据映射 + 中心无关的 O3 任务文件；导出每个预测实例一行。",
          notes=NOTES["aces"])
    path = FIG / "ACES_Fig4.png"
    fw = 4.5
    fh = fit_h(path, fw)
    figure(slide, path, CL, 1.76, fw, fh, "论文原图：ACES Figure 4")
    caption(slide, CL, 1.76 + fh + 0.05, fw, 0.5,
            [("原图 ", {"bold": True, "color": NAVY}),
             ("Xu J, Gallifant J, Johnson AEW, McDermott MBA. ACES. ICLR 2025, Figure 4（p7）：入院后 48 小时预测院内死亡", {})])
    rx = CL + fw + 0.25
    rw = CL + CW - rx
    p2 = FIG / "Lauritsen_Fig2_ad.png"
    f2w = 3.3
    f2h = fit_h(p2, f2w)
    f2x = CL + CW - f2w
    figure(slide, p2, f2x, 1.76, f2w, f2h, "论文原图：Lauritsen 2021 Fig.2（a–d）")
    caption(slide, f2x, 1.76 + f2h + 0.04, f2w, 0.62,
            [("旁证 ", {"bold": True, "color": NAVY}),
             ("Lauritsen 2021, npj Digit Med 4:158, Fig. 2（p5）：同一批住院，", {}),
             ("a 发病前固定时刻 AUROC 0.906（正负 1:15）；b 滑动窗口 0.756（1:750）", {"bold": True, "color": AMBER})])
    hw_ = f2x - rx - 0.2
    add_rect(slide, rx, 1.76, hw_, 0.28, fill=DARK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    add_text(slide, rx, 1.76, hw_, 0.28, "怎么做（对照左图 A–E）", size=11.5, color=WHITE, bold=True, align="c",
             anchor="m", margins=(0, 0, 0, 0))
    legend_rows = [("A", "7CB342", "谓词：入院 / 出院 / 死亡映射到本库编码"),
                   ("C", "C0504D", "触发：每次入院产生一个预测"),
                   ("B", "5B9BD5", "输入窗：至触发后 24 h，且至少 5 条事件"),
                   ("D", "D4A017", "间隔窗：48 h 内不得出院或死亡，否则排除"),
                   ("E", "9B59B6", "目标窗：到下次出院或死亡，死亡 = 1")]
    yy = 2.08
    for letter, col, text in legend_rows:
        b = add_rect(slide, rx, yy + 0.025, 0.29, 0.29, fill=WHITE, line=col, line_w=2.0,
                     shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
        shape_text(b, letter, 10.5, NAVY, bold=True, margins=(0, 0, 0, 0), wrap=False)
        add_text(slide, rx + 0.37, yy, hw_ - 0.37, 0.33, text, size=10.5, color=BODY, anchor="m",
                 margins=(0, 0, 0, 0), line_spacing=1.0)
        yy += 0.33
    # 我们的 O3 按 ACES 的写法（示意）
    oy = yy + 0.08
    oh = 5.04 - oy
    add_rect(slide, rx, oy, hw_, oh, fill=PALE, line=MID, line_w=1.0, dash=MSO_LINE_DASH_STYLE.DASH,
             name="O3 按 ACES 写法")
    add_text(slide, rx + 0.1, oy + 0.03, hw_ - 0.2, 0.26, "我们的 O3 按这种写法拆开（示意）", size=10.5, color=NAVY,
             bold=True, anchor="m", margins=(0, 0, 0, 0))
    o3 = [("C", "C0504D", "触发：首次门急诊就诊 = t0（院内发病取首次阳性）"),
          ("B", "5B9BD5", "起点窗：t0 ± 24 h，用来定基线"),
          ("E", "9B59B6", "标签窗：t0 后 14 天，住院或 ≥重型 = 1"),
          ("–", "8A94A6", "排除：当次收住院、基线已达重型；关联不到记“未知”")]
    ry = oy + 0.31
    rh = (oy + oh - 0.05 - ry) / len(o3)
    for letter, col, text in o3:
        b = add_rect(slide, rx + 0.1, ry + (rh - 0.19) / 2, 0.19, 0.19, fill=WHITE, line=col, line_w=1.25,
                     shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
        shape_text(b, letter, 8, NAVY, bold=True, margins=(0, 0, 0, 0), wrap=False)
        add_text(slide, rx + 0.4, ry, hw_ - 0.48, rh, text, size=9.5, color=BODY, anchor="m", margins=(0, 0, 0, 0),
                 line_spacing=1.0)
        ry += rh
    yy = 5.12
    hw = (rw - 0.15) / 2
    block(slide, rx, yy, hw, 6.28 - yy, "优势", [
        "任务定义可共享、跨库复用（换库只换谓词）；排除规则显式",
        "针对复现难：MIMIC-III 研究过半队列重建不出，人数差可达 25%（p1）"], kind="pro", size=10.5, gap=2)
    block(slide, rx + hw + 0.15, yy, hw, 6.28 - yy, "局限（§4.2、附录 B）", [
        "数据要先是事件流（MEDS / ESGPT）；文本信息要先抽成谓词",
        "与同类工具只做了初步对比，作者自认可能有偏"], kind="con", size=10.5, gap=2)


def build_isaric(slide):
    frame(slide, "论文 ④", "ISARIC 4C：转重结局怎么定、怎么验证",
          "英国 260 家医院 74,944 名住院成人：复合结局 + 入院时 11 个常规变量 + 按地区内-外交叉验证。",
          ask_lead="对我们：", ask="O3 写清组成与理由；保留生理类口径、死亡单列（老年人升级治疗少）；两个中心不够，要多收中心。",
          notes=NOTES["isaric"])
    path = FIG / "ISARIC4C_Fig2.png"
    fw = 7.85
    fh = fit_h(path, fw)
    box = figure(slide, path, CL, 1.76, fw, fh, "论文原图：ISARIC 4C Figure 2（内-外交叉验证）")
    mark(slide, box, -0.006, 0.742, 1.008, 0.822)
    caption(slide, CL, 1.76 + fh + 0.05, fw, 0.32,
            [("原图 ", {"bold": True, "color": NAVY}),
             ("Gupta RK 等, Lancet Respir Med 2021;9:349–59, Figure 2（p355，CC BY 4.0）：8 个地区轮流留一；"
              "橙框为随机效应合并（本页所加）", {})])
    ty = 1.76 + fh + 0.45
    th = 6.28 - ty
    tiles = [("结局", "开始通气支持（无创、有创、ECMO）、进 HDU/ICU 或死亡；≈ WHO 进展量表 ≥6，不受各院呼吸支持习惯影响（p350）"),
             ("时点", "入院时；院内感染取首次评估（p356）。起病或首次阳性在入院 7 天内算社区获得（p351）"),
             ("变量", "只纳入 ≥60% 人群可得的预设变量（p351），留下 11 个：年龄、SpO2 + 吸空气 / 吸氧、呼吸、尿素、CRP 等（p354）"),
             ("验证", "8 地区留一：C 0.75–0.77，合并 0.76；伦敦整区留出（8,239 人）C 0.77、校准斜率 0.96（p355）")]
    gap = 0.14
    tw = (fw - 3 * gap) / 4
    for i, (k, v) in enumerate(tiles):
        x = CL + i * (tw + gap)
        add_rect(slide, x, ty, tw, th, fill=WHITE, line=BORDER, shadow=True)
        add_rect(slide, x, ty, tw, 0.32, fill=DARK)
        add_text(slide, x + 0.1, ty, tw - 0.2, 0.32, k, size=11.5, color=WHITE, bold=True, anchor="m",
                 margins=(0, 0, 0, 0))
        add_text(slide, x + 0.1, ty + 0.38, tw - 0.18, th - 0.42, v, size=10, color=BODY, margins=(0, 0, 0, 0),
                 line_spacing=1.05)
    rx = CL + fw + 0.25
    rw = CL + CW - rx
    block(slide, rx, 1.76, rw, 1.2, "优势", [
        "复合结局跨院可比；43.2% 发生，中位 4 天（p354）",
        "前瞻、标准化病例报告表；用地区间差异检验泛化"], kind="pro", size=10.5, gap=2)
    block(slide, rx, 3.04, rw, 1.56, "局限", [
        "只限住院成人、2020 年英国 COVID",
        "“≥60% 可得”让 LDH、D-二聚体进不了模型（p358）",
        "年长者恶化更多直接死亡、较少升级治疗（p356）→ 治疗类结局受升级决策影响"], kind="con", size=10.5, gap=2)
    block(slide, rx, 4.68, rw, 1.6, "请讨论", [
        "O3 把“14 天内住院”也算结局（≈ WHO 量表 ≥4 分）；ISARIC 取 ≥6，理由是各院呼吸支持习惯不同、结局要跨院可比",
        "O3 是否加“≥重型”的敏感性口径？"], kind="con", size=10.5, gap=3, fill=AMBER_BG)


# ---------------------------------------------------------------------------
# 第 8 页：四篇对照
# ---------------------------------------------------------------------------
def build_compare(slide):
    frame(slide, "对照", "四篇对照：取其所长，补其所短",
          "已有：原值可追溯、两院同表、分级时间线；还缺：验收测试、呼吸支持表、任务配置化、门急诊样本与更多中心。",
          ask_lead="原则：", ask="先做不改定义的技术项（可在虚构数据上做）；改定义的口径登记为规则集 v0.4，旧版保留、两院重算对比。",
          notes=NOTES["compare"])
    cols = [("论文 · 解决的问题", 1.85, NAVY), ("优势 → 我们采用", 2.75, CYAN), ("局限 → 我们要补", 2.75, AMBER),
            ("我们现在", 2.45, MUTED), ("落到计划", 2.13, DARK)]
    gap = 0.075
    xs = []
    x = CL
    for name, w, col in cols:
        xs.append(x)
        hb = add_rect(slide, x, 1.76, w, 0.34, fill=col if col != MUTED else "8A94A6")
        shape_text(hb, name, 11.5, WHITE, bold=True)
        x += w + gap
    rows = [
        ("①", "MIMIC-IV", "一个库怎么建",
         "少加工、保留原始时间语义；版本化发布 + 单元测试",
         "单中心；日期平移看不到流感季；派生概念在库外",
         "std_v3 有原值、来源、时间精度、manifest；没有带阈值的验收",
         "验收测试\n时间来源列"),
        ("②", "CLIF", "多中心怎么合",
         "_category 与 _name 并列；呼吸支持细表；联邦外部验证",
         "每家落地成本高；按科室（ADT）定义重症有偏",
         "两院同表同编码；还没有呼吸支持表；ICU 只看科室名",
         "呼吸支持长表\n允许取值清单\nICU = 科室 + 医嘱"),
        ("③", "ACES", "任务怎么写",
         "谓词与窗口分离；排除规则显式；抽取可复现",
         "要求事件流格式；文本信息要先抽",
         "规则集 v0.3 里判据映射与任务窗口在同一文件",
         "v0.4 拆两层\n导出预测实例表"),
        ("④", "ISARIC 4C", "结局与验证",
         "复合结局跨院可比；按地区留出验证",
         "只限住院；老年人升级治疗少；需要多个地区",
         "O3 门急诊只有 17 次；只有 2 个中心",
         "申请门急诊数据\n样本量估算 · 前瞻收集\n多收中心"),
    ]
    ry, rh, rg = 2.18, 0.95, 0.08
    for i, (num, name, prob, pro, con, now, plan) in enumerate(rows):
        y = ry + i * (rh + rg)
        add_rect(slide, CL, y, CW, rh, fill=WHITE, line=BORDER, shadow=True)
        add_rect(slide, xs[0], y, cols[0][1], rh, fill=LIGHT)
        num_badge(slide, xs[0] + 0.28, y + rh / 2, num, fill=DARK, d=0.36, size=12)
        add_text(slide, xs[0] + 0.52, y, cols[0][1] - 0.56, rh,
                 [{"runs": name, "bold": True, "size": 12.5, "color": NAVY},
                  {"runs": prob, "size": 10.5, "color": MUTED}], size=12, anchor="m", margins=(0, 0, 0, 0))
        for k, (text, col) in enumerate(((pro, BODY), (con, BODY), (now, BODY))):
            add_text(slide, xs[k + 1] + 0.1, y, cols[k + 1][1] - 0.16, rh, text, size=11, color=col, anchor="m",
                     margins=(0, 0, 0, 0), line_spacing=1.05)
        pb = add_rect(slide, xs[4] + 0.06, y + 0.1, cols[4][1] - 0.12, rh - 0.2, fill=PALE, line=MID, line_w=0.75,
                      shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
        shape_text(pb, plan, 10.5, NAVY, bold=True, margins=(0.06, 0.02, 0.06, 0.02))


# ---------------------------------------------------------------------------
# 第 9 页：后续安排（三条；10-27 由按周的时间线改来）
# ---------------------------------------------------------------------------
PLAN_TAG = {  # 每条右侧的状态标签：(底色, 文字色)
    "需讨论拍板": (AMBER_BG, AMBER),
    "技术项 · 可先做": (CYAN_BG, "0089AA"),
    "需协调信息科": (RED_BG, RED),
}


def build_plan(slide):
    """10-27 改为三条：每条一行（左：做什么与依据；中：一句话；右：状态与产出），不按周排，时间只留 12 月流感高峰。"""
    frame(slide, "后续安排", "后续安排：按四篇的长处补数据集，流感高峰前上线收集",
          "三件事：定口径、补数据底座、补门急诊样本；技术项可先做，改定义的等口径定稿后再重算。",
          ask_lead="唯一时间节点：", ask="12 月流感高峰前上线前瞻收集；GAM 补充数据、证型、六模型汇总等原计划照常并行。",
          notes=NOTES["plan"])
    rows = [
        ("1", "定口径", "规则集 v0.4 · 依据 GD 答复",
         "讨论确定 ICU、慢性低氧、再住院、确诊、发热 5 处口径，\n登记为 v0.4，两院按新旧版本重算对比。",
         "需讨论拍板", "v0.4 两院真实计数"),
        ("2", "补数据底座", "借鉴 MIMIC-IV · CLIF · ACES",
         "验收测试与时间来源列；呼吸支持长表与 ICU 查找表；\n规则集拆两层，导出预测实例表。",
         "技术项 · 可先做", "验收报告 · 呼吸支持表\nO3 任务文件"),
        ("3", "补门急诊样本", "借鉴 ISARIC 4C",
         "按 GD 给的检索条件申请两院门急诊、发热门诊数据，\n估算样本量；前瞻表单定稿后上线收集。",
         "需协调信息科", "数据申请进展 · 样本量估算"),
    ]
    gap = 0.2
    top, bot = 1.76, 6.3
    rh = (bot - top - 2 * gap) / 3
    lw = 3.3     # 左：做什么与依据
    rw = 2.75    # 右：状态与产出
    for i, (num, head, src, desc, tag_text, out) in enumerate(rows):
        y = top + i * (rh + gap)
        add_rect(slide, CL, y, CW, rh, fill=WHITE, line=BORDER, shadow=True, name=f"{head}·行")
        add_rect(slide, CL, y, lw, rh, fill=LIGHT)
        num_badge(slide, CL + 0.45, y + rh / 2, num, fill=DARK, d=0.5, size=18)
        add_text(slide, CL + 0.85, y, lw - 0.95, rh,
                 [{"runs": head, "bold": True, "size": 20, "color": NAVY},
                  {"runs": src, "size": 11, "color": MUTED, "space_before": 2}],
                 size=20, anchor="m", margins=(0, 0, 0, 0))
        mx = CL + lw + 0.3
        rx = CL + CW - rw
        add_text(slide, mx, y, rx - mx - 0.3, rh, desc, size=15, color=BODY, anchor="m", margins=(0, 0, 0, 0),
                 line_spacing=1.15)
        add_line(slide, rx, y + 0.22, rx, y + rh - 0.22, BORDER, 1.0)
        bg, fg = PLAN_TAG[tag_text]
        pill_at(slide, rx + 0.25, y + rh / 2 - 0.38, tag_text, bg, fg, size=11, h=0.3)
        add_text(slide, rx + 0.25, y + rh / 2 + 0.04, rw - 0.4, 0.5,
                 [[("产出：", {"bold": True, "color": NAVY}), (out, {})]], size=11, color=BODY,
                 margins=(0, 0, 0, 0))


# ---------------------------------------------------------------------------
# 封面、致谢、附录
# ---------------------------------------------------------------------------
def fix_cover(cover):
    for shp in cover.shapes:
        if not shp.has_text_frame:
            continue
        text = shp.text_frame.text.strip()
        if text.startswith("老年流感"):
            base.set_shape_text(shp, "老年流感转重研究：近期工作与论文阅读汇报")
        elif text.startswith("理想数据"):
            base.set_shape_text(shp, "已做工作 · 数据集设计 · 典型论文 · 后续安排")
        elif text.startswith("2026"):
            base.set_shape_text(shp, "2026年10月26日")
    cover.notes_slide.notes_text_frame.text = NOTES["cover"]


def build_closing(slide):
    from lxml import etree
    from pptx.oxml.ns import qn
    band = add_rect(slide, 0, 2.55, SW, 1.6, fill="4472C4", name="致谢横带")
    shape_text(band, "谢谢！欢迎讨论与指正", 40, WHITE)
    for r in band.text_frame.paragraphs[0].runs:
        rPr = r._r.get_or_add_rPr()
        eff = etree.Element(qn("a:effectLst"))
        sh = etree.SubElement(eff, qn("a:outerShdw"), blurRad="50800", dist="38100", dir="5400000", algn="ctr",
                              rotWithShape="0")
        clr = etree.SubElement(sh, qn("a:srgbClr"), val="000000")
        etree.SubElement(clr, qn("a:alpha"), val="45000")
        rPr.find(qn("a:solidFill")).addnext(eff)
    add_text(slide, 1.0, 4.45, SW - 2.0, 0.5,
             "附录 A1–A5：两院判据差异 · GD 临床答复 · 中医证型 · 需要讨论确定的口径 · 34 篇阅读路线",
             size=16, color=NAVY, align="c", anchor="m")
    slide.notes_slide.notes_text_frame.text = NOTES["closing"]


APPENDIX = [  # (编号, v1 的页面函数)
    ("A1", "build_sitediff"),
    ("A2", "build_answers"),
    ("A3", "build_tcm"),
    ("A4", "build_decide"),
    ("A5", "build_route"),
]


def build_appendix(prs, blank):
    """沿用 v1 的页面，只把章节标签改成“附录 Ax”，并把指向 v1 页码的引用改成附录编号。"""
    base.NOTES["sitediff"] = base.NOTES["sitediff"].replace("见第 9 页", "见附录 A2")
    base.NOTES["decide"] = base.NOTES["decide"].replace("第 5 页", "附录 A1")
    orig = base.frame
    for code, fn in APPENDIX:
        def appendix_frame(slide, badge, title, key, _code=code, **kw):
            return orig(slide, f"附录 {_code}", title, key, **kw)
        base.frame = appendix_frame
        try:
            slide = prs.slides.add_slide(blank)
            getattr(base, fn)(slide)
        finally:
            base.frame = orig
        replace_text(slide, "见第 9 页", "见附录 A2")


def main():
    prs = Presentation(str(base.SRC))
    fix_cover(prs.slides[0])
    base.delete_slides_after_first(prs)
    blank = prs.slide_layouts.get_by_name("Blank")
    for build in (build_work, build_design, build_mimic, build_clif, build_aces, build_isaric, build_compare,
                  build_plan, build_closing):
        build(prs.slides.add_slide(blank))
    build_appendix(prs, blank)
    prs.core_properties.title = base.DECK_TITLE
    prs.core_properties.subject = ("已做工作（10-17 至 10-25）、目前的数据集设计、4 篇典型论文（MIMIC-IV、CLIF、ACES、"
                                   "ISARIC 4C）及其优势与局限、后续安排；附录为两院判据、GD 答复、证型、待定口径与阅读路线")
    prs.save(str(OUT))
    print(f"已生成：{OUT}（共 {len(prs.slides)} 页）")


if __name__ == "__main__":
    main()
