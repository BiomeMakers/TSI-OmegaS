"""The balance index in ITS OWN regime: long windows, many assets.

Why. In signed_balance_headtohead.py the global balance index is measured on
20-day windows over 8 or 42 nodes, which is the configuration of this paper. In
that configuration the index SATURATES: correlations are almost all positive,
the network is perfectly balanced, and kappa pins at 1.000 on 26% to 70% of
windows. Comparing on those windows tests the index outside the regime its
authors use, so a favourable result there is not evidence about the index.

Bartesaghi, Diaz-Diaz, Grassi and Uberti (Physica A 674, 130698, 2025) use
400-day windows stepped by 30 days over 385 S&P500 stocks, plus a 50-asset
subset at 100-day windows, plus a 42-stock EuroStoxx set at 45-day windows.
This script reruns the comparison at those three window lengths on the
42-asset diversified network, which is the same size as their EuroStoxx set.

Ground truth is THEIR definition of a systemic event, not our episode list: the
average return across all assets falling below a threshold tau over a 20-day
window. This removes our labelling from the comparison entirely.

Three things are measured:
  1. Does kappa still saturate at longer windows?
  2. Their own headline check: does the conditional mean of average returns
     decrease monotonically as kappa rises? If we reproduce that, our
     implementation and data are sound.
  3. Detection at a genuinely equal alarm budget, plus threshold-free PR-AUC,
     against Omega, the effective rank and the Absorption Ratio.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.stats import spearmanr

TAU = -0.005          # their weaker threshold; -0.01 leaves too few events here
EVENT_WIN = 20        # days, as in their Section 5.2


def global_balance(S):
    return float(np.trace(expm(S)) / np.trace(expm(np.abs(S))))


def binarise(C, thr=0.25):
    B = np.zeros_like(C)
    B[C > thr] = 1.0
    B[C < -thr] = -1.0
    np.fill_diagonal(B, 0.0)
    return B


def omega_paper(A, n):
    """(C * D / M) * Var(deg) with M = 1/lambda_2, exactly as in the preprint."""
    A2 = A @ A
    den = A2.sum() - np.trace(A2)
    if den <= 0:
        return 0.0
    C = np.trace(A2 @ A) / den
    deg = A.sum(1)
    dens = A.sum() / (n * (n - 1))
    ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
    M = 1.0 / max(ev[1], 1e-6)
    return (C * dens / M) * np.var(deg)


def f1_exact(x, c, frac=0.10, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    n = len(x)
    k = max(1, int(round(frac * n)))
    order = np.lexsort((rng.random(n), -x))
    al = np.zeros(n, bool)
    al[order[:k]] = True
    tp = (al & c).sum()
    p = tp / al.sum()
    r = tp / c.sum() if c.sum() else 0
    return (2 * p * r / (p + r) if p + r else 0), p, r


def pr_auc(x, c):
    o = np.argsort(-np.asarray(x, float))
    cc = np.asarray(c)[o]
    tp = np.cumsum(cc)
    prec = tp / np.arange(1, len(cc) + 1)
    rec = tp / cc.sum()
    return float(np.trapezoid(prec, rec))


def main():
    d = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"), parse_dates=['Date'])
    px = d.pivot(index='Date', columns='Ticker', values='Close').dropna(how='any')
    ret = np.log(px / px.shift(1)).dropna()
    n = ret.shape[1]
    # their event definition: cross-sectional mean of the 20-day average return
    avg20 = ret.mean(axis=1).rolling(EVENT_WIN).mean()
    print(f"42 assets, {ret.index.min().date()} to {ret.index.max().date()}, "
          f"{len(ret)} days. Event threshold tau={TAU} on a {EVENT_WIN}-day average.\n")

    for WIN, STEP in [(45, 30), (100, 30), (400, 30)]:
        rows = []
        for i in range(WIN, len(ret), STEP):
            w = ret.iloc[i - WIN:i]
            C = np.nan_to_num(w.corr().values, nan=0.0)
            S = C.copy()
            np.fill_diagonal(S, 0.0)
            A = np.abs(S)
            ev = np.clip(np.linalg.eigvalsh(C), 1e-9, None)
            p = ev / ev.sum()
            cov = np.sort(np.linalg.eigvalsh(w.cov().values))[::-1]
            date = ret.index[i - 1]
            rows.append(dict(date=date,
                             kappa=global_balance(S),
                             kappa_bin=global_balance(binarise(C)),
                             Omega=omega_paper(A, n),
                             erank=-float(np.exp(-(p * np.log(p)).sum())),
                             AR=cov[:max(1, round(n / 5))].sum() / cov.sum(),
                             mean_corr=A[np.triu_indices(n, 1)].mean(),
                             avg20=avg20.get(date, np.nan)))
        R = pd.DataFrame(rows).dropna(subset=['avg20']).reset_index(drop=True)
        c = (R.avg20 < TAU).values
        sat = np.mean(R.kappa >= R.kappa.max() - 1e-12)
        satb = np.mean(R.kappa_bin >= R.kappa_bin.max() - 1e-12)
        rho = spearmanr(R.kappa, R.mean_corr).statistic

        print(f"=== window {WIN} days, step {STEP} -> {len(R)} windows, "
              f"{c.mean():.1%} labelled systemic ===")
        print(f"  saturation: kappa at its max in {sat:.1%} of windows "
              f"(binary {satb:.1%}); kappa range {R.kappa.min():.4f}-{R.kappa.max():.4f}")
        print(f"  their sanity check, Spearman(kappa, mean |corr|) = {rho:.3f} "
              "(they report 0.877 on the S&P500)")
        # their headline: conditional mean of average returns by kappa band
        qs = R.kappa.quantile([0, .2, .4, .6, .8, 1.0]).values
        bands = pd.cut(R.kappa, np.unique(qs), include_lowest=True)
        cm = R.groupby(bands, observed=True).avg20.mean()
        print("  conditional mean of the 20-day average return by kappa quintile:")
        print("    " + "  ".join(f"{v:+.5f}" for v in cm.values)
              + ("   MONOTONE DECREASING (reproduces their result)"
                 if all(np.diff(cm.values) < 0) else "   not monotone"))
        print(f"  {'metric':<12}{'F1@10%':>9}{'prec':>8}{'rec':>8}{'PR-AUC':>9}"
              f"   (base rate {c.mean():.3f})")
        for name in ['Omega', 'kappa', 'kappa_bin', 'erank', 'AR']:
            f, p_, r_ = f1_exact(R[name].values, c)
            print(f"  {name:<12}{f:>9.3f}{p_:>8.3f}{r_:>8.3f}{pr_auc(R[name].values, c):>9.3f}")
        print()
        R.to_csv(RES(f"their_regime_w{WIN}.csv"), index=False)


if __name__ == "__main__":
    main()
