"""Two measurements before deciding whether the line is really dead.

Both failures of the previous run were more specific than "the idea does not
work", and neither of them actually tested what the idea claims.

MEASUREMENT A. The step-zero screen killed Omega as a conditioning variable
because it correlates 0.935 with market volatility. But Omega is ONE NUMBER, and
volatility is one number, so a high correlation between them was always the
likely outcome. The state the index actually produces is diag(A^3), a vector
with one entry per asset. A vector cannot be collinear with a scalar. So the
screen has to be redone at the level where the claim lives: is diag(A^3) per
node collinear with the obvious per-node alternatives, which are each asset's
own volatility, its degree in the correlation network, and its loading on the
leading factor? If it is, the line dies here for good. If it is not, the scalar
result says nothing about the vector one.

MEASUREMENT B. The scenario engine failed on the dollar-neutral portfolio, and
the cause is identified: C = BB' + D with the Marchenko-Pastur truncation keeps
about four factors and throws the residual correlation away, while a neutral
portfolio's variance lives almost entirely in that residual. That is a defect of
the representation, not of the idea, and it has an obvious repair: keep more
factors. This is not moving the goalposts, it is fixing a model whose failure
mode we can name. To keep it honest, the number of factors is chosen on the
FIRST HALF of the sample using the long-short portfolio only, and then evaluated
once on the SECOND half across all four portfolios.

PRE-REGISTERED: the repair works only if, on the held-out half, the long-short
portfolio reaches a KS p above 0.05 at the 1 and 10-day horizons AND the other
three portfolios do not get worse.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.stats import kstest, norm, spearmanr

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP = 60, 10
N_SCEN, BURN, NU = 2000, 40, 6.0
LAMBDA = 0.94
rng = np.random.default_rng(0)


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

    EV, V_, sd_, lead_, ends, tri_, deg_ = [], [], [], [], [], [], []
    for i in range(WIN, len(Rv) - 63, STEP):
        wnd = Rv[i - WIN:i]
        C = np.nan_to_num(np.corrcoef(wnd, rowvar=False), nan=0.0)
        ev, V = np.linalg.eigh(C)
        EV.append(ev); V_.append(V)
        sd_.append(wnd.std(axis=0)); lead_.append(V[:, -1]); ends.append(i)
        A = np.abs(C.copy()); np.fill_diagonal(A, 0.0)
        tri_.append(np.diag(A @ A @ A)); deg_.append(A.sum(1))

    # ---------------- A: is the per-node state collinear with the obvious ones?
    print("A) IS diag(A^3) PER NODE JUST A RESTATEMENT OF SOMETHING SIMPLER?")
    print("   cross-sectional Spearman within each window, averaged over windows")
    r_vol = np.mean([spearmanr(tri_[t], sd_[t]).statistic for t in range(len(ends))])
    r_deg = np.mean([spearmanr(tri_[t], deg_[t]).statistic for t in range(len(ends))])
    r_lead = np.mean([spearmanr(tri_[t], np.abs(lead_[t])).statistic for t in range(len(ends))])
    print(f"   vs the asset's own volatility : {r_vol:+.3f}")
    print(f"   vs its degree, sum |corr|     : {r_deg:+.3f}")
    print(f"   vs |loading on factor 1|      : {r_lead:+.3f}")
    print(f"   (for reference, the scalar Omega vs market volatility was +0.935)\n")

    # ---------------- B: repair the representation, k chosen on the first half
    def run(kind, HZ, k, idx):
        pe, ce, real = [], [], []
        for t in idx:
            i = ends[t]
            if i + HZ > len(Rv):
                continue
            w = weights(kind, n, sd_[t], lead_[t])
            u = sd_[t] * w
            var = np.empty(t)
            for p in range(t):
                ev, V = EV[p], V_[p]
                kk = min(k, n)
                B = V[:, -kk:] * np.sqrt(np.maximum(ev[-kk:], 0))
                d = np.clip(1.0 - (B ** 2).sum(1), 1e-6, None)
                bt = B.T @ u
                var[p] = float(bt @ bt + (d * u * u).sum())
            var *= HZ
            pr_hist = Rv[max(0, i - 250):i] @ w
            mu = float(pr_hist[-WIN:].mean()) * HZ
            sel = rng.integers(0, t, N_SCEN)
            sc = np.sqrt(np.clip(var[sel] * (NU - 2) / NU, 1e-16, None))
            draws = mu + rng.standard_t(NU, N_SCEN) * sc
            r = float((Rv[i:i + HZ] @ w).sum())
            real.append(r); pe.append(float((draws <= r).mean()))
            ce.append([float(np.quantile(draws, q)) for q in (0.025, 0.975)])
        real, ce = np.array(real), np.array(ce)
        cov = ((real >= ce[:, 0]) & (real <= ce[:, 1])).mean()
        return cov, kstest(pe, 'uniform').pvalue

    half = BURN + (len(ends) - BURN) // 2
    cal, ev_idx = range(BURN, half), range(half, len(ends))
    print("B) REPAIRING THE REPRESENTATION. Factor count chosen on the FIRST half,")
    print("   on the long-short portfolio only.")
    print(f"   {'k factors':>10}{'LS cover':>10}{'LS KS p':>10}")
    best, bk = -1, None
    for k in (4, 20, 50, 100, 200):
        c, p = run('longshort', 10, k, cal)
        print(f"   {k:>10}{c:>10.1%}{p:>10.3f}")
        score = -abs(c - 0.95)
        if score > best:
            best, bk = score, k
    print(f"   -> chosen k = {bk}\n")

    print(f"   HELD-OUT HALF with k = {bk}   (nominal 95%)")
    print(f"   {'portfolio':<14}{'1d cover':>10}{'p':>8}{'10d cover':>11}{'p':>8}")
    rows = []
    for kind in ('equal', 'concentrated', 'sectoral', 'longshort'):
        c1, p1 = run(kind, 1, bk, ev_idx)
        c10, p10 = run(kind, 10, bk, ev_idx)
        print(f"   {kind:<14}{c1:>10.1%}{p1:>8.3f}{c10:>11.1%}{p10:>8.3f}")
        rows.append(dict(portfolio=kind, k=bk, cov1=c1, p1=p1, cov10=c10, p10=p10))
    pd.DataFrame(rows).to_csv(RES("scenario_repair.csv"), index=False)


if __name__ == "__main__":
    main()
