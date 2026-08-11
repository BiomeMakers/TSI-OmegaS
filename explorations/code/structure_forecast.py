"""Does Omega predict the correlation STRUCTURE ahead, beyond persistence?

PRE-REGISTERED. Criterion and outcomes written before the script was first run.

WHY THIS AND NOT RETURNS. The preprint establishes that Omega is a coincident
state index: its cross-correlation with the stress index peaks at lag zero.
Asking it to pick assets by 5-day forward return was therefore a test it could
not pass by construction, and it did not (see investment_rule_headtohead.py,
a pre-registered null for both our rule and the published balance rule).

Correlation structure is a different target. It is far more persistent than
returns, so there is signal to find, and predicting it is a claim a coincident
index is allowed to make: the question is not "where do prices go" but "how
coupled will this market be next month".

TARGETS, measured on a FUTURE window disjoint from the estimation window:
  mean_corr   mean absolute pairwise correlation
  erank       effective rank, exp of the entropy of the correlation spectrum

THE RIVAL IS PERSISTENCE, and it is a strong one. Today's value of the same
target already predicts most of next month's. The only question worth asking is
whether Omega adds anything ON TOP of that, so every model below contains the
persistence term and the test is incremental.

MODELS (OLS, standardised, fitted on the training half only):
  base      target_future ~ target_now
  +omega    target_future ~ target_now + omega_now
  +kappa    target_future ~ target_now + kappa_now     (their index, same test)
  +both     target_future ~ target_now + omega_now + kappa_now

PRE-REGISTERED CRITERION. A predictor adds if the out-of-sample R^2 improves
over the base model AND the 95% block-bootstrap CI of that improvement excludes
zero. Blocks of 20 windows, because forward windows overlap.

PRE-REGISTERED OUTCOMES.
  (a) omega adds and kappa does not -> the structural forecast is a genuine use
      for the index and is worth a note of its own.
  (b) both add                      -> real effect, not ours alone; report both.
  (c) only kappa adds               -> report it; it is their index, not ours.
  (d) neither adds                  -> persistence dominates and the line closes.
      Do NOT then sweep horizons or window lengths looking for one that works.

SPLIT. Time-ordered, never random: fit on the first half of the windows,
evaluate on the second. No parameter is chosen on the test half.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

WIN, STEP, FWD = 60, 10, 21          # estimate on 60 days, predict the next 21
rng = np.random.default_rng(0)


def structure(C):
    """The two targets, from a correlation matrix."""
    n = C.shape[0]
    A = np.abs(C.copy())
    np.fill_diagonal(A, 0.0)
    mean_corr = A[np.triu_indices(n, 1)].mean()
    ev = np.clip(np.linalg.eigvalsh(C), 1e-9, None)
    p = ev / ev.sum()
    return mean_corr, float(np.exp(-(p * np.log(p)).sum()))


def omega_paper(A, n):
    A2 = A @ A
    den = A2.sum() - np.trace(A2)
    if den <= 0:
        return 0.0
    C = np.trace(A2 @ A) / den
    deg = A.sum(1)
    dens = A.sum() / (n * (n - 1))
    ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
    return (C * dens / (1.0 / max(ev[1], 1e-6))) * np.var(deg)


def build(ret, n):
    rows = []
    for i in range(WIN, len(ret) - FWD, STEP):
        Cn = np.nan_to_num(ret.iloc[i - WIN:i].corr().values, nan=0.0)
        Cf = np.nan_to_num(ret.iloc[i:i + FWD].corr().values, nan=0.0)
        S = Cn.copy()
        np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        mc_n, er_n = structure(Cn)
        mc_f, er_f = structure(Cf)
        rows.append(dict(date=ret.index[i - 1],
                         mean_corr_now=mc_n, erank_now=er_n,
                         mean_corr_fut=mc_f, erank_fut=er_f,
                         omega=omega_paper(A, n),
                         kappa=float(np.trace(expm(S)) / np.trace(expm(np.abs(S))))))
    return pd.DataFrame(rows)


def ols_r2(Xtr, ytr, Xte, yte):
    Xtr = np.column_stack([np.ones(len(Xtr)), Xtr])
    Xte = np.column_stack([np.ones(len(Xte)), Xte])
    beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    pred = Xte @ beta
    ss_res = ((yte - pred) ** 2).sum()
    ss_tot = ((yte - ytr.mean()) ** 2).sum()
    return 1 - ss_res / ss_tot, (yte - pred) ** 2, (yte - (Xte[:, :2] @ beta[:2])) ** 2


def run(R, target, label):
    z = lambda v: (v - v.mean()) / v.std()
    y = R[f"{target}_fut"].values
    cols = {'base': [f"{target}_now"],
            '+omega': [f"{target}_now", 'omega'],
            '+kappa': [f"{target}_now", 'kappa'],
            '+both': [f"{target}_now", 'omega', 'kappa']}
    half = len(R) // 2
    ytr, yte = y[:half], y[half:]
    res, sq = {}, {}
    for name, cs in cols.items():
        X = np.column_stack([z(R[c].values) for c in cs])
        r2, e2, _ = ols_r2(X[:half], ytr, X[half:], yte)
        res[name], sq[name] = r2, e2
    print(f"\n  target: {label}   (train n={half}, test n={len(yte)})")
    print(f"    {'model':<10}{'OOS R2':>9}{'dR2 vs base':>13}{'95% CI (blocks of 20)':>26}  verdict")
    for name in ['base', '+omega', '+kappa', '+both']:
        if name == 'base':
            print(f"    {name:<10}{res[name]:>9.4f}")
            continue
        d = res[name] - res['base']
        diff = sq['base'] - sq[name]              # positive = the model helps
        boots = []
        m = len(diff)
        for _ in range(2000):
            idx = []
            while len(idx) < m:
                s = rng.integers(0, max(1, m - 20))
                idx.extend(range(s, min(s + 20, m)))
            idx = np.array(idx[:m])
            boots.append(diff[idx].sum() / ((yte - ytr.mean()) ** 2).sum())
        lo, hi = np.percentile(boots, [2.5, 97.5])
        v = "ADDS" if lo > 0 else ("hurts" if hi < 0 else "no")
        print(f"    {name:<10}{res[name]:>9.4f}{d:>+13.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>26}  {v}")


def main():
    d = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"), parse_dates=['Date'])
    px = d.pivot(index='Date', columns='Ticker', values='Close').dropna(how='any')
    ret = np.log(px / px.shift(1)).dropna()
    R = build(ret, ret.shape[1])
    print(f"42-asset network: {len(R)} windows, estimate on {WIN} days, predict the next {FWD}.")
    print(f"  persistence of the targets: corr(now, future) = "
          f"{np.corrcoef(R.mean_corr_now, R.mean_corr_fut)[0,1]:.3f} (mean corr), "
          f"{np.corrcoef(R.erank_now, R.erank_fut)[0,1]:.3f} (effective rank)")
    run(R, 'mean_corr', 'mean absolute correlation, next 21 days')
    run(R, 'erank', 'effective rank, next 21 days')
    R.to_csv(RES("structure_forecast.csv"), index=False)


if __name__ == "__main__":
    main()
