"""样本量情景脚本的测试：只用公开例子和解析性质，不碰病例数据。"""
from __future__ import annotations

import random
from math import exp, log

import pytest

import pmsampsize_scenarios as P


def test_max_r2():
    assert P.max_r2(0.174) == pytest.approx(0.603, abs=1e-3)      # 1 − exp(2 lnL0 / n)
    assert P.max_r2(0.5) == pytest.approx(0.75, abs=1e-9)


def test_pmsampsize_example():
    """pmsampsize 文档的二分类例子：R² 0.288、24 个参数、结局率 17.4%。"""
    d = P.sample_size(0.288, 24, 0.174)
    assert (d["n1"], d["n2"], d["n3"]) == (623, 662, 221)
    assert d["n"] == 662 and d["epp"] == pytest.approx(4.8, abs=0.05)
    assert d["shrinkage"] == pytest.approx(0.905, abs=1e-3)


def test_c_statistic_matches_documented_example():
    """同一份文档用 C = 0.89 配结局率 17.4% 代替 R² 0.288。"""
    assert P.r2_from_c(0.89, 0.174) == pytest.approx(0.288, abs=0.003)


def test_c_statistic_matches_simulation():
    """积分与按模型抽样的结果一致。"""
    rng = random.Random(20261031)
    c, rate, n = 0.75, 0.10, 300_000
    mu = 2 ** 0.5 * P.NORMAL.inv_cdf(c)
    a = log(rate / (1 - rate)) - mu * mu / 2
    ll = 0.0
    for _ in range(n):
        ev = rng.random() < rate
        x = rng.gauss(mu if ev else 0.0, 1.0)
        p = 1 / (1 + exp(-(a + mu * x)))
        ll += log(p if ev else 1 - p)
    null = rate * log(rate) + (1 - rate) * log(1 - rate)
    assert 1 - exp(-2 * (ll / n - null)) == pytest.approx(P.r2_from_c(c, rate), abs=0.002)


def test_c_half_means_no_signal():
    assert P.r2_from_c(0.5, 0.1) == pytest.approx(0.0, abs=1e-6)


def test_monotonic():
    """参数多、C 低都要更多人。"""
    assert P.from_c(0.75, 30, 0.10)["n"] > P.from_c(0.75, 20, 0.10)["n"] > P.from_c(0.75, 10, 0.10)["n"]
    assert P.from_c(0.70, 20, 0.10)["n"] > P.from_c(0.75, 20, 0.10)["n"] > P.from_c(0.80, 20, 0.10)["n"]


def test_conservative_uses_nagelkerke():
    d = P.conservative(20, 0.10)
    assert d["nagelkerke"] == pytest.approx(0.15, abs=0.002)


def test_r2_over_limit():
    with pytest.raises(ValueError):
        P.sample_size(0.7, 10, 0.05)


def test_report(tmp_path, monkeypatch):
    text = P.report()
    b = P.from_c(P.BASE["c"], P.BASE["params"], P.BASE["rate"])
    assert f"**{b['n']} 例**" in text and "### 30 个候选参数" in text and "没有用任何病例数据" in text
    monkeypatch.setattr("sys.argv", ["x", "--out", str(tmp_path / "a" / "r.md")])
    P.main()
    assert (tmp_path / "a" / "r.md").read_text(encoding="utf-8") == text
