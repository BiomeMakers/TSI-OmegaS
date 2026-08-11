"""Does the scenario engine survive outside the one portfolio it was built on?

The engine was calibrated on a single equal-weight portfolio at a single
10-day horizon. That is the weakest possible evidence for a risk engine: the
equal-weight portfolio of 464 stocks is the easiest object in the universe to
model, because idiosyncratic risk is almost entirely diversified away and what
is left is one factor. A risk engine has to hold up on the portfolios people
actually run, and at the horizons they actually report.

FOUR PORTFOLIOS
  equal        1/N. The easy case, kept as the reference.
  concentrated the 10 highest-variance names of the estimation window. Little
               diversification, so the idiosyncratic part of the model matters.
  sectoral     the 50 names loading most on the leading factor: a directional
               bet on one part of the market.
  long-short   dollar-neutral, long the 50 lowest loadings and short the 50
               highest. The hardest case by far, because the market factor
               cancels and what is left is precisely the correlation structure
               the model claims to capture. If the engine is going to fail
               anywhere, it fails here.

THREE HORIZONS: 1 day, 10 days, one quarter (63 days).

Same judgement as before, calibration and not accuracy, and the same rival: a
Gaussian with EWMA variance of the same portfolio, given the same drift term.

STEP ZERO is also here. Omega and the TSI are the same object: Omega is the
symbol, TSI is the name. The question that decides whether a state-dependent
correlation model has anywhere to go is whether that state is anything more
than volatility wearing a hat. If Omega and market volatility correlate at 0.9,
the conditioning variable is already in the literature and the line closes, the
same way the exposure rule closed at 0.85 against volatility targeting.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.stats import kstest, norm, pearsonr, spearmanr

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP = 60, 10
N_SCEN, BURN, NU = 2000, 40, 6.0
LAMBDA = 0.94
rng = np.random.default_rng(0)


def factorise(C):
    n = C.shape[0]
    ev, V = np.linalg.eigh(C)
    edge = (1 + np.sqrt(n / WIN)) ** 2
    k = max(1, int((ev > edge).sum()))
    B = V[:, -k:] * np.sqrt(np.maximum(ev[-k:], 0))
    d = np.clip(1.0 - (B ** 2).sum(1), 1e-6, None)
    return B, d, V[:, -1]


def weights(kind, n, sd, lead):
    if kind == 'equal':
        return np.full(n, 1.0 / n)
    w = np.zeros(n)
    if kind == 'concentrated':
        w[np.argsort(-sd)[:10]] = 0.1
    elif kind == 'sectoral':
        w[np.argsort(-np.abs(lead))[:50]] = 1 / 50
    elif kind == 'longshort':
        o = np.argsort(np.abs(lead))
        w[o[:50]] = 1 / 50
        w[o[-50:]] = -1 / 50
    return w


def main():
    px = pd.read_pickle(PANEL).dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    Rv, n = ret.values, ret.shape[1]

    B_, d_, lead_, sd_, ends = [], [], [], [], []
    omega, kappa, mktvol = [], [], []
    for i in range(WIN, len(Rv) - 63, STEP):
        wnd = Rv[i - WIN:i]
        C = np.nan_to_num(np.corrcoef(wnd, rowvar=False), nan=0.0)
        B, d, lead = factorise(C)
        B_.append(B); d_.append(d); lead_.append(lead)
        sd_.append(wnd.std(axis=0)); ends.append(i)
        A = np.abs(C.copy()); np.fill_diagonal(A, 0.0)
        A2 = A @ A
        den = A2.sum() - np.trace(A2)
        deg = A.sum(1)
        ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
        omega.append((np.trace(A2 @ A) / den * (A.sum() / (n * (n - 1))) * max(ev[1], 1e-6)) * np.var(deg))
        mktvol.append(float(wnd.mean(axis=1).std() * np.sqrt(252)))
    omega, mktvol = np.array(omega), np.array(mktvol)

    print("STEP ZERO: is Omega anything more than market volatility?")
    print(f"  Pearson {pearsonr(omega, mktvol)[0]:+.3f}   "
          f"Spearman {spearmanr(omega, mktvol)[0]:+.3f}   "
          f"(log-Omega vs log-vol Pearson {pearsonr(np.log(omega+1e-12), np.log(mktvol))[0]:+.3f})")
    print(f"  R^2 of a linear fit: {pearsonr(omega, mktvol)[0]**2:.3f}  -> "
          f"{1-pearsonr(omega, mktvol)[0]**2:.0%} of Omega is NOT explained by volatility\n")

    print(f"CALIBRATION ACROSS PORTFOLIOS AND HORIZONS ({len(ends)-BURN} out-of-sample windows)")
    print(f"  {'portfolio':<14}{'HZ':>4}{'engine 95%':>12}{'50%':>7}{'KS p':>8}"
          f"{'rival 95%':>11}{'50%':>7}{'KS p':>8}")
    rows = []
    for kind in ('equal', 'concentrated', 'sectoral', 'longshort'):
        for HZ in (1, 10, 63):
            pe, pr, ce, cr, real = [], [], [], [], []
            for t in range(BURN, len(ends)):
                i = ends[t]
                if i + HZ > len(Rv):
                    continue
                w = weights(kind, n, sd_[t], lead_[t])
                u = sd_[t] * w
                var_all = np.array([float((B_[p].T @ u) @ (B_[p].T @ u) + (d_[p] * u * u).sum())
                                    for p in range(t)]) * HZ
                pr_hist = Rv[max(0, i - 250):i] @ w
                mu = float(pr_hist[-WIN:].mean()) * HZ
                sel = rng.integers(0, t, N_SCEN)
                sc = np.sqrt(np.clip(var_all[sel] * (NU - 2) / NU, 1e-16, None))
                draws = mu + rng.standard_t(NU, N_SCEN) * sc
                r = float((Rv[i:i + HZ] @ w).sum())
                real.append(r)
                pe.append(float((draws <= r).mean()))
                ce.append([float(np.quantile(draws, q)) for q in (0.025, 0.25, 0.75, 0.975)])
                wts = LAMBDA ** np.arange(len(pr_hist))[::-1]
                sd = np.sqrt(max(float((wts * pr_hist ** 2).sum() / wts.sum()) * HZ, 1e-16))
                pr.append(float(norm.cdf(r, mu, sd)))
                cr.append([float(norm.ppf(q, mu, sd)) for q in (0.025, 0.25, 0.75, 0.975)])
            real = np.array(real); ce = np.array(ce); cr = np.array(cr)
            c95e = ((real >= ce[:, 0]) & (real <= ce[:, 3])).mean()
            c50e = ((real >= ce[:, 1]) & (real <= ce[:, 2])).mean()
            c95r = ((real >= cr[:, 0]) & (real <= cr[:, 3])).mean()
            c50r = ((real >= cr[:, 1]) & (real <= cr[:, 2])).mean()
            ke, kr = kstest(pe, 'uniform'), kstest(pr, 'uniform')
            print(f"  {kind:<14}{HZ:>4}{c95e:>12.1%}{c50e:>7.1%}{ke.pvalue:>8.3f}"
                  f"{c95r:>11.1%}{c50r:>7.1%}{kr.pvalue:>8.3f}")
            rows.append(dict(portfolio=kind, hz=HZ, eng95=c95e, eng50=c50e, engp=ke.pvalue,
                             riv95=c95r, riv50=c50r, rivp=kr.pvalue))
    pd.DataFrame(rows).to_csv(RES("scenario_generality.csv"), index=False)
    print("\n  nominal: 95.0% and 50.0%; KS p below 0.05 means the calibration is rejected")


if __name__ == "__main__":
    main()
