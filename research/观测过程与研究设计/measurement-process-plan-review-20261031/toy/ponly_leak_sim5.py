"""(e) Same as (d) but hospital B's policy is STRUCTURED: variable-specific baselines and a more
reactive (state-dependent) policy. A: a=[0.3,0.3,0.3], g=1. B: a=[0.3,-1.0,-2.5], g=2.0.
Library of 4 'tune hospitals' with other structured policies (B itself not included)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, importlib.util, io, contextlib
spec = importlib.util.spec_from_file_location("s", "ponly_leak_sim.py"); s = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(s)
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
rng = np.random.default_rng(31)
T, V, N = s.T, s.V, s.N; half = N // 2

def simulate_struct(n, a_vec, g):
    sv = rng.normal(size=n); drift = rng.normal(0, 0.5, size=n); t = np.linspace(0, 1, T)
    sev = sv[:, None] + drift[:, None]*t[None, :]
    x = np.empty((n, T, V))
    for v in range(V):
        e = np.zeros((n, T)); e[:, 0] = rng.normal(size=n)
        for k in range(1, T): e[:, k] = 0.7*e[:, k-1] + rng.normal(scale=np.sqrt(1-0.49), size=n)
        x[:, :, v] = s.MU[v] + s.BETA[v]*sev + s.SD[v]*e
    p = s.sigmoid(np.asarray(a_vec)[None, None, :] + g*sev[:, :, None])
    m = rng.random((n, T, V)) < p; m[:, 0, :] |= rng.random((n, V)) < 0.5
    y = (rng.random(n) < s.sigmoid(-2.3 + 1.1*sev[:, -1])).astype(int)
    return x, m, y

A_POL = ([0.3, 0.3, 0.3], 1.0); B_POL = ([0.3, -1.0, -2.5], 2.0)
LIB = [([0.0, -0.5, -1.5], 1.5), ([-0.5, -1.5, -0.5], 2.5), ([0.2, -2.0, -2.0], 1.0), ([-1.0, -0.5, -2.8], 2.0)]
xa, ma, ya = simulate_struct(N, *A_POL); xb, mb, yb = simulate_struct(N, *B_POL)
def sev_hat(x): return ((x - s.MU) / s.BETA).mean(2)
def transplant(x, m, src, tgt):
    sh = sev_hat(x)[:, :, None]
    ratio = np.minimum(1.0, s.sigmoid(np.asarray(tgt[0])[None,None,:] + tgt[1]*sh) / s.sigmoid(np.asarray(src[0])[None,None,:] + src[1]*sh))
    return m & (rng.random(m.shape) < ratio)
def desc(m): return m.mean((0, 1))                 # per-variable measurement rate (label-free)
def feats(x, m, d=None):
    P = s.summaries_observed(x, m, ("mean","last")); M = s.m_features(m)
    X = np.column_stack([P, M])
    if d is not None:
        D = np.tile(d, (len(x), 1)); cnt = m.sum(1)
        X = np.column_stack([X, D, cnt / (D*T + 1e-6)])   # descriptor + counts normalised by hospital rate
    return X
xtr, mtr, ytr = xa[:half], ma[:half], ya[:half]
v_mcar = [mtr & (rng.random(mtr.shape) < rng.uniform(0.25, 1.0)) for _ in LIB]
v_tp = [transplant(xtr, mtr, A_POL, pol) for pol in LIB]
print("per-variable rate  A:", np.round(desc(ma), 3), " B:", np.round(desc(mb), 3), " library:", [np.round(desc(v), 2).tolist() for v in v_tp])
sets = {"ERM": (feats(xtr, mtr), ytr, False),
        "MCAR-drop aug": (np.r_[feats(xtr, mtr), *[feats(xtr, v) for v in v_mcar]], np.tile(ytr, 5), False),
        "policy-transplant aug": (np.r_[feats(xtr, mtr), *[feats(xtr, v) for v in v_tp]], np.tile(ytr, 5), False),
        "transplant aug + descriptor": (np.r_[feats(xtr, mtr, desc(mtr)), *[feats(xtr, v, desc(v)) for v in v_tp]], np.tile(ytr, 5), True)}
for mn, make in {"LR": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
                 "GBT": lambda: HGB(max_iter=300, learning_rate=0.05, random_state=0)}.items():
    for arm, (X, y, use_d) in sets.items():
        clf = make().fit(X, y)
        Xb = feats(xb, mb, desc(mb)) if use_d else feats(xb, mb)
        Xa = feats(xa[half:], ma[half:], desc(ma[half:])) if use_d else feats(xa[half:], ma[half:])
        pa, pb = clf.predict_proba(Xa)[:, 1], clf.predict_proba(Xb)[:, 1]
        print(f"{mn:3s} {arm:28s} int {roc_auc_score(ya[half:], pa):.3f} | ext B AUROC {roc_auc_score(yb, pb):.3f}  Brier {brier_score_loss(yb, pb):.4f}  O:E {yb.mean()/pb.mean():.2f}")
clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(s.summaries_observed(xtr, mtr, ("mean","last")), ytr)
pb = clf.predict_proba(s.summaries_observed(xb, mb, ("mean","last")))[:, 1]
print(f"LR  (reference) P-only ERM          ext B AUROC {roc_auc_score(yb, pb):.3f}  Brier {brier_score_loss(yb, pb):.4f}  O:E {yb.mean()/pb.mean():.2f}")
