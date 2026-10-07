# -*- coding: utf-8 -*-
"""玩具模拟：组内多样本强化学习奖励的有限组大小偏差（纯合成数据，不涉及任何患者数据）。

目的：核对两个推断，再决定是否写进调研报告。
  A. 连续目标：DAR（arXiv 2605.20740v2 式 5–6）用 V 统计量形式的经验 CRPS（成对项除以 2K^2）
     做留一贡献。推导：在高斯真值 N(0,1)、高斯策略 N(mu, s^2) 下，其总体最优 s = sqrt(a/(1-a))，
     a = (K-1)^2 / (2K^2)；K=8 时 s≈0.79，K=12 时 s≈0.85（80% 区间实际覆盖约 0.69 / 0.72）。
     公平（U 统计量，成对项除以 2K(K-1)）版本应收敛到 s≈1。
  B. 二元事件：策略以概率 q 生成"事件"，真值 y~Bern(p)。
     - 逐样本匹配奖励 1[e_i=y]（ETHOS-RL，arXiv 2609.12277 的形式）：期望奖励关于 q 线性，最优 q∈{0,1}；
     - 经验 Brier（样本频率的 Brier，V 统计量类）留一贡献：最优 q=(2Kp-1)/(2(K-1))，p=0.1、K=8 时约 0.043；
     - 公平 Brier（Ferro 2014）或"留一基线"无偏估计：最优 q=p。

策略梯度用得分函数（REINFORCE）估计，与 basemodel/experiments/reward_bench/grpo_tsfm.py 的做法一致。
"""
from __future__ import annotations

import json
import sys

import numpy as np


# ---------------------------------------------------------------------------
# A. 连续目标：高斯策略
# ---------------------------------------------------------------------------

def crps_v(x, y):
    """V 统计量形式的经验 CRPS（越小越好），x: (M, K)，y: (M,)。成对项除以 2K^2（含对角线 0）。"""
    K = x.shape[1]
    t1 = np.abs(x - y[:, None]).mean(axis=1)
    pair = np.abs(x[:, :, None] - x[:, None, :]).sum(axis=(1, 2))
    return t1 - pair / (2.0 * K * K)


def crps_u(x, y):
    """U 统计量形式（公平）的经验 CRPS：成对项除以 2K(K-1)。"""
    K = x.shape[1]
    t1 = np.abs(x - y[:, None]).mean(axis=1)
    pair = np.abs(x[:, :, None] - x[:, None, :]).sum(axis=(1, 2))
    return t1 - pair / (2.0 * K * (K - 1))


def loo_contribution(x, y, score):
    """DAR 式留一贡献：c_k = 得分(去掉 k) - 得分(全部)，得分越小越好，所以 c_k 越大表示样本 k 越有用。
    返回 (M, K)。"""
    M, K = x.shape
    full = score(x, y)
    c = np.empty((M, K))
    for k in range(K):
        rest = np.delete(x, k, axis=1)
        c[:, k] = score(rest, y) - full
    return c


def fair_loo_baseline(x, y):
    """项目 R-f 的估计（rewards.energy_loo_advantages 的一维向量化版）：
    误差项减去其余样本误差均值；成对项系数 1，再减去"不含样本 i 的样本对"的平均距离。"""
    M, K = x.shape
    d = np.abs(x - y[:, None])
    P = np.abs(x[:, :, None] - x[:, None, :])
    a_err = -d + (d.sum(axis=1, keepdims=True) - d) / (K - 1)
    spread = P.sum(axis=2) / (K - 1)
    pairs_wo = (P.sum(axis=(1, 2))[:, None] / 2.0 - P.sum(axis=2)) / ((K - 1) * (K - 2) / 2.0)
    return a_err + (spread - pairs_wo)


def grpo_norm(a):
    """GRPO 组内标准化：减组均值，再除以组内标准差。"""
    a = a - a.mean(axis=1, keepdims=True)
    return a / (a.std(axis=1, keepdims=True) + 1e-6)


def run_gauss(scheme: str, K: int, steps: int = 6000, M: int = 512, lr: float = 0.02, seed: int = 0):
    """返回收敛后的 s（取最后 1/3 步的均值）。真值 y~N(0,1)，策略 N(mu, s^2)，初始 s=0.3。"""
    rng = np.random.default_rng(seed)
    mu, rho = 0.5, np.log(0.3)
    m_mu = m_rho = v_mu = v_rho = 0.0
    b1, b2 = 0.9, 0.999
    hist = []
    for t in range(1, steps + 1):
        s = np.exp(rho)
        y = rng.standard_normal(M)
        eps = rng.standard_normal((M, K))
        x = mu + s * eps
        if scheme == "fair_loo":
            A = fair_loo_baseline(x, y)
        elif scheme == "dar_v_raw":
            A = loo_contribution(x, y, crps_v)
        elif scheme == "dar_v_grpo":
            A = grpo_norm(loo_contribution(x, y, crps_v))
        elif scheme == "dar_u_raw":
            A = loo_contribution(x, y, crps_u)
        elif scheme == "dar_u_grpo":
            A = grpo_norm(loo_contribution(x, y, crps_u))
        else:
            raise ValueError(scheme)
        # 得分函数：d log p / d mu = eps/s；d log p / d rho = eps^2 - 1
        g_mu = float(np.mean(A * eps / s))
        g_rho = float(np.mean(A * (eps ** 2 - 1.0)))
        # Adam（梯度上升）
        m_mu = b1 * m_mu + (1 - b1) * g_mu; v_mu = b2 * v_mu + (1 - b2) * g_mu ** 2
        m_rho = b1 * m_rho + (1 - b1) * g_rho; v_rho = b2 * v_rho + (1 - b2) * g_rho ** 2
        mh_mu, vh_mu = m_mu / (1 - b1 ** t), v_mu / (1 - b2 ** t)
        mh_rho, vh_rho = m_rho / (1 - b1 ** t), v_rho / (1 - b2 ** t)
        mu += lr * mh_mu / (np.sqrt(vh_mu) + 1e-8)
        rho += lr * mh_rho / (np.sqrt(vh_rho) + 1e-8)
        if t > steps * 2 // 3:
            hist.append(np.exp(rho))
    return float(np.mean(hist)), float(mu)


def theory_s(K: int) -> float:
    a = (K - 1) ** 2 / (2.0 * K * K)
    return float(np.sqrt(a / (1 - a)))


def cov80(s: float) -> float:
    """策略 N(0, s^2) 的 80% 中心区间对真值 N(0,1) 的实际覆盖率。"""
    from math import erf, sqrt
    z = 1.2815515655 * s
    return erf(z / sqrt(2.0))


# ---------------------------------------------------------------------------
# B. 二元事件：伯努利策略
# ---------------------------------------------------------------------------

def run_bern(scheme: str, K: int, p: float = 0.1, steps: int = 6000, M: int = 1024, lr: float = 0.02,
             seed: int = 0):
    """返回收敛后的 q（最后 1/3 步均值）。策略 logit theta，初始 q=0.3。"""
    rng = np.random.default_rng(seed)
    theta = np.log(0.3 / 0.7)
    m = v = 0.0
    b1, b2 = 0.9, 0.999
    hist = []
    for t in range(1, steps + 1):
        q = 1.0 / (1.0 + np.exp(-theta))
        y = (rng.random(M) < p).astype(float)
        e = (rng.random((M, K)) < q).astype(float)
        qhat = e.mean(axis=1, keepdims=True)
        q_wo = (e.sum(axis=1, keepdims=True) - e) / (K - 1)            # 去掉自身后的频率
        if scheme == "match_grpo":                                      # ETHOS-RL 式：逐样本匹配 + GRPO
            A = grpo_norm((e == y[:, None]).astype(float))
        elif scheme == "match_rloo":                                    # 逐样本匹配 + 留一基线（无标准化）
            r = (e == y[:, None]).astype(float)
            A = r - (r.sum(axis=1, keepdims=True) - r) / (K - 1)
        elif scheme == "brier_loo_baseline":                            # 无偏：-2(q_-i - y)(e_i - q_-i)
            A = -2.0 * (q_wo - y[:, None]) * (e - q_wo)
        elif scheme == "brier_dar_v":                                   # 频率 Brier 的留一贡献（V 统计量类）
            full = (qhat - y[:, None]) ** 2
            A = (q_wo - y[:, None]) ** 2 - full
        elif scheme == "brier_dar_fair":                                # 公平 Brier（Ferro 2014）的留一贡献
            def fair(qq, n):
                return (qq - y[:, None]) ** 2 - qq * (1 - qq) / (n - 1)
            A = fair(q_wo, K - 1) - fair(qhat, K)
        else:
            raise ValueError(scheme)
        g = float(np.mean(A * (e - q)))                                 # d log p(e) / d theta = e - q
        m = b1 * m + (1 - b1) * g; v = b2 * v + (1 - b2) * g ** 2
        theta += lr * (m / (1 - b1 ** t)) / (np.sqrt(v / (1 - b2 ** t)) + 1e-8)
        theta = float(np.clip(theta, -12, 12))
        if t > steps * 2 // 3:
            hist.append(1.0 / (1.0 + np.exp(-theta)))
    return float(np.mean(hist))


def main():
    out = {"gauss": [], "bern": []}
    for K in (8, 12):
        for scheme in ("fair_loo", "dar_v_raw", "dar_v_grpo", "dar_u_raw", "dar_u_grpo"):
            ss = [run_gauss(scheme, K, seed=s)[0] for s in range(3)]
            s_mean = float(np.mean(ss))
            row = {"K": K, "scheme": scheme, "s_mean": round(s_mean, 3), "s_seeds": [round(v, 3) for v in ss],
                   "cov80_implied": round(cov80(s_mean), 3)}
            out["gauss"].append(row)
            print("GAUSS", row, flush=True)
        print("GAUSS theory V-stat K=%d: s=%.3f cov80=%.3f" % (K, theory_s(K), cov80(theory_s(K))), flush=True)
    for K in (8, 20):
        for scheme in ("match_grpo", "match_rloo", "brier_loo_baseline", "brier_dar_v", "brier_dar_fair"):
            qs = [run_bern(scheme, K, seed=s) for s in range(3)]
            row = {"K": K, "p_true": 0.1, "scheme": scheme, "q_mean": round(float(np.mean(qs)), 4),
                   "q_seeds": [round(v, 4) for v in qs]}
            out["bern"].append(row)
            print("BERN", row, flush=True)
        print("BERN theory brier_dar_v K=%d: q*=%.4f" % (K, (2 * K * 0.1 - 1) / (2 * (K - 1))), flush=True)
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "toy_out.json", "w"), indent=1)


if __name__ == "__main__":
    main()
