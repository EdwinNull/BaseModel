# -*- coding: utf-8 -*-
"""
《本周工作总结》v2 用的数据图（2026-11-07）。样式用 PPT/脚本/journal_style.py（与 G:/paper-research/figure-toolkit/ 同一份），
期刊规范取 thesis（中文）。图按放到幻灯片上的实际尺寸出图，字号是幻灯片上的真实字号，所以把字号从印刷用的 9 pt 调到 10–11 pt。

输出：PPT/素材/图_20261107/fig_*.pdf（矢量）、fig_*.png（600 dpi）。

数据都是聚合量：
- forest_mimic_ed_聚合.csv：服务器 logs/2026-11-03（补丁前）、logs/2026-11-04（补丁 1）、logs/2026-11-06（3b）的 per_run 与 summary
  按 W/tmp/weekly_forest.py 的口径汇总（点 = 各 seed 均值，区间 = 各 seed 区间端点的均值，flag_worse 取 summary）；
- 其余数字写在本脚本里，出处见各函数的注释。

运行（BaseModel 根目录）：python PPT/脚本/build_figures_20261107.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from journal_style import COLORS, GRAY, TEXT, check_fonts, panel_labels, save_fig, style_cycle, use_style  # noqa: E402

J = "thesis"
OUT = HERE.parent / "素材" / "图_20261107"
BLUE, VERM, GREEN = COLORS[0], COLORS[1], COLORS[2]


def setup():
    use_style(J)
    mpl.rcParams.update({
        "font.size": 12, "axes.labelsize": 12, "axes.titlesize": 12.5, "xtick.labelsize": 11, "ytick.labelsize": 11,
        "legend.fontsize": 11.5, "lines.linewidth": 1.5, "lines.markersize": 5.5, "axes.linewidth": 0.7,
        "xtick.major.width": 0.7, "ytick.major.width": 0.7, "axes.unicode_minus": True, "errorbar.capsize": 0,
    })


def finish(fig, name):
    issues = check_fonts(fig, J)
    paths = save_fig(fig, name, outdir=str(OUT), formats=("pdf", "png"))
    print(name, "字号检查", "通过" if not issues else issues, paths[-1])
    plt.close(fig)


def fig_context():
    """来源：导师讨论稿终版第一部分 §3–§4（上下文）；MC-MED 15 格、MIMIC-IV-ED 8 / 16 格见 TSFM 结果 v1 §1、v2 §1.2。"""
    rows = [("TimesFM 3.0", 15360, None, "约 15,360"), ("Chronos-2", 8192, 2048, "2,048–8,192"), ("Time-MoE", 4096, None, "≤4,096"),
            ("VisionTS", 4032, 1728, "1,728–4,032"), ("Sundial", 2880, None, "2,880"), ("Timer-XL", 2880, None, "2,880"),
            ("MIRA", 512, None, "≤512"), ("MIMIC-IV-ED 4 h", 16, None, "16 格（敏感性）"), ("MC-MED 15 min", 15, None, "15 格"),
            ("MIMIC-IV-ED 2 h", 8, None, "8 格（主分析）")]
    fig, ax = plt.subplots(figsize=(6.75, 4.95))
    y = np.arange(len(rows))[::-1]
    for yi, (name, hi, lo, lab) in zip(y, rows):
        ours = name.startswith("MI") and name != "MIRA" or name.startswith("MC")
        c = VERM if ours else BLUE
        ax.plot([1, hi], [yi, yi], color="#D9D9D9", lw=1.0, zorder=1)
        if lo:
            ax.plot([lo, hi], [yi, yi], color=c, lw=3.2, zorder=2, solid_capstyle="round")
        ax.plot(hi, yi, "o", color=c, ms=7, zorder=3)
        ax.text(hi * 1.28, yi, lab, va="center", ha="left", fontsize=11, color=TEXT)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xscale("log")
    ax.set_xlim(1, 130000)
    ax.set_xticks([1, 10, 100, 1000, 10000])
    ax.set_xticklabels(["1", "10", "100", "1,000", "10,000"])
    ax.minorticks_off()
    ax.set_xlabel("上下文长度（点或格，对数坐标）")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    finish(fig, "fig_context")


GROUP_ORDER = [("age", "18-64", "年龄 18–64"), ("age", "65-79", "年龄 65–79"), ("age", ">=80", "年龄 ≥80"), ("sex", "女", "女"), ("sex", "男", "男"),
               ("esi", "ESI 1-2", "ESI 1–2"), ("esi", "ESI 3-5", "ESI 3–5"), ("arrival", "自行到达", "自行到达"),
               ("arrival", "急救车/直升机送达", "急救车/直升机"), ("arrival", "其他/未知", "其他/未知"), ("dx_resp", "非呼吸系统主诊断", "非呼吸系统诊断"),
               ("dx_resp", "呼吸系统主诊断", "呼吸系统诊断"), ("density", "<=1", "vitalsign ≤1 次"), ("density", ">1", "vitalsign >1 次"),
               ("density_x_esi", "<=1 | ESI 1-2", "≤1 × ESI 1–2"), ("density_x_esi", "<=1 | ESI 3-5", "≤1 × ESI 3–5"),
               ("density_x_esi", ">1 | ESI 1-2", ">1 × ESI 1–2"), ("density_x_esi", ">1 | ESI 3-5", ">1 × ESI 3–5")]
MODELS = [("lr", "LR（1 次）"), ("lgbm", "LightGBM"), ("brits", "BRITS"), ("mtand", "mTAND"), ("raindrop", "Raindrop")]


def fig_forest():
    d = pd.read_csv(OUT / "forest_mimic_ed_聚合.csv")
    fig, axs = plt.subplots(1, 5, figsize=(12.23, 4.62), sharey=True, sharex=True)
    n = len(GROUP_ORDER)
    ys = n - 1 - np.arange(n)
    versions = [("before", GRAY, "o", 0.17), ("p3b", BLUE, "D", -0.17)]
    breaks = [i for i in range(1, n) if GROUP_ORDER[i][0] != GROUP_ORDER[i - 1][0]]
    for ax, (m, mname) in zip(axs, MODELS):
        ax.axhspan(ys[14] - 0.5, ys[14] + 0.5, color="#FBEBD9", lw=0, zorder=0)
        for b in breaks:
            ax.axhline(ys[b] + 0.5, color="#E3E3E3", lw=0.6, zorder=0)
        ax.axvline(0, color="#9A9A9A", lw=0.8, zorder=1)
        for tag, c, mk, off in versions:
            sub = d[(d["version"] == tag) & (d["model"] == m)]
            for (axis, g, _), y in zip(GROUP_ORDER, ys):
                r = sub[(sub["axis"] == axis) & (sub["group"] == g)]
                if r.empty:
                    continue
                r = r.iloc[0]
                ax.plot([r["lo"], r["hi"]], [y + off, y + off], color=c, lw=0.9, zorder=2)
                ax.plot(r["d"], y + off, mk, ms=3.9, mec=c, mew=0.8, mfc=c if bool(r["flag_worse"]) else "white", zorder=3)
        ax.set_title(mname, fontsize=12)
        ax.set_xlim(-0.27, 0.10)
        ax.set_xticks([-0.2, -0.1, 0, 0.1], ["−0.2", "−0.1", "0", "0.1"])
        ax.set_ylim(-0.6, n - 0.4)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    base = d[(d["version"] == "before") & (d["model"] == "lgbm")]
    labels = []
    for axis, g, lab in GROUP_ORDER:
        r = base[(base["axis"] == axis) & (base["group"] == g)].iloc[0]
        labels.append(f"{lab}  {int(r['n']):,}/{int(r['ev']):,}")
    axs[0].set_yticks(ys, labels, fontsize=10.5)
    fig.supxlabel("子集减补集的 AUROC", fontsize=12)
    h = [Line2D([], [], color=GRAY, marker="o", ms=5, lw=0.9, label="补丁前"), Line2D([], [], color=BLUE, marker="D", ms=4.6, lw=0.9, label="3b 输入"),
         Line2D([], [], color=TEXT, marker="o", ms=5, lw=0, mfc=TEXT, label="实心：过半数 seed 区间上限 <0"),
         Line2D([], [], color=TEXT, marker="o", ms=5, lw=0, mfc="white", label="空心：未达判据")]
    fig.legend(handles=h, loc="outside upper center", ncol=4, columnspacing=2.2)
    finish(fig, "fig_forest")


def fig_patches():
    """来源：周报 §2；补丁 3 结果 §2.1、§3.1。总体 AUROC，发现集。"""
    steps = ["补丁前", "补丁 1", "3a", "3b"]
    names = ["LR", "LightGBM", "BRITS", "mTAND", "Raindrop"]
    mc = [[0.705, 0.709, 0.725, 0.729], [0.734, 0.740, 0.760, 0.772], [0.730, 0.735, 0.748, 0.747], [0.690, 0.700, 0.731, 0.741], [0.708, 0.713, 0.731, 0.736]]
    mi = [[0.846, 0.893, 0.917, 0.924], [0.877, 0.905, 0.928, 0.937], [0.879, 0.904, 0.923, 0.928], [0.862, 0.892, 0.919, 0.928], [0.874, 0.903, 0.925, 0.932]]
    fig, axs = plt.subplots(1, 2, figsize=(12.23, 2.95))
    styles = style_cycle(5)
    for ax, data, title, lo in zip(axs, (mc, mi), ("MC-MED（8,085 次，999 个阳性）", "MIMIC-IV-ED（38,242 次，2,072 个阳性）"), (0.68, 0.84)):
        for vals, name, (c, mk, ls) in zip(data, names, styles):
            ax.plot(steps, vals, color=c, marker=mk, ls=ls, label=name)
        ax.set_ylim(lo, lo + 0.10)
        ax.set_yticks(np.arange(lo, lo + 0.101, 0.02))
        ax.set_ylabel("总体 AUROC")
        ax.set_title(title, loc="left")
        ax.set_xlim(-0.15, 3.42)
        last = sorted(v[-1] for v in data)
        ax.annotate(f"{last[-1]:.3f}", (3, last[-1]), xytext=(7, 0), textcoords="offset points", va="center", fontsize=11)
        ax.annotate(f"{last[0]:.3f}", (3, last[0]), xytext=(7, -3), textcoords="offset points", va="center", fontsize=11)
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside right center", handlelength=2.6)
    finish(fig, "fig_patches")


def fig_ablation():
    """来源：补丁 3 后续 §2.3（LightGBM，MIMIC-IV-ED，交叉拟合）；补丁 3 结果 §2.3、§3.3（LightGBM，发现集）。"""
    blocks = ["窗口生命体征", "t0 前化验", "主诉", "年龄与 ESI", "到达方式"]
    overall = [0.012, 0.009, 0.006, 0.005, 0.002]
    sparse = [0.015, 0.028, 0.017, 0.004, 0.008]
    fig, axs = plt.subplots(1, 2, figsize=(12.23, 3.72), width_ratios=[1, 1.15])
    ax = axs[0]
    y = np.arange(len(blocks))[::-1]
    ax.barh(y + 0.19, overall, height=0.34, color=GRAY, label="总体")
    ax.barh(y - 0.19, sparse, height=0.34, color=VERM, label="≤1 × ESI 1–2")
    for yi, a, b in zip(y, overall, sparse):
        ax.text(a + 0.0005, yi + 0.19, f"+{a:.3f}", va="center", fontsize=11)
        ax.text(b + 0.0005, yi - 0.19, f"+{b:.3f}", va="center", fontsize=11)
    ax.set_yticks(y, blocks)
    ax.set_xlim(0, 0.034)
    ax.set_xticks([0, 0.01, 0.02, 0.03], ["0", "0.01", "0.02", "0.03"])
    ax.set_xlabel("3b 去掉该块后 AUROC 的下降量")
    ax.set_title("MIMIC-IV-ED，LightGBM，交叉拟合", loc="left")
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="lower right")

    ax = axs[1]
    rows = [("≤1 × ESI 1–2", -0.178, -0.113, -0.093), ("≤1 × ESI 3–5", -0.053, -0.063, -0.071), ("≥75 岁", -0.042, -0.041, -0.037),
            ("急救车/直升机", -0.036, -0.031, -0.023), ("MC-MED ≤15 个值", -0.056, -0.034, -0.025)]
    y = np.arange(len(rows))[::-1]
    ax.axvline(0, color="#9A9A9A", lw=0.8)
    for yi, (name, a, b, c) in zip(y, rows):
        ax.plot([a, c], [yi, yi], color="#BDBDBD", lw=1.4, zorder=1)
        ax.plot(a, yi, "o", ms=7, color=GRAY, zorder=3)
        ax.plot(b, yi, "s", ms=6, mfc="white", mec=BLUE, mew=1.1, zorder=3)
        ax.plot(c, yi, "D", ms=6, color=BLUE, zorder=3)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xlim(-0.2, 0.01)
    ax.set_xticks([-0.2, -0.15, -0.1, -0.05, 0], ["−0.20", "−0.15", "−0.10", "−0.05", "0"])
    ax.set_xlabel("子集减补集的 AUROC（LightGBM，发现集）")
    ax.set_title("子集差距随输入的变化", loc="left")
    ax.tick_params(axis="y", length=0)
    h = [Line2D([], [], color=GRAY, marker="o", ms=6, lw=0, label="补丁 1"), Line2D([], [], color=BLUE, marker="s", ms=5.5, lw=0, mfc="white", label="3a"),
         Line2D([], [], color=BLUE, marker="D", ms=5.5, lw=0, label="3b")]
    ax.legend(handles=h, loc="lower left", ncol=1)
    panel_labels(axs, J, x=-0.2, y=1.03)
    finish(fig, "fig_ablation")


def fig_zs():
    """来源：TSFM v1 结果 §4（R-max、监督参照）；v2 结果 §2.1（S-max 及区间、LOCF、Context-max）。"""
    order = ["Chronos-2", "MIRA†", "Timer-XL", "Sundial", "LightGTS", "Time-MoE‡", "VisionTS", "TimesFM"]
    smax = {"MC-MED": {"Chronos-2": (0.669, 0.641, 0.700), "MIRA†": (0.668, 0.640, 0.697), "Sundial": (0.667, 0.638, 0.697), "Time-MoE‡": (0.664, 0.635, 0.694),
                       "VisionTS": (0.663, 0.634, 0.694), "LightGTS": (0.659, 0.631, 0.689), "Timer-XL": (0.659, 0.630, 0.689), "TimesFM": (0.635, 0.606, 0.665)},
            "D103": {"Chronos-2": (0.729, 0.716, 0.742), "MIRA†": (0.726, 0.712, 0.739), "Timer-XL": (0.724, 0.710, 0.737), "Sundial": (0.723, 0.710, 0.735),
                     "LightGTS": (0.721, 0.708, 0.734), "Time-MoE‡": (0.718, 0.705, 0.731), "VisionTS": (0.718, 0.705, 0.731), "TimesFM": (0.716, 0.703, 0.729)}}
    rmax = {"MC-MED": {"Chronos-2": 0.501, "MIRA†": 0.504, "Timer-XL": 0.500, "Sundial": 0.500, "LightGTS": 0.500, "Time-MoE‡": 0.500, "VisionTS": 0.500, "TimesFM": 0.521},
            "D103": {"Chronos-2": 0.631, "MIRA†": 0.631, "Timer-XL": 0.628, "Sundial": 0.626, "LightGTS": 0.620, "Time-MoE‡": 0.618, "VisionTS": 0.617, "TimesFM": 0.638}}
    refs = {"MC-MED": {"locf": (0.638, 0.609, 0.668), "ctx": (0.691, 0.663, 0.721), "sup": (0.705, 0.754), "xlim": (0.47, 0.79), "ctx_shift": 0.010, "sup_shift": 0.020},
            "D103": {"locf": (0.687, 0.673, 0.700), "ctx": (0.755, 0.742, 0.767), "sup": (0.845, 0.879), "xlim": (0.58, 0.90)}}
    titles = {"MC-MED": "MC-MED decomp_60（3,434 次，427 个阳性）", "D103": "MIMIC-IV-ED D103，2 h（37,806 次，2,039 个阳性）"}
    fig, axs = plt.subplots(1, 2, figsize=(12.23, 3.68), sharey=True)
    y = np.arange(len(order))[::-1]
    for ax, key in zip(axs, ("MC-MED", "D103")):
        r = refs[key]
        ax.axvspan(r["sup"][0], r["sup"][1], color=GREEN, alpha=0.16, lw=0, zorder=0)
        ax.axvspan(r["ctx"][1], r["ctx"][2], color=VERM, alpha=0.13, lw=0, zorder=0)
        ax.axvline(r["ctx"][0], color=VERM, lw=1.3, zorder=1)
        ax.axvspan(r["locf"][1], r["locf"][2], color=GRAY, alpha=0.13, lw=0, zorder=0)
        ax.axvline(r["locf"][0], color=GRAY, lw=1.3, ls="--", zorder=1)
        for yi, m in zip(y, order):
            p, lo, hi = smax[key][m]
            ax.plot([lo, hi], [yi, yi], color=BLUE, lw=1.2, zorder=2)
            ax.plot(p, yi, "o", color=BLUE, ms=5.5, zorder=3)
            ax.plot(rmax[key][m], yi, "D", ms=5, mfc="white", mec="#555555", mew=0.9, zorder=3)
        ax.set_xlim(*r["xlim"])
        ax.set_ylim(-0.6, len(order) - 0.1)
        ax.set_xlabel("AUROC")
        ax.set_title(titles[key], loc="left")
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        top = len(order) - 0.42
        ax.text(r["locf"][0], top, "LOCF", ha="center", va="bottom", fontsize=10.5, color=TEXT, bbox=dict(fc="white", ec="none", pad=0.6))
        ax.text(r["ctx"][0] - r.get("ctx_shift", 0), top, "Context-max", ha="center", va="bottom", fontsize=10.5, color=TEXT, bbox=dict(fc="white", ec="none", pad=0.6))
        ax.text(sum(r["sup"]) / 2 + r.get("sup_shift", 0), top, "监督模型", ha="center", va="bottom", fontsize=10.5, color=TEXT, bbox=dict(fc="white", ec="none", pad=0.6))
    axs[0].set_yticks(y, order)
    h = [Line2D([], [], color=BLUE, marker="o", ms=5.5, lw=1.2, label="S-max（不截断）及 95% 区间"),
         Line2D([], [], color="#555555", marker="D", ms=5, lw=0, mfc="white", label="R-max（截断）")]
    fig.legend(handles=h, loc="outside lower center", ncol=2)
    finish(fig, "fig_zs")


def fig_jline():
    """来源：J2 至 J4 结果 §J2（Z1、Z2，英文状态，主分析）。"""
    rows = [("O1 主口径，GD", "191（23）", (0.579, 0.443, 0.707), (0.602, 0.481, 0.728)), ("O1 主口径，GAM", "84（10）", (0.711, 0.494, 0.884), (0.693, 0.503, 0.850)),
            ("O1 新开始氧疗，GD", "73（27）", (0.664, 0.528, 0.785), (0.718, 0.580, 0.839)), ("O1 新开始氧疗，GAM", "69（14）", (0.635, 0.445, 0.813), (0.564, 0.387, 0.738)),
            ("O1 生理类，GD", "271（61）", (0.704, 0.634, 0.774), (0.766, 0.700, 0.827)), ("O1 生理类，GAM", "115（31）", (0.558, 0.428, 0.680), (0.564, 0.433, 0.695)),
            ("O2 主口径，GD", "210（20）", (0.582, 0.445, 0.708), (0.579, 0.429, 0.728))]
    fig, ax = plt.subplots(figsize=(7.45, 4.92))
    y = np.arange(len(rows))[::-1]
    ax.axvline(0.5, color="#9A9A9A", lw=1.0, ls="--", zorder=1)
    for yi, (_, _, z1, z2) in zip(y, rows):
        for vals, c, mk, off in ((z1, BLUE, "o", 0.16), (z2, VERM, "D", -0.16)):
            ax.plot(vals[1:], [yi + off] * 2, color=c, lw=1.3, zorder=2)
            ax.plot(vals[0], yi + off, mk, color=c, ms=5.5, zorder=3)
    ax.set_yticks(y, [f"{r[0]}  {r[1]}" for r in rows])
    ax.set_xlim(0.35, 0.92)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    ax.set_xlabel("AUROC 及 95% 区间（虚线为 0.5）")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    h = [Line2D([], [], color=BLUE, marker="o", ms=5.5, lw=1.3, label="Z1 OpenJev-Flash-9B"), Line2D([], [], color=VERM, marker="D", ms=5, lw=1.3, label="Z2 Qwen3.5-9B 基座")]
    fig.legend(handles=h, loc="outside upper center", ncol=2)
    finish(fig, "fig_jline")


def fig_slope():
    """来源：J6 结果、J6b 结果 §1（发现集 8,085 次；Z1、Z2、LR、LightGBM 的 AUROC 及 95% CI）。"""
    series = [("Z1", (0.691, 0.671, 0.711), (0.661, 0.647, 0.675), BLUE, "o", "-"), ("Z2", (0.662, 0.642, 0.682), (0.680, 0.666, 0.693), VERM, "s", "-"),
              ("LR", (0.702, 0.683, 0.721), (0.733, 0.721, 0.746), GRAY, "^", "--"), ("LightGBM", (0.731, 0.711, 0.749), (0.742, 0.729, 0.755), "#444444", "D", "--")]
    fig, ax = plt.subplots(figsize=(4.7, 3.62))
    for i, (name, a, b, c, mk, ls) in enumerate(series):
        dx = (i - 1.5) * 0.012
        ax.plot([0 + dx, 1 + dx], [a[0], b[0]], color=c, marker=mk, ls=ls, zorder=3)
        ax.plot([0 + dx] * 2, a[1:], color=c, lw=0.9, zorder=2)
        ax.plot([1 + dx] * 2, b[1:], color=c, lw=0.9, zorder=2)
    for name, y in (("Z1", 0.661), ("Z2", 0.680), ("LR", 0.731), ("LightGBM", 0.746)):
        ax.text(1.07, y, name, va="center", fontsize=11.5)
    ax.set_xticks([0, 1], ["decomp_60", "收住院"])
    ax.set_xlim(-0.12, 1.42)
    ax.set_ylim(0.63, 0.77)
    ax.set_yticks([0.64, 0.68, 0.72, 0.76])
    ax.set_ylabel("AUROC")
    finish(fig, "fig_slope")


if __name__ == "__main__":
    setup()
    fig_context()
    fig_forest()
    fig_patches()
    fig_ablation()
    fig_zs()
    fig_jline()
    fig_slope()
