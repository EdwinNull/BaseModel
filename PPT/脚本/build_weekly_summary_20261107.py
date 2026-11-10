# -*- coding: utf-8 -*-
"""
生成《老年流感转重研究 · 本周工作总结》（2026-11-07，本周指 11-02 周一至 11-07 周六）。

输入：PPT/模板/hospital_优化版.pptx（模板，只读，不会被修改）
      result/急诊监督模型/ed_ts_bench_本周周报_图/forest_mimic_ed.png（子集森林图，只含聚合量）
输出：PPT/成品/周报与进展/本周工作总结_20261107.pptx

样式与工具函数直接复用 PPT/脚本/build_weekly_summary_20261023.py（标题栏 + 章节标签 + 青色分隔线 + 关键信息条 +
浅黄结论框 + 页脚页码）。图表都是可在 PowerPoint 里编辑的原生图表。

数字都是聚合量，来源（都在本仓库 docs/ 或 plans/ 下）：
- result/急诊监督模型/ed_ts_bench_本周周报_20261102-1108.md、ed_ts_bench_确认集结果_D109_20261104.md：两库任务、补丁 1、2、确认集；
- result/急诊监督模型/ed_ts_bench_补丁3_发现集结果_20261107.md、ed_ts_bench_补丁3后续_局限处理_结果_20261107.md：补丁 3、D139–D142；
- docs/汇报/导师讨论/TSFM八模型子集_导师讨论稿_终版_20261107.md、导师汇报_讨论准备_20261107.md：八模型总体、子集、数据侧难点、请导师给意见；
- result/时序基础模型/TSFM八模型零样本_*_结果_*.md：v1、r2、v2；
- result/零样本决策读出/J线_最终报告_20261105.md、J2至J4、J2b、J6、J6b 结果：J 线；
- research/数据集资源/ts-datasets-survey-20261103、research/数据集资源/ed-datasets-20261103、research/时序基础模型与子集/tsfm-survey-20261105：调研；
- flucase/README.md（11-03、11-05 各行）、docs/flucase/使用教程/医生复核说明_草稿_20261103.md：复核；
- plans/时序基础模型/TSFM八模型冻结嵌入线性探针_方案_20261107.md：③ 的设计。③ 的运行状态是 11-07 中午在服务器上看的，正式结果未出。
措辞按讨论准备 §7。没有读任何真实病例。

运行（BaseModel 根目录）：python PPT/脚本/build_weekly_summary_20261107.py
依赖：python-pptx、lxml（本机 Anaconda 环境有）
"""

import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_weekly_summary_20261023 as base  # noqa: E402  10-23 周总结：样式、封面、删页
from build_weekly_summary_20261023 import (  # noqa: E402
    AMBER, BODY, BORDER, CL, CW, CYAN, DARK, FONT, GREY, LIGHT, MID, MUTED, NAVY, NOTE_BG, PALE, RED, SW, WHITE,
    add_line, add_oval, add_rect, add_table, add_text, bullets, card, chart_fonts, frame, hide_value_axis, rgb,
    shape_text, stat_tile)

OUT = HERE.parent / "成品" / "周报与进展" / "本周工作总结_20261107.pptx"
FOREST = HERE.parents[1] / "result" / "急诊监督模型" / "ed_ts_bench_本周周报_图" / "forest_mimic_ed.png"

base.DECK_TITLE = "老年流感转重研究 · 本周工作总结"

C_LR, C_LGB, C_BRITS, C_MTAND, C_RD = GREY, DARK, CYAN, AMBER, RED
MODEL_COLORS = [C_LR, C_LGB, C_BRITS, C_MTAND, C_RD]
TOP, BOTTOM = 1.76, 6.32   # 内容区上下边界（关键信息条之下、结论框之上）


# ---------------------------------------------------------------------------
# 演讲者备注（每页标建议时长，合计约 25 分钟）
# ---------------------------------------------------------------------------
NOTES = {
    "cover": "封面。本周指 11-02 周一至 11-07 周六。四条线：急诊子集诊断（ed_ts_bench）、八个时序基础模型零样本、决策模型零样本"
             "（J 线）、flucase 复核。所有数字都是聚合量；公开数据只在服务器上用本地模型运行；全部结论除确认集那一步外都标探索性。"
             "全程约 25 分钟，主线在第 2 页。",
    "summary": "约 1 分钟。先给结论。11-02 组会定了五步：调研、跑模型、划子集、打补丁、备选数据集，都已有结果。最重要的一句："
               "差的子集是数据侧难点，不是某个模型的缺陷（D144）。下面五行对应后面的页。还没出结果的是冻结嵌入 + 线性探针（③），"
               "不要当成已做。",
    "week": "约 1.5 分钟。时间线按天讲。11-03 下午 D103–D107 锁定后，MIMIC-IV-ED 建库，当天两库子集发现。11-04 补丁 1、补丁 2，"
            "研究者放行补丁 1 后确认集评价一次。11-05 补丁 3 跑完 84 个 run，J 线 J1–J6b 完成。11-06 按梁睿颖的 MC-MED 设置在 "
            "MIMIC-IV-ED 上做八模型零样本。11-07 连续分数 r2、4 h 上下文 v2、补丁 3 后续四项（D139–D142），定稿导师讨论稿，③ 方案"
            "锁定。原周计划里的 M0/M1b/M2 多医院后训练按 11-02 组会结论暂缓。",
    "survey": "约 1.5 分钟。左图是八个模型的典型或最大上下文，对数坐标；橙色是我们的三个窗口：MIMIC-IV-ED 2 h 8 格、4 h 16 格，"
              "MC-MED 15 格，差两到三个数量级。LightGTS 约数百点，没有精确数字，所以没画。TimesFM 3.0 最长约 15,360。"
              "右边三块：模型原文主要是 ICU 前 48 小时或长序列（来源 S101–S116）；分组性能几乎没人报，只有 Raindrop 按年龄、性别跨组；"
              "33 篇弱子集文献集中在种族与保险、年龄、测量过程、时间；公开急诊原始库只核实到这两个（S121–S128），衍生库与 "
              "MIMIC-IV-ED 同源，不能当外部验证。国内、韩国、台湾、欧洲本轮没找到公开的急诊时序数据，英文检索覆盖有限。",
    "design": "约 1.5 分钟。左表是两库任务，两个任务不同，不能直接比较。MIMIC-IV-ED 没有床旁连续监护，所以定到院 2 h 预测，"
              "此后 12 h 内进 ICU 或院内死亡（D103）。右边是流程：先登记子集（D104），发现集上找子集、比补丁，确认集只用一次。"
              "D105：MC-MED 的发现集是验证集 + 测试集 A 半，确认集是 B 半；MIMIC-IV-ED 验证集发现、测试集确认。每个 run 用自己验证集"
              "的 Platt 再校准（D106）。判据：过半数 seed 的 95% 区间上限 <0，区间是患者聚类 bootstrap 1,000 次。D111 之后不再用确认集。",
    "forest": "约 1.5 分钟。读法：每行一个登记子集，横轴是子集减补集的 AUROC，小于 0 表示这个子集排序更差。蓝色补丁前，橙色补丁 1。"
              "实心是过半数 seed 稳定变差。五个小图的实心点位置几乎一样，所以短板是所有模型共有的。框出来的 ≤1 × ESI 1–2 是最差的格子，"
              "约 −0.19 到 −0.23。MC-MED 的图没放：实心点只在观测 ≤15 个值及其两个交叉格。"
              "“子集减补集”是相对量，按强预测因子切出来的子集组内 AUROC 会机械性变低，所以原因都是假设。",
    "patch": "约 2 分钟。两张图纵轴跨度相同，都是 0.10。补丁 2 叠在补丁 1 上，3a、3b 也叠在补丁 1 上，所以线上没画补丁 2。"
             "MIMIC-IV-ED 上补丁 1 涨幅大，MC-MED 上小；3a 两库都涨，五个模型同一量级，mTAND 起点最低涨得最多；3b 在 MIMIC-IV-ED "
             "上五个模型都再涨，MC-MED 上只有 LightGBM、mTAND 过判据。补丁 2 与补丁 1 的差 −0.002 到 +0.003，预先登记的低密度格子"
             "组内差 −0.009 到 +0.005，所以推断低密度子集差是因为窗口里信息少。这是推断，不是检验结论。3b 已定为默认输入集（D138）。",
    "confirm": "约 1.5 分钟。这是本周唯一一次确认性评价。左边确认 B：补丁 1 减补丁前，MIMIC-IV-ED 五个模型都提升，各 seed 区间下限最小 "
               "+0.011；MC-MED 五个模型都无明确差别，点估计与发现集接近，但 312 个阳性区分不出这么小的差别。右边确认 A：44 对缺陷复现 "
               "29 对，全在 MIMIC-IV-ED。MC-MED 那 10 对方向相同，幅度大多不到发现集一半；未复现不等于不存在。"
               "“≤1 次”在发现集上补丁后不再变差，这一点在确认集上没有复现：差距缩小到 −0.010 到 −0.036，五个模型仍标出。"
               "确认集已用掉，多重比较未校正。",
    "ablation": "约 1.5 分钟。左图是 D139 成分消融：3b 去掉一块后下降多少，LightGBM、MIMIC-IV-ED、训练集内 5 折交叉拟合。"
                "灰色是总体，红色是 ≤1 × ESI 1–2。稀疏格的增益主要来自化验和主诉，大于生命体征本身。共病、用药、既往就诊、疼痛评分、"
                "既往 30 天化验去掉后几乎不变。右表是子集差距的变化。≤1 × ESI 3–5 差距反而扩大，是补集涨得更多，组内 AUROC 仍是升的。"
                "MC-MED 上低密度格靠分诊体征补；3b 的增益来自灌注指数与 HRV，化验覆盖率最高 16.6%，没有帮助。"
                "Raindrop 放宽到 60 轮、静态分支 32 维（D140）结论不变。",
    "zs": "约 2 分钟。按表从上到下读。R-max 把阈值距离截断在 0：MC-MED 上退化到 0.50，除 TimesFM 外 99.8%–100% 的就诊风险分为 0，"
          "这是读出公式的性质，不是代码错误，复算与梁睿颖总表最大差 3.6e-15。换成不截断的 S-max 后不再退化，但八个模型都低于 "
          "Context-max，配对差区间上限都 <0。LOCF 的 R-max 为 0.500 / 0.602，Context-max 为 0.500 / 0.659。监督模型远高，说明窗口里"
          "有信息，只是固定公式读不出来。S-max 是看过截断结果后才定的，结论标探索性。名次不解读：各模型都接近 LOCF。"
          "4 h 上下文：HR 贴着最后一个值的比例从 72%–83% 降到 38%–43%，但 MAE 和风险分都没有变好；4 h 改变了人群，只作敏感性（D145）。",
    "zs_sub": "约 1.5 分钟。正式判据是 95% 区间上限 <0 且 Holm 后 p<0.05。≤1 × ESI 1–2 是所有模型都差；≥75 岁监督模型过判据，零样本同向"
              "但没过；急救车、直升机送达只有监督模型差；男性不差。旧版方向性筛查里的 18–44 岁、高密度测量复核后只作描述。"
              "右上：预测误差的差异 LOCF 也有，所以反映的是子集体征本身的波动。右下：Time-MoE 冻结路径直接输入原始值，换成官方归一化后"
              "AUROC 反而下降，所以不是挑有利结果，但这是看过 v1 结果后定的（D134），要如实说。"
              "本表是零样本评价队列，监督参照是补丁前版本，所以 ≥75 岁只有 2 个监督模型过判据；下一页是补丁 3 的 3b 输入。",
    "hard": "约 2 分钟。本页来自补丁 3 的 3b 输入、发现集全部就诊。≥75 岁：MIMIC-IV-ED 五个模型差 −0.037 到 −0.044，都达到判据；"
            "MC-MED −0.022 到 −0.044，只有 mTAND 达到；交叉拟合中仍在。MIMIC-IV-ED 上 ≥75 岁 AUPRC 与 <75 岁相当，但患病率是两倍多，"
            "差在排序。原因分两库。≤1 × ESI 1–2：数据里只能看到记录少，原因没有核实，不要推测成结论。"
            "对主课题：报告整体 AUROC 时要同时给分层结果，年龄子集同时报 AUROC、AUPRC 和患病率。转重定义不改（D146）。",
    "j1": "约 1.5 分钟。J 线回答：不用本院标签，决策模型零样本在两院流感住院上能做到什么程度。Z1 是 OpenJev-Flash-9B，Z2 是 Qwen3.5-9B "
          "基座。横轴从 0.5 随机水平起。7 个分层里只有两个的区间不含 0.5。两院方向相反，但生理类在两院不是同一个结局：GAM 基本没有 "
          "P/F。Z1 的概率主要跟着是否已吸氧或有呼吸支持走，但拿掉氧疗项后判别基本不变，去掉后模型仍能部分读出用氧状态，所以对照不完整。"
          "事件少，GAM 主口径只有 10 个事件，全部是探索性估计，不是临床模型验证。",
    "j2": "约 1.5 分钟。四个数。第一，O/E 0.28–0.42：未校准的概率明显高估；同中心只调截距能修正整体偏差；Platt 在这个样本量上斜率会翻负。"
          "第二，监督模型大多在 25–100 个标签内追上零样本，GD 生理类 100 个标签时 0.77–0.79 对 0.71。第三，所需样本量。第四，两院差距："
          "判据不同不是主因，真正原因还没解释。右图 MC-MED：Z1 在收住院上相对监督模型更吃亏，Z2 没有这个现象，所以论文的方向只在 Z1 重现。"
          "这不是公平的模型优劣比较：监督模型用了标签。J5 门急诊没有运行，等门急诊数据和 O3 分量的决定。",
    "flucase": "约 1 分钟。研究者试用后的两处修改。一是分派：改成本中心医生自领，每条至少两位，全部一致才生效，不一致去共识。二是证据："
               "原来只显示一个单元格，医生判断不了，现在按问题类型带相关记录，只给原始记录，不给系统的判断。11-05 发现两个复核员没绑中心，"
               "GD、GAM 各只有 1 人能领；绑定后各 2 人，并补了 set-site 命令。测试是服务器上 304 个通过、1 个跳过。这一页没有用任何真实病例内容。",
    "next": "约 1.5 分钟。不再调零样本读出公式。③ 要回答：基础模型的表示里有没有上下文摘要之外的风险信息。这一步不再是严格零样本。"
            "先验预期是持平：10 月 F2 在 MIMIC-IV ICU 24 h 逐小时视图上比较 12 个基础模型，最好时与手工摘要 + LightGBM 持平；约 73% 的上下文"
            "是常数，实例标准化后这部分嵌入不带数值高低的信息，所以实际检验的是非常数短序列的形状。方案 11-07 锁定，冒烟通过，11-07 "
            "中午嵌入抽取还在跑，正式结果未出，不要预测结果。右边是下周要接上的事。",
    "decide": "约 2–5 分钟。前五条是想请导师给意见的问题，后三条是 J 线留下的、要和临床一起定的事。第 1 条注意适用范围：零样本、固定阈值读出、"
              "≤4 h 窗口。第 3 条涉及转重定义和主要指标，属 A 档，要导师和临床负责人一起定。",
    "closing": "结束页。附录 A1 是八个模型的上下文、预训练数据和缺失支持；A2 是本周决策 D103–D148 的分组摘要。",
    "a1": "附录。八个模型都没有在原论文里做 Age、Gender、ESI 这类患者子集分析。MIRA 的预训练语料可能与 MIMIC-IV-ED 重叠，结果表里单独标注；"
          "即便重叠，它也没有明显更好。服务器上的 TimesFM 权重 README 写的是 3.0（PyTorch）。",
    "a2": "附录。按主题归组，原文在服务器决策记录 docs/basemodel/plan/week02/研究者决策记录_20261005.md 和各方案 §1。",
}


# ---------------------------------------------------------------------------
# 图表工具
# ---------------------------------------------------------------------------
def new_chart(slide, kind, x, y, w, h, cats, series, name=None, descr=None):
    cd = CategoryChartData()
    cd.categories = cats
    for n, vals in series:
        cd.add_series(n, vals)
    gf = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    if name:
        gf.name = name
    if descr:
        gf._element.nvGraphicFramePr.cNvPr.set("descr", descr)
    ch = gf.chart
    ch.has_title = False
    ch.has_legend = False
    ch.font.size = Pt(11)
    ch.font.name = FONT
    ch.font.color.rgb = rgb(BODY)
    return ch


def quiet_cat_axis(ch, size=11.5, reverse=False):
    ca = ch.category_axis
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    ca.format.line.color.rgb = rgb(BORDER)
    ca.tick_labels.font.size = Pt(size)
    ca.tick_labels.font.color.rgb = rgb(BODY)
    ca.has_major_gridlines = False
    if reverse:
        ca.reverse_order = True
    return ca


def fixed_value_axis(ch, lo, hi, unit, fmt="0.00", show=True):
    va = ch.value_axis
    va.minimum_scale, va.maximum_scale = lo, hi
    va.major_unit = unit
    if not show:
        hide_value_axis(va)
        return va
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("E3EAF3")
    va.major_gridlines.format.line.width = Pt(0.75)
    va.major_tick_mark = XL_TICK_MARK.NONE
    va.format.line.fill.background()
    va.tick_labels.number_format = fmt
    va.tick_labels.number_format_is_linked = False
    va.tick_labels.font.size = Pt(10.5)
    va.tick_labels.font.color.rgb = rgb(MUTED)
    return va


def fill_series(s, color):
    s.format.fill.solid()
    s.format.fill.fore_color.rgb = rgb(color)
    s.format.line.fill.background()
    s.invert_if_negative = False


def label_series(s, fmt, size=10.5, color=NAVY, pos=XL_LABEL_POSITION.OUTSIDE_END):
    dl = s.data_labels
    dl.show_value = True
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = pos
    dl.font.size = Pt(size)
    dl.font.bold = True
    dl.font.color.rgb = rgb(color)


def legend(ch, pos=XL_LEGEND_POSITION.TOP, size=10.5):
    ch.has_legend = True
    ch.legend.position = pos
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(size)
    ch.legend.font.color.rgb = rgb(MUTED)


def log_value_axis(ch, base_n=10):
    scaling = ch.value_axis._element.find(qn("c:scaling"))
    lb = etree.Element(qn("c:logBase"))
    lb.set("val", str(base_n))
    scaling.insert(0, lb)


def widen_label(dl, w, h=0.09):
    """给单个数据标注指定宽高（PowerPoint 自己缩放标注时写的 c15 扩展），否则窄图里范围文字会折成两行。"""
    c15 = "http://schemas.microsoft.com/office/drawing/2012/chart"
    ext_lst = etree.SubElement(dl._dLbl, qn("c:extLst"))
    ext = etree.SubElement(ext_lst, qn("c:ext"), uri="{CE6537A1-D6FC-4f65-9D91-7224C49458BB}", nsmap={"c15": c15})
    layout = etree.SubElement(ext, "{%s}layout" % c15)
    ml = etree.SubElement(layout, qn("c:manualLayout"))
    etree.SubElement(ml, qn("c:w"), val=str(w))
    etree.SubElement(ml, qn("c:h"), val=str(h))


def range_chart(slide, x, y, w, h, rows, show_cats=True, name=None, descr=None):
    """悬空条：rows = [(类别, 下界, 上界, 颜色, 标注)]。下界系列透明；第三个透明系列只用来把标注放到条的右边。"""
    cats = [r[0] for r in rows]
    start = [r[1] for r in rows]
    span = [max(r[2] - r[1], 0.006) for r in rows]
    carrier = [0.22] * len(rows)
    ch = new_chart(slide, XL_CHART_TYPE.BAR_STACKED, x, y, w, h, cats,
                   [("下界", start), ("范围", span), ("标注", carrier)], name=name, descr=descr)
    plot = ch.plots[0]
    plot.gap_width = 55
    plot.overlap = 100
    s0, s1, s2 = plot.series
    for s in (s0, s2):
        s.format.fill.background()
        s.format.line.fill.background()
    s1.invert_if_negative = False
    for i, r in enumerate(rows):
        pt = s1.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = rgb(r[3])
        pt.format.line.fill.background()
        dl = s2.points[i].data_label
        tf = dl.text_frame
        tf.text = r[4]
        tf.word_wrap = False
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT
        run = tf.paragraphs[0].runs[0]
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = rgb(NAVY)
        dl.position = XL_LABEL_POSITION.INSIDE_BASE
        widen_label(dl, round((0.09 * len(r[4]) + 0.14) / w, 3))
    fixed_value_axis(ch, 0.45, 1.12, 0.1, show=False)
    ca = quiet_cat_axis(ch, size=11.5, reverse=True)
    if not show_cats:
        ca.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    chart_fonts(ch)
    return ch


def panel(slide, x, y, w, h, title=None, size=13.5):
    add_rect(slide, x, y, w, h, fill=WHITE, line=BORDER, shadow=True)
    if title:
        add_text(slide, x + 0.16, y + 0.06, w - 0.3, 0.34, title, size=size, color=NAVY, bold=True, anchor="m",
                 margins=(0, 0, 0, 0))


def flow(slide, x, y, w, h, steps, fills, size=12.5, sub_size=10.5):
    """首段五边形、其余燕尾的流程条。steps = [(主文字, 小字)]。"""
    n, overlap = len(steps), 0.14
    sw = (w + overlap * (n - 1)) / n
    for i, (head, sub) in enumerate(steps):
        shp = MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON
        s = add_rect(slide, x + i * (sw - overlap), y, sw, h, fill=fills[i], shape=shp)
        s.adjustments[0] = 0.22
        paras = [{"runs": [(head, {"bold": True, "size": size})]}]
        if sub:
            paras.append({"runs": [(sub, {"size": sub_size})]})
        left = 0.14 if i == 0 else 0.3
        shape_text(s, paras, size, WHITE, margins=(left, 0.02, 0.2, 0.02))


# ---------------------------------------------------------------------------
# 各页
# ---------------------------------------------------------------------------
def build_summary(slide):
    frame(slide, "要点", "五个问题与一句话回答",
          "本周按 11-02 组会的五步走完：差的子集是数据侧难点，不是某个模型的缺陷。",
          ask_lead="还没有结果：", ask="冻结嵌入 + 线性探针（③）方案已锁定，嵌入抽取进行中；FF-LSTM、GRU-D 等梁睿颖。",
          notes=NOTES["summary"])
    items = [
        ("01", "子集上哪里差？", "两库都没有“只有时序模型差”的子集；稳定变差的格子，LightGBM 和时序模型一起差。", "第 4–6 页"),
        ("02", "补丁有没有用？", "加输入有用，两库五个模型都提高；训练时删观测没有作用；补丁 1 只在 MIMIC-IV-ED 上得到确认。", "第 7–9 页"),
        ("03", "基础模型零样本行不行？", "八个模型的预测与 LOCF 持平，风险分不超过 Context-max，定为负结果（D144）。", "第 10–12 页"),
        ("04", "医院数据上零样本行不行？", "决策模型只在少数分层上站得住，概率要本地校准；字段缺口比样本量更急。", "第 13–14 页"),
        ("05", "flucase 到哪一步？", "本中心医生自领复核 11-04 上线，每条至少两位医生，GD、GAM 各有 2 个账号能领。", "第 15 页"),
    ]
    h, gap = 0.78, 0.115
    for i, (num, q, a, page) in enumerate(items):
        y = 1.76 + i * (h + gap)
        add_rect(slide, 0.72, y, 11.9, h, fill=WHITE, line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
                 radius=0.12, shadow=True)
        nb = add_rect(slide, 0.92, y + 0.13, 0.66, 0.52, fill=DARK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
        shape_text(nb, num, 18, WHITE, bold=True)
        add_text(slide, 1.76, y + 0.05, 9.2, 0.36, q, size=16, color=NAVY, bold=True, anchor="m")
        add_text(slide, 1.76, y + 0.40, 9.35, 0.32, a, size=13, color=BODY, anchor="m")
        add_line(slide, 11.18, y + 0.17, 11.18, y + h - 0.17, BORDER, 1)
        add_text(slide, 11.22, y, 1.32, h, page, size=12.5, color=MID, bold=True, align="c", anchor="m")


def build_week(slide):
    frame(slide, "本周", "六天四条线：子集诊断、八模型零样本、J 线、flucase",
          "11-02 至 11-07：组会定方向，当周建任务、跑模型、打补丁，再用零样本和医院数据两头验证。",
          ask_lead="组会五步：", ask="① 调研 ② 跑模型 ③ 划子集 ④ 打补丁 ⑤ 备选数据集都有结果；缺 FF-LSTM、GRU-D 两个模型。",
          notes=NOTES["week"])
    ly = 2.43
    add_line(slide, 0.85, ly, 12.45, ly, DARK, 2.5, arrow_end=True)
    days = [
        ("11-02 周一", "组会定五步\n写本周计划"),
        ("11-03 周二", "D103–D107 锁定\n两库子集发现"),
        ("11-04 周三", "补丁 1、2\n确认集评价一次"),
        ("11-05 周四", "补丁 3：84 个 run\nJ2–J4、J6"),
        ("11-06 周五", "八模型零样本 v1\n33 篇弱子集调研"),
        ("11-07 周六", "r2、v2、D139–D142\n③ 方案锁定"),
    ]
    x0, step = 1.5, (11.8 - 1.5) / 5
    for i, (date, label) in enumerate(days):
        mx = x0 + i * step
        add_oval(slide, mx, ly, 0.26, fill=DARK, line=WHITE, line_w=2)
        add_text(slide, mx - 1.0, 1.76, 2.0, 0.46, date, size=13.5, color=NAVY, bold=True, align="c", anchor="b")
        add_text(slide, mx - 1.0, 2.60, 2.0, 0.56, label, size=12, color=MUTED, align="c")
    sx0, sx1 = x0 + 2 * step - 0.92, x0 + 3 * step + 0.92
    trk = add_rect(slide, sx0, 3.24, sx1 - sx0, 0.29, fill=PALE, line=MID, line_w=1,
                   shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    shape_text(trk, "J 线 J0–J6b 完成 · flucase 部署两次", 11, NAVY, bold=True, wrap=False)

    cards = [
        ("① 子集诊断（ed_ts_bench）", ["MIMIC-IV-ED 时序任务建成：387,249 次就诊，事件 5.35%",
                                  "两库 × 五个模型，子集预先登记",
                                  "补丁 1–3；确认集只评价一次"]),
        ("② 八模型零样本（TSFM）", ["MIMIC-IV-ED 验证集：每个模型 114,268 条序列",
                              "复算 MC-MED 总表，AUROC 最大差 1.1e-16",
                              "2 h / 4 h、截断 / 连续分数都看过"]),
        ("③ 决策模型零样本（J 线）", ["两院 7 个分层，真实数据只评价一次",
                                "不含氧疗的对照（J2b）",
                                "MC-MED 比较病情型与运营型结局"]),
        ("④ flucase 复核", ["改为本中心医生自领，每条至少两位",
                          "条目带相关记录，可看整份文书",
                          "11-04、11-05 部署到京东云"]),
    ]
    gap = 0.2
    cw = (CW - 3 * gap) / 4
    for i, (head, lines) in enumerate(cards):
        x = CL + i * (cw + gap)
        card(slide, x, 3.66, cw, 2.64, head, header_h=0.44, header_size=13.5)
        add_text(slide, x + 0.14, 4.20, cw - 0.26, 2.05, bullets(lines, gap=8), size=13, color=BODY,
                 margins=(0, 0, 0, 0))


def build_survey(slide):
    frame(slide, "调研", "模型偏长上下文，原论文基本没做患者子集",
          "八个模型的上下文从几百到上万个点，我们的急诊窗口只有 8–16 格。",
          ask_lead="所以：", ask="把基础模型放到急诊上本身是分布外使用；两库统一做子集审计，是在补文献的空白。",
          notes=NOTES["survey"])
    lw = 6.55
    panel(slide, CL, TOP, lw, BOTTOM - TOP, "典型或最大上下文长度（格 / 点，对数坐标）")
    cats = ["TimesFM 3.0", "Chronos-2", "Time-MoE", "VisionTS", "Sundial", "Timer-XL", "MIRA",
            "MIMIC-IV-ED 4 h（敏感性）", "MC-MED 15 min", "MIMIC-IV-ED 2 h"]
    vals = [15360, 8192, 4096, 4032, 2880, 2880, 512, 16, 15, 8]
    ch = new_chart(slide, XL_CHART_TYPE.BAR_CLUSTERED, CL + 0.1, TOP + 0.38, lw - 0.25, 3.72, cats, [("上下文", vals)],
                   name="上下文长度图", descr="八个基础模型与本项目三个窗口的上下文长度，对数坐标")
    plot = ch.plots[0]
    plot.gap_width = 40
    plot.vary_by_categories = False
    s = plot.series[0]
    fill_series(s, DARK)
    for i in (7, 8, 9):
        pt = s.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = rgb(AMBER)
        pt.format.line.fill.background()
    label_series(s, "#,##0")
    log_value_axis(ch)
    fixed_value_axis(ch, 1, 200000, None, show=False)
    quiet_cat_axis(ch, size=11.5, reverse=True)
    chart_fonts(ch)
    add_text(slide, CL + 0.16, BOTTOM - 0.46, lw - 0.3, 0.42,
             "TimesFM 3.0 为最长约值；VisionTS 取典型 lookback 上限（1728–4032）；LightGTS 约数百点、依赖周期 token，未画。",
             size=10, color=MUTED, margins=(0, 0, 0, 0))

    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    blocks = [
        ("模型原文：12 个模型 + 2 个急诊基准", DARK, 1.58,
         ["不规则时序模型多在 ICU 前 48 h 上调出来，每例几十到几百个时点",
          "按年龄、病情、观测密度报告分组性能的几乎没有，只有 Raindrop 按年龄、性别跨组"]),
        ("文献里的弱子集：33 篇", MID, 1.34,
         ["集中在种族与保险、年龄、测量过程、时间四个方向",
          "MC-MED 上只找到 MC-BEC 一份分组结果（单阈值 TPR）"]),
        ("备用急诊数据（组会第 ⑤ 步）", CYAN, 1.42,
         ["带时间戳体征的公开急诊原始库，只核实到 MIMIC-IV-ED、MC-MED 两个",
          "衍生库与 MIMIC-IV-ED 同源，不能当外部验证"]),
    ]
    y = TOP
    for head, color, h, lines in blocks:
        card(slide, rx, y, rw, h, head, header_h=0.38, header_size=13, header_fill=color)
        add_text(slide, rx + 0.14, y + 0.44, rw - 0.26, h - 0.48, bullets(lines, gap=3), size=12, color=BODY,
                 margins=(0, 0, 0, 0), line_spacing=1.04)
        y += h + 0.12


def build_design(slide):
    frame(slide, "设计", "两库任务与“先发现、再确认”",
          "两个急诊库各跑五个模型；子集预先登记，发现集上找问题，确认集只用一次。",
          ask_lead="注意：", ask="两库任务不同，不能直接比较；MIMIC-IV-ED 也不是 MC-MED 的外部验证。",
          notes=NOTES["design"])
    c = lambda t: {"text": t, "align": "l"}
    head = lambda t: {"text": t, "bold": True, "color": NAVY, "fill": PALE}
    rows = [
        ["", "MC-MED", "MIMIC-IV-ED"],
        [head("任务"), c("decomp_60：60 分钟内新出现 HR>110、MAP<65 或 SpO₂<90"),
         c("D103：到院 2 h 预测，此后 12 h 内进 ICU 或院内死亡")],
        [head("输入窗口"), c("到床后 15 min，1 分钟网格"), c("[到院, 2 h)，分诊值放第 0 分钟 + vitalsign")],
        [head("体征"), c("HR、RR、SpO₂、SBP、DBP、MAP"), c("HR、RR、SpO₂、SBP、DBP、体温")],
        [head("观测密度"), c("三分位切点 15、31 个值"), c("vitalsign 时点中位 1 个")],
        [head("发现集"), c("8,085 次 / 999 阳性（12.4%）"), c("38,242 次 / 2,072 阳性（5.4%）")],
        [head("确认集"), c("2,602 次 / 312 阳性"), c("39,231 次 / 2,092 阳性")],
    ]
    lw = 7.55
    add_table(slide, CL, TOP, [1.15, 3.2, 3.2], [0.42, 0.94, 0.74, 0.74, 0.58, 0.57, 0.57], rows, size=12.5,
              header_size=13, margins=(0.1, 0.03, 0.08, 0.03))
    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    card(slide, rx, TOP, rw, BOTTOM - TOP, "怎么找、怎么验", header_h=0.42, header_size=14)
    steps = [
        ("登记", "看结果前定子集：年龄、性别、ESI、到达方式、主诊断、观测密度及与 ESI 交叉（D104）"),
        ("发现", "LR 跑 1 次，LightGBM、BRITS、mTAND、Raindrop 各 5 个 seed；每个 run 做 Platt 再校准（D106）"),
        ("判据", "过半数 seed 的 95% 区间上限 <0，患者聚类 bootstrap 1,000 次"),
        ("确认", "只放行补丁 1，确认集评价一次（D109）"),
        ("之后", "确认集不再使用，只在发现集探索，结论标探索性（D111）"),
    ]
    y = TOP + 0.52
    hs = [0.8, 1.02, 0.78, 0.56, 0.8]
    for (tag, text), h in zip(steps, hs):
        t = add_rect(slide, rx + 0.14, y + 0.03, 0.62, 0.3, fill=MID, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3)
        shape_text(t, tag, 11.5, WHITE, bold=True, wrap=False)
        add_text(slide, rx + 0.84, y, rw - 0.96, h, text, size=12, color=BODY, margins=(0, 0.02, 0, 0), line_spacing=1.04)
        y += h


def build_forest(slide):
    frame(slide, "子集", "没有“只有时序模型差”的子集",
          "MIMIC-IV-ED 上五个模型的短板几乎重合，LightGBM 和三个时序模型一起差。",
          ask_lead="所以：", ask="“给时序模型结构打补丁”目前没有子集目标；两库共同的短板是观测少的就诊。",
          notes=NOTES["forest"])
    iw = 8.8
    ih = iw * 1260 / 2430
    pic = slide.shapes.add_picture(str(FOREST), Inches(CL), Inches(TOP - 0.02), Inches(iw), Inches(ih))
    pic.name = "MIMIC-IV-ED 子集森林图"
    pic._element.nvPicPr.cNvPr.set("descr", "MIMIC-IV-ED 发现集五个模型的子集森林图，补丁前与补丁 1")
    add_rect(slide, CL, TOP - 0.02, iw, ih, line=BORDER, name="图框")
    add_rect(slide, CL + 0.012 * iw, TOP - 0.02 + 0.733 * ih, 0.976 * iw, 0.042 * ih, line=AMBER, line_w=2,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12, name="标注框")
    rx, rw = CL + iw + 0.2, CW - iw - 0.2
    card(slide, rx, TOP, rw, 1.42, "怎么读", header_h=0.36, header_size=13)
    add_text(slide, rx + 0.12, TOP + 0.41, rw - 0.22, 1.0, bullets([
        "横轴：子集减补集 AUROC，<0 为更差",
        "实心：过半数 seed 稳定变差",
    ], gap=3), size=11.5, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)
    y2 = TOP + 1.54
    card(slide, rx, y2, rw, BOTTOM - y2, "读到什么", header_h=0.36, header_size=13, header_fill=AMBER)
    add_text(slide, rx + 0.12, y2 + 0.42, rw - 0.22, BOTTOM - y2 - 0.46, bullets([
        "最差：≤1 次 × ESI 1–2，约 −0.19 到 −0.23",
        "≥80 岁、急救车 / 直升机送达也变差",
        "MC-MED 只在 ≤15 个值及其交叉格",
    ], gap=3, color=AMBER), size=11.5, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)


def line_panel(slide, x, y, w, h, title, data, lo, hi):
    panel(slide, x, y, w, h, title)
    steps = ["补丁前", "补丁 1", "3a", "3b"]
    ch = new_chart(slide, XL_CHART_TYPE.LINE_MARKERS, x + 0.08, y + 0.36, w - 0.14, h - 0.4, steps, data,
                   name=title, descr=title + "：五个模型总体 AUROC 随补丁变化")
    for s, color in zip(ch.plots[0].series, MODEL_COLORS):
        s.smooth = False
        s.format.line.color.rgb = rgb(color)
        s.format.line.width = Pt(2.25)
        s.marker.style = XL_MARKER_STYLE.CIRCLE
        s.marker.size = 7
        s.marker.format.fill.solid()
        s.marker.format.fill.fore_color.rgb = rgb(color)
        s.marker.format.line.color.rgb = rgb(WHITE)
    fixed_value_axis(ch, lo, hi, 0.02)
    quiet_cat_axis(ch, size=11.5)
    legend(ch, XL_LEGEND_POSITION.RIGHT, 10.5)
    chart_fonts(ch)


def build_patch(slide):
    frame(slide, "补丁", "加信息有用，删观测没用",
          "总体 AUROC 主要靠输入提高：MIMIC-IV-ED 五个模型 3b 都到 0.92 以上，MC-MED 0.73–0.77。",
          ask_lead="怎么理解（推断）：", ask="低密度子集差，更可能是窗口里信息本来就少，不是训练时见到的稀疏样本不够。",
          notes=NOTES["patch"])
    pw = (CW - 0.22) / 2
    h = 2.56
    mc = [("LR", [0.705, 0.709, 0.725, 0.729]), ("LightGBM", [0.734, 0.740, 0.760, 0.772]),
          ("BRITS", [0.730, 0.735, 0.748, 0.747]), ("mTAND", [0.690, 0.700, 0.731, 0.741]),
          ("Raindrop", [0.708, 0.713, 0.731, 0.736])]
    mi = [("LR", [0.846, 0.893, 0.917, 0.924]), ("LightGBM", [0.877, 0.905, 0.928, 0.937]),
          ("BRITS", [0.879, 0.904, 0.923, 0.928]), ("mTAND", [0.862, 0.892, 0.919, 0.928]),
          ("Raindrop", [0.874, 0.903, 0.925, 0.932])]
    line_panel(slide, CL, TOP, pw, h, "MC-MED 发现集，总体 AUROC", mc, 0.68, 0.78)
    line_panel(slide, CL + pw + 0.22, TOP, pw, h, "MIMIC-IV-ED 发现集，总体 AUROC", mi, 0.84, 0.94)
    ctr = lambda t: {"text": t, "align": "c"}
    tag = lambda t: {"text": t, "bold": True, "color": NAVY}
    rows = [
        ["步骤", "加了什么", {"text": "MC-MED 增益", "align": "c"}, {"text": "MIMIC-IV-ED 增益", "align": "c"}],
        [tag("补丁 1（D108）"), "ESI、年龄作静态输入", ctr("+0.004…+0.009，部分 seed"), ctr("+0.025…+0.047，全部 seed")],
        [tag("补丁 2（D110）"), "训练时随机删观测（叠在补丁 1 上，图中未画）", ctr("−0.002…+0.003，无稳定差别"), ctr("−0.002…+0.003，无稳定差别")],
        [tag("3a（D113）"), "到院时就有的信息：到达方式、主诉、既往、用药、分诊体征", ctr("+0.013…+0.032"), ctr("+0.018…+0.027，全部 seed")],
        [tag("3b（D113）"), "再加 t0 前已出结果的化验等；定为默认输入集（D138）", ctr("−0.000…+0.012，2 个模型过判据"), ctr("+0.005…+0.009，全部 seed")],
    ]
    add_table(slide, CL, TOP + h + 0.1, [1.6, 5.03, 2.8, 2.8], [0.34, 0.385, 0.385, 0.385, 0.385], rows, size=11.5,
              header_size=12, margins=(0.08, 0.02, 0.06, 0.02))


def build_confirm(slide):
    frame(slide, "确认集", "补丁 1 和缺陷都只在 MIMIC-IV-ED 上得到确认",
          "D109 评价一次：MIMIC-IV-ED 的提升几乎与发现集相同，MC-MED 312 个阳性区分不出小差别。",
          ask_lead="收口：", ask="确认集已用掉，多重比较未校正；之后的补丁只在发现集探索，结论一律标探索性（D111）。",
          notes=NOTES["confirm"])
    tiles = [("5 / 5", "MIMIC-IV-ED 判为提升（+0.023…+0.042）"),
             ("0 / 5", "MC-MED：五个模型都是“无明确差别”"),
             ("29 / 44", "发现的缺陷复现，全在 MIMIC-IV-ED")]
    tw = (CW - 2 * 0.2) / 3
    for i, (big, label) in enumerate(tiles):
        stat_tile(slide, CL + i * (tw + 0.2), TOP, tw, 0.92, big, label, big_size=21, label_size=11.5)
    y = TOP + 1.04
    ctr = lambda t: {"text": t, "align": "c"}
    name = lambda t: {"text": t, "bold": True, "color": NAVY}
    rows_b = [
        ["补丁 1 减补丁前", {"text": "MC-MED", "align": "c"}, {"text": "MIMIC-IV-ED", "align": "c"}],
        [name("LR"), ctr("−0.001"), ctr("+0.042")],
        [name("LightGBM"), ctr("+0.000"), ctr("+0.025")],
        [name("BRITS"), ctr("+0.002"), ctr("+0.023")],
        [name("mTAND"), ctr("+0.009"), ctr("+0.029")],
        [name("Raindrop"), ctr("+0.006"), ctr("+0.028")],
    ]
    add_table(slide, CL, y, [1.75, 1.1, 1.3], [0.36] + [0.632] * 5, rows_b, size=12.5, header_size=12,
              margins=(0.08, 0.02, 0.06, 0.02))
    yes = lambda t: {"text": t, "align": "c", "bold": True, "color": DARK}
    no = lambda t: {"text": t, "align": "c", "bold": True, "color": MUTED}
    rows_a = [
        ["子集（发现的缺陷）", {"text": "确认集 n（阳性）", "align": "c"}, {"text": "子集减补集：发现集 → 确认集", "align": "c"},
         {"text": "结论", "align": "c"}],
        [name("≥80 岁"), ctr("4,735（471）"), ctr("−0.032…−0.041 → −0.049…−0.061"), yes("复现 5")],
        [name("急救车 / 直升机送达"), ctr("14,947（1,342）"), ctr("−0.029…−0.035 → −0.028…−0.035"), yes("复现 4")],
        [name("vitalsign ≤1 次"), ctr("30,169（613）"), ctr("−0.042…−0.072 → −0.071…−0.100"), yes("复现 5")],
        [name("≤1 × ESI 1–2"), ctr("9,463（442）"), ctr("−0.188…−0.227 → −0.198…−0.220"), yes("复现 5")],
        [name("≤1 × ESI 3–5"), ctr("20,641（153）"), ctr("−0.060…−0.086 → −0.098…−0.156"), yes("复现 5")],
        [name(">1 × ESI 3–5"), ctr("2,887（87）"), ctr("−0.061…−0.088 → −0.047…−0.062"), yes("复现 5")],
        [name("非呼吸系统主诊断"), ctr("37,082（1,865）"), ctr("−0.035…−0.049 → −0.003…−0.017"), no("未复现 5")],
        [name("MC-MED ≤15 个值"), ctr("853（106）"), ctr("−0.069…−0.084 → −0.009…−0.030"), no("未复现 4")],
        [name("MC-MED ≤15 × ESI 3–5"), ctr("696（70）"), ctr("−0.062…−0.095 → −0.024…−0.055"), no("未复现 4")],
        [name("MC-MED ≤15 × ESI 1–2"), ctr("155（36）"), ctr("−0.073、−0.080 → +0.000、−0.014"), no("未复现 2")],
    ]
    add_table(slide, CL + 4.35, y, [2.42, 1.5, 2.96, 1.0], [0.36] + [0.316] * 10, rows_a, size=11, header_size=11.5,
              margins=(0.07, 0.01, 0.05, 0.01))


def build_ablation(slide):
    frame(slide, "输入", "稀疏高危格靠化验和主诉补，≥75 岁差距不随输入缩小",
          "训练集内 5 折交叉拟合复现了补丁 3 的增益：3a +0.019…+0.026，3b 再 +0.009…+0.015，区间都在 0 以上。",
          ask_lead="MC-MED：", ask="低密度格靠分诊体征补；3b 增益来自灌注指数与 HRV，化验覆盖率最高 16.6%，没有帮助。",
          notes=NOTES["ablation"])
    lw = 5.95
    panel(slide, CL, TOP, lw, BOTTOM - TOP, "3b 去掉一块后 AUROC 下降多少（MIMIC-IV-ED，LightGBM）")
    cats = ["窗口生命体征", "t0 前化验", "主诉", "年龄与 ESI", "到达方式"]
    ch = new_chart(slide, XL_CHART_TYPE.BAR_CLUSTERED, CL + 0.08, TOP + 0.38, lw - 0.16, 3.72, cats,
                   [("总体", [0.012, 0.009, 0.006, 0.005, 0.002]), ("≤1 × ESI 1–2", [0.015, 0.028, 0.017, 0.004, 0.008])],
                   name="成分消融图", descr="各输入块对总体与稀疏高危格的独立贡献")
    plot = ch.plots[0]
    plot.gap_width = 55
    plot.overlap = -5
    fill_series(plot.series[0], GREY)
    fill_series(plot.series[1], RED)
    label_series(plot.series[0], "+0.000")
    label_series(plot.series[1], "+0.000")
    fixed_value_axis(ch, 0, 0.034, 0.01, show=False)
    quiet_cat_axis(ch, size=12, reverse=True)
    legend(ch, XL_LEGEND_POSITION.TOP, 11)
    chart_fonts(ch)
    add_text(slide, CL + 0.16, BOTTOM - 0.42, lw - 0.3, 0.38,
             "其余五块（共病、用药、既往就诊、疼痛评分、既往 30 天化验）去掉后，总体各 ≤+0.001，稀疏格各 ≤+0.002。",
             size=10, color=MUTED, margins=(0, 0, 0, 0))

    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    bad = lambda t: {"text": t, "align": "c", "bold": True, "color": RED}
    ok = lambda t: {"text": t, "align": "c", "bold": True, "color": DARK}
    ctr = lambda t: {"text": t, "align": "c"}
    name = lambda t: {"text": t, "bold": True, "color": NAVY}
    rows = [
        ["子集减补集（五个模型）", {"text": "补丁 1", "align": "c"}, {"text": "3b", "align": "c"}, {"text": "3b 后", "align": "c"}],
        [name("≤1 × ESI 1–2"), ctr("−0.178…−0.218"), ctr("−0.093…−0.103"), bad("都判差")],
        [name("急救车 / 直升机送达"), ctr("−0.036…−0.044"), ctr("−0.018…−0.027"), bad("都判差")],
        [name("≥75 岁（MIMIC-IV-ED）"), ctr("−0.042…−0.051"), ctr("−0.037…−0.044"), bad("都判差")],
        [name("≤1 × ESI 3–5"), ctr("−0.027…−0.054"), ctr("−0.058…−0.097"), bad("都判差")],
        [name("≤15 个值（MC-MED）"), ctr("−0.031…−0.069"), ctr("−0.012…−0.035"), ok("不再判差")],
    ]
    add_table(slide, rx, TOP, [2.2, 1.35, 1.35, rw - 4.9], [0.4] + [0.46] * 5, rows, size=11.5, header_size=11.5,
              margins=(0.07, 0.02, 0.05, 0.02))
    y2 = TOP + 2.82
    card(slide, rx, y2, rw, BOTTOM - y2, "读法", header_h=0.36, header_size=13)
    add_text(slide, rx + 0.14, y2 + 0.42, rw - 0.26, BOTTOM - y2 - 0.46, bullets([
        "加信息后两组都提高，≥75 岁差距仍在",
        "≤1 × ESI 3–5 组内 AUROC 仍升，差距变大是补集涨得更多",
        "Raindrop 放宽训练上限后结论不变（D140）",
    ], gap=3), size=12, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)


def build_zs(slide):
    frame(slide, "零样本", "八个基础模型：预测 ≈ LOCF，风险分不超过 Context-max",
          "“先预测、再套阈值”读出的风险，不比直接看上下文里最异常的值好。",
          ask_lead="定性（D144）：", ask="“零样本 + 固定阈值读出”写成负结果；这不等于基础模型的表示没用，下一步另行检验。",
          notes=NOTES["zs"])
    lw = 8.05
    panel(slide, CL, TOP, lw, BOTTOM - TOP, "风险分 AUROC（范围条；两库任务不同，不能直接比较）")
    c0, c1 = 4.45, lw - 4.45 - 0.1
    add_text(slide, CL + 1.9, TOP + 0.4, c0 - 1.9, 0.3, "MC-MED decomp_60", size=12, color=NAVY, bold=True,
             margins=(0, 0, 0, 0))
    add_text(slide, CL + c0 + 0.1, TOP + 0.4, c1, 0.3, "MIMIC-IV-ED D103（2 h）", size=12, color=NAVY, bold=True,
             margins=(0, 0, 0, 0))
    mc = [("八模型 截断 R-max", 0.500, 0.521, GREY, "0.500–0.521"),
          ("LOCF 连续分数", 0.638, 0.638, CYAN, "0.638"),
          ("八模型 连续 S-max", 0.635, 0.669, DARK, "0.635–0.669"),
          ("Context-max 连续分数", 0.691, 0.691, AMBER, "0.691"),
          ("五个监督模型", 0.705, 0.754, RED, "0.705–0.754")]
    mi = [("八模型 截断 R-max", 0.617, 0.638, GREY, "0.617–0.638"),
          ("LOCF 连续分数", 0.687, 0.687, CYAN, "0.687"),
          ("八模型 连续 S-max", 0.716, 0.729, DARK, "0.716–0.729"),
          ("Context-max 连续分数", 0.755, 0.755, AMBER, "0.755"),
          ("五个监督模型", 0.845, 0.879, RED, "0.845–0.879")]
    range_chart(slide, CL + 0.08, TOP + 0.68, c0 - 0.08, 3.3, mc, name="MC-MED 风险分",
                descr="MC-MED 上各读出方式与监督模型的 AUROC 范围")
    range_chart(slide, CL + c0 + 0.02, TOP + 0.68, c1, 3.3, mi, show_cats=False, name="MIMIC-IV-ED 风险分",
                descr="MIMIC-IV-ED 上各读出方式与监督模型的 AUROC 范围")
    add_text(slide, CL + 0.16, BOTTOM - 0.5, lw - 0.3, 0.46,
             "R-max 把阈值距离截断在 0，S-max 不截断；S-max 是看过截断结果后才定的，标探索性。八个模型与 Context-max 的配对差，区间上限都 <0。",
             size=10, color=MUTED, margins=(0, 0, 0, 0))
    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    ctr = lambda t: {"text": t, "align": "c"}
    name = lambda t: {"text": t, "bold": True, "color": NAVY}
    rows = [
        ["HR 总体 MAE", {"text": "模型最低", "align": "c"}, {"text": "LOCF", "align": "c"}],
        [name("MC-MED"), ctr("4.68"), ctr("4.69")],
        [name("MIMIC-IV-ED 2 h"), ctr("10.94"), ctr("10.76")],
        [name("MIMIC-IV-ED 4 h"), ctr("9.94"), ctr("9.70")],
    ]
    add_table(slide, rx, TOP, [1.85, 1.1, rw - 2.95], [0.38, 0.38, 0.38, 0.38], rows, size=12.5, header_size=12,
              margins=(0.08, 0.02, 0.06, 0.02))
    y2 = TOP + 1.66
    card(slide, rx, y2, rw, BOTTOM - y2, "为什么", header_h=0.38, header_size=13.5)
    add_text(slide, rx + 0.14, y2 + 0.45, rw - 0.26, BOTTOM - y2 - 0.5, bullets([
        "预测基本平直：2 h 时 HR 72%–83% 的序列贴着最后一个值",
        "所以几乎不越阈：MC-MED 上除 TimesFM 外，99.8%–100% 的就诊风险分为 0",
        "4 h 不再那么平直（38%–43%），误差和风险分都没变好",
        "监督模型远高：窗口里有信息，固定公式读不出来",
    ], gap=4), size=12, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)


def build_zs_sub(slide):
    frame(slide, "零样本", "子集上没有“只有零样本模型才差”的格子",
          "最难的格子所有模型都差；预测误差的子集差异，LOCF 也有几乎相同的差值。",
          ask_lead="判据：", ask="子集减补集的 95% 区间上限 <0 且 Holm 校正后 p<0.05；“8/8 同向”只是方向，不算达到判据。",
          notes=NOTES["zs_sub"])
    name = lambda t: {"text": t, "bold": True, "color": NAVY}
    ctr = lambda t: {"text": t, "align": "c"}
    rows = [
        ["D103 风险子集", {"text": "N / 事件", "align": "c"}, {"text": "零样本 AUROC 差", "align": "c"},
         {"text": "判差", "align": "c"}, {"text": "监督 AUROC 差", "align": "c"}, {"text": "判差", "align": "c"},
         {"text": "归类", "align": "l"}],
        [name("≤1 × ESI 1–2"), ctr("9,167 / 466"), ctr("−0.056…−0.080"), ctr("全部"), ctr("−0.195…−0.235"), ctr("全部"),
         {"text": "子集本身难（最差）", "bold": True, "color": RED}],
        [name("vitalsign ≤1 次"), ctr("29,083 / 613"), ctr("−0.009…−0.036"), ctr("部分"), ctr("−0.041…−0.077"), ctr("全部"),
         "子集本身难"],
        [name("≥75 岁"), ctr("6,810 / 664"), ctr("−0.021…−0.029"), ctr("无"), ctr("−0.027…−0.032"), ctr("2 个"),
         "监督过判据，零样本同向"],
        [name("急救车 / 直升机"), ctr("14,102 / 1,348"), ctr("−0.005…−0.023"), ctr("无"), ctr("−0.019…−0.034"), ctr("1 个"),
         "只有监督模型差"],
        [name("男性"), ctr("17,062 / 1,084"), ctr("−0.004…−0.020"), ctr("无"), ctr("−0.008…−0.014"), ctr("无"), "不差"],
    ]
    add_table(slide, CL, TOP, [2.0, 1.7, 1.85, 0.8, 1.85, 0.8, 3.23], [0.42] + [0.48] * 5, rows, size=12,
              header_size=12, margins=(0.07, 0.02, 0.05, 0.02))
    y2 = TOP + 2.96
    h = BOTTOM - y2
    w2 = (CW - 0.22) / 2
    card(slide, CL, y2, w2, h, "LOCF 对照：差异大多不是模型特有", header_h=0.38, header_size=13.5)
    add_text(slide, CL + 0.14, y2 + 0.45, w2 - 0.26, h - 0.5, bullets([
        "HR 预测误差，<65 岁相对补集：模型 +20.1%，LOCF +20.2%",
        "模型多吃亏只在上下文不平直的就诊：vitalsign >1 次组 MAE 是 LOCF 的 1.13 倍，补集 1.01 倍",
    ], gap=4), size=12, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)
    x2 = CL + w2 + 0.22
    card(slide, x2, y2, w2, h, "Time-MoE 口径（D134，看过 v1 结果后定）", header_h=0.38, header_size=13.5, header_fill=AMBER)
    add_text(slide, x2 + 0.14, y2 + 0.45, w2 - 0.26, h - 0.5, bullets([
        "冻结路径直接输入原始值，第 1 步 HR 平均高 32–33 次/分",
        "官方归一化后 AUROC 反而下降：MC-MED 0.600 → 0.500，D103 0.720 → 0.618",
        "冻结路径只作复现记录，不参与排名",
    ], gap=3, color=AMBER), size=12, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)


def build_hard(slide):
    frame(slide, "难点", "≥75 岁与早期体征稀疏的高危就诊，所有模型都更难",
          "补丁、交叉拟合和训练设置敏感性分析都没有消除这两类子集（D144）。",
          ask_lead="对主课题：", ask="混合年龄队列的总体 AUROC 会高估模型在老年人上的排序能力；转重定义不因此修改（D146）。",
          notes=NOTES["hard"])
    name = lambda t: {"text": t, "bold": True, "color": NAVY}
    ctr = lambda t: {"text": t, "align": "c"}
    rows = [
        ["子集", "数据集", {"text": "N / 事件（患病率）", "align": "c"}, {"text": "组内 AUROC", "align": "c"},
         {"text": "补集 AUROC", "align": "c"}, {"text": "组内 AUPRC", "align": "c"}, {"text": "对照组患病率（AUPRC）", "align": "c"}],
        [name("≥75 岁"), "MIMIC-IV-ED", ctr("6,880 / 674（9.8%）"), ctr("0.890–0.904"), ctr("0.929–0.942"), ctr("0.598–0.636"),
         ctr("<75 岁 4.5%（0.592–0.639）")],
        [name("≥75 岁"), "MC-MED", ctr("1,720 / 234（13.6%）"), ctr("0.701–0.754"), ctr("0.736–0.776"), ctr("0.293–0.354"),
         ctr("<75 岁 12.0%（0.300–0.383）")],
        [name("≤1 × ESI 1–2"), "MIMIC-IV-ED", ctr("9,309 / 488（5.2%）"), ctr("0.837–0.858"), ctr("0.940–0.951"), ctr("0.372–0.428"),
         ctr("全体 5.4%（0.592–0.638）")],
    ]
    add_table(slide, CL, TOP, [1.5, 1.4, 2.2, 1.45, 1.45, 1.45, 2.78], [0.42, 0.47, 0.47, 0.47], rows, size=12.5, header_size=12,
              margins=(0.08, 0.02, 0.06, 0.02))
    add_text(slide, CL, TOP + 1.86, CW, 0.26, "补丁 3 的 3b 输入，发现集全部就诊；范围取五个监督模型。", size=10, color=MUTED,
             margins=(0, 0, 0, 0))
    y2, h = TOP + 2.16, BOTTOM - TOP - 2.16
    gap = 0.2
    w3 = (CW - 2 * gap) / 3
    cards = [
        ("≥75 岁 · MIMIC-IV-ED：病例构成", DARK, [
            "≥75 岁非事件 58% 收住院（<75 岁 30%）",
            "预测风险中位数是 <75 岁的 3–5 倍",
            "剔除标签外的重症非事件，差距只缩小不到四分之一"]),
        ("≥75 岁 · MC-MED：标签成分", MID, [
            "≥75 岁事件 66% 由 SpO₂ 触发（<75 岁 51%）",
            "SpO₂ 触发的事件对所有模型都最难",
            "五个模型方向都为负，仅 mTAND 过判据"]),
        ("≤1 × ESI 1–2：记录少", RED, [
            "2 h 内最多 1 个生命体征时刻的高危就诊",
            "化验、主诉把差距从约 −0.2 缩到约 −0.1",
            "4 h 也补不上：52% 仍 ≤1 个时刻，还丢 22.9% 的事件"]),
    ]
    for i, (head, color, lines) in enumerate(cards):
        x = CL + i * (w3 + gap)
        card(slide, x, y2, w3, h, head, header_h=0.4, header_size=13.5, header_fill=color)
        add_text(slide, x + 0.14, y2 + 0.48, w3 - 0.26, h - 0.52, bullets(lines, gap=7, color=color), size=13, color=BODY,
                 margins=(0, 0, 0, 0), line_spacing=1.04)


def build_j1(slide):
    frame(slide, "J 线", "医院数据：零样本判别只在少数分层上站得住",
          "不用本院标签时，Z1 的 7 个分层里只有 2 个的 95% 区间不含 0.5。",
          ask_lead="怎么做的：", ask="规则集 v0.6 导出，本地模型离线运行，真实数据只评价一次，共 7,013 次前向；全部是探索性估计。",
          notes=NOTES["j1"])
    lw = 7.3
    panel(slide, CL, TOP, lw, BOTTOM - TOP, "AUROC，英文状态输入，主分析（横轴从 0.5 随机水平起）")
    cats = ["O1 主口径 · GD 191（23）", "O1 主口径 · GAM 84（10）", "O1 新开始氧疗 · GD 73（27）", "O1 新开始氧疗 · GAM 69（14）",
            "O1 生理类 · GD 271（61）", "O1 生理类 · GAM 115（31）", "O2 主口径 · GD 210（20）"]
    z1 = [0.579, 0.711, 0.664, 0.635, 0.704, 0.558, 0.582]
    z2 = [0.602, 0.693, 0.718, 0.564, 0.766, 0.564, 0.579]
    ch = new_chart(slide, XL_CHART_TYPE.BAR_CLUSTERED, CL + 0.06, TOP + 0.38, lw - 0.12, BOTTOM - TOP - 0.68, cats,
                   [("Z1 OpenJev-Flash-9B", z1), ("Z2 Qwen3.5-9B 基座", z2)], name="J 线判别图",
                   descr="7 个分层上 Z1、Z2 的 AUROC")
    plot = ch.plots[0]
    plot.gap_width = 45
    plot.overlap = -5
    fill_series(plot.series[0], DARK)
    fill_series(plot.series[1], CYAN)
    label_series(plot.series[0], "0.000", size=10)
    label_series(plot.series[1], "0.000", size=10)
    fixed_value_axis(ch, 0.5, 0.82, 0.1, show=False)
    quiet_cat_axis(ch, size=11, reverse=True)
    legend(ch, XL_LEGEND_POSITION.TOP, 10.5)
    chart_fonts(ch)
    add_text(slide, CL + 0.16, BOTTOM - 0.3, lw - 0.3, 0.26, "括号内为 n（事件）。区间很宽：例如 GAM 主口径 Z1 0.711（0.494–0.884）。",
             size=10, color=MUTED, margins=(0, 0, 0, 0))
    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    card(slide, rx, TOP, rw, BOTTOM - TOP, "读到什么", header_h=0.42, header_size=14)
    add_text(slide, rx + 0.15, TOP + 0.54, rw - 0.34, BOTTOM - TOP - 0.6, [
        {"runs": [("站得住的两格：", {"bold": True, "color": NAVY}), ("GD 生理类 0.704（0.634–0.774）、GD 新开始氧疗 0.664（0.528–0.785）", {})],
         "space_after": 9},
        {"runs": [("两院方向相反：", {"bold": True, "color": NAVY}),
                  ("生理类减主口径，Z1 在 GD +0.210，在 GAM −0.228", {})], "space_after": 9},
        {"runs": [("但不是同一个结局：", {"bold": True, "color": NAVY}),
                  ("GD 生理类事件 84% 由 P/F≤300 触发，GAM 93% 由呼吸≥30 触发", {})], "space_after": 9},
        {"runs": [("Z1 没有比 Z2 排序更好：", {"bold": True, "color": NAVY}), ("但校准截距更好，对提示改动也更稳", {})], "space_after": 9},
        {"runs": [("氧疗：", {"bold": True, "color": NAVY}),
                  ("Z1 的概率跟着氧疗走，但判别不来自显式的氧疗项，去掉后 7 个分层差都在 ±0.022 内（J2b）", {})]},
    ], size=12.5, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.05)


def build_j2(slide):
    frame(slide, "J 线", "概率要本地校准，两院差距还没有解释",
          "零样本能省标签，但省不掉校准；监督模型大多在 25–100 个标签内追上。",
          ask_lead="字段缺口比样本量更急：", ask="GD 几乎没有 SpO2，GAM 没有 FiO2 和 P/F；要在前瞻表单定稿前解决。",
          notes=NOTES["j2"])
    lw = 6.55
    tw, th, gap = (lw - 0.2) / 2, (BOTTOM - TOP - 0.2) / 2, 0.2
    tiles = [
        ("0.28–0.42", "校准", "未校准时 Z1 明显高估（O/E，主口径与 O2）。同中心只调截距可修正整体偏差，Platt 斜率会翻负"),
        ("25–100 个", "标签预算", "监督模型大多在这个标签数内追上零样本。GD 生理类 100 个标签：0.77–0.79 对 0.71"),
        ("140–280 例", "每中心样本量", "零样本加只调截距的估计；监督模型约 1,300–3,700 例"),
        ("+0.229", "两院差距", "都只算呼吸≥30 并补齐 GD 后，Z1 的 GD 减 GAM（CI 0.086–0.370）；判据不同不是主因"),
    ]
    for i, (big, tag, text) in enumerate(tiles):
        x = CL + (i % 2) * (tw + gap)
        y = TOP + (i // 2) * (th + gap)
        add_rect(slide, x, y, tw, th, fill=WHITE, line=BORDER, shadow=True)
        add_text(slide, x + 0.16, y + 0.1, tw - 0.3, 0.3, tag, size=12, color=MUTED, bold=True, margins=(0, 0, 0, 0))
        add_text(slide, x + 0.16, y + 0.38, tw - 0.3, 0.56, big, size=24, color=DARK, bold=True, anchor="m", margins=(0, 0, 0, 0))
        add_text(slide, x + 0.16, y + 0.98, tw - 0.38, th - 1.04, text, size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.04)
    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    panel(slide, rx, TOP, rw, BOTTOM - TOP, "MC-MED：零样本对同源特征监督模型（AUROC）")
    ch = new_chart(slide, XL_CHART_TYPE.COLUMN_CLUSTERED, rx + 0.06, TOP + 0.38, rw - 0.12, 3.0, ["decomp_60", "收住院"],
                   [("Z1", [0.691, 0.661]), ("Z2", [0.662, 0.680]), ("LR", [0.702, 0.733]), ("LightGBM", [0.731, 0.742])],
                   name="J6b 比较图", descr="MC-MED 上两个结局的零样本与监督模型 AUROC")
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.overlap = -5
    for s, color in zip(plot.series, [DARK, CYAN, GREY, AMBER]):
        fill_series(s, color)
        label_series(s, "0.000", size=10)
    fixed_value_axis(ch, 0.5, 0.8, 0.1, show=False)
    quiet_cat_axis(ch, size=12)
    legend(ch, XL_LEGEND_POSITION.TOP, 10.5)
    chart_fonts(ch)
    add_text(slide, rx + 0.16, TOP + 3.42, rw - 0.3, 1.12, bullets([
        "纵轴从 0.5 起；8,085 次就诊",
        "Z1 在收住院上更吃亏：差中差 −0.060、−0.041，区间不含 0",
        "Z2 为 −0.013、+0.006，区间都含 0",
    ], gap=2), size=11.5, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.03)


def build_flucase(slide):
    frame(slide, "flucase", "复核改成本中心医生自领，每条至少两位",
          "研究者试用后改了两处：谁来判（自领）、凭什么判（带上相关记录）。11-04 上线。",
          ask_lead="还要定：", ask="医生复核说明里有两处待定（记得的与病历不一致怎么判、每人大致做多少）；阿里云旧 flucase 删除前要确认。",
          notes=NOTES["flucase"])
    steps = [("建批次", "研究者选中心，开放"), ("自领", "本中心医生都看得到"), ("看记录", "原文 + 相关记录"),
             ("判定", "是 / 否 / 不确定 + 理由"), ("定稿", "全部一致生效，否则共识")]
    flow(slide, CL, TOP + 0.02, CW, 0.82, steps, [DARK, MID, CYAN, MID, DARK], size=13.5, sub_size=10.5)
    y2 = TOP + 1.0
    tile_h = 0.92
    h = BOTTOM - y2 - tile_h - 0.14
    gap = 0.2
    w3 = (CW - 2 * gap) / 3
    cards = [
        ("分派：每条至少两位医生", DARK, [
            "A、B 类一样，不少于 2 人",
            "医生看得到“已判 n / 至少 2 位”，看不到是谁、判的什么",
            "别的中心看不到也取不到"]),
        ("证据：只给原始记录", CYAN, [
            "每条带本次就诊的时间范围",
            "吸氧类：原表同时间其他列，前后 24 小时呼吸支持记录，前后 12 小时 SpO2",
            "不给系统的判断；可看整份文书"]),
        ("上线：京东云两次部署", MID, [
            "11-04：自领与相关记录",
            "11-05：复核员绑中心，补 set-site 命令",
            "check 按中心列出能自领的账号"]),
    ]
    for i, (head, color, lines) in enumerate(cards):
        x = CL + i * (w3 + gap)
        card(slide, x, y2, w3, h, head, header_h=0.42, header_size=14, header_fill=color)
        add_text(slide, x + 0.14, y2 + 0.5, w3 - 0.26, h - 0.54, bullets(lines, gap=7, color=color), size=13, color=BODY,
                 margins=(0, 0, 0, 0), line_spacing=1.04)
    tiles = [("≥ 2 位", "每条复核的不同医生数"), ("30 分钟", "打开一条后的占位时间"),
             ("2 个 / 中心", "GD、GAM 各自能领的账号"), ("304 个", "服务器上通过的测试（1 个跳过）")]
    tw = (CW - 3 * gap) / 4
    for i, (big, label) in enumerate(tiles):
        stat_tile(slide, CL + i * (tw + gap), BOTTOM - tile_h, tw, tile_h, big, label, big_size=19, label_size=11.5)


def build_next(slide):
    frame(slide, "下一步", "冻结嵌入 + 线性探针：表示里有没有额外信息",
          "不再调零样本读出公式；③ 方案 11-07 已锁定，嵌入抽取进行中，正式结果未出。",
          ask_lead="判读规则看结果前写定：", ask="八个模型都持平，这条线在急诊短窗口上收尾；有增益只作探索，要在 MC-MED 上复现。",
          notes=NOTES["next"])
    lw = 7.55
    add_text(slide, CL, TOP - 0.02, lw, 0.3, "主比较：同一分类头下，“摘要 + 嵌入”对“摘要”（MIMIC-IV-ED D103，2 h）", size=13, color=NAVY,
             bold=True, margins=(0, 0, 0, 0))
    steps = [("2 h 上下文", "HR、MAP、SpO₂"), ("冻结编码器", "八模型末层表示"), ("PCA 32 维", "只在训练集拟合"),
             ("分类头", "L2 LR 为主")]
    flow(slide, CL, TOP + 0.32, lw, 0.82, steps, [DARK, MID, CYAN, DARK], size=13, sub_size=10.5)
    y2 = TOP + 1.3
    h = BOTTOM - y2
    gap = 0.18
    w2 = (lw - gap) / 2
    card(slide, CL, y2, w2, h, "先验预期是“持平”", header_h=0.4, header_size=14, header_fill=AMBER)
    add_text(slide, CL + 0.14, y2 + 0.5, w2 - 0.26, h - 0.54, bullets([
        "10 月 F2：MIMIC-IV ICU 24 h 视图上 12 个基础模型，最好时与手工摘要 + LightGBM 持平",
        "约 73% 的上下文是常数，实际检验的是非常数短序列的形状",
    ], gap=8, color=AMBER), size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.04)
    x2 = CL + w2 + gap
    card(slide, x2, y2, w2, h, "同时看", header_h=0.4, header_size=14)
    add_text(slide, x2 + 0.14, y2 + 0.5, w2 - 0.26, h - 0.54, bullets([
        "嵌入能否替代摘要",
        "3b 输入之上加嵌入是否还有增益（LightGBM）",
        "≥75 岁、≤1 × ESI 1–2 的差距是否改变",
        "这一步不再是严格零样本；测试集不读",
    ], gap=7), size=13, color=BODY, margins=(0, 0, 0, 0), line_spacing=1.04)
    rx, rw = CL + lw + 0.22, CW - lw - 0.22
    card(slide, rx, TOP, rw, BOTTOM - TOP, "下周要接上的事", header_h=0.42, header_size=14)
    items = [
        ("③ 判读", "结果出来后写入讨论稿"),
        ("两个模型", "FF-LSTM、GRU-D 等梁睿颖，消息待发"),
        ("前瞻表单", "SpO2 与吸氧状态、FiO2、血气时点、呼吸测量频率"),
        ("J5 门急诊", "代码已好，等门急诊数据和 O3 分量"),
        ("GAM", "回原始数据核实能否补 FiO2"),
        ("flucase", "建复核批次，开放给医生"),
    ]
    y = TOP + 0.54
    step = (BOTTOM - y - 0.04) / len(items)
    for i, (tag, text) in enumerate(items):
        add_text(slide, rx + 0.14, y, 1.08, step - 0.06, tag, size=12, color=NAVY, bold=True, anchor="m", margins=(0, 0, 0, 0))
        add_text(slide, rx + 1.24, y, rw - 1.36, step - 0.06, text, size=12, color=BODY, anchor="m", margins=(0, 0, 0, 0),
                 line_spacing=1.03)
        if i < len(items) - 1:
            add_line(slide, rx + 0.14, y + step - 0.03, rx + rw - 0.14, y + step - 0.03, "E3EAF3", 0.75)
        y += step


def build_decide(slide):
    frame(slide, "讨论", "想请导师给意见的问题",
          "前五条关于这条线怎么收、怎么接主课题；后三条是 J 线留下的、要和临床一起定的事。",
          ask_lead="A 档：", ask="转重定义、主要指标、口径与模型路线归研究者和导师定；这里只给证据，不替代决定。",
          notes=NOTES["decide"])
    who = lambda t, c=DARK: {"text": t, "align": "c", "bold": True, "color": c}
    q = lambda t: {"text": t, "bold": True, "color": NAVY}
    n = lambda t: {"text": t, "align": "c", "bold": True, "color": MUTED}
    rows = [
        [{"text": "#", "align": "c"}, "问题", "背景", {"text": "谁定", "align": "c"}],
        [n("1"), q("负结果能否作为阶段结论"), "拟写：急诊短窗口上，零样本预测轨迹不比上下文本身多带来风险信息；范围是否再收窄", who("导师")],
        [n("2"), q("③ 之后的走向"), "若持平，这条线是否收尾，精力转到监督模型和医院数据", who("导师")],
        [n("3"), q("≥75 岁怎样接主课题"), "是否要分层 AUROC、校准，并单独描述对照组构成", who("导师 + 临床", AMBER)],
        [n("4"), q("两库任务口径是否统一"), "越阈型恶化对进 ICU 或死亡；写成一篇是否要有共同任务", who("导师")],
        [n("5"), q("Time-MoE 口径是否统一"), "MC-MED 原始总表是冻结路径，本文主表用官方归一化", who("导师")],
        [n("6"), q("O2_NEW 还是 o2_hypox"), "J 线两个中心方向相反、区间都含 0，没有给出一致证据", who("研究者", MID)],
        [n("7"), q("J5 的 O3 分量"), "建议两个分量各报一遍，等门急诊数据", who("研究者", MID)],
        [n("8"), q("前瞻表单四项字段"), "SpO2 与吸氧状态、FiO2、血气时点、呼吸测量频率，定稿前解决", who("研究者 + 临床", AMBER)],
    ]
    add_table(slide, CL, TOP, [0.45, 2.75, 7.53, 1.5], [0.38] + [0.51] * 8, rows, size=12, header_size=12.5,
              margins=(0.08, 0.02, 0.06, 0.02))


def build_closing(slide):
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
    add_text(slide, 1.0, 4.45, SW - 2.0, 0.5, "附录 A1：八个基础模型一览 · A2：本周决策 D103–D148",
             size=16, color=NAVY, align="c", anchor="m")
    slide.notes_slide.notes_text_frame.text = NOTES["closing"]


def build_a1(slide):
    frame(slide, "附录 A1", "八个基础模型一览",
          "没有一个模型是专门为“急诊、短窗口、生命体征、患者子集”设计的；原论文都没做患者子集分析。",
          notes=NOTES["a1"])
    name = lambda t: {"text": t, "bold": True, "color": NAVY}
    rows = [
        ["模型", "预训练 / 主要数据", "上下文", "医疗数据", "不规则 / 缺失支持"],
        [name("MIRA"), "MIMIC-III/IV、WAVES、PTB-XL、Sleep-EDF", "≤512，点级 token", "是，以医疗数据为主", "原生连续时间戳"],
        [name("Time-MoE"), "Time-300B，约 90.5% 自然 / 气象", "≤4096", "极少，仅公共卫生汇总", "规则网格；缺失处切分"],
        [name("Sundial"), "TimeBench，ERA5 占比高，含少量 ECG", "2880，patch 16", "少量 ECG", "规则网格；缺失支持有限"],
        [name("TimesFM 3.0"), "GiftEvalPretrain + Wiki + Trends + 合成", "最长约 15,360", "未明确报告", "规则网格为主"],
        [name("Timer-XL"), "UTSD + LOTSA，含少量 EEG/ECG/PPG/HR", "2880，patch 96", "部分", "未明确"],
        [name("LightGTS"), "33 个跨域数据集，含 EEG/ECG 等", "约数百点，周期 token", "部分", "依赖规则周期"],
        [name("VisionTS"), "仅 ImageNet 视觉预训练", "典型 1728–4032", "否", "规则序列、周期折图"],
        [name("Chronos-2"), "Chronos/GIFT 子集 + 大量合成数据", "2048→8192", "未明确报告", "有 missing mask，无时间间隔建模"],
    ]
    add_table(slide, CL, TOP, [1.5, 4.5, 2.03, 1.9, 2.3], [0.42] + [0.52] * 8, rows, size=12, header_size=12.5,
              margins=(0.08, 0.02, 0.06, 0.02))


def build_a2(slide):
    frame(slide, "附录 A2", "本周决策 D103–D148",
          "按主题归组；原文在服务器决策记录和各方案 §1。",
          notes=NOTES["a2"])
    tag = lambda t: {"text": t, "bold": True, "color": NAVY}
    rows = [
        ["编号", "主题", "定了什么"],
        [tag("D103–D107"), "子集诊断口径", "MIMIC-IV-ED 到院 2 h 预测 12 h 进 ICU 或死亡；登记子集；发现与确认分开；Platt 再校准；模型与变量"],
        [tag("D108–D113"), "补丁与确认集", "补丁 1 加 ESI、年龄；补丁 2 删观测；确认集只评一次（D109），之后只在发现集探索（D111）；补丁 3 加输入"],
        [tag("D120–D129"), "J 线", "读出形式；v0.6 三个口径；用 std_v3_20261030_4；Z3 保留；physiologic 跨院口径；J2b、J6、J6b 各运行一次"],
        [tag("D130–D133"), "八模型零样本 v1", "主分析用 D103 标签；15 分钟网格；只用验证集；可读 MC-MED 逐例预测做同一脚本复算"],
        [tag("D134–D136"), "r2 与 v2", "Time-MoE 主表用官方归一化；连续分数继续；另立 4 h 上下文版本"],
        [tag("D137–D142"), "补丁 3 之后", "≥75 岁列为登记格子；3b 作默认输入集；交叉拟合；Raindrop 敏感性；≥75 岁诊断；4 h 可行性计数"],
        [tag("D143–D147"), "汇报口径", "③ 另立新版本；两类写成数据侧难点，零样本规则读出写成负结果；主分析维持 2 h；3b 与转重定义不变"],
        [tag("D148"), "③ 的设计", "先只做 MIMIC-IV-ED D103；八个模型；主比较“摘要 + 嵌入”对“摘要”；LR 为主、LightGBM 为次"],
    ]
    add_table(slide, CL, TOP, [1.5, 2.1, 8.63], [0.4] + [0.54] * 8, rows, size=12, header_size=12.5,
              margins=(0.08, 0.02, 0.06, 0.02))


def fix_cover(cover):
    for shp in cover.shapes:
        if not shp.has_text_frame:
            continue
        text = shp.text_frame.text.strip()
        if text.startswith("老年流感"):
            base.set_shape_text(shp, "老年流感转重研究：本周工作总结")
        elif text.startswith("理想数据"):
            base.set_shape_text(shp, "子集诊断 · 基础模型零样本 · 决策模型零样本 · flucase 复核")
        elif text.startswith("2026"):
            base.set_shape_text(shp, "2026年11月7日")
    cover.notes_slide.notes_text_frame.text = NOTES["cover"]


def main():
    prs = Presentation(str(base.SRC))
    fix_cover(prs.slides[0])
    base.delete_slides_after_first(prs)
    blank = prs.slide_layouts.get_by_name("Blank")
    builders = [build_summary, build_week, build_survey, build_design, build_forest, build_patch, build_confirm,
                build_ablation, build_zs, build_zs_sub, build_hard, build_j1, build_j2, build_flucase, build_next,
                build_decide, build_closing, build_a1, build_a2]
    for build in builders:
        build(prs.slides.add_slide(blank))
    prs.core_properties.title = base.DECK_TITLE
    prs.core_properties.subject = "11-02 至 11-07：急诊子集诊断、八模型零样本、J 线、flucase 复核与下一步"
    prs.save(str(OUT))
    print(f"已生成：{OUT}（共 {len(prs.slides)} 页）")


if __name__ == "__main__":
    main()
