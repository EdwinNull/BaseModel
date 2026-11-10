"""Toy simulation (synthetic data only): does a 'P-only' input still encode the
measurement process M?  And how do P-only / M-only / P+M behave across two
hospitals that differ only in measurement intensity?

Latent severity s -> physiology x (3 vars, 24 hourly bins) and outcome y.
Measurement prob per hour = sigmoid(a_hosp + g*s): sicker -> measured more.
Hospital A dense (a=0.3), hospital B sparse (a=-1.7). Same patients' law otherwise.
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss

rng = np.random.default_rng(20261031)
T, V = 24, 3
MU = np.array([85.0, 18.0, 96.0]); BETA = np.array([8.0, 3.0, -2.0]); SD = np.array([6.0, 2.5, 1.5])

def sigmoid(z): return 1/(1+np.exp(-z))

def simulate(n, a_hosp, g=1.0):
    s = rng.normal(size=n)
    drift = rng.normal(0, 0.5, size=n)          # within-stay worsening/improving
    t = np.linspace(0, 1, T)
    sev = s[:, None] + drift[:, None]*t[None, :]  # n x T
    x = np.empty((n, T, V))
    for v in range(V):
        e = np.zeros((n, T)); e[:, 0] = rng.normal(size=n)
        for k in range(1, T): e[:, k] = 0.7*e[:, k-1] + rng.normal(scale=np.sqrt(1-0.49), size=n)
        x[:, :, v] = MU[v] + BETA[v]*sev + SD[v]*e
    pobs = sigmoid(a_hosp + g*sev)[:, :, None] * np.ones((1, 1, V))
    m = rng.random((n, T, V)) < pobs
    m[:, 0, :] |= rng.random((n, V)) < 0.5      # admission set often measured
    y = rng.random(n) < sigmoid(-2.3 + 1.1*sev[:, -1])
    return x, m, y.astype(int)

def summaries_observed(x, m, which=("mean","sd","min","max","last")):
    feats = []
    for v in range(V):
        xv = np.where(m[:, :, v], x[:, :, v], np.nan)
        cnt = m[:, :, v].sum(1)
        with np.errstate(all='ignore'):
            f = {"mean": np.nanmean(xv, 1), "sd": np.nanstd(xv, 1),
                 "min": np.nanmin(xv, 1), "max": np.nanmax(xv, 1)}
        idx_last = np.where(m[:, :, v], np.arange(T)[None, :], -1).max(1)
        f["last"] = np.where(idx_last >= 0, x[np.arange(len(x)), np.maximum(idx_last, 0), v], np.nan)
        for k in which:
            col = f[k]; col = np.where(np.isnan(col), MU[v], col)  # never-measured -> pop mean
            if k == "sd": col = np.where(cnt <= 1, 0.0, col)
            feats.append(col)
    return np.column_stack(feats)

def grid_impute(x, m, how):
    xi = np.where(m, x, np.nan)
    if how == "mean":
        return np.where(np.isnan(xi), MU[None, None, :], xi)
    out = xi.copy()                                       # LOCF, leading -> pop mean
    for k in range(T):
        if k == 0: out[:, 0, :] = np.where(np.isnan(out[:, 0, :]), MU[None, :], out[:, 0, :])
        else: out[:, k, :] = np.where(np.isnan(out[:, k, :]), out[:, k-1, :], out[:, k, :])
    return out

def grid_summaries(g):
    last = g[:, -1, :]; mean = g.mean(1); sd = g.std(1); mn = g.min(1); mx = g.max(1)
    return np.column_stack([mean, sd, mn, mx, last])

def m_features(m):
    cnt = m.sum(1)                                        # n x V
    idx_last = np.where(m, np.arange(T)[None, :, None], -1).max(1)
    hrs_since = np.where(idx_last >= 0, T-1-idx_last, T)
    hours_any = m.any(2).sum(1)[:, None]
    return np.column_stack([cnt, hrs_since, hours_any])

def auc_probe(Xtr, ytr, Xte, yte):
    clf = HGB(max_iter=300, learning_rate=0.05, random_state=0).fit(Xtr, ytr)
    return roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])

N = 8000
xa, ma, ya = simulate(N, a_hosp=0.3)    # hospital A (dense)
xb, mb, yb = simulate(N, a_hosp=-1.7)   # hospital B (sparse)
print(f"mean measurements/var/24h  A={ma.sum(1).mean():.1f}  B={mb.sum(1).mean():.1f}; prevalence A={ya.mean():.3f} B={yb.mean():.3f}")

# ---------- 1. M-recoverability probe: can P-only inputs predict measurement intensity? ----------
variants = {
  "P-only, grid LOCF -> summaries":        lambda x, m: grid_summaries(grid_impute(x, m, "locf")),
  "P-only, grid mean-impute -> summaries": lambda x, m: grid_summaries(grid_impute(x, m, "mean")),
  "P-only, observed values: mean/sd/min/max/last": lambda x, m: summaries_observed(x, m),
  "P-only, observed values: mean/last only":       lambda x, m: summaries_observed(x, m, ("mean","last")),
}
half = N//2
intensity = (ma.sum((1, 2)) > np.median(ma.sum((1, 2)))).astype(int)
print("\n[1] M-recoverability within hospital A: AUROC for 'above-median #measurements' from P-only input")
for name, f in variants.items():
    X = f(xa, ma)
    print(f"  {name:48s} {auc_probe(X[:half], intensity[:half], X[half:], intensity[half:]):.3f}")
# reference: same probe from true severity only (how much is explained just because sicker = measured more)
sev_proxy = (xa.mean(1) - MU) / BETA            # oracle physiology (all hours, no missingness)
print(f"  {'oracle: full (unmasked) physiology':48s} {auc_probe(sev_proxy[:half], intensity[:half], sev_proxy[half:], intensity[half:]):.3f}")

# ---------- 2. Hospital identifiability from each input group ----------
print("\n[2] Hospital A vs B classifier AUROC (pooled, 50/50 split)")
lab = np.r_[np.zeros(N), np.ones(N)].astype(int); perm = rng.permutation(2*N); tr, te = perm[:N], perm[N:]
for name, X in {"P-only (observed mean/last)": np.r_[summaries_observed(xa, ma, ("mean","last")), summaries_observed(xb, mb, ("mean","last"))],
                "P-only (grid LOCF summaries)": np.r_[grid_summaries(grid_impute(xa, ma, "locf")), grid_summaries(grid_impute(xb, mb, "locf"))],
                "M-only": np.r_[m_features(ma), m_features(mb)]}.items():
    print(f"  {name:32s} {auc_probe(X[tr], lab[tr], X[te], lab[te]):.3f}")

# ---------- 3. Outcome models: train on A, test on A (internal) and B (external) ----------
print("\n[3] Outcome AUROC / Brier / O:E; train on A(first half), internal = A(second half), external = B")
def arms(x, m):
    P = summaries_observed(x, m, ("mean","last")); M = m_features(m)
    return {"P-only": P, "M-only": M, "P+M": np.column_stack([P, M])}
A, B = arms(xa, ma), arms(xb, mb)
for model_name, make in {"LR": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
                         "GBT": lambda: HGB(max_iter=300, learning_rate=0.05, random_state=0)}.items():
    for arm in ["P-only", "M-only", "P+M"]:
        clf = make().fit(A[arm][:half], ya[:half])
        pa = clf.predict_proba(A[arm][half:])[:, 1]; pb = clf.predict_proba(B[arm])[:, 1]
        ai, ae = roc_auc_score(ya[half:], pa), roc_auc_score(yb, pb)
        print(f"  {model_name:3s} {arm:6s} AUROC int {ai:.3f} ext {ae:.3f} TGap {ai-ae:+.3f} | Brier int {brier_score_loss(ya[half:], pa):.4f} ext {brier_score_loss(yb, pb):.4f} | O:E ext {yb.mean()/pb.mean():.2f}")
