from pathlib import Path
p=Path("experiments/rw_gam2gd/evaluate.py")
s=p.read_text()
s=s.replace("from sklearn.linear_model import LogisticRegression\n", "")
old="""    slope = LogisticRegression(penalty=None, max_iter=1000).fit(lp[:, None], y).coef_[0, 0]\n    # 截距：以 lp 为偏移量的只含截距的逻辑回归，用牛顿法求解（sklearn 不支持 offset）\n"""
new="""    # 用二维 Newton/IRLS 求解 logit(y) ~ intercept + slope*logit(p)。
    # 该拟合在 bootstrap 内层反复调用；避免每次构造 sklearn estimator 的高额开销。
    X = np.column_stack((np.ones_like(lp), lp))
    beta = np.array([0.0, 1.0], dtype=float)
    for _ in range(50):
        z = np.clip(X @ beta, -35.0, 35.0)
        mu = 1.0 / (1.0 + np.exp(-z))
        w = mu * (1.0 - mu)
        h = (X * w[:, None]).T @ X
        g = X.T @ (y - mu)
        try:
            step = np.linalg.solve(h, g)
        except np.linalg.LinAlgError:
            break
        beta += step
        if np.max(np.abs(step)) < 1e-10:
            break
    slope = float(beta[1])
    # 截距：以 lp 为偏移量的只含截距的逻辑回归，用牛顿法求解
"""
if old not in s: raise SystemExit("pattern not found")
p.write_text(s.replace(old,new))
