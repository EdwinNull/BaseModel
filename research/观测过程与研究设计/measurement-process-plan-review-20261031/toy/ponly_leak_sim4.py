"""(d) Toy proof-of-concept for policy-transplant post-training (synthetic only).
Train on hospital A (dense). Policy library = 4 'tune hospitals' with baselines {-0.2,-0.8,-1.3,-2.3}
(estimated from unlabeled data; B's own baseline -1.7 is NOT in the library). Test on hospital B.
Arms (all P+M inputs): ERM; MCAR-drop augmentation; policy-transplant augmentation;
transplant + policy descriptor (hospital mean measurement rate, from unlabeled data) as conditioning.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, importlib.util, io, contextlib
spec = importlib.util.spec_from_file_location("s", "ponly_leak_sim.py"); s = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(s)
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
rng = np.random.default_rng(23)
xa, ma, ya, xb, mb, yb, N, half = s.xa, s.ma, s.ya, s.xb, s.mb, s.yb, s.N, s.half
LIB = [-0.2, -0.8, -1.3, -2.3]

def sev_hat(x): return ((x - s.MU) / s.BETA).mean(2)
def transplant(x, m, a_src, a_tgt):
    sh = sev_hat(x)
    ratio = np.minimum(1.0, s.sigmoid(a_tgt + sh) / s.sigmoid(a_src + sh))[:, :, None]
    return m & (rng.random(m.shape) < ratio)
def rate(m): return m.mean()                       # policy descriptor: overall measurement rate (label-free)
def feats(x, m, desc=None, inter=False):
    P = s.summaries_observed(x, m, ("mean","last")); M = s.m_features(m)
    X = np.column_stack([P, M])
    if desc is not None:
        d = np.full((len(x), 1), desc)
        X = np.column_stack([X, d] + ([M * d] if inter else []))
    return X

xtr, mtr, ytr = xa[:half], ma[:half], ya[:half]
r_src = rate(mtr)
# build training sets
views_mcar, views_tp = [], []
for a in LIB:
    keep = rng.uniform(0.25, 1.0)                              # MCAR drop with random keep rate
    views_mcar.append(mtr & (rng.random(mtr.shape) < keep))
    views_tp.append(transplant(xtr, mtr, 0.3, a))
train_sets = {
  "ERM":                         (feats(xtr, mtr), ytr, None),
  "MCAR-drop aug":               (np.r_[feats(xtr, mtr), *[feats(xtr, v) for v in views_mcar]], np.tile(ytr, 1+len(LIB)), None),
  "policy-transplant aug":       (np.r_[feats(xtr, mtr), *[feats(xtr, v) for v in views_tp]], np.tile(ytr, 1+len(LIB)), None),
  "transplant aug + descriptor": (np.r_[feats(xtr, mtr, rate(mtr), True), *[feats(xtr, v, rate(v), True) for v in views_tp]], np.tile(ytr, 1+len(LIB)), "desc"),
}
r_b = rate(mb)   # estimated from B's unlabeled data
print(f"measurement rate: A={r_src:.3f}  library={[round(rate(v),3) for v in views_tp]}  B={r_b:.3f}")
for model_name, make in {"LR": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
                         "GBT": lambda: HGB(max_iter=300, learning_rate=0.05, random_state=0)}.items():
    for arm, (X, y, kind) in train_sets.items():
        clf = make().fit(X, y)
        if kind == "desc":
            Xa_te, Xb = feats(xa[half:], ma[half:], rate(ma[half:]), True), feats(xb, mb, r_b, True)
        else:
            Xa_te, Xb = feats(xa[half:], ma[half:]), feats(xb, mb)
        pa, pb = clf.predict_proba(Xa_te)[:, 1], clf.predict_proba(Xb)[:, 1]
        print(f"{model_name:3s} {arm:28s} int AUROC {roc_auc_score(ya[half:], pa):.3f} | ext B AUROC {roc_auc_score(yb, pb):.3f}  Brier {brier_score_loss(yb, pb):.4f}  O:E {yb.mean()/pb.mean():.2f}")
# reference: P-only ERM on B
clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(s.summaries_observed(xtr, mtr, ("mean","last")), ytr)
pb = clf.predict_proba(s.summaries_observed(xb, mb, ("mean","last")))[:, 1]
print(f"LR  (reference) P-only ERM          ext B AUROC {roc_auc_score(yb, pb):.3f}  Brier {brier_score_loss(yb, pb):.4f}  O:E {yb.mean()/pb.mean():.2f}")
