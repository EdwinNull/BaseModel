"""(c') same as (c) but implemented the way it must be done on real data: policy transplant by
THINNING only. Keep each observed A-measurement with prob p_B(state)/p_A(state) (<=1), so no value
is ever invented. State proxy = per-hour severity estimate (in real data: a fitted policy model)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, importlib.util, io, contextlib
spec = importlib.util.spec_from_file_location("s", "ponly_leak_sim.py"); s = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(s)
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
rng = np.random.default_rng(11)
xa, ma, ya, N, half = s.xa, s.ma, s.ya, s.N, s.half
sev_hat = ((xa - s.MU) / s.BETA).mean(2)
ratio = (s.sigmoid(-1.7 + sev_hat) / s.sigmoid(0.3 + sev_hat))[:, :, None]
m_thin = ma & (rng.random(ma.shape) < ratio)
print(f"obs/var/24h: A original {ma.sum(1).mean():.1f} -> transplanted to B policy {m_thin.sum(1).mean():.1f} (B actual {s.mb.sum(1).mean():.1f})")
def arm(x, m, a):
    P = s.summaries_observed(x, m, ("mean","last")); M = s.m_features(m)
    return {"P-only": P, "M-only": M, "P+M": np.column_stack([P, M])}[a]
for a in ["P-only", "M-only", "P+M"]:
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(arm(xa, ma, a)[:half], ya[:half])
    p0 = clf.predict_proba(arm(xa, ma, a)[half:])[:, 1]; p1 = clf.predict_proba(arm(xa, m_thin, a)[half:])[:, 1]
    thr = np.quantile(p0, 0.8); flip = np.mean((p0 >= thr) != (p1 >= thr))
    print(f"LR {a:6s} mean|dp| {np.mean(np.abs(p1-p0)):.3f}  P90|dp| {np.quantile(np.abs(p1-p0),0.9):.3f}  signed {np.mean(p1-p0):+.3f}  flip(top20%) {flip:.3f}  AUROC {roc_auc_score(ya[half:],p0):.3f}->{roc_auc_score(ya[half:],p1):.3f}  O:E {ya[half:].mean()/p0.mean():.2f}->{ya[half:].mean()/p1.mean():.2f}")
