"""Part 2, step one: measure the RIVAL before building anything.

Modelling the dynamics of the correlation matrix is not a new idea. It is DCC,
Engle's dynamic conditional correlation, from 2002, and it has been in
production across the industry for twenty years. So DCC is not what we would be
inventing: it is what anything we build has to beat. This script measures it,
before any of our own machinery exists, so that we know whether there is a
margin worth chasing and how big it is.

THREE FORECASTERS of the correlation matrix over the next 21 days:
  sample    the correlation of the last 60 days, i.e. pure persistence. The
            naive benchmark that already explained R^2 = 0.40 of next month's
            mean correlation in the earlier test.
  ewma      exponentially weighted correlation, RiskMetrics style.
  dcc       DCC(1,1) with correlation targeting on EWMA-devolatilised
            residuals, with (a, b) chosen on the FIRST HALF only and the second
            half touched once.

METRICS. Two, because they answer different questions. The Frobenius distance to
the realised correlation matrix asks how well the whole structure is predicted.
The portfolio-variance error asks how well the thing a practitioner actually
uses is predicted; a model can win on one and lose on the other.

WHY THIS TERRAIN IS DIFFERENT FROM THE INVESTMENT ONE. Risk forecasting is not
reflexive. If everyone has a better variance model, the model stays better,
because there is nothing to arbitrage away. That is why GARCH-family models have
survived thirty years while return signals decay in months, and it is why this
line can live where the previous one died.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP, HZ = 60, 10, 21
LAM_VOL, LAM_COR = 0.94, 0.97


def corr_from_cov(S):
    d = np.sqrt(np.clip(np.diag(S), 1e-12, None))
    return S / np.outer(d, d)


def devol(R, lam=LAM_VOL):
    """EWMA volatility per asset; returns standardised residuals."""
    v = np.empty_like(R)
    s = R[:60].var(axis=0)
    for t in range(len(R)):
        v[t] = np.sqrt(np.clip(s, 1e-12, None))
        s = lam * s + (1 - lam) * R[t] ** 2
    return R / v


def dcc_path(z, a, b, ends):
    """R_t at the requested indices, DCC(1,1) with correlation targeting."""
    n = z.shape[1]
    Qbar = np.corrcoef(z, rowvar=False)
    Q = Qbar.copy()
    want = set(ends)
    out = {}
    for t in range(len(z)):
        if t in want:
            out[t] = corr_from_cov(Q)
        u = z[t]
        Q = (1 - a - b) * Qbar + a * np.outer(u, u) + b * Q
    return out, Qbar


def ewma_corr(R, ends, lam=LAM_COR):
    n = R.shape[1]
    S = np.cov(R[:60], rowvar=False)
    want = set(ends)
    out = {}
    for t in range(len(R)):
        if t in want:
            out[t] = corr_from_cov(S)
        S = lam * S + (1 - lam) * np.outer(R[t], R[t])
    return out


def offdiag_err(P, T):
    n = P.shape[0]
    iu = np.triu_indices(n, 1)
    return float(np.sqrt(np.mean((P[iu] - T[iu]) ** 2)))


def main():
    px = pd.read_pickle(PANEL).dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    Rv = ret.values
    n = Rv.shape[1]
    w = np.full(n, 1.0 / n)
    ends = list(range(WIN, len(Rv) - HZ, STEP))
    real = {t: np.nan_to_num(np.corrcoef(Rv[t:t + HZ], rowvar=False), nan=0.0) for t in ends}
    vols = {t: Rv[t - WIN:t].std(axis=0) for t in ends}
    realvar = {t: float(np.var(Rv[t:t + HZ] @ w)) for t in ends}
    print(f"{n} assets, {len(Rv)} days, {len(ends)} evaluation points, horizon {HZ} days.")

    samp = {t: np.nan_to_num(np.corrcoef(Rv[t - WIN:t], rowvar=False), nan=0.0) for t in ends}
    ew = ewma_corr(Rv, ends)
    z = devol(Rv)
    half = ends[len(ends) // 2]
    cal = [t for t in ends if t <= half]
    ev = [t for t in ends if t > half]

    best, ba, bb = None, None, None
    for a in (0.005, 0.01, 0.02, 0.04):
        for b in (0.90, 0.94, 0.97):
            if a + b >= 0.999:
                continue
            P, _ = dcc_path(z, a, b, ends)
            e = np.mean([offdiag_err(P[t], real[t]) for t in cal])
            if best is None or e < best:
                best, ba, bb = e, a, b
    print(f"  DCC chosen on the calibration half: a={ba}, b={bb} (error there {best:.4f})")
    P, _ = dcc_path(z, ba, bb, ends)

    print(f"\nHELD-OUT HALF, {len(ev)} points")
    print(f"  {'forecaster':<14}{'RMSE off-diag':>15}{'portfolio var error':>22}")
    res = {}
    for name, F in [('sample (60d)', samp), ('ewma', ew), ('dcc', P)]:
        e1 = np.mean([offdiag_err(F[t], real[t]) for t in ev])
        e2 = np.mean([abs(float((vols[t] * w) @ F[t] @ (vols[t] * w)) - realvar[t]) for t in ev])
        res[name] = (e1, e2)
        print(f"  {name:<14}{e1:>15.4f}{e2:>22.3e}")
    b0 = res['sample (60d)']
    print(f"\n  relative to pure persistence:")
    for k in ('ewma', 'dcc'):
        print(f"    {k:<12}structure {100*(res[k][0]/b0[0]-1):>+7.1f}%   "
              f"portfolio variance {100*(res[k][1]/b0[1]-1):>+7.1f}%")
    pd.DataFrame({k: v for k, v in res.items()}, index=['rmse_offdiag', 'var_err']).to_csv(
        RES("corr_forecast_rival.csv"))


if __name__ == "__main__":
    main()
