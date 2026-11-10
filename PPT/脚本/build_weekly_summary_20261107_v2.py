# -*- coding: utf-8 -*-
"""
生成《老年流感转重研究 · 本周工作总结》v2（2026-11-07）。

相对 v1（build_weekly_summary_20261107.py）的改动，研究者 11-07 要求去掉 AI 风格、图改成期刊级：
- 版式：保留校训封面和蓝色标题栏；去掉章节徽章、青色分隔线、顶部色条、浅蓝信息条、浅黄结论框、彩色标题卡片、
  投影、大数字卡片、01/02 编号块、时间线圆点和箭头流程条；表格改成三线表；每页底部写数据口径和出处。
- 图：由 PPT/脚本/build_figures_20261107.py 用 matplotlib 按期刊规范出图（journal_style，thesis），不再是 PowerPoint 原生图表；
  要改图改那个脚本，矢量版在 PPT/素材/图_20261107/*.pdf。
- 文字：标题改成陈述实际内容，去掉对仗、口号、“不是…是…”句式、粗体引导词和只为强调的引号；能写数字的地方写数字。

输入：PPT/模板/hospital_优化版.pptx（模板，只读）、PPT/素材/图_20261107/fig_*.png。
输出：PPT/成品/周报与进展/本周工作总结_20261107_v2.pptx
11-07 又用 Humanizer 技能过了一遍文字：去掉收尾句、对称分号句、格言式句子和表格首列的逐行加粗，只改措辞。
数字来源同 v1（见 v1 脚本开头）。③ 的运行状态是 11-07 13:15 在服务器上看的。没有读任何真实病例。

运行（BaseModel 根目录）：先 python PPT/脚本/build_figures_20261107.py，再 python PPT/脚本/build_weekly_summary_20261107_v2.py
依赖：python-pptx、lxml（本机 Anaconda 环境有）、matplotlib
"""

import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_weekly_summary_20261023 as base  # noqa: E402
from build_weekly_summary_20261023 import (  # noqa: E402
    BODY, CL, CW, DARK, MID, MUTED, NAVY, SW, WHITE, add_rect, add_slide_number, add_text, bullets, fill_text,
    set_cell_border, shape_text)

OUT = HERE.parent / "成品" / "周报与进展" / "本周工作总结_20261107_v2.pptx"
FIG = HERE.parent / "素材" / "图_20261107"
DECK = "老年流感转重研究 · 本周工作总结"
TOP = 1.50
RULE = "33415C"


# ---------------------------------------------------------------------------
# 演讲者备注（合计约 25 分钟）
# ---------------------------------------------------------------------------
NOTES = {
    "cover": "本周指 11-02 到 11-07。讲四部分：急诊子集诊断、八个基础模型零样本、J 线、flucase。数字都是聚合量，除确认集那一步外结论都标探索性。全程约 25 分钟。",
    "summary": "约 1 分钟。这六条是本周的结论，后面按这个顺序讲。冻结嵌入加线性探针的嵌入已经抽完，探针还没开始拟合，今天只讲设计。",
    "week": "约 1.5 分钟。11-02 组会定了五步：调研、跑模型、划子集、打补丁、找备选急诊数据。11-03 下午任务口径锁定后建库，当天做完子集发现。"
            "11-04 做补丁 1、2，放行补丁 1 后评价确认集。11-05 跑补丁 3，J 线也在这两天做完。11-06、11-07 做八个基础模型零样本和补丁 3 的后续分析。"
            "原来排的多医院后训练按组会结论这周没有做。",
    "survey": "约 1.5 分钟。图是八个模型的典型或最大上下文长度，对数坐标，橙色是我们的三个窗口，差两到三个数量级。LightGTS 约数百点，没有精确数字，所以没画。"
              "公开急诊原始库只核实到我们手上这两个，中文资源还要再查。",
    "design": "约 1.5 分钟。两库任务不同，MIMIC-IV-ED 没有床旁连续监护，所以定到院 2 h 预测，此后 12 h 内进 ICU 或院内死亡。"
              "右边是流程。D105 的切分：MC-MED 发现集是验证集加测试集 A 半，确认集是 B 半；MIMIC-IV-ED 验证集发现，测试集确认。D111 之后确认集不再使用。",
    "forest": "约 1.5 分钟。每行一个登记子集，括号外是就诊数和阳性数。横轴是子集减补集的 AUROC，小于 0 表示这个子集排序更差。灰色是补丁前，蓝色是 3b 输入，实心是过半数 seed 稳定变差。"
              "五列的实心点位置接近，所以短板是共有的。橙色底的一行是最差的格子，3b 之后差距缩小一半左右，仍然最差。"
              "子集减补集是相对量，按强预测因子切出来的子集组内 AUROC 会机械性变低，原因目前都是假设。",
    "patch": "约 2 分钟。两张图纵轴跨度相同，都是 0.10。补丁 2 叠在补丁 1 上，3a、3b 也叠在补丁 1 上，所以线上没有画补丁 2。"
             "MIMIC-IV-ED 补丁 1 涨幅大，MC-MED 小。3a 两库都涨，五个模型同一量级。3b 在 MC-MED 上只有 LightGBM、mTAND 过判据。"
             "补丁 2 在预先登记的低密度格子上组内差也只有 −0.009 到 +0.005，我们据此推断低密度子集差是因为窗口内信息少，这一点没有单独检验。3b 已定为默认输入集（D138）。",
    "confirm": "约 1.5 分钟。这是本周唯一一次确认性评价。左表：MIMIC-IV-ED 五个模型都提升，各 seed 区间下限最小 +0.011；MC-MED 都无明确差别，点估计和发现集接近。"
               "右表：44 对缺陷复现 29 对，全在 MIMIC-IV-ED。MC-MED 那 10 对方向相同，幅度大多不到发现集一半。"
               "vitalsign ≤1 次在发现集上补丁后不再变差，确认集上没有复现：差距缩小到 −0.010 到 −0.036，五个模型仍被标出。",
    "ablation": "约 1.5 分钟。左图是训练集内 5 折交叉拟合的成分消融，3b 去掉一块后下降多少。≤1 × ESI 1–2 的增益主要来自化验和主诉，大于生命体征本身。"
                "共病、用药、既往就诊、疼痛评分、既往 30 天化验去掉后几乎不变。右图是 LightGBM 的子集差距。≤1 × ESI 3–5 差距变大，是补集涨得更多，组内 AUROC 仍在升。"
                "≥75 岁基本不动。五个模型的范围在周报和补丁 3 报告里。Raindrop 放宽训练上限后结论不变（D140）。",
    "zs": "约 2 分钟。蓝点是不截断的 S-max，空心菱形是截断的 R-max。MC-MED 上 R-max 约 0.50，这是读出公式的性质：预测基本平直，几乎不越阈，复算与梁睿颖总表的差在 3.6e-15 以内。"
          "S-max 八个模型都在 Context-max 左边，配对差区间上限都小于 0。绿色带是五个监督模型，说明窗口里有信息。S-max 是看过截断结果后才定的，标探索性。"
          "模型名次不解读，各模型都接近 LOCF。4 h 上下文改变了人群，只作敏感性（D145）。† MIRA 预训练语料可能与 MIMIC-IV-ED 重叠。‡ Time-MoE 用官方归一化。",
    "zs_sub": "约 1.5 分钟。这张表是零样本评价队列，监督参照是补丁前的版本，所以 ≥75 岁只有 2 个监督模型过判据；下一页用的是 3b 输入，五个都过。"
              "旧版方向性筛查里的 18–44 岁、高密度测量，复核后只作描述。Time-MoE 换口径是看过 v1 结果后定的，换了以后 AUROC 下降。",
    "hard": "约 2 分钟。本页是 3b 输入、发现集全部就诊。MIMIC-IV-ED 上 ≥75 岁五个模型差 −0.037 到 −0.044，都达到判据，交叉拟合中仍在。"
            "≥75 岁的 AUPRC 与 <75 岁相当，患病率是两倍多，所以差距出在排序上。≤1 × ESI 1–2 数据里只能看到记录少，为什么记录少没有核实。",
    "j1": "约 1.5 分钟。J 线问的是：不用本院标签，决策模型零样本在两院流感住院上能做到什么程度。虚线是 0.5。事件少，区间都很宽，这张图主要看区间。"
          "GAM 基本没有 P/F，所以两院的生理类不是同一个结局。",
    "j2": "约 1.5 分钟。右图里 Z1 从 decomp_60 到收住院下降，监督模型上升，差中差区间不含 0，Z2 没有这个现象。监督模型用了标签，零样本没有，所以这里只看差距在哪个结局上更大。"
          "J5 门急诊没有运行，等门急诊数据和 O3 分量的决定。",
    "flucase": "约 1 分钟。研究者试用时发现只显示一个单元格，医生没法判断，所以加了相关记录。分派改成本中心医生自领。11-05 发现两个复核员没绑中心，每个中心只有 1 人能领，绑定后各 2 人，也补了命令。",
    "next": "约 1.5 分钟。零样本读出公式不再调整。下一步在训练集上拟合线性探针，所以不再是严格零样本，先验预期是持平。方案 11-07 锁定，冒烟通过，八个模型的嵌入已经抽完，探针拟合还没运行。",
    "decide": "约 2–5 分钟。前五条想请老师给意见。第 1 条要注意适用范围：零样本、固定阈值读出、不超过 4 h 的窗口。第 3 条涉及转重定义和主要指标，要和临床负责人一起定。后三条是 J 线留下的。",
    "closing": "附录 A1 是八个模型的记录，A2 是本周决策。",
    "a1": "八个模型的原论文都没有 Age、Gender、ESI 这类患者子集分析。服务器上的 TimesFM 权重 README 写的是 3.0（PyTorch）。",
    "a2": "原文在服务器决策记录 docs/basemodel/plan/week02/研究者决策记录_20261005.md 和各方案 §1。",
}


# ---------------------------------------------------------------------------
# 版式工具
# ---------------------------------------------------------------------------
def page(slide, title, lead=None, source=None, notes=None):
    add_rect(slide, 0, 0.24, 10.30, 0.58, fill=MID, name="标题栏")
    add_text(slide, 0.5, 0.24, 9.6, 0.58, title, size=22, color=WHITE, bold=True, anchor="m", margins=(0, 0, 0, 0), name="标题")
    if lead:
        add_text(slide, CL, 0.93, CW, 0.5, lead, size=16, color=NAVY, anchor="m", margins=(0, 0, 0, 0), name="本页要点")
    if source:
        add_text(slide, CL, 6.70, CW, 0.32, source, size=10, color=MUTED, anchor="m", margins=(0, 0, 0, 0), name="口径与出处")
    add_text(slide, CL, 7.06, 9.0, 0.28, DECK, size=10.5, color=MUTED, anchor="m", margins=(0, 0, 0, 0), name="页脚")
    add_slide_number(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes


def picture(slide, name, x, y, w, alt):
    pic = slide.shapes.add_picture(str(FIG / f"{name}.png"), Inches(x), Inches(y), width=Inches(w))
    pic.name = name
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic


def tline(slide, x, y, col_w, row_h, rows, size=12.5, head_size=None, margins=(0.07, 0.02, 0.07, 0.02)):
    """三线表：表头上下各一条线，表尾一条线，没有底色。"""
    nr, nc = len(rows), len(col_w)
    gf = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(sum(col_w)), Inches(sum(row_h)))
    t = gf.table
    t.first_row = t.horz_banding = t.vert_banding = False
    for i, v in enumerate(col_w):
        t.columns[i].width = Inches(v)
    for i, v in enumerate(row_h):
        t.rows[i].height = Inches(v)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            spec = val if isinstance(val, dict) else {"text": val}
            cell = t.cell(r, c)
            cell.fill.background()
            if r == 0:
                set_cell_border(cell, RULE, 1.25, "T")
                ln_b = cell._tc.get_or_add_tcPr()
                set_header_bottom(ln_b)
            elif r == nr - 1:
                set_cell_border(cell, RULE, 1.25, "B")
            else:
                set_cell_border(cell, None)
            cell.margin_left, cell.margin_top, cell.margin_right, cell.margin_bottom = [Inches(m) for m in margins]
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.text_frame.word_wrap = True
            fill_text(cell.text_frame, spec.get("text", ""), size=spec.get("size", (head_size or size) if r == 0 else size),
                      color=spec.get("color", NAVY if r == 0 else BODY), bold=spec.get("bold", r == 0),
                      align=spec.get("align", "l"), line_spacing=1.03)
    return t


def set_header_bottom(tcPr):
    """表头下线：在 set_cell_border 写好的四条边里，把下边改成 0.75 pt。"""
    from lxml import etree
    from pptx.oxml.ns import qn
    ln = tcPr.find(qn("a:lnB"))
    for ch in list(ln):
        ln.remove(ch)
    ln.set("w", str(int(0.75 * 12700)))
    sf = etree.SubElement(ln, qn("a:solidFill"))
    etree.SubElement(sf, qn("a:srgbClr"), val=RULE)


def block(slide, x, y, w, h, heading, text, size=13):
    paras = [{"runs": [(heading, {"bold": True, "color": NAVY})], "space_after": 3}]
    paras += [{"runs": t, "space_after": 4} for t in ([text] if isinstance(text, str) else text)]
    add_text(slide, x, y, w, h, paras, size=size, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.1)


def lines(slide, x, y, w, h, items, size=13, gap=5):
    add_text(slide, x, y, w, h, bullets(items, gap=gap, color=MUTED), size=size, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.08)


ctr = lambda t: {"text": t, "align": "c"}
name = lambda t: {"text": t}
hc = lambda t: {"text": t, "align": "c"}


# ---------------------------------------------------------------------------
# 各页
# ---------------------------------------------------------------------------
def build_summary(slide):
    page(slide, "本周结论", notes=NOTES["summary"],
         source="未完成：冻结嵌入 + 线性探针（③）的探针拟合未运行，正式结果未出；FF-LSTM、GRU-D 等梁睿颖。")
    items = [
        ("两库都没有只影响时序模型的子集：稳定变差的子集，LightGBM 和三个时序模型一起差。", "第 4–6 页"),
        ("加输入后两库总体 AUROC 都提高，训练时随机删观测没有稳定差别。补丁 1 在 MIMIC-IV-ED 确认集上成立，在 MC-MED 上未得到确认。", "第 7–9 页"),
        ("八个基础模型零样本的预测误差与 LOCF 接近，风险分低于 Context-max。这部分按负结果报告（D144）。", "第 10–11 页"),
        ("≥75 岁和早期体征稀疏的高危就诊，监督模型同样更差，按数据侧难点报告（D144）。", "第 12 页"),
        ("J 线 Z1 在两院 7 个分层上只有 2 个的区间不含 0.5，概率需要本地校准，字段缺口要在前瞻表单定稿前解决。", "第 13–14 页"),
        ("flucase 改为本中心医生自领复核，每条至少两位医生，11-04 部署。", "第 15 页"),
    ]
    y, h = 1.12, 0.91
    for i, (text, pg) in enumerate(items):
        add_text(slide, CL, y, 0.5, h, str(i + 1), size=20, color=MID, bold=True, anchor="m", margins=(0, 0, 0, 0))
        add_text(slide, CL + 0.5, y, 10.3, h, text, size=15, color=BODY, anchor="m", margins=(0, 0, 0, 0), line_spacing=1.12)
        add_text(slide, CL + 10.9, y, 1.33, h, pg, size=12, color=MUTED, align="r", anchor="m", margins=(0, 0, 0, 0))
        y += h


def build_week(slide):
    page(slide, "本周进度", lead="11-02 组会定的五步都有结果，只有 FF-LSTM、GRU-D 两个模型未做。", notes=NOTES["week"],
         source="原周计划里的多医院后训练（M0/M1b/M2）本周没有做。决策编号对应服务器决策记录，摘要见附录 A2。")
    rows = [
        ["日期", "完成的工作", "决策"],
        [name("11-02 周一"), "组会定本周五步，写周计划", "无"],
        [name("11-03 周二"), "MIMIC-IV-ED 计数核查与建库（387,249 次就诊，事件 5.35%）；12 个模型的数据调研，备用急诊数据检索；两库五个模型的子集发现", "D103–D109"],
        [name("11-04 周三"), "补丁 1、2 发现集评价；放行补丁 1 后评价确认集一次；J0 读出核对；flucase 部署自领复核", "D110–D112"],
        [name("11-05 周四"), "补丁 3 跑完 84 个 run；J1–J6b 完成，真实数据只评价一次；flucase 补复核员绑中心", "D113、D120–D129"],
        [name("11-06 周五"), "八个基础模型零样本 v1（MIMIC-IV-ED 验证集，每个模型 114,268 条序列）；33 篇弱子集文献调研", "D130–D137"],
        [name("11-07 周六"), "连续分数 r2、4 h 上下文 v2；补丁 3 评价与后续四项分析；导师讨论稿定稿；③ 方案锁定", "D138–D148"],
    ]
    tline(slide, CL, TOP, [1.4, 8.83, 2.0], [0.4, 0.5, 0.82, 0.82, 0.82, 0.82, 0.82], rows, size=13, head_size=13)


def build_survey(slide):
    page(slide, "调研：模型的数据与子集报告情况", lead="急诊窗口只有 8–16 格，八个模型的上下文多在数千点以上，原论文也基本没有按患者分组报告。", notes=NOTES["survey"],
         source="来源：research/数据集资源/ts-datasets-survey-20261103、ed-datasets-20261103、tsfm-survey-20261105；导师讨论稿第一部分 §3–§4。LightGTS 约数百点，未画。")
    picture(slide, "fig_context", CL, TOP, 6.75, "八个基础模型与本项目三个窗口的上下文长度，对数坐标")
    x, w = CL + 7.0, CW - 7.0
    block(slide, x, TOP + 0.05, w, 1.75, "模型原文（12 个模型、2 个急诊基准）",
          "不规则时序模型的标准测试集多是 ICU 前 48 h，每例几十到几百个时点。按年龄、病情或观测密度报告分组性能的很少，只有 Raindrop 做了年龄、性别跨组实验。")
    block(slide, x, TOP + 1.83, w, 1.4, "弱子集文献（33 篇）",
          "报告较多的方向是种族与保险、年龄、测量过程和时间。MC-MED 上只找到 MC-BEC 一份分组结果，指标是单阈值 TPR。")
    block(slide, x, TOP + 3.3, w, 1.75, "备用急诊数据",
          "带时间戳体征的公开急诊原始库只核实到 MIMIC-IV-ED 和 MC-MED。衍生库与 MIMIC-IV-ED 同源，不能做外部验证。这轮以英文检索为主，中文资源还要再查。")


def build_design(slide):
    page(slide, "任务与评价设计", lead="两库各跑五个模型，子集在看结果前登记。两库任务不同，结果不能直接比较。", notes=NOTES["design"],
         source="决策 D103–D111。MIMIC-IV-ED 不是 MC-MED 的外部验证。")
    rows = [
        ["", "MC-MED", "MIMIC-IV-ED"],
        [name("任务"), "decomp_60：60 分钟内新出现 HR>110、MAP<65 或 SpO₂<90", "D103：到院 2 h 预测，此后 12 h 内进 ICU 或院内死亡"],
        [name("输入窗口"), "到床后 15 min，1 分钟网格", "[到院, 2 h)，分诊值放第 0 分钟，加 vitalsign"],
        [name("体征"), "HR、RR、SpO₂、SBP、DBP、MAP", "HR、RR、SpO₂、SBP、DBP、体温"],
        [name("观测密度"), "三分位切点 15、31 个值", "vitalsign 时点中位 1 个"],
        [name("发现集"), "8,085 次，999 个阳性（12.4%）", "38,242 次，2,072 个阳性（5.4%）"],
        [name("确认集"), "2,602 次，312 个阳性", "39,231 次，2,092 个阳性"],
    ]
    tline(slide, CL, TOP, [1.1, 3.25, 3.25], [0.42, 0.92, 0.78, 0.78, 0.6, 0.6, 0.6], rows, size=13, head_size=13)
    x, w = CL + 7.95, CW - 7.95
    add_text(slide, x, TOP + 0.05, w, 4.9, [
        {"runs": [("评价流程", {"bold": True, "color": NAVY})], "space_after": 6},
        {"runs": "1. 看结果前登记子集：年龄、性别、ESI、到达方式、主诊断、观测密度及其与 ESI 的交叉（D104）", "space_after": 7},
        {"runs": "2. 发现集上找子集、比补丁。LR 跑 1 次，其余四个模型各 5 个 seed，每个 run 做 Platt 再校准（D106）", "space_after": 7},
        {"runs": "3. 过半数 seed 的 95% 区间上限 <0 才算稳定变差，患者聚类 bootstrap 1,000 次", "space_after": 7},
        {"runs": "4. 只放行补丁 1，确认集评价一次（D109）", "space_after": 7},
        {"runs": "5. 之后确认集不再使用，只在发现集探索（D111）"},
    ], size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.1)


def build_forest(slide):
    page(slide, "子集结果：MIMIC-IV-ED 发现集", lead="五个模型稳定变差的子集基本重合，没有只影响时序模型的子集。", notes=NOTES["forest"],
         source="38,242 次就诊，2,072 个阳性。行标签后为 n/阳性。点为各 seed 均值，横线为各 seed 95% 区间端点的均值。")
    picture(slide, "fig_forest", CL, 1.42, CW, "MIMIC-IV-ED 发现集五个模型的子集森林图，补丁前与 3b")
    add_text(slide, CL, 6.1, CW, 0.58, "最差的是 ≤1 × ESI 1–2（橙底）：补丁前 −0.19 到 −0.23，3b 后约 −0.10。MC-MED 上稳定变差的只有 ≤15 个值及其与 ESI 的交叉格，3b 后不再被标出。",
             size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.1)


def build_patch(slide):
    page(slide, "补丁 1–3 的总体效果", lead="加输入后两库总体 AUROC 都提高，训练时删观测没有稳定差别。", notes=NOTES["patch"],
         source="发现集，LR 1 次，其余为 5 个 seed 均值。补丁 2、3a、3b 都叠在补丁 1 上，图中未画补丁 2。低密度子集差可能是窗口内信息少，没有单独检验。")
    picture(slide, "fig_patches", CL, 1.42, CW, "两库五个模型总体 AUROC 随补丁变化")
    rows = [
        ["步骤", "加了什么", hc("MC-MED 增益"), hc("MIMIC-IV-ED 增益")],
        [name("补丁 1（D108）"), "ESI、年龄作静态输入", ctr("+0.004 到 +0.009，部分 seed"), ctr("+0.025 到 +0.047，全部 seed")],
        [name("补丁 2（D110）"), "训练时随机删观测", ctr("−0.002 到 +0.003，无稳定差别"), ctr("−0.002 到 +0.003，无稳定差别")],
        [name("3a（D113）"), "到院时已有的信息：到达方式、主诉、既往诊断、用药、分诊体征", ctr("+0.013 到 +0.032"), ctr("+0.018 到 +0.027，全部 seed")],
        [name("3b（D113）"), "再加 t0 前已出结果的化验等；定为默认输入集（D138）", ctr("0.000 到 +0.012，2 个模型过判据"), ctr("+0.005 到 +0.009，全部 seed")],
    ]
    tline(slide, CL, 4.47, [1.55, 5.1, 2.79, 2.79], [0.36, 0.42, 0.42, 0.42, 0.42], rows, size=12, head_size=12)


def build_confirm(slide):
    page(slide, "确认集评价（D109）", lead="MIMIC-IV-ED 上补丁 1 五个模型都判为提升，44 对缺陷复现 29 对；MC-MED 上都没有确认。", notes=NOTES["confirm"],
         source="放行补丁 1 后评价一次，判据为过半数 seed 的 95% 区间不跨 0，不做多重比较校正。结果见 ed_ts_bench_确认集结果_D109_20261104.md。")
    rows_b = [
        ["补丁 1 减补丁前", hc("MC-MED"), hc("MIMIC-IV-ED")],
        [name("LR"), ctr("−0.001"), ctr("+0.042")],
        [name("LightGBM"), ctr("+0.000"), ctr("+0.025")],
        [name("BRITS"), ctr("+0.002"), ctr("+0.023")],
        [name("mTAND"), ctr("+0.009"), ctr("+0.029")],
        [name("Raindrop"), ctr("+0.006"), ctr("+0.028")],
    ]
    tline(slide, CL, TOP, [1.65, 1.05, 1.3], [0.38] + [0.72] * 5, rows_b, size=13, head_size=12)
    rows_a = [
        ["发现的缺陷", hc("确认集 n（阳性）"), hc("子集减补集：发现集 → 确认集"), hc("结果")],
        [name("≥80 岁"), ctr("4,735（471）"), ctr("−0.032…−0.041 → −0.049…−0.061"), ctr("复现 5 对")],
        [name("急救车/直升机送达"), ctr("14,947（1,342）"), ctr("−0.029…−0.035 → −0.028…−0.035"), ctr("复现 4 对")],
        [name("vitalsign ≤1 次"), ctr("30,169（613）"), ctr("−0.042…−0.072 → −0.071…−0.100"), ctr("复现 5 对")],
        [name("≤1 × ESI 1–2"), ctr("9,463（442）"), ctr("−0.188…−0.227 → −0.198…−0.220"), ctr("复现 5 对")],
        [name("≤1 × ESI 3–5"), ctr("20,641（153）"), ctr("−0.060…−0.086 → −0.098…−0.156"), ctr("复现 5 对")],
        [name(">1 × ESI 3–5"), ctr("2,887（87）"), ctr("−0.061…−0.088 → −0.047…−0.062"), ctr("复现 5 对")],
        [name("非呼吸系统主诊断"), ctr("37,082（1,865）"), ctr("−0.035…−0.049 → −0.003…−0.017"), ctr("未复现 5 对")],
        [name("MC-MED ≤15 个值"), ctr("853（106）"), ctr("−0.069…−0.084 → −0.009…−0.030"), ctr("未复现 4 对")],
        [name("MC-MED ≤15 × ESI 3–5"), ctr("696（70）"), ctr("−0.062…−0.095 → −0.024…−0.055"), ctr("未复现 4 对")],
        [name("MC-MED ≤15 × ESI 1–2"), ctr("155（36）"), ctr("−0.073、−0.080 → +0.000、−0.014"), ctr("未复现 2 对")],
    ]
    tline(slide, CL + 4.25, TOP, [2.28, 1.45, 3.05, 1.2], [0.38] + [0.36] * 10, rows_a, size=11.5, head_size=11.5,
          margins=(0.05, 0.01, 0.05, 0.01))
    add_text(slide, CL, 5.65, CW, 0.95, "MC-MED 确认集只有 312 个阳性，把握有限。未复现的 10 对方向相同，幅度大多不到发现集一半，不能据此排除这些缺陷。确认集已用掉，之后的补丁只在发现集比较，结论标探索性（D111）。",
             size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.12)


def build_ablation(slide):
    page(slide, "输入成分消融与子集差距", lead="≤1 × ESI 1–2 的增益主要来自化验和主诉，≥75 岁的差距加输入后基本不变。", notes=NOTES["ablation"],
         source="(a) 训练集内 5 折交叉拟合（D139），其余五块去掉后总体各 ≤+0.001。(b) 发现集，只画 LightGBM。≥75 岁的补丁 1 为两组组内 AUROC 之差。")
    picture(slide, "fig_ablation", CL, 1.42, CW, "成分消融与子集差距变化")
    lines(slide, CL, 5.24, CW, 1.4, [
        "补丁 3 的增益在交叉拟合中复现：3a 减补丁 1 为 +0.019 到 +0.026，3b 减 3a 为 +0.009 到 +0.015，区间都在 0 以上。",
        "五个模型上 ≤1 × ESI 1–2 的差距从 −0.178…−0.218 缩到 −0.093…−0.103，仍都判差；≥75 岁从 −0.042…−0.051 到 −0.037…−0.044。",
        "MC-MED 低密度格主要靠分诊体征；3b 的增益来自灌注指数与 HRV，化验覆盖率最高 16.6%，没有帮助。",
    ], size=12.5, gap=4)


def build_zs(slide):
    page(slide, "八个基础模型零样本：总体", lead="不截断的风险分仍低于 Context-max，预测误差与 LOCF 接近。这部分按负结果报告（D144）。", notes=NOTES["zs"],
         source="† MIRA 预训练语料可能与 MIMIC-IV-ED 重叠。‡ 官方归一化。S-max 是看过截断结果后才定的，标探索性。竖线与色带为 LOCF、Context-max 的 S-max 及 95% 区间。")
    picture(slide, "fig_zs", CL, 1.42, CW, "八个基础模型的 S-max 与 R-max，对比 LOCF、Context-max 和监督模型")
    lines(slide, CL, 5.2, CW, 1.45, [
        "HR 总体 MAE，模型最低对 LOCF：MC-MED 4.68 对 4.69；MIMIC-IV-ED 2 h 10.94 对 10.76，4 h 9.94 对 9.70。",
        "截断的 R-max 在 MC-MED 上约 0.50。预测基本平直，几乎不越阈，除 TimesFM 外 99.8%–100% 的就诊风险分为 0。",
        "4 h 上下文下预测不再那么平直（HR 贴着最后一个值的序列从 72%–83% 降到 38%–43%），误差和风险分都没有变好。",
        "结论只针对零样本加固定阈值读出。五个监督模型 0.705–0.754、0.845–0.879，说明窗口里有信息。",
    ], size=12.5, gap=3)


def build_zs_sub(slide):
    page(slide, "八个基础模型零样本：子集", lead="没有只在零样本模型上变差的子集。≤1 × ESI 1–2 所有模型都判为差。", notes=NOTES["zs_sub"],
         source="判据：子集减补集的 95% 区间上限 <0 且 Holm 校正后 p<0.05。MIMIC-IV-ED D103，零样本评价队列 37,806 次；监督参照为补丁前版本。")
    rows = [
        ["D103 风险子集", hc("N / 事件"), hc("零样本 AUROC 差"), hc("判差"), hc("监督 AUROC 差"), hc("判差"), "判断"],
        [name("≤1 × ESI 1–2"), ctr("9,167 / 466"), ctr("−0.056…−0.080"), ctr("全部"), ctr("−0.195…−0.235"), ctr("全部"), "子集本身难，差距最大"],
        [name("vitalsign ≤1 次"), ctr("29,083 / 613"), ctr("−0.009…−0.036"), ctr("部分"), ctr("−0.041…−0.077"), ctr("全部"), "子集本身难"],
        [name("≥75 岁"), ctr("6,810 / 664"), ctr("−0.021…−0.029"), ctr("无"), ctr("−0.027…−0.032"), ctr("2 个"), "监督过判据，零样本同向"],
        [name("急救车/直升机"), ctr("14,102 / 1,348"), ctr("−0.005…−0.023"), ctr("无"), ctr("−0.019…−0.034"), ctr("1 个"), "只有监督模型差"],
        [name("男性"), ctr("17,062 / 1,084"), ctr("−0.004…−0.020"), ctr("无"), ctr("−0.008…−0.014"), ctr("无"), "不差"],
    ]
    tline(slide, CL, TOP, [2.0, 1.7, 1.85, 0.8, 1.85, 0.8, 3.23], [0.42] + [0.47] * 5, rows, size=12.5, head_size=12.5)
    w = (CW - 0.4) / 2
    block(slide, CL, 4.45, w, 2.1, "预测误差的子集差异",
          "<65 岁 HR 误差，模型 +20.1%，LOCF +20.2%，所以这类差异主要反映子集体征本身的波动。模型相对 LOCF 多出来的误差集中在上下文有变化的就诊：vitalsign >1 次组是 LOCF 的 1.13 倍，补集 1.01 倍。")
    block(slide, CL + w + 0.4, 4.45, w, 2.1, "Time-MoE 口径（D134）",
          "主表改用官方归一化，这是看过 v1 结果后定的。冻结路径直接输入原始值，第 1 步 HR 平均高 32–33 次/分。换口径后 AUROC 下降：MC-MED 0.600 → 0.500，D103 0.720 → 0.618。冻结路径只作复现记录。")


def build_hard(slide):
    page(slide, "两类更难的子集", lead="≥75 岁和 ≤1 × ESI 1–2 在监督模型上同样更差，补丁和交叉拟合都没有消除（D144）。", notes=NOTES["hard"],
         source="补丁 3 的 3b 输入，发现集全部就诊，范围取五个监督模型。MC-MED ≥75 岁五个模型方向都为负，只有 mTAND 过判据。")
    rows = [
        ["子集", "数据集", hc("N / 事件（患病率）"), hc("组内 AUROC"), hc("补集 AUROC"), hc("组内 AUPRC"), hc("对照组患病率（AUPRC）")],
        [name("≥75 岁"), "MIMIC-IV-ED", ctr("6,880 / 674（9.8%）"), ctr("0.890–0.904"), ctr("0.929–0.942"), ctr("0.598–0.636"), ctr("<75 岁 4.5%（0.592–0.639）")],
        [name("≥75 岁"), "MC-MED", ctr("1,720 / 234（13.6%）"), ctr("0.701–0.754"), ctr("0.736–0.776"), ctr("0.293–0.354"), ctr("<75 岁 12.0%（0.300–0.383）")],
        [name("≤1 × ESI 1–2"), "MIMIC-IV-ED", ctr("9,309 / 488（5.2%）"), ctr("0.837–0.858"), ctr("0.940–0.951"), ctr("0.372–0.428"), ctr("全体 5.4%（0.592–0.638）")],
    ]
    tline(slide, CL, TOP, [1.5, 1.4, 2.2, 1.45, 1.45, 1.45, 2.78], [0.44, 0.5, 0.5, 0.5], rows, size=13, head_size=12.5)
    w = (CW - 0.7) / 3
    block(slide, CL, 3.68, w, 2.0, "≥75 岁，MIMIC-IV-ED",
          "差距主要来自病例构成。非事件中 58% 收住院（<75 岁 30%），预测风险中位数是 <75 岁的 3–5 倍；剔除标签外的重症非事件后，差距只缩小不到四分之一。")
    block(slide, CL + w + 0.35, 3.68, w, 2.0, "≥75 岁，MC-MED",
          "差距主要来自标签成分。事件中 66% 由 SpO₂ 触发（<75 岁 51%），这类事件对所有模型都最难。")
    block(slide, CL + 2 * (w + 0.35), 3.68, w, 2.0, "≤1 × ESI 1–2，MIMIC-IV-ED",
          "2 h 内最多 1 个生命体征时刻。加化验、主诉后差距从约 −0.2 缩到约 −0.1。改到 4 h 后 52% 的就诊仍只有 ≤1 个时刻，还会丢掉 22.9% 的事件。")
    add_text(slide, CL, 5.78, CW, 0.75, "混合年龄队列的总体 AUROC 会高估模型在老年人上的排序能力，主课题上要同时报分层结果。转重定义不因此修改（D146）。",
             size=14, color=NAVY, margins=(0, 0, 0, 0), line_spacing=1.12)


def build_j1(slide):
    page(slide, "J 线：两院判别", lead="不用本院标签时，Z1 的 7 个分层里只有 GD 生理类和 GD 新开始氧疗的 95% 区间不含 0.5。", notes=NOTES["j1"],
         source="规则集 v0.6，英文状态输入。本地模型离线运行，真实数据只评价一次，7,013 次前向。标签为 n（事件）。全部是探索性估计，不是临床模型验证。")
    picture(slide, "fig_jline", CL, 1.46, 7.45, "7 个分层上 Z1、Z2 的 AUROC 及 95% 区间")
    x, w = CL + 7.75, CW - 7.75
    lines(slide, x, TOP + 0.1, w, 4.9, [
        "事件少，区间很宽，GAM 主口径只有 10 个事件。",
        "生理类减主口径，Z1 在 GD +0.210，在 GAM −0.228。两院的生理类并不是同一个结局：GD 的事件 84% 由 P/F≤300 触发，GAM 93% 由呼吸≥30 触发。",
        "Z1 的排序没有比 Z2 好，校准截距更好，对提示改动也更稳。",
        "Z1 的概率跟着氧疗走。去掉氧疗项后 7 个分层的 AUROC 差都在 ±0.022 内；去掉后模型仍能部分读出用氧状态，这个对照不完整。",
    ], size=14, gap=10)


def build_j2(slide):
    page(slide, "J 线：校准、标签预算与 MC-MED 比较", lead="两院差距的原因还没有查明，概率要在本地校准后才能用。", notes=NOTES["j2"],
         source="左表 Z1 = OpenJev-Flash-9B，Z2 = Qwen3.5-9B 基座；O/E 为观察事件数除以预测事件数。右图为 MC-MED 发现集 8,085 次，竖线为 95% CI。")
    rows = [
        ["问题", "结果"],
        [name("未校准概率"), "Z1 在主口径和 O2 上高估（O/E 0.28–0.42），GD 新开始氧疗上低估（1.82）。同中心只调截距可修正整体偏差，Platt 的斜率会翻负。"],
        [name("标签预算"), "监督模型大多在 25–100 个标签内追上零样本。GD 生理类 100 个标签时 0.77–0.79 对 0.71。"],
        [name("每中心样本量"), "零样本加只调截距约 140–280 例；监督模型约 1,300–3,700 例。"],
        [name("两院差距"), "都只算呼吸≥30 并补齐 GD 后，GD 减 GAM：Z1 +0.229，Z2 +0.261，区间不含 0。判据不同不是主因。"],
        [name("字段缺口"), "GD 几乎没有 SpO2，GAM 没有 FiO2 和 P/F，要在前瞻表单定稿前解决。"],
    ]
    tline(slide, CL, TOP, [1.45, 5.75], [0.4, 1.12, 0.84, 0.72, 0.98, 0.72], rows, size=13, head_size=13)
    x = CL + 7.5
    picture(slide, "fig_slope", x, TOP - 0.04, 4.7, "MC-MED 上 Z1、Z2、LR、LightGBM 在两个结局上的 AUROC")
    add_text(slide, x + 0.05, 5.15, 4.65, 1.45, "Z1 在收住院上相对监督模型更差，差中差 −0.060（对 LR）、−0.041（对 LightGBM），区间不含 0；Z2 为 −0.013、+0.006，区间含 0。",
             size=12.5, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.1)


def build_flucase(slide):
    page(slide, "flucase：复核流程调整", lead="试用后改了分派和证据两处，11-04 部署到京东云，11-05 补了账号绑定。", notes=NOTES["flucase"],
         source="发布 flucase_20261103_111544_c7a654c、flucase_20261105_053754_1551d21。服务器上 304 个测试通过、1 个跳过。只用虚构数据测试。")
    add_text(slide, CL, TOP + 0.05, 4.5, 4.9, [
        {"runs": [("现在的流程", {"bold": True, "color": NAVY})], "space_after": 6},
        {"runs": "1. 研究者按中心建批次，开放给本中心医生", "space_after": 7},
        {"runs": "2. 医生在“待复核”里自领，打开一条占位 30 分钟", "space_after": 7},
        {"runs": "3. 看原文片段和相关记录，可打开整份文书", "space_after": 7},
        {"runs": "4. 选是、否或不确定，写一句理由，问到时间的填首次时间", "space_after": 7},
        {"runs": "5. 每条至少两位医生，全部一致才生效，不一致去共识"},
    ], size=14, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.12)
    rows = [
        ["", "改之前", "改之后"],
        [name("分派"), "研究者指定复核员，轮流分派", "本中心医生自领，看得到已判人数，看不到是谁、判了什么；原方式保留"],
        [name("证据"), "只显示一个单元格", "加就诊时间范围、原表同时间其他列、前后的吸氧和 SpO2 记录、病历提及处；不给系统的判断"],
        [name("账号"), "两个复核员没绑中心，GD、GAM 各 1 人能领", "绑定后各 2 人；补 set-site 命令，check 按中心列出能领的账号"],
    ]
    tline(slide, CL + 4.8, TOP, [0.8, 2.6, 4.03], [0.42, 1.1, 1.3, 1.1], rows, size=13, head_size=13)
    add_text(slide, CL, 5.7, CW, 0.9, "医生复核说明还有两处待定：医生记得的情况和病历不一致时怎么判，每人大致做多少。阿里云旧 flucase 11-07 起可以清理，删除前要确认。",
             size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.12)


def build_next(slide):
    page(slide, "下一步：冻结嵌入 + 线性探针（③）", lead="检验基础模型的表示里有没有上下文摘要之外的风险信息，零样本读出公式不再调整。", notes=NOTES["next"],
         source="方案 plans/时序基础模型/TSFM八模型冻结嵌入线性探针_方案_20261107.md（D143、D148）。八个模型的嵌入已抽取，探针拟合未运行，正式结果未出。")
    w = 7.1
    block(slide, CL, TOP + 0.03, w, 1.55, "设计",
          "MIMIC-IV-ED D103，2 h 上下文（HR、MAP、SpO₂）。八个模型冻结编码器取末层表示，每个变量在训练集上 PCA 到 32 维。主比较：同一分类头下，摘要 + 嵌入对摘要；L2 逻辑回归为主，LightGBM 为次。")
    block(slide, CL, TOP + 1.68, w, 1.55, "先验预期是持平",
          "10 月 F2 在 MIMIC-IV ICU 24 h 视图上比较 12 个基础模型，最好时与手工摘要 + LightGBM 持平。约 73% 的上下文是常数，所以实际检验的是非常数短序列的形状。")
    block(slide, CL, TOP + 3.33, w, 1.5, "判读规则（看结果前写定）",
          "八个模型都持平，这条线在急诊短窗口上收尾；有增益只作探索，要在 MC-MED 上复现。测试集不读。")
    rows = [
        ["下周要接上的事", "现状"],
        [name("③ 拟合与判读"), "嵌入已抽取；结果出来后写入讨论稿"],
        [name("FF-LSTM、GRU-D"), "等梁睿颖，消息待发"],
        [name("前瞻表单四项"), "SpO2 与吸氧状态、FiO2、血气时点、呼吸测量频率"],
        [name("J5 门急诊"), "代码已好，等门急诊数据和 O3 分量"],
        [name("GAM FiO2"), "回原始数据核实能否补"],
        [name("flucase"), "建复核批次，开放给医生"],
    ]
    tline(slide, CL + 7.45, TOP, [1.75, 3.03], [0.42, 0.62, 0.62, 0.96, 0.8, 0.62, 0.62], rows, size=12.5, head_size=12.5)


def build_decide(slide):
    page(slide, "需要讨论的问题", notes=NOTES["decide"], source="1–5 想请导师给意见，6–8 是 J 线留下的待定项。转重定义、主要指标、口径和模型路线属 A 档。")
    n = lambda t: {"text": t, "align": "c", "color": MUTED}
    q = lambda t: {"text": t}
    rows = [
        [hc("#"), "问题", "背景", hc("谁定")],
        [n("1"), q("负结果能否作为阶段结论"), "拟写：急诊短窗口上，零样本预测轨迹不比上下文本身多带来风险信息。范围是否再收窄", ctr("导师")],
        [n("2"), q("③ 之后的走向"), "若持平，这条线是否收尾，精力转到监督模型和医院数据", ctr("导师")],
        [n("3"), q("≥75 岁怎样接主课题"), "是否要分层 AUROC、校准，并单独描述对照组构成", ctr("导师、临床")],
        [n("4"), q("两库任务口径是否统一"), "越阈型恶化对进 ICU 或死亡；写成一篇是否要有共同任务", ctr("导师")],
        [n("5"), q("Time-MoE 口径是否统一"), "MC-MED 原始总表是冻结路径，本文主表用官方归一化", ctr("导师")],
        [n("6"), q("O2_NEW 还是 o2_hypox"), "J 线两个中心方向相反、区间都含 0，没有给出一致证据", ctr("研究者")],
        [n("7"), q("J5 的 O3 分量"), "建议两个分量各报一遍，等门急诊数据", ctr("研究者")],
        [n("8"), q("前瞻表单四项字段"), "SpO2 与吸氧状态、FiO2、血气时点、呼吸测量频率，定稿前解决", ctr("研究者、临床")],
    ]
    tline(slide, CL, 1.05, [0.45, 2.85, 7.43, 1.5], [0.42] + [0.6] * 8, rows, size=13, head_size=13)


def build_closing(slide):
    band = add_rect(slide, 0, 2.55, SW, 1.6, fill="4472C4", name="致谢横带")
    shape_text(band, "谢谢！欢迎讨论与指正", 40, WHITE)
    add_text(slide, 1.0, 4.45, SW - 2.0, 0.5, "附录 A1：八个基础模型　A2：本周决策 D103–D148", size=16, color=NAVY, align="c", anchor="m")
    slide.notes_slide.notes_text_frame.text = NOTES["closing"]


def build_a1(slide):
    page(slide, "附录 A1：八个基础模型", lead="原论文都没有做患者子集分析；这些模型都不是为急诊短窗口生命体征设计的。", notes=NOTES["a1"],
         source="来源：导师讨论稿第一部分 §3 与附录 A。")
    rows = [
        ["模型", "预训练或主要数据", "上下文", "医疗数据", "不规则、缺失支持"],
        [name("MIRA"), "MIMIC-III/IV、WAVES、PTB-XL、Sleep-EDF", "≤512，点级 token", "是，以医疗数据为主", "原生连续时间戳"],
        [name("Time-MoE"), "Time-300B，约 90.5% 自然、气象", "≤4096", "极少，仅公共卫生汇总", "规则网格；缺失处切分"],
        [name("Sundial"), "TimeBench，ERA5 占比高，含少量 ECG", "2880，patch 16", "少量 ECG", "规则网格；缺失支持有限"],
        [name("TimesFM 3.0"), "GiftEvalPretrain + Wiki + Trends + 合成", "最长约 15,360", "未明确报告", "规则网格为主"],
        [name("Timer-XL"), "UTSD + LOTSA，含少量 EEG/ECG/PPG/HR", "2880，patch 96", "部分", "未明确"],
        [name("LightGTS"), "33 个跨域数据集，含 EEG/ECG 等", "约数百点，周期 token", "部分", "依赖规则周期"],
        [name("VisionTS"), "仅 ImageNet 视觉预训练", "典型 1728–4032", "否", "规则序列、周期折图"],
        [name("Chronos-2"), "Chronos/GIFT 子集 + 大量合成数据", "2048→8192", "未明确报告", "有 missing mask，无时间间隔建模"],
    ]
    tline(slide, CL, TOP, [1.5, 4.4, 2.03, 1.9, 2.4], [0.42] + [0.56] * 8, rows, size=12.5, head_size=13)


def build_a2(slide):
    page(slide, "附录 A2：本周决策 D103–D148", notes=NOTES["a2"], source="原文在服务器决策记录和各方案 §1。")
    rows = [
        ["编号", "主题", "定了什么"],
        [name("D103–D107"), "子集诊断口径", "MIMIC-IV-ED 到院 2 h 预测 12 h 进 ICU 或死亡；登记子集；发现与确认分开；Platt 再校准；模型与变量"],
        [name("D108–D113"), "补丁与确认集", "补丁 1 加 ESI、年龄；补丁 2 删观测；确认集只评一次（D109），之后只在发现集探索（D111）；补丁 3 加输入"],
        [name("D120–D129"), "J 线", "读出形式；v0.6 三个口径；用 std_v3_20261030_4；Z3 保留；physiologic 跨院口径；J2b、J6、J6b 各运行一次"],
        [name("D130–D133"), "八模型零样本 v1", "主分析用 D103 标签；15 分钟网格；只用验证集；可读 MC-MED 逐例预测做同一脚本复算"],
        [name("D134–D136"), "r2 与 v2", "Time-MoE 主表用官方归一化；连续分数继续；另立 4 h 上下文版本"],
        [name("D137–D142"), "补丁 3 之后", "≥75 岁列为登记格子；3b 作默认输入集；交叉拟合；Raindrop 敏感性；≥75 岁诊断；4 h 可行性计数"],
        [name("D143–D147"), "汇报口径", "③ 另立新版本；两类子集写成数据侧难点，零样本规则读出写成负结果；主分析维持 2 h；3b 与转重定义不变"],
        [name("D148"), "③ 的设计", "先只做 MIMIC-IV-ED D103；八个模型；主比较摘要 + 嵌入对摘要；LR 为主、LightGBM 为次"],
    ]
    tline(slide, CL, 1.05, [1.5, 2.1, 8.63], [0.42] + [0.62] * 8, rows, size=12.5, head_size=13)


def fix_cover(cover):
    for shp in cover.shapes:
        if not shp.has_text_frame:
            continue
        text = shp.text_frame.text.strip()
        if text.startswith("老年流感"):
            base.set_shape_text(shp, "老年流感转重研究：本周工作总结")
        elif text.startswith("理想数据"):
            base.set_shape_text(shp, "急诊子集诊断、基础模型零样本、J 线、flucase")
        elif text.startswith("2026"):
            base.set_shape_text(shp, "2026年11月7日")
    cover.notes_slide.notes_text_frame.text = NOTES["cover"]


def main():
    prs = Presentation(str(base.SRC))
    fix_cover(prs.slides[0])
    base.delete_slides_after_first(prs)
    blank = prs.slide_layouts.get_by_name("Blank")
    for build in (build_summary, build_week, build_survey, build_design, build_forest, build_patch, build_confirm, build_ablation,
                  build_zs, build_zs_sub, build_hard, build_j1, build_j2, build_flucase, build_next, build_decide, build_closing,
                  build_a1, build_a2):
        build(prs.slides.add_slide(blank))
    prs.core_properties.title = DECK
    prs.core_properties.subject = "11-02 至 11-07：急诊子集诊断、八个基础模型零样本、J 线、flucase 复核与下一步"
    prs.save(str(OUT))
    print(f"已生成：{OUT}（共 {len(prs.slides)} 页）")


if __name__ == "__main__":
    main()
