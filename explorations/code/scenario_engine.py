"""Part 1: a scenario engine over correlation structure, judged by CALIBRATION.

WHAT THIS IS AND IS NOT. It does not say what will happen. It says which
correlation configurations are plausible, with what probability, and what each
would cost. That is a risk object, not a forecast, and it is therefore not in
conflict with the finding that the index is coincident: a coincident state
reading is exactly what you want to initialise a simulation from.

THE STATE. Each window's correlation matrix is summarised as a factor structure,
C = B B' + D, with B the loadings on the factors that sit above the
Marchenko-Pastur edge and D the idiosyncratic variances. Two reasons for this
representation rather than the raw matrix: it is interpretable (all weight on
one factor is a crisis, spread loadings are calm) and, decisively, ANY (B, D)
reconstructs a valid correlation matrix. Sampling matrix entries directly
produces matrices that are not positive semi-definite, i.e. that correspond to
no possible market, and everything computed on them is meaningless.

THE GENERATOR. Historical mode: block resampling of past states, so every
scenario is a configuration that actually occurred. This is the version a risk
committee accepts without argument, and the only one implemented here. The
synthetic mode, which extrapolates loadings beyond the observed range to produce
the crisis that has not happened yet, needs the dynamics of part 2 and is left
for then.

THE DAMAGE. For a portfolio w, the variance under a scenario is
||B'w||^2 + w'Dw, which needs no matrix to be materialised. Tail loss uses a
multivariate t, not a Gaussian. For the worst scenarios we also report which
assets carry the concentration, using diag(A^3), the attribution layer.

HOW IT IS JUDGED, and this is the whole point. Not by accuracy. By CALIBRATION:
when the engine said 10%, did it happen 10% of the time? Measured with the
probability integral transform of the realised return in the predictive
distribution, which should be uniform, plus the coverage of nominal intervals.
An uncalibrated scenario engine is worse than none, because it manufactures
confidence. The rival is the industry default: a Gaussian with an EWMA
covariance, RiskMetrics style.

NO LOOK-AHEAD. The state pool at time t contains only windows that ended before
t, with a burn-in.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.stats import kstest

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP, HZ = 60, 10, 10          # estimate on 60 days, predict the next 10
N_SCEN, BURN = 2000, 40
LAMBDA = 0.94                        # RiskMetrics decay for the rival
rng = np.random.default_rng(0)


def factorise(C):
    """C = B B' + D with the factors above the Marchenko-Pastur edge."""
    n = C.shape[0]
    ev, V = np.linalg.eigh(C)
    q = n / WIN
    edge = (1 + np.sqrt(q)) ** 2
    k = max(1, int((ev > edge).sum()))
    L, U = ev[-k:], V[:, -k:]
    B = U * np.sqrt(np.maximum(L, 0))
    d = np.clip(1.0 - (B ** 2).sum(1), 1e-6, None)
    return B, d


def main():
    px = pd.read_pickle(PANEL).dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    n = ret.shape[1]
    w = np.full(n, 1.0 / n)

    states, real, vols, mus = [], [], [], []
    for i in range(WIN, len(ret) - HZ, STEP):
        wnd = ret.iloc[i - WIN:i]
        C = np.nan_to_num(wnd.corr().values, nan=0.0)
        B, d = factorise(C)
        states.append((B, d))
        vols.append(wnd.std().values)
        mus.append(float((wnd.values @ w).mean()))
        real.append(float(ret.iloc[i:i + HZ].values @ w).__float__() if False
                    else float((ret.iloc[i:i + HZ].values @ w).sum()))
    print(f"{n} assets, {len(ret)} days, {len(states)} states, "
          f"factors per state: median {int(np.median([b.shape[1] for b,_ in states]))}, "
          f"max {max(b.shape[1] for b,_ in states)}")

    # ---- predictive distributions, walk-forward, no look-ahead
    pit_eng, pit_ewma, cov_eng, cov_ewma = [], [], [], []
    losses_last = None
    for t in range(BURN, len(states)):
        s = vols[t]                                  # current volatility level
        # The predictive distribution must be centred somewhere. Zero is the
        # wrong choice for equities: over this decade the drift is large, and a
        # zero-mean forecast is miscalibrated through the mean alone. We use the
        # trailing in-window mean, and give the rival exactly the same treatment.
        mu = mus[t] * HZ
        pool = rng.integers(0, t, N_SCEN)            # only past states
        draws = np.empty(N_SCEN)
        for j, p in enumerate(pool):
            B, d = states[p]
            sw = s * w
            var = float((B.T @ sw) @ (B.T @ sw) + (d * sw * sw).sum()) * HZ
            # multivariate t tail: chi-square mixing, nu = 6
            nu = 6.0
            scale = np.sqrt(var * (nu - 2) / nu)
            draws[j] = mu + rng.standard_t(nu) * scale
        r = real[t]
        pit_eng.append(float((draws <= r).mean()))
        cov_eng.append([float(np.quantile(draws, q)) for q in (0.025, 0.25, 0.75, 0.975)])
        # rival: Gaussian with EWMA covariance of the same portfolio
        hist = ret.iloc[:].values[:len(ret)]
        end = WIN + t * STEP
        pr = ret.iloc[max(0, end - 250):end].values @ w
        wts = LAMBDA ** np.arange(len(pr))[::-1]
        v = float((wts * pr ** 2).sum() / wts.sum()) * HZ
        sd = np.sqrt(max(v, 1e-12))
        from scipy.stats import norm
        pit_ewma.append(float(norm.cdf(r, mu, sd)))
        cov_ewma.append([float(norm.ppf(q, mu, sd)) for q in (0.025, 0.25, 0.75, 0.975)])
        if t == len(states) - 1:
            losses_last = draws

    def report(name, pit, cov):
        pit = np.array(pit)
        cov = np.array(cov)
        r = np.array(real[BURN:])
        c95 = float(((r >= cov[:, 0]) & (r <= cov[:, 3])).mean())
        c50 = float(((r >= cov[:, 1]) & (r <= cov[:, 2])).mean())
        ks = kstest(pit, 'uniform')
        print(f"  {name:<22}{c95:>10.1%}{c50:>10.1%}{ks.statistic:>10.3f}{ks.pvalue:>10.3f}"
              f"{pit.mean():>10.3f}")

    print(f"\nCALIBRATION over {len(pit_eng)} out-of-sample windows "
          f"(horizon {HZ} days, equal-weight portfolio)")
    print(f"  {'engine':<22}{'95% cover':>10}{'50% cover':>10}{'KS':>10}{'p':>10}{'mean PIT':>10}")
    print(f"  {'nominal':<22}{0.95:>10.1%}{0.50:>10.1%}{'-':>10}{'-':>10}{0.5:>10.3f}")
    report("scenarios (states)", pit_eng, cov_eng)
    report("EWMA gaussian (rival)", pit_ewma, cov_ewma)

    # ---- what the engine says today
    q = np.quantile(losses_last, [0.01, 0.05, 0.25, 0.5])
    print(f"\nTODAY'S SCENARIO DISTRIBUTION, {HZ}-day equal-weight return")
    print(f"  1% worst {q[0]:+.2%}   5% {q[1]:+.2%}   25% {q[2]:+.2%}   median {q[3]:+.2%}")
    for thr in (-0.05, -0.10):
        print(f"  P(loss worse than {thr:.0%}) = {float((losses_last <= thr).mean()):.1%}")

    # ---- attribution in the tail: which assets carry the concentration
    worst = np.argsort([np.trace(np.abs(B @ B.T)) for B, _ in states])[-30:]
    tri = np.zeros(n)
    for p in worst:
        B, d = states[p]
        A = np.abs(B @ B.T)
        np.fill_diagonal(A, 0.0)
        tri += np.diag(A @ A @ A)
    top = np.argsort(-tri)[:10]
    print("\n  assets carrying the concentration in the 30 most concentrated states:")
    print("   ", ", ".join(px.columns[top]))
    pd.DataFrame(dict(pit_scenarios=pit_eng, pit_ewma=pit_ewma,
                      realised=real[BURN:])).to_csv(RES("scenario_calibration.csv"), index=False)


if __name__ == "__main__":
    main()
