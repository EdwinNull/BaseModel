#!/usr/bin/env python3
"""生成《时序基础模型在急诊公开数据子集上的表现差异》阶段汇报（HTML，图为内嵌 SVG）。

图中数字全部抄自 result、docs/汇报 下的聚合结果文档，每个图函数的 SRC 注明出处；
不读任何逐患者数据。在仓库根目录运行：

    python scripts/report_html/build_tsfm_subgroup_report_20261110.py

模板里的 <!--FIG:key--> 被替换为对应图的 SVG 和数据表。
"""
from __future__ import annotations

import html
import io
import re
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TEMPLATE = HERE / "tsfm_subgroup_report_20261110.template.html"
OUT = ROOT / "docs/汇报/导师讨论/时序基础模型急诊子集问题_阶段汇报_20261110.html"

# 参考调色板前五个槽位（dataviz references/palette.md，浅色模式）；前三个已按全配对校验
S = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
NEG = "#e34948"
GRAY = "#8a8984"
INK = "#1f1f1d"
INK2 = "#52514e"
AXIS = "#b9b8b2"
FONT_STACK = ("'Helvetica Neue',Arial,'PingFang SC','Hiragino Sans GB',"
              "'Microsoft YaHei','Noto Sans CJK SC',sans-serif")
SCALE = 1.2  # SVG 用户单位到页面像素的放大倍数，决定图中字号（10 pt × 1.2 ≈ 12 px）

plt.rcParams.update({
    "svg.fonttype": "none",
    "font.family": ["Arial", "Hiragino Sans GB"],
    "font.size": 10,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.labelsize": 10,
    "axes.labelcolor": INK2,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "xtick.major.size": 3,
    "ytick.major.size": 0,
    "legend.fontsize": 9.5,
    "legend.frameon": False,
    "text.color": INK,
    "axes.unicode_minus": True,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


class Fig:
    """一张图：记录每个可悬停标记的提示文字，导出时写进 SVG 的 <title>。"""

    def __init__(self, key: str, w: float, h: float, nrows: int = 1, ncols: int = 1, **kw):
        self.key = key
        self.w = w
        self.fig, self.axes = plt.subplots(nrows, ncols, figsize=(w, h), **kw)
        self.tips: dict[str, str] = {}
        self.table: tuple[list[str], list[list[str]]] | None = None

    def tip(self, artist, text: str):
        gid = f"{self.key}-tt{len(self.tips)}"
        artist.set_gid(gid)
        self.tips[gid] = text
        return artist

    def svg(self) -> str:
        buf = io.StringIO()
        self.fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.06)
        plt.close(self.fig)
        s = buf.getvalue()
        s = s[s.index("<svg"):]
        s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
        s = re.sub(r'(<svg[^>]*?)\swidth="[^"]+"\sheight="[^"]+"', r"\1", s, count=1)
        s = s.replace("<svg ", f'<svg role="img" style="max-width:{self.w * 72 * SCALE:.0f}px" ', 1)
        # 多张图内嵌在同一页面，matplotlib 的通用 id 会重复，加图前缀
        s = re.sub(r'id="((?:figure|axes|patch|line2d|text|xtick|ytick|matplotlib\.axis|legend|'
                   r'PathCollection|LineCollection|PolyCollection|FancyBboxPatch|BarContainer)_\d+)"',
                   lambda m: f'id="{self.key}-{m.group(1)}"', s)
        s = re.sub(r"font-family: [^;\"]+", f"font-family: {FONT_STACK}", s)
        for gid, text in self.tips.items():
            opening = f'<g id="{gid}">'
            assert opening in s, f"{gid} 没有出现在 SVG 里"
            s = s.replace(opening, f'<g id="{gid}" class="tt"><title>{html.escape(text)}</title>', 1)
        return s

    def html(self) -> str:
        out = self.svg()
        if self.table:
            head, rows = self.table
            th = "".join(f"<th>{html.escape(h)}</th>" for h in head)
            trs = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows)
            out += (f'<details class="data"><summary>查看本图数据</summary>'
                    f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></details>')
        return out


def panel(ax, letter: str, title: str):
    ax.set_title(f"{letter}  {title}", pad=8)


def f3(x: float) -> str:
    return f"{x:+.3f}".replace("-", "−")


# ---------------------------------------------------------------- 图 2：零样本总体
def fig_overall() -> Fig:
    """SRC：docs/汇报/导师讨论/TSFM八模型子集_导师讨论稿_终版_20261107.md「两库总体结果」表。"""
    f = Fig("f-overall", 10.5, 2.9, ncols=2, sharey=True)
    data = [
        ("MC-MED · decomp_60（到床后 15 min 输入）",
         {"R": (0.500, 0.521, 0.500, 0.500), "S": (0.635, 0.669, 0.638, 0.691), "SUP": (0.705, 0.754)}),
        ("MIMIC-IV-ED · D103（到院后 2 h 输入）",
         {"R": (0.617, 0.638, 0.602, 0.659), "S": (0.716, 0.729, 0.687, 0.755), "SUP": (0.845, 0.879)}),
    ]
    labels = ["八个 TSFM，截断读出 R-max", "八个 TSFM，连续读出 S-max", "五个监督模型（补丁前）"]
    rows = []
    for (ax, letter), (title, d) in zip(zip(f.axes, "ab"), data):
        for y, key in zip([2, 1], ["R", "S"]):
            lo, hi, locf, cm = d[key]
            ln, = ax.plot([lo, hi], [y, y], color=S[0], lw=5, solid_capstyle="round")
            f.tip(ln, f"{labels[2 - y]}：AUROC {lo:.3f}–{hi:.3f}")
            m, = ax.plot(locf, y + 0.18, "D", ms=6.5, color=GRAY, mec="white", mew=1)
            f.tip(m, f"LOCF：{locf:.3f}")
            m, = ax.plot(cm, y - 0.18, "s", ms=6.5, color=S[1], mec="white", mew=1)
            f.tip(m, f"Context-max（直接看上下文最异常值）：{cm:.3f}")
            rows.append([title.split(" · ")[0], labels[2 - y], f"{lo:.3f}–{hi:.3f}", f"{locf:.3f}", f"{cm:.3f}"])
        lo, hi = d["SUP"]
        ln, = ax.plot([lo, hi], [0, 0], color=S[2], lw=5, solid_capstyle="round")
        f.tip(ln, f"五个监督模型：AUROC {lo:.3f}–{hi:.3f}")
        rows.append([title.split(" · ")[0], labels[2], f"{lo:.3f}–{hi:.3f}", "—", "—"])
        ax.axvline(0.5, color=AXIS, lw=0.8, ls=(0, (2, 2)))
        ax.set_xlim(0.47, 0.90)
        ax.set_ylim(-0.6, 2.6)
        ax.set_yticks([2, 1, 0], labels)
        ax.set_xlabel("AUROC")
        panel(ax, letter, title)
    handles = [Line2D([], [], color=S[0], lw=5, label="八个 TSFM 的范围"),
               Line2D([], [], color=S[2], lw=5, label="五个监督模型的范围"),
               Line2D([], [], ls="", marker="D", color=GRAY, ms=6.5, label="LOCF（沿用末值）"),
               Line2D([], [], ls="", marker="s", color=S[1], ms=6.5, label="Context-max")]
    f.fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.55, -0.2))
    f.fig.subplots_adjust(wspace=0.08)
    f.table = (["数据集", "风险分", "AUROC 范围", "LOCF", "Context-max"], rows)
    return f


# ---------------------------------------------------------------- 图 3：测量过程
def fig_measure() -> Fig:
    """SRC：docs/汇报/导师讨论/回复导师_子集数据差异与基础模型影响_两库全实验_20261108.md 附表 1。"""
    f = Fig("f-measure", 10.5, 3.6, ncols=2, gridspec_kw={"width_ratios": [1.25, 1]})
    cats = ["ESI 1–2", "ESI 3", "ESI 4–5", "急救车送达", "自行到达", "≥75 岁", "<65 岁"]
    mimic = [50.7, 81.2, 87.3, 58.0, 76.4, 56.9, 73.9]
    mcmed = [13.1, 21.9, 59.2, 18.1, 21.9, 15.3, 23.9]
    ypos = [8.4, 7.4, 6.4, 4.8, 3.8, 2.2, 1.2]
    ax = f.axes[0]
    h = 0.36
    rows = []
    for y, c, a, b in zip(ypos, cats, mimic, mcmed):
        r = ax.barh(y + h / 2, a, height=h, color=S[0], edgecolor="white", lw=1)[0]
        f.tip(r, f"MIMIC-IV-ED {c}：{a:.1f}% 只有一次测量")
        r = ax.barh(y - h / 2, b, height=h, color=S[1], edgecolor="white", lw=1)[0]
        f.tip(r, f"MC-MED {c}：{b:.1f}% 只有一分钟有观测")
        rows.append(["HR 只有一次测量（%）", c, f"{a:.1f}", f"{b:.1f}"])
    ax.set_yticks(ypos, cats)
    ax.set_xlim(0, 100)
    ax.set_xlabel("心率只有一次测量的就诊（%）")
    panel(ax, "a", "测量过程：窗口内心率只测一次的比例")
    f.fig.legend(handles=[Patch(color=S[0], label="MIMIC-IV-ED（2 h 窗口）"),
                          Patch(color=S[1], label="MC-MED（15 min 窗口）")],
                 loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.1))

    ax = f.axes[1]
    cats_b = ["ESI 1–2", "ESI 3", "ESI 4–5", "急救车送达", "自行到达"]
    mimic_b = [11.4, 1.0, None, 9.6, 1.9]
    mcmed_b = [17.0, 11.0, 7.3, 17.3, 10.5]
    yb = [6.4, 5.4, 4.4, 2.8, 1.8]
    for y, c, a, b in zip(yb, cats_b, mimic_b, mcmed_b):
        if a is None:
            ax.text(0.3, y + h / 2, "事件 <10，不报", va="center", fontsize=8.5, color=INK2)
        else:
            r = ax.barh(y + h / 2, a, height=h, color=S[0], edgecolor="white", lw=1)[0]
            f.tip(r, f"MIMIC-IV-ED {c}：D103 结局率 {a:.1f}%")
        r = ax.barh(y - h / 2, b, height=h, color=S[1], edgecolor="white", lw=1)[0]
        f.tip(r, f"MC-MED {c}：decomp_60 结局率 {b:.1f}%")
        rows.append(["结局率（%）", c, "事件 <10" if a is None else f"{a:.1f}", f"{b:.1f}"])
    ax.set_yticks(yb, cats_b)
    ax.set_xlim(0, 20)
    ax.set_xlabel("结局率（%；两库终点不同，不能横向比较）")
    panel(ax, "b", "结局率")
    f.fig.subplots_adjust(wspace=0.38)
    f.table = (["量", "子集", "MIMIC-IV-ED", "MC-MED"], rows)
    return f


# ---------------------------------------------------------------- 图 4：零样本失效方式
def fig_zs_mech() -> Fig:
    """SRC：回复导师_子集数据差异…_20261108.md 附表 3；急诊子集数据分布与基础模型机制_结果_20261108.md §5。"""
    f = Fig("f-zsmech", 10.5, 2.9, ncols=3, gridspec_kw={"width_ratios": [1, 1, 1]})
    ax = f.axes[0]
    pts = [("MIMIC-IV-ED", 1.000, 1.184, S[0], "o"), ("MC-MED", 1.000, 1.229, S[1], "s")]
    rows = []
    for i, (name, c, nc, col, mk) in enumerate(pts):
        off = 0.12 if i == 0 else -0.12
        m, = ax.plot(c, 1 + off, mk, ms=8, color=col, mec="white", mew=1)
        f.tip(m, f"{name} 常数输入：八模型平均 MAE / LOCF MAE = {c:.3f}")
        m, = ax.plot(nc, 0 + off, mk, ms=8, color=col, mec="white", mew=1)
        f.tip(m, f"{name} 非常数输入：八模型平均 MAE / LOCF MAE = {nc:.3f}")
        rows.append(["a", name, "MAE 比值：常数输入", f"{c:.3f}"])
        rows.append(["a", name, "MAE 比值：非常数输入", f"{nc:.3f}"])
    ax.axvline(1.0, color=AXIS, lw=0.8, ls=(0, (2, 2)))
    ax.set_yticks([1, 0], ["常数输入", "非常数输入"])
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlim(0.95, 1.28)
    ax.set_xlabel("八模型平均 MAE ÷ LOCF MAE（心率）")
    ax.legend(handles=[Line2D([], [], ls="", marker="o", color=S[0], ms=7, label="MIMIC-IV-ED"),
                       Line2D([], [], ls="", marker="s", color=S[1], ms=7, label="MC-MED")],
              loc="upper right", handletextpad=0.2)
    panel(ax, "a", "预测误差相对 LOCF")

    slopes = {"MIMIC-IV-ED": {"回到上下文均值": (-0.32, -0.70), "回到人群水平": (-0.41, -0.02)},
              "MC-MED": {"回到上下文均值": (-0.56, -0.62), "回到人群水平": (-0.13, -0.02)}}
    for ax, letter, name in zip(f.axes[1:], "bc", slopes):
        h = 0.34
        for y, (meas, (real, model)) in zip([1, 0], slopes[name].items()):
            r = ax.barh(y + h / 2, real, height=h, color=GRAY, edgecolor="white", lw=1)[0]
            f.tip(r, f"{name} {meas}：真实数据斜率 {real:+.2f}".replace("-", "−"))
            r = ax.barh(y - h / 2, model, height=h, color=S[0], edgecolor="white", lw=1)[0]
            f.tip(r, f"{name} {meas}：八模型平均斜率 {model:+.2f}".replace("-", "−"))
            rows.append([letter, name, f"{meas} 斜率：真实 / 八模型平均",
                         f"{real:+.2f} / {model:+.2f}".replace("-", "−")])
        ax.axvline(0, color=AXIS, lw=0.8)
        ax.set_xlim(-0.8, 0.05)
        ax.set_yticks([1, 0], list(slopes[name]))
        ax.set_ylim(-0.6, 1.6)
        ax.set_xlabel("未来变化对偏离量的回归斜率")
        panel(ax, letter, f"{name}：回落规律")
    f.axes[2].legend(handles=[Patch(color=GRAY, label="真实数据"), Patch(color=S[0], label="八模型平均")],
                     loc="lower left")
    f.fig.subplots_adjust(wspace=0.55)
    f.table = (["面板", "数据集", "量", "值"], rows)
    return f


# ---------------------------------------------------------------- 图 5：补丁轨迹
MODELS = ["LR", "LightGBM", "BRITS", "mTAND", "Raindrop"]
MARKS = ["o", "s", "^", "D", "v"]


def fig_patch_overall() -> Fig:
    """SRC：ed_ts_bench_本周周报_20261102-1108.md §2；ed_ts_bench_补丁3_发现集结果_20261107.md §2.1、§3.1。"""
    f = Fig("f-patch", 10.5, 3.3, ncols=2)
    stages = ["补丁前\n6 项体征", "补丁 1\n+ESI、年龄", "补丁 3a\n+到院时信息", "补丁 3b\n+已出结果检查"]
    data = {
        "MC-MED（发现集 8,085 次 / 999 个阳性）": {
            "LR": [0.705, 0.709, 0.725, 0.729], "LightGBM": [0.734, 0.740, 0.760, 0.772],
            "BRITS": [0.730, 0.735, 0.748, 0.747], "mTAND": [0.690, 0.700, 0.731, 0.741],
            "Raindrop": [0.708, 0.713, 0.731, 0.736]},
        "MIMIC-IV-ED（发现集 38,242 次 / 2,072 个阳性）": {
            "LR": [0.846, 0.893, 0.917, 0.924], "LightGBM": [0.877, 0.905, 0.928, 0.937],
            "BRITS": [0.879, 0.904, 0.923, 0.928], "mTAND": [0.862, 0.892, 0.919, 0.928],
            "Raindrop": [0.874, 0.903, 0.925, 0.932]},
    }
    rows = []
    for ax, letter, (title, d) in zip(f.axes, "ab", data.items()):
        for i, mname in enumerate(MODELS):
            v = d[mname]
            ax.plot(range(4), v, color=S[i], lw=1.6, zorder=2)
            for x, val in enumerate(v):
                m, = ax.plot(x, val, MARKS[i], ms=6.5, color=S[i], mec="white", mew=1, zorder=3)
                f.tip(m, f"{mname} · {stages[x].replace(chr(10), ' ')}：AUROC {val:.3f}")
            rows.append([title.split("（")[0], mname] + [f"{x:.3f}" for x in v])
        ax.set_xticks(range(4), stages)
        ax.set_xlim(-0.25, 3.25)
        ax.set_ylabel("总体 AUROC（5 个 seed 均值）")
        ax.grid(axis="y", color="#efeeea", lw=0.8)
        ax.set_axisbelow(True)
        panel(ax, letter, title)
    f.axes[0].set_ylim(0.68, 0.78)
    f.axes[1].set_ylim(0.84, 0.94)
    handles = [Line2D([], [], color=S[i], marker=MARKS[i], ms=6, lw=1.6, label=m) for i, m in enumerate(MODELS)]
    f.fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.1))
    f.fig.subplots_adjust(wspace=0.25)
    f.table = (["数据集", "模型"] + [s.replace("\n", " ") for s in stages], rows)
    return f


# ---------------------------------------------------------------- 图 6：子集差距
def fig_subgap() -> Fig:
    """SRC：ed_ts_bench_补丁3_发现集结果_20261107.md §2.3、§3.3（五个模型，补丁 1 → 3a → 3b）。"""
    mimic = {
        "≤1 次 × ESI 1–2": [(-0.218, -0.128, -0.103), (-0.178, -0.113, -0.093), (-0.187, -0.116, -0.098),
                           (-0.188, -0.107, -0.096), (-0.190, -0.115, -0.097)],
        "≤1 次 × ESI 3–5": [(-0.032, -0.071, -0.097), (-0.053, -0.063, -0.071), (-0.054, -0.075, -0.087),
                           (-0.027, -0.047, -0.058), (-0.043, -0.059, -0.064)],
        ">1 次 × ESI 3–5": [(-0.107, -0.099, -0.078), (-0.078, -0.062, -0.036), (-0.086, -0.086, -0.070),
                           (-0.088, -0.081, -0.061), (-0.082, -0.077, -0.060)],
        ">1 次 × ESI 1–2": [(-0.058, -0.024, -0.013), (-0.048, -0.021, -0.017), (-0.036, -0.019, -0.017),
                           (-0.073, -0.036, -0.023), (-0.048, -0.026, -0.024)],
        "≥80 岁": [(-0.047, -0.050, -0.042), (-0.044, -0.045, -0.040), (-0.046, -0.049, -0.044),
                  (-0.053, -0.052, -0.048), (-0.048, -0.051, -0.047)],
        "≥75 岁": [(-0.046, -0.046, -0.039), (-0.042, -0.041, -0.037), (-0.042, -0.042, -0.038),
                  (-0.051, -0.049, -0.044), (-0.047, -0.046, -0.043)],
        "65–79 岁": [(-0.017, -0.014, -0.017), (-0.023, -0.020, -0.023), (-0.022, -0.018, -0.019),
                    (-0.027, -0.026, -0.026), (-0.022, -0.019, -0.023)],
        "急救车 / 直升机送达": [(-0.036, -0.030, -0.018), (-0.036, -0.031, -0.023), (-0.038, -0.032, -0.023),
                         (-0.044, -0.041, -0.027), (-0.041, -0.035, -0.026)],
        "vitalsign ≤1 次": [(0.014, 0.001, -0.007), (0.007, -0.001, -0.006), (0.001, -0.001, -0.004),
                           (0.027, 0.016, 0.004), (0.007, 0.003, 0.001)],
    }
    mcmed = {
        "观测 ≤15 个": [(-0.031, -0.010, -0.012), (-0.056, -0.034, -0.025), (-0.063, -0.035, -0.035),
                      (-0.069, -0.028, -0.024), (-0.055, -0.026, -0.029)],
        "≤15 × ESI 3–5": [(-0.035, -0.011, -0.017), (-0.053, -0.042, -0.037), (-0.062, -0.038, -0.039),
                         (-0.093, -0.052, -0.030), (-0.067, -0.039, -0.039)],
        "≤15 × ESI 1–2": [(-0.040, -0.033, -0.020), (-0.075, -0.017, -0.004), (-0.073, -0.043, -0.034),
                         (-0.038, 0.014, -0.021), (-0.046, -0.014, -0.018)],
        "≥80 岁": [(-0.059, -0.063, -0.044), (-0.028, -0.046, -0.023), (-0.031, -0.043, -0.032),
                  (-0.025, -0.050, -0.039), (-0.036, -0.047, -0.033)],
        "≥75 岁": [(-0.042, -0.050, -0.035), (-0.014, -0.038, -0.022), (-0.017, -0.034, -0.027),
                  (-0.013, -0.054, -0.044), (-0.017, -0.041, -0.032)],
    }
    f = Fig("f-subgap", 10.5, 4.6, ncols=2, gridspec_kw={"width_ratios": [1.15, 1]})
    stage_names = ["补丁 1", "补丁 3a", "补丁 3b"]
    rows = []
    for ax, letter, title, d, xlim in [(f.axes[0], "a", "MIMIC-IV-ED", mimic, (-0.235, 0.035)),
                                        (f.axes[1], "b", "MC-MED", mcmed, (-0.105, 0.025))]:
        names = list(d)
        n = len(names)
        for r, name in enumerate(names):
            y0 = n - 1 - r
            if r % 2 == 0:
                ax.axhspan(y0 - 0.5, y0 + 0.5, color="#f6f5f1", lw=0, zorder=0)
            for k in range(3):
                vals = [m[k] for m in d[name]]
                y = y0 + 0.24 - 0.24 * k
                lo, hi, mean = min(vals), max(vals), sum(vals) / 5
                ax.plot([lo, hi], [y, y], color=S[k], lw=1.6, zorder=2)
                mk, = ax.plot(mean, y, ["o", "s", "^"][k], ms=6.5, color=S[k], mec="white", mew=1, zorder=3)
                detail = "，".join(f"{mm} {f3(v)}" for mm, v in zip(MODELS, vals))
                f.tip(mk, f"{title} {name} · {stage_names[k]}：五模型均值 {f3(mean)}（{detail}）")
                rows.append([title, name, stage_names[k]] + [f3(v) for v in vals])
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_yticks(range(n), names[::-1])
        ax.set_ylim(-0.6, n - 0.4)
        ax.set_xlim(*xlim)
        ax.set_xlabel("子集 AUROC − 补集 AUROC")
        panel(ax, letter, f"{title}：子集减补集")
    handles = [Line2D([], [], color=S[k], marker=["o", "s", "^"][k], ms=6, lw=1.6, label=s)
               for k, s in enumerate(["补丁 1（+ESI、年龄）", "补丁 3a（+到院时信息）", "补丁 3b（+已出结果检查）"])]
    f.fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.07))
    f.fig.subplots_adjust(wspace=0.42)
    f.table = (["数据集", "子集", "阶段"] + MODELS, rows)
    return f


# ---------------------------------------------------------------- 图 7：常数输入：预测误差与风险排序脱钩
def fig_const() -> Fig:
    """SRC：常数上下文可行性_结果_20261108.md 常数就诊表（D157）；D157-D160_急诊路线收尾与后续主线_20261108.md（D158–D160）。"""
    f = Fig("f-const", 10.5, 3.7, ncols=2, gridspec_kw={"width_ratios": [1, 1.05]})
    ax = f.axes[0]
    groups = [
        ("LOCF 与五个钉住的零样本臂", GRAY, "D", [("LOCF = 零样本", 0.644, 0.656)]),
        ("零样本 + 锚点 / 下限", S[0], "o", [("z_ci_anc8", 0.618, 0.663), ("z_cd_anc8", 0.629, 0.664),
                                       ("floor_cd", 0.605, 0.663)]),
        ("训练小模型补回统计量", S[1], "s", [("stats_ci", 0.532, 0.635), ("stats_cd", 0.530, 0.648),
                                      ("stats_gate", 0.529, 0.638)]),
        ("再加年龄、性别、ESI、到达方式", S[2], "^", [("stats_gate_cov", 0.518, 0.686), ("stats_gate_cov_mask", 0.518, 0.685),
                                    ("stats_ci_cov_mask", 0.521, 0.689)]),
    ]
    rows = []
    for gname, col, mk, pts in groups:
        for name, x, y in pts:
            m, = ax.plot(x, y, mk, ms=8, color=col, mec="white", mew=1, zorder=3)
            f.tip(m, f"{name}：nMAE {x:.3f}（相对 LOCF {100 * (x / 0.644 - 1):+.0f}%），S-max AUROC {y:.3f}")
            rows.append(["a", gname, name, f"{x:.3f}", f"{y:.3f}"])
    ax.axhline(0.656, color=AXIS, lw=0.8, ls=(0, (2, 2)))
    ax.axvline(0.644, color=AXIS, lw=0.8, ls=(0, (2, 2)))
    ax.text(0.5105, 0.6575, "LOCF 的 AUROC", fontsize=8.5, color=INK2, va="bottom")
    ax.annotate("", xy=(0.522, 0.6265), xytext=(0.600, 0.6265),
                arrowprops=dict(arrowstyle="->", color=INK2, lw=0.8))
    ax.text(0.561, 0.6285, "预测误差更低", fontsize=8.5, color=INK2, ha="center", va="bottom")
    ax.set_xlim(0.505, 0.655)
    ax.set_ylim(0.622, 0.697)
    ax.set_xlabel("常数就诊上的体征预测 nMAE（越小越好）")
    ax.set_ylabel("D103 风险 AUROC（S-max）")
    ax.legend(handles=[Line2D([], [], ls="", marker=mk, color=col, ms=7, label=g) for g, col, mk, _ in groups],
              loc="upper right", fontsize=8.5, handletextpad=0.2, borderaxespad=0.2)
    panel(ax, "a", "补回水平降低了预测误差，排序却没跟着变好")

    ax = f.axes[1]
    bars = [
        ("D160 四组读出 D−B（全体）", 0.000001, "+0.000001", None, S[0]),
        ("D159 eICU 密集体征，表格 + 预测摘要", 0.000, "≈ 0", (-0.011, 0.011), S[0]),
        ("D158 3b + 预测时序摘要（全体）", 0.0008, "+0.0008", None, S[0]),
        ("D158 同上，非常数层", 0.0023, "+0.0023", None, S[0]),
        ("D159 3b + 实际未来体征（全体）", 0.016, "+0.016", None, S[1]),
        ("D159 同上，常数层", 0.037, "+0.037", None, S[1]),
    ]
    for y, (name, v, label, ci, col) in enumerate(bars[::-1]):
        r = ax.barh(y, v, height=0.55, color=col, edgecolor="white", lw=1)[0]
        tip = f"{name}：ΔAUROC {label}"
        if ci:
            ax.errorbar(v, y, xerr=[[v - ci[0]], [ci[1] - v]], fmt="none", ecolor=INK2, elinewidth=1, capsize=3)
            tip += f"（95% CI {ci[0]:+.3f} 至 {ci[1]:+.3f}）".replace("-", "−")
        f.tip(r, tip)
        ax.text(max(v, ci[1] if ci else v) + 0.0008, y, label, va="center", fontsize=8.5, color=INK2)
        rows.append(["b", "现实增量" if col == S[0] else "上限（用到未来真实体征）", name, label,
                     "—" if not ci else f"{ci[0]:+.3f}, {ci[1]:+.3f}"])
    ax.set_yticks(range(len(bars)), [b[0] for b in bars[::-1]])
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlim(-0.013, 0.045)
    ax.set_xlabel("在表格模型之上增加的 AUROC")
    ax.legend(handles=[Patch(color=S[0], label="现实可得（用预测）"), Patch(color=S[1], label="上限（用实际未来体征）")],
              loc="center right")
    panel(ax, "b", "时间信息在表格模型之上的增量")
    f.fig.subplots_adjust(wspace=0.95)
    f.table = (["面板", "组", "臂 / 比较", "nMAE 或 ΔAUROC", "AUROC 或 95% CI"], rows)
    return f


# ---------------------------------------------------------------- 图 8：四组读出与配对分解
def fig_four_arm() -> Fig:
    """SRC：MIMIC-IV-ED_四组读出与排序分解_结果_20261108.md（D160）。"""
    f = Fig("f-fourarm", 10.5, 3.2, ncols=2, gridspec_kw={"width_ratios": [1, 1.15]})
    ax = f.axes[0]
    arms = [("A 测量模式", 0.823286, 0.585331, 0.768567), ("B A+末值+协变量", 0.900901, 0.840457, 0.858784),
            ("C B+零样本分数", 0.900936, 0.840301, 0.858934), ("D B+微调分数", 0.900902, 0.839615, 0.859532)]
    layers = ["全体（45,041 / 2,296）", "常数层（31,144 / 512）", "非常数层（13,897 / 1,784）"]
    rows = []
    for i, (name, *vals) in enumerate(arms):
        y = 3 - i
        for k, v in enumerate(vals):
            m, = ax.plot(v, y + 0.2 - 0.2 * k, ["o", "s", "^"][k], ms=7, color=S[k], mec="white", mew=1)
            f.tip(m, f"{name} · {layers[k]}：AUROC {v:.4f}")
        rows.append(["a", name] + [f"{v:.4f}" for v in vals])
    ax.set_yticks([3, 2, 1, 0], [a[0] for a in arms])
    ax.set_ylim(-0.6, 3.6)
    ax.set_xlim(0.56, 0.93)
    ax.set_xlabel("AUROC（训练集内部 eval，D103 终点）")
    ax.legend(handles=[Line2D([], [], ls="", marker=["o", "s", "^"][k], color=S[k], ms=7, label=l)
                       for k, l in enumerate(layers)], loc="lower left", fontsize=8.5, handletextpad=0.2)
    panel(ax, "a", "四组监督读出")

    ax = f.axes[1]
    pairs = [("常数事件 × 常数非事件", -0.002914, (-0.005968, 0.000520)),
             ("常数事件 × 非常数非事件", 0.014127, (0.012342, 0.016204)),
             ("非常数事件 × 常数非事件", -0.091253, (-0.098258, -0.084452)),
             ("非常数事件 × 非常数非事件", 0.000851, (-0.001024, 0.002499)),
             ("合计", -0.079188, (-0.088119, -0.069177))]
    for y, (name, v, ci) in enumerate(pairs[::-1]):
        col = INK2 if name == "合计" else (NEG if v < 0 else S[0])
        r = ax.barh(y, v, height=0.55, color=col, edgecolor="white", lw=1)[0]
        ax.errorbar(v, y, xerr=[[v - ci[0]], [ci[1] - v]], fmt="none", ecolor=INK, elinewidth=0.9, capsize=2.5)
        f.tip(r, f"{name}：贡献 {v:+.6f}（95% CI {ci[0]:+.6f} 至 {ci[1]:+.6f}）".replace("-", "−"))
        rows.append(["b", name, f"{v:+.6f}", f"{ci[0]:+.6f}, {ci[1]:+.6f}"])
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(range(len(pairs)), [p[0] for p in pairs[::-1]])
    ax.set_xlim(-0.105, 0.025)
    ax.set_xlabel("对 AUROC 差（锚点微调 − 锚点零样本）的贡献")
    panel(ax, "b", "原始分数下降 0.079 的配对分解")
    f.fig.subplots_adjust(wspace=0.75)
    f.table = (["面板", "臂 / 配对类型", "值", "值 / 95% CI"], rows)
    return f


# ---------------------------------------------------------------- 图 9：D166 跨通道敏感性
def fig_d166() -> Fig:
    """SRC：result/时序基础模型/Chronos-2归一化空间跨通道敏感性_结果_20261110.md §3、§4（D166）。"""
    f = Fig("f-d166", 10.5, 2.8, ncols=2, gridspec_kw={"width_ratios": [1.2, 1]})
    ax = f.axes[0]
    vals = [("HR", 0.0029, 0.0704, 813), ("MAP", 0.0031, 0.0718, 760), ("SpO₂", 0.0027, 0.0753, 4340)]
    rows = []
    ax.axvspan(1e-9, 1e-6, color="#f1f0ec", lw=0, zorder=0)
    ax.text(3e-8, 2.45, "数值噪声底以下", fontsize=8.5, color=INK2, ha="center")
    for i, (name, b, d, nb) in enumerate(vals):
        y = 2 - i
        ax.plot([b, d], [y, y], color=AXIS, lw=1, zorder=1)
        m, = ax.plot(b, y, "o", ms=8, color=S[1], mec="white", mew=1, zorder=3)
        f.tip(m, f"{name} B 组（目标常数，n={nb:,}）：打乱后 ẑ 变化中位数 {b}")
        m, = ax.plot(d, y, "s", ms=8, color=S[0], mec="white", mew=1, zorder=3)
        f.tip(m, f"{name} D 组（目标有动态）：打乱后 ẑ 变化中位数 {d}")
        ax.text((b * d) ** 0.5, y + 0.14, f"B/D ≈ {100 * b / d:.0f}%", fontsize=8.5, color=INK2, ha="center")
        rows.append(["a", name, f"{b}", f"{d}", f"{100 * b / d:.1f}%"])
    ax.set_xscale("log")
    ax.set_xlim(1e-8, 0.5)
    ax.set_yticks([2, 1, 0], [v[0] for v in vals])
    ax.set_ylim(-0.5, 2.75)
    ax.set_xlabel("跨就诊打乱辅助通道后 ẑ 变化的中位数（arcsinh 单位，对数轴）")
    ax.legend(handles=[Line2D([], [], ls="", marker="o", color=S[1], ms=7, label="B 组：目标常数"),
                       Line2D([], [], ls="", marker="s", color=S[0], ms=7, label="D 组：目标有动态")],
              loc="lower left", fontsize=8.5, handletextpad=0.2)
    panel(ax, "a", "网络输出 ẑ 对辅助通道的响应")

    ax = f.axes[1]
    att = [("HR", 0.789, 0.748, 0.803, 0.798), ("MAP", 0.790, 0.750, 0.803, 0.798), ("SpO₂", 0.778, 0.692, 0.801, 0.795)]
    for i, (name, b_avg, b_last, d_avg, d_last) in enumerate(att):
        y = 2 - i
        for v, col, filled, off, lab in [(b_avg, S[1], True, 0.12, "B 组 12 层平均"), (b_last, S[1], False, 0.12, "B 组最后一层"),
                                         (d_avg, S[0], True, -0.12, "D 组 12 层平均"), (d_last, S[0], False, -0.12, "D 组最后一层")]:
            m, = ax.plot(v, y + off, "o", ms=7.5, color=col, mfc=col if filled else "white", mew=1.4)
            f.tip(m, f"{name} {lab}：放到其他行的注意力 {v:.3f}")
        rows.append(["b", name, f"B {b_avg:.3f} / {b_last:.3f}", f"D {d_avg:.3f} / {d_last:.3f}", "均匀 0.800"])
    ax.axvline(0.8, color=AXIS, lw=0.8, ls=(0, (2, 2)))
    ax.text(0.8015, 2.42, "均匀分配 0.80", fontsize=8.5, color=INK2)
    ax.set_yticks([2, 1, 0], [a[0] for a in att])
    ax.set_ylim(-0.5, 2.75)
    ax.set_xlim(0.68, 0.83)
    ax.set_xlabel("目标行放到同组其他行的注意力质量")
    ax.legend(handles=[Line2D([], [], ls="", marker="o", color=INK2, ms=7, label="12 层平均"),
                       Line2D([], [], ls="", marker="o", color=INK2, mfc="white", mew=1.4, ms=7, label="最后一层")],
              loc="upper left", fontsize=8.5, handletextpad=0.2)
    panel(ax, "b", "分组注意力")
    f.fig.subplots_adjust(wspace=0.3)
    f.table = (["面板", "目标通道", "B 组", "D 组", "B/D 或参照"], rows)
    return f


# ---------------------------------------------------------------- 图 10：MC-MED 年龄差距
def fig_mcmed_age() -> Fig:
    """SRC：result/急诊低氧机制/MC-MED_年龄与事件成分标准化_D162_结果.md。"""
    f = Fig("f-age", 10.5, 2.8, ncols=3, gridspec_kw={"width_ratios": [1.15, 1, 1]})
    comps = ["SpO₂ 触发", "HR 触发", "MAP 触发"]
    share = {"<75 岁（3,965 个事件）": [50.47, 38.92, 10.62], "≥75 岁（1,354 个事件）": [62.56, 23.19, 14.25]}
    rows = []
    ax = f.axes[0]
    for y, (name, sh) in zip([1, 0], share.items()):
        left = 0
        for k, v in enumerate(sh):
            r = ax.barh(y, v, left=left, height=0.5, color=S[k], edgecolor="white", lw=2)[0]
            f.tip(r, f"{name} · {comps[k]}：{v:.1f}%")
            if v > 9:
                ax.text(left + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="white",
                        fontweight="bold")
            left += v
        rows.append(["a", name] + [f"{v:.2f}%" for v in sh])
    ax.set_yticks([1, 0], list(share))
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 1.9)
    ax.set_xlabel("事件构成（%）")
    ax.legend(handles=[Patch(color=S[k], label=c) for k, c in enumerate(comps)], loc="upper center",
              ncol=3, fontsize=8.5, bbox_to_anchor=(0.5, 1.02), handlelength=1, columnspacing=0.8)
    panel(ax, "a", "事件由哪项体征触发")

    ax = f.axes[1]
    auc = [("SpO₂ 触发", 0.7202, 0.7300), ("HR 触发", 0.8431, 0.7722), ("MAP 触发", 0.7027, 0.7898)]
    for k, (name, young, old) in enumerate(auc):
        y = 2 - k
        ax.plot([young, old], [y, y], color=AXIS, lw=1)
        m, = ax.plot(young, y, "o", ms=7.5, color=S[k], mfc="white", mew=1.6)
        f.tip(m, f"LightGBM {name}，<75 岁：AUROC {young:.4f}")
        m, = ax.plot(old, y, "o", ms=7.5, color=S[k], mec="white", mew=1)
        f.tip(m, f"LightGBM {name}，≥75 岁：AUROC {old:.4f}")
        rows.append(["b", name, f"<75 {young:.4f}", f"≥75 {old:.4f}", ""])
    ax.set_yticks([2, 1, 0], [a[0] for a in auc])
    ax.set_ylim(-0.5, 2.5)
    ax.set_xlim(0.68, 0.90)
    ax.set_xlabel("成分 AUROC（LightGBM，训练集 OOF）")
    ax.legend(handles=[Line2D([], [], ls="", marker="o", color=INK2, mfc="white", mew=1.6, ms=7, label="<75 岁"),
                       Line2D([], [], ls="", marker="o", color=INK2, ms=7, label="≥75 岁")],
              loc="lower right", fontsize=8.5, handletextpad=0.2)
    panel(ax, "b", "各成分内的判别")

    ax = f.axes[2]
    gaps = [("LR", -0.0235, (-0.0403, -0.0035), -0.0100, (-0.0268, 0.0097)),
            ("LightGBM", -0.0178, (-0.0335, -0.0015), -0.0094, (-0.0261, 0.0079))]
    for k, (name, raw, rci, std, sci) in enumerate(gaps):
        y = 1 - k
        for v, ci, off, filled, lab in [(raw, rci, 0.13, False, "原始差"), (std, sci, -0.13, True, "统一事件构成后")]:
            ax.errorbar(v, y + off, xerr=[[v - ci[0]], [ci[1] - v]], fmt="none", ecolor=INK2, elinewidth=1, capsize=2.5)
            m, = ax.plot(v, y + off, "o", ms=7.5, color=INK, mfc=INK if filled else "white", mew=1.4)
            f.tip(m, f"{name} {lab}：{v:+.4f}（95% CI {ci[0]:+.4f} 至 {ci[1]:+.4f}）".replace("-", "−"))
        rows.append(["c", name, f"原始 {raw:+.4f} [{rci[0]:+.4f}, {rci[1]:+.4f}]",
                     f"标准化 {std:+.4f} [{sci[0]:+.4f}, {sci[1]:+.4f}]", ""])
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks([1, 0], ["LR", "LightGBM"])
    ax.set_ylim(-0.6, 1.95)
    ax.set_xlim(-0.045, 0.015)
    ax.set_xlabel("≥75 岁 − <75 岁 AUROC")
    ax.legend(handles=[Line2D([], [], ls="", marker="o", color=INK, mfc="white", mew=1.4, ms=7, label="原始差"),
                       Line2D([], [], ls="", marker="o", color=INK, ms=7, label="统一事件构成后")],
              loc="upper left", fontsize=8.5, handletextpad=0.2)
    panel(ax, "c", "年龄差距")
    f.fig.subplots_adjust(wspace=0.5)
    f.table = (["面板", "项", "值 1", "值 2", "值 3"], [r + [""] * (5 - len(r)) if len(r) < 5 else r for r in rows])
    return f


# ---------------------------------------------------------------- 图 11：小样本组合
def fig_small() -> Fig:
    """SRC：result/急诊监督模型/小样本配方确认_结果_20261108.md §1（D156）。"""
    f = Fig("f-small", 6.4, 3.0)
    ax = f.axes
    ns = [1000, 2500, 5000]
    conf = {"MC-MED": [(0.0147, 0.0096, 0.0199), (0.0104, 0.0062, 0.0147), (0.0074, 0.0040, 0.0111)],
            "MIMIC-IV-ED": [(0.0095, 0.0083, 0.0107), (0.0082, 0.0072, 0.0094), (0.0064, 0.0055, 0.0074)]}
    sset = {"MC-MED": [0.0120, 0.0103, 0.0072], "MIMIC-IV-ED": [0.0094, 0.0070, 0.0055]}
    rows = []
    for k, (name, cs) in enumerate(conf.items()):
        col = [S[1], S[0]][k]
        mk = ["s", "o"][k]
        off = -0.08 if k == 0 else 0.08
        xs = [i + off for i in range(3)]
        ax.plot(xs, [c[0] for c in cs], color=col, lw=1.4)
        for i, (v, lo, hi) in enumerate(cs):
            ax.errorbar(xs[i], v, yerr=[[v - lo], [hi - v]], fmt="none", ecolor=col, elinewidth=1.2, capsize=3)
            m, = ax.plot(xs[i], v, mk, ms=7.5, color=col, mec="white", mew=1)
            f.tip(m, f"{name} n={ns[i]:,}：确认集 ΔAUROC +{v:.4f}（95% CI +{lo:.4f} 至 +{hi:.4f}）")
            m, = ax.plot(xs[i] + 0.16 * (1 if k else -1), sset[name][i], mk, ms=6, color=col, mfc="white", mew=1.2)
            f.tip(m, f"{name} n={ns[i]:,}：选择阶段（S 集）估计 +{sset[name][i]:.4f}")
            rows.append([name, f"{ns[i]:,}", f"+{v:.4f}", f"+{lo:.4f}, +{hi:.4f}", f"+{sset[name][i]:.4f}"])
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(range(3), [f"n = {n:,}" for n in ns])
    ax.set_xlim(-0.45, 2.45)
    ax.set_ylim(-0.001, 0.021)
    ax.set_ylabel("ens_bag − 单个 LightGBM 的 ΔAUROC")
    ax.legend(handles=[Line2D([], [], color=S[1], marker="s", ms=6, label="MC-MED 确认集"),
                       Line2D([], [], color=S[0], marker="o", ms=6, label="MIMIC-IV-ED 确认集"),
                       Line2D([], [], ls="", marker="o", color=INK2, mfc="white", mew=1.2, ms=6, label="选择阶段估计（S 集）")],
              loc="upper right", fontsize=8.5)
    ax.set_title("每个训练规模 20 次整人抽样；区间为确认集患者整群 bootstrap", fontsize=9, fontweight="normal", color=INK2)
    f.table = (["数据集", "训练规模", "确认集 ΔAUROC", "95% CI", "S 集估计"], rows)
    return f


FIGS = {
    "overall": fig_overall, "measure": fig_measure, "zsmech": fig_zs_mech, "patch": fig_patch_overall,
    "subgap": fig_subgap, "const": fig_const, "fourarm": fig_four_arm, "d166": fig_d166,
    "age": fig_mcmed_age, "small": fig_small,
}


def main():
    page = TEMPLATE.read_text(encoding="utf-8")
    for key, fn in FIGS.items():
        marker = f"<!--FIG:{key}-->"
        assert page.count(marker) == 1, f"模板里 {marker} 应恰好出现一次"
        page = page.replace(marker, fn().html())
    left = re.findall(r"<!--FIG:[^>]+-->", page)
    assert not left, f"模板里有未定义的图：{left}"
    OUT.write_text(page, encoding="utf-8")
    print(f"写出 {OUT.relative_to(ROOT)}（{len(page) / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
