"""前瞻要收多少例：二分类结局预测模型开发的最小样本量情景（数据集验收计划 20261029 第 8 项）。

按 Riley 2020（BMJ 2020;368:m441）与 Riley 2019（Stat Med 38:1276，doi:10.1002/sim.7992）的三条准则，取其中最大的：
  1. 过拟合小：预期收缩 ≥0.9；
  2. 表观与校正后的 Nagelkerke R² 相差 ≤0.05；
  3. 总体结局率的 95% 置信区间半宽 ≤0.05。
公式与取整照 R 包 pmsampsize 1.1.3（pmsampsize_bin.R）。预期的 Cox-Snell R² 有两种来法：
  - 从 C 统计量换算（Riley 2021，Stat Med 40:859，doi:10.1002/sim.8806）：事件的线性预测值 ~ N(μ, 1)、非事件 ~ N(0, 1)，
    μ = √2 Φ⁻¹(C)。pmsampsize 用 100 万人模拟，这里按同一个模型做数值积分，结果不依赖随机种子；
  - 没有可靠的 C 时取保守值 Nagelkerke R² = 0.15。

不读任何病例数据，结局率、C 统计量、候选参数数都是假设，见报告“假设的出处”。只用标准库。

运行（仓库根目录）：
  python scripts/sample_size/pmsampsize_scenarios.py --out docs/实验/前瞻样本量情景_20261031.md
"""
from __future__ import annotations

import argparse
from math import ceil, exp, log, log1p, sqrt
from pathlib import Path
from statistics import NormalDist

RATES = (0.05, 0.10, 0.15, 0.20)         # O3 结局率
CSTATS = (0.70, 0.75, 0.80)
PARAMS = (10, 20, 30)                    # 候选参数数
BASE = {"rate": 0.10, "c": 0.75, "params": 20}
LOSS = 0.10                              # 前瞻随访失访率的假设，只用来折算入组数
NORMAL = NormalDist()


def max_r2(rate: float) -> float:
    """结局率决定的 Cox-Snell R² 上限。"""
    return 1 - (rate ** rate * (1 - rate) ** (1 - rate)) ** 2


def r2_from_c(c: float, rate: float, steps: int = 20000) -> float:
    """C 统计量 + 结局率 → Cox-Snell R²。两个等方差正态下，真实模型就是 logit p = α + μx，直接积分对数似然。"""
    mu = sqrt(2) * NORMAL.inv_cdf(c)
    alpha = log(rate / (1 - rate)) - mu * mu / 2
    lo, hi = -9.0, mu + 9.0
    h = (hi - lo) / steps
    ll = 0.0
    for i in range(steps + 1):
        x = lo + i * h
        lp = alpha + mu * x
        ev, non = -log1p(exp(-lp)), -log1p(exp(lp))
        w = h / 2 if i in (0, steps) else h
        ll += w * (rate * NORMAL.pdf(x - mu) * ev + (1 - rate) * NORMAL.pdf(x) * non)
    null = rate * log(rate) + (1 - rate) * log(1 - rate)
    return 1 - exp(-2 * (ll - null))


def sample_size(r2: float, params: int, rate: float, shrinkage: float = 0.9) -> dict:
    """三条准则各要多少人，取最大的。"""
    mx = max_r2(rate)
    if r2 >= mx:
        raise ValueError(f"R² {r2} 超过这个结局率下的上限 {mx:.3f}")
    s2 = r2 / (r2 + 0.05 * mx)
    n1 = ceil(params / ((shrinkage - 1) * log(1 - r2 / shrinkage)))
    n2 = ceil(params / ((s2 - 1) * log(1 - r2 / s2)))
    n3 = ceil((1.96 / 0.05) ** 2 * rate * (1 - rate))
    n = max(n1, n2, n3)
    return {"n1": n1, "n2": n2, "n3": n3, "n": n, "events": n * rate, "epp": n * rate / params, "r2": r2, "max_r2": mx, "nagelkerke": r2 / mx,
            "shrinkage": max(shrinkage, s2)}


def from_c(c: float, params: int, rate: float) -> dict:
    return sample_size(round(r2_from_c(c, rate), 4), params, rate)        # 取整同 pmsampsize


def conservative(params: int, rate: float) -> dict:
    return sample_size(round(0.15 * max_r2(rate), 3), params, rate)


def _cell(d: dict) -> str:
    return f"{d['n']}（{d['events']:.0f}）"


def _pct(x: float) -> str:
    return f"{x:.0%}"


def report() -> str:
    b = from_c(BASE["c"], BASE["params"], BASE["rate"])
    enrol = ceil(b["n"] / (1 - LOSS))
    worst, best = from_c(CSTATS[0], PARAMS[-1], RATES[0]), from_c(CSTATS[-1], PARAMS[0], RATES[-1])
    L = ["# 前瞻要收多少例：样本量情景（2026-10-31）", "",
         "只含假设，没有用任何病例数据。由 `scripts/sample_size/pmsampsize_scenarios.py` 生成；对应数据集验收计划（20261029）第 8 项。", "",
         "## 结论", "",
         f"- **建议的规划基准**：结局率 {_pct(BASE['rate'])}、C 统计量 {BASE['c']}、{BASE['params']} 个候选参数，至少要 **{b['n']} 例**可分析的病例"
         f"（约 {b['events']:.0f} 个事件）；按 {_pct(LOSS)} 失访折算，要入组约 **{enrol} 例**。基准是 Claude 提的，属 A 档，要研究者定。",
         f"- **范围很宽**：这张表从 {best['n']} 例到 {worst['n']} 例。三个假设的影响都大：候选参数从 10 到 30，例数翻 3 倍（成正比）；"
         f"结局率从 20% 到 5%，翻约 3 倍；C 从 0.80 到 0.70，翻约 2.5 倍。",
         "- **最能自己控制的是候选参数数**：结局率和 C 只能估，参数数可以在前瞻表单定稿时就压下来，少一半参数就少一半病例。",
         "- **这些都是开发模型的下限**，不含外部验证，也没有考虑中心之间的差异。", "",
         "## 怎么算", "",
         "二分类结局按三条准则取最大值（Riley 2020）：",
         "1. 过拟合小：预期收缩 ≥0.9；", "2. 表观与校正后的 Nagelkerke R² 相差 ≤0.05；", "3. 总体结局率的 95% 置信区间半宽 ≤0.05。", "",
         "公式与取整照 R 包 pmsampsize 1.1.3。预期的 R² 从 C 统计量换算（Riley 2021）；没有可靠的 C 时用保守值 Nagelkerke R² = 0.15。", "",
         "**候选参数数不是变量数**：连续变量算 1 个（用样条要多算），k 类的分类变量算 k − 1 个。所有进入筛选的候选都要算，不是最后留下的。", "",
         "## 情景表", "", "每格是“最少例数（事件数）”。", ""]
    for p in PARAMS:
        L += [f"### {p} 个候选参数", "", "| O3 结局率 | " + " | ".join(f"C = {c}" for c in CSTATS) + " | 保守（Nagelkerke 0.15） |", "|---|" + "---:|" * (len(CSTATS) + 1)]
        for r in RATES:
            L.append(f"| {_pct(r)} | " + " | ".join(_cell(from_c(c, p, r)) for c in CSTATS) + f" | {_cell(conservative(p, r))} |")
        L.append("")
    L += ["## 规划基准的细节", "", "| 准则 | 例数 |", "|---|---:|", f"| 1 过拟合小 | {b['n1']} |", f"| 2 R² 差值小 | {b['n2']} |", f"| 3 结局率精确 | {b['n3']} |",
          f"| **取最大** | **{b['n']}** |", "",
          f"- 换算出的 Cox-Snell R² {b['r2']:.4f}（这个结局率下的上限 {b['max_r2']:.3f}，Nagelkerke {b['nagelkerke']:.3f}）；",
          f"- 收缩 {b['shrinkage']:.3f}；每个参数约 {b['epp']:.1f} 个事件。", "",
          "## 假设的出处", "", "| 假设 | 取值 | 依据 | 可靠程度 |", "|---|---|---|---|",
          "| O3 结局率 | 5%–20% | 计划第 8 项定的范围。INSIGHT FLU 002 门诊 14 天进展 5.1%（全年龄、H1N1pdm，基于摘要），可作下限 | 老年人的实际结局率还不知道：GAM 门急诊 1138 / 1166 次随访未知，算不出来 |",
          "| C 统计量 | 0.70–0.80 | 本项目 A4：GD 上逻辑回归 AUROC 0.65–0.69（住院结局、用公开数据训练）；Xiu 2026 验证集 0.819（单中心、随机切分，基于摘要） | 没有老年门急诊 O3 的直接数据。前者偏低，后者内部验证、偏乐观，所以取中间 |",
          "| 候选参数数 | 10 / 20 / 30 | Gao 2026 系统综述的主要危险因素（年龄、心血管病、免疫抑制、慢性呼吸病、神经系统病，基于摘要）约 5 个，再加体征、检验、起病时长 | 要等前瞻表单定稿后按实际条目数 |",
          f"| 失访率 | {_pct(LOSS)} | Claude 的假设，只用来把最少例数折算成入组数 | 没有依据，要按实际随访能力改 |", "",
          "## 没算进去的", "",
          "- **外部验证**：要另算样本量，这里的例数只够开发。",
          "- **中心效应**：公式按单一人群算；多中心合并时，中心差异大就要更多。",
          "- **缺失数据**：前瞻表单的缺失没有折算。",
          "- **J 线标签预算曲线（J3c）**：计划要和它合成一份，但 J 线还没开始，等 J3c 出结果再合。", "",
          "## 校验", "",
          "- 公式逐行对照 pmsampsize 1.1.3 的源码；",
          "- pmsampsize 文档的例子（R² 0.288、24 个参数、结局率 17.4%）在这里得到 662 例，是按源码移植算出来的，没有在 R 里跑过（本机没有 R）；",
          "- 文档用 C = 0.89 配同一个结局率作例子，这里换算出 R² ≈ 0.288，两个例子对得上；",
          "- C 到 R² 的积分与蒙特卡洛模拟一致（见测试）。", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="前瞻样本量情景：只含假设，不读病例数据")
    ap.add_argument("--out", type=Path, default=Path("docs/实验/前瞻样本量情景_20261031.md"))
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(report(), encoding="utf-8", newline="\n")
    print(f"已写 {a.out}")


if __name__ == "__main__":
    main()
