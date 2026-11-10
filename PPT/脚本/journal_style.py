"""
journal_style.py —— 期刊级 matplotlib 作图规范
=================================================
用法:
    from journal_style import use_style, figsize, save_fig, panel_labels, COLORS, MARKERS
    use_style("nature")                      # 或 "ieee" / "elsevier" / "thesis"(中文学位论文)
    fig, ax = plt.subplots(figsize=figsize("nature", cols=1, aspect=0.75))
    ...
    save_fig(fig, "fig1_forecast")           # 同时导出 PDF(矢量) + PNG(600 dpi) + TIFF

设计原则:
  * 尺寸按期刊栏宽(mm)给定,出图后不再缩放,字号即最终印刷字号
  * 字体嵌入为 TrueType(fonttype 42),投稿系统和 Illustrator 都能正常编辑
  * 配色为 Okabe-Ito 色盲友好色,顺序经过色觉缺陷分离度校验;
    多条曲线时颜色始终搭配 marker / 线型做第二编码,黑白打印也能区分
  * 去掉上/右边框,不画网格,图例无边框 —— 数据本身最显眼
"""
from __future__ import annotations

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler

MM = 1 / 25.4  # 毫米 -> 英寸

# ---------------------------------------------------------------- 期刊参数
# width_mm: 单栏 / 1.5 栏 / 双栏;font: 正文字号(pt);small: 刻度等小字号;min_pt: 期刊最小字号要求
JOURNALS = {
    "nature":   {"width_mm": {1: 89, 1.5: 120, 2: 183},  "font": 7, "small": 6, "min_pt": 5,
                 "panel": "{}",   "panel_upper": False},
    "ieee":     {"width_mm": {1: 88.9, 2: 181.9},          "font": 8, "small": 8, "min_pt": 8,
                 "panel": "({})", "panel_upper": False},
    "elsevier": {"width_mm": {1: 90, 1.5: 140, 2: 190},  "font": 8, "small": 7, "min_pt": 6,
                 "panel": "({})", "panel_upper": False},
    # 中文学位论文 / 中文期刊:A4 版心约 150-160 mm,正文五号(10.5pt),图中小五号(9pt)
    "thesis":   {"width_mm": {1: 80, 2: 150},             "font": 9, "small": 9, "min_pt": 7.5,
                 "panel": "({})", "panel_upper": False},
}

# Okabe-Ito,顺序已用 CVD 校验(相邻色对 deutan ΔE ≥ 9.6)
COLORS = ["#0072B2",  # 蓝
          "#D55E00",  # 朱红
          "#009E73",  # 蓝绿
          "#E69F00",  # 橙
          "#CC79A7",  # 紫红
          "#56B4E9"]  # 天蓝
GRAY = "#7F7F7F"      # 参考线、基线模型、"其他"
TEXT = "#222222"
MARKERS = ["o", "s", "^", "D", "v", "P"]
LINESTYLES = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1))]

# 字体回退链:Windows 有 Arial;Linux 用 Liberation Sans(与 Arial 等宽);中文用雅黑/黑体/思源
SANS = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
CJK = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei"]


def use_style(journal: str = "nature", cjk: bool | None = None) -> dict:
    """应用期刊样式。cjk=True 时启用中文字体回退(thesis 默认开启)。返回该期刊参数。"""
    j = JOURNALS[journal]
    if cjk is None:
        cjk = journal == "thesis"
    from matplotlib import font_manager
    installed = {f.name for f in font_manager.fontManager.ttflist}
    fonts = [f for f in ((SANS + CJK) if cjk else SANS) if f in installed] or ["DejaVu Sans"]
    if cjk and not any(f in installed for f in CJK):
        print("警告:未找到中文字体,中文会显示为方块。Windows 一般自带 Microsoft YaHei / SimHei。")
    mpl.rcdefaults()
    mpl.rcParams.update({
        # 字体
        "font.family": fonts,               # 直接给具体字体列表,matplotlib 才会逐字回退(英文 Arial、中文雅黑)
        "font.sans-serif": fonts,
        "font.size": j["font"],
        "axes.titlesize": j["font"],
        "axes.labelsize": j["font"],
        "xtick.labelsize": j["small"],
        "ytick.labelsize": j["small"],
        "legend.fontsize": j["small"],
        "axes.unicode_minus": not cjk,      # 中文字体下负号显示为方块的问题
        "mathtext.fontset": "custom",
        "mathtext.rm": fonts[0], "mathtext.it": f"{fonts[0]}:italic", "mathtext.bf": f"{fonts[0]}:bold",
        # 线条与坐标轴(印刷尺度:pt)
        "lines.linewidth": 1.2,
        "lines.markersize": 3.5,
        "lines.markeredgewidth": 0.6,
        "axes.linewidth": 0.6,
        "axes.edgecolor": TEXT,
        "axes.labelcolor": TEXT,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.axisbelow": True,
        "axes.prop_cycle": cycler(color=COLORS),
        "axes.titleweight": "normal",
        "axes.labelpad": 2.5,
        "xtick.color": TEXT, "ytick.color": TEXT,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.pad": 2, "ytick.major.pad": 2,
        "grid.color": "#E3E3E3", "grid.linewidth": 0.5, "grid.linestyle": "-",
        # 图例
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "legend.borderaxespad": 0.3,
        "legend.labelspacing": 0.3,
        # 误差线
        "errorbar.capsize": 2,
        # 输出
        "figure.dpi": 150,
        "figure.constrained_layout.use": True,   # 自动排版,且保持图幅 = 期刊栏宽
        "figure.constrained_layout.h_pad": 0.02,
        "figure.constrained_layout.w_pad": 0.02,
        "savefig.dpi": 600,
        "savefig.bbox": None,                     # 不裁切,导出尺寸严格等于 figsize
        "savefig.pad_inches": 0.02,
        "savefig.transparent": False,
        "pdf.fonttype": 42,                 # 嵌入 TrueType,可编辑
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "image.cmap": "viridis",            # 顺序型默认色图(感知均匀、色盲友好)
    })
    return j


def figsize(journal: str = "nature", cols: float = 1, aspect: float = 0.75,
            height_mm: float | None = None) -> tuple[float, float]:
    """按期刊栏宽返回 (宽, 高) 英寸。aspect = 高/宽;也可直接给 height_mm。"""
    w = JOURNALS[journal]["width_mm"][cols]
    h = height_mm if height_mm is not None else w * aspect
    return (w * MM, h * MM)


def style_cycle(n: int):
    """返回 n 组 (颜色, marker, 线型),用于多条曲线的第二编码。超过 6 组请改用分面小图。"""
    if n > len(COLORS):
        raise ValueError(f"{n} 条曲线太多:超过 {len(COLORS)} 条请合并为'其他'或拆成小图(small multiples)")
    return list(zip(COLORS, MARKERS, LINESTYLES))[:n]


def panel_labels(axes, journal: str = "nature", x: float = -0.18, y: float = 1.04, start: str = "a"):
    """给多面板图加 a/b/c(Nature 加粗小写)或 (a)/(b)(IEEE、Elsevier)。"""
    j = JOURNALS[journal]
    axes = list(axes.flat) if hasattr(axes, "flat") else list(axes)
    for i, ax in enumerate(axes):
        letter = chr(ord(start) + i)
        letter = letter.upper() if j["panel_upper"] else letter
        ax.text(x, y, j["panel"].format(letter), transform=ax.transAxes,
                fontsize=j["font"] + 1, fontweight="bold", va="bottom", ha="left")


def save_fig(fig, name: str, outdir: str = "figures",
             formats=("pdf", "png", "tiff"), dpi: int = 600) -> list[str]:
    """导出投稿用文件:PDF(矢量,首选)、PNG/TIFF(600 dpi 位图,TIFF 用 LZW 无损压缩)。"""
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for fmt in formats:
        p = os.path.join(outdir, f"{name}.{fmt}")
        kw = {"dpi": dpi}
        if fmt in ("tif", "tiff"):
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(p, **kw)
        paths.append(p)
    return paths


def check_fonts(fig, journal: str = "nature") -> list[str]:
    """检查图中是否有小于期刊最小字号的文字,返回问题列表(空列表 = 通过)。"""
    min_pt = JOURNALS[journal]["min_pt"]
    issues = []
    for t in fig.findobj(mpl.text.Text):
        if t.get_text().strip() and t.get_visible() and t.get_fontsize() < min_pt - 1e-6:
            issues.append(f"'{t.get_text()[:20]}' 字号 {t.get_fontsize():.1f}pt < {min_pt}pt")
    return issues


def sig_bracket(ax, x1: float, x2: float, y: float, text: str = "*", h: float = 0.02):
    """在两组柱子之间加显著性括号(h 为相对 y 轴范围的高度)。"""
    span = ax.get_ylim()[1] - ax.get_ylim()[0]
    hh = h * span
    ax.plot([x1, x1, x2, x2], [y, y + hh, y + hh, y], lw=0.6, c=TEXT)
    ax.text((x1 + x2) / 2, y + hh, text, ha="center", va="bottom", fontsize=mpl.rcParams["font.size"])
