"""Part 2 of the toy (synthetic only). Uses functions from ponly_leak_sim.py.
(a) Thinning-invariance test: can a classifier tell ORIGINAL vs MCAR-THINNED (keep 50%)
    versions of the same patients apart, using only P-only features?  ~0.5 => P-only
    representation is (in distribution) invariant to the measurement process.
(b) Incremental M information beyond oracle physiology.
(c) Patient-level drift (OPS) of an A-trained outcome model when A patients are
    re-observed under B's (sparser, informative) policy, physiology held fixed.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, importlib.util, sys, io, contextlib
spec = importlib.util.spec_from_file_location("s", "ponly_leak_sim.py"); s = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(s)
from sklearn.metrics import roc_auc_score
rng = np.random.default_rng(7)
xa, ma, ya, N, half = s.xa, s.ma, s.ya, s.N, s.half

variants = {
  "grid LOCF -> mean/sd/min/max/last": lambda x, m: s.grid_summaries(s.grid_impute(x, m, "locf")),
  "grid mean-impute -> summaries":     lambda x, m: s.grid_summaries(s.grid_impute(x, m, "mean")),
  "observed: mean/sd/min/max/last":    lambda x, m: s.summaries_observed(x, m),
  "observed: mean/last only":          lambda x, m: s.summaries_observed(x, m, ("mean","last")),
}
keep = rng.random(ma.shape) < 0.5
m_thin = ma & keep                     # MCAR thinning: physiology untouched, only M changes
idx = rng.permutation(N); tr, te = idx[:half], idx[half:]   # split by patient (pairs stay together)
print("(a) Thinning-invariance test, AUROC original vs MCAR-thinned (same patients; 0.5 = invariant)")
for name, f in variants.items():
    X0, X1 = f(xa, ma), f(xa, m_thin)
    Xtr = np.r_[X0[tr], X1[tr]]; ytr = np.r_[np.zeros(len(tr)), np.ones(len(tr))]
    Xte = np.r_[X0[te], X1[te]]; yte = np.r_[np.zeros(len(te)), np.ones(len(te))]
    print(f"   {name:36s} {s.auc_probe(Xtr, ytr, Xte, yte):.3f}")
X0, X1 = s.m_features(ma), s.m_features(m_thin)
print(f"   {'(reference) M-only features':36s} {s.auc_probe(np.r_[X0[tr],X1[tr]], np.r_[np.zeros(len(tr)),np.ones(len(tr))], np.r_[X0[te],X1[te]], np.r_[np.zeros(len(te)),np.ones(len(te))]):.3f}")

print("\n(b) Predicting above-median #measurements: oracle physiology alone vs oracle + P-only features")
intensity = (ma.sum((1, 2)) > np.median(ma.sum((1, 2)))).astype(int)
oracle = (xa.mean(1) - s.MU) / s.BETA
base = s.auc_probe(oracle[:half], intensity[:half], oracle[half:], intensity[half:])
print(f"   oracle physiology only                 {base:.3f}")
for name, f in variants.items():
    X = np.column_stack([oracle, f(xa, ma)])
    print(f"   oracle + {name:30s} {s.auc_probe(X[:half], intensity[:half], X[half:], intensity[half:]):.3f}")

print("\n(c) Patient-level drift when A's patients are re-observed under B's policy (physiology fixed)")
# B policy applied to A's physiology: re-draw the mask with B's baseline intensity, same severity path.
# Reconstruct severity from oracle (exact in this toy) to draw the counterfactual mask.
sev_hat = ((xa - s.MU) / s.BETA).mean(2)   # approx severity path (noise averaged over 3 vars)
p_b = s.sigmoid(-1.7 + 1.0*sev_hat)[:, :, None] * np.ones((1, 1, s.V))
m_cf = rng.random(ma.shape) < p_b; m_cf[:, 0, :] |= rng.random((N, s.V)) < 0.5
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
def arm(x, m, a):
    P = s.summaries_observed(x, m, ("mean","last")); M = s.m_features(m)
    return {"P-only": P, "M-only": M, "P+M": np.column_stack([P, M])}[a]
for a in ["P-only", "M-only", "P+M"]:
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(arm(xa, ma, a)[:half], ya[:half])
    p0 = clf.predict_proba(arm(xa, ma, a)[half:])[:, 1]; p1 = clf.predict_proba(arm(xa, m_cf, a)[half:])[:, 1]
    thr = np.quantile(p0, 0.8)
    flip = np.mean((p0 >= thr) != (p1 >= thr))
    print(f"   LR {a:6s} mean|dp| {np.mean(np.abs(p1-p0)):.3f}  P90|dp| {np.quantile(np.abs(p1-p0),0.9):.3f}  signed mean dp {np.mean(p1-p0):+.3f}  flip(top20%) {flip:.3f}  AUROC {roc_auc_score(ya[half:],p0):.3f}->{roc_auc_score(ya[half:],p1):.3f}")
