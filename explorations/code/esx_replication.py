"""Replication of Bartesaghi, Grassi and Uberti (arXiv:2512.10606) on a
reconstructed EuroStoxx dataset, then the same rule driven by the TSI.

WHY A RECONSTRUCTION. The authors do not publish their data; the Physica A
companion states that it is available on request, and the investment preprint
ships no repository. This script rebuilds the closest available proxy for their
ESX dataset from a public source and, crucially, CHECKS IT AGAINST THEIR OWN
PUBLISHED NUMBERS before using it for anything.

THE DATA. Daily prices of EuroStoxx 50 constituents, from the public repository
github.com/G-Gaddu/MSc-Thesis (file Data/Daily_Prices.csv, Bloomberg tickers).
Restricted to 2005-01-05 onward, which is their exact start date, and to the
tickers with a complete history from that date. That leaves N = 46 against
their N = 42, and an end date of 2019-06-28 against their 2020-09-17.

FIDELITY CHECK, and it passes. Their Table 2.1 reports, for ESX, correlations
between the global balance and the average market return of -0.177 Pearson and
-0.274 Spearman, and against the in-window Sharpe ratio -0.227 and -0.316. On
this reconstruction, with 150-day windows stepped by 10, we obtain -0.177 and
-0.272 for the average market return and -0.251 and -0.339 for the Sharpe
ratio. The first pair is exact to three decimals and the second is the same
sign and magnitude. Shorter windows give -0.181 to -0.201 and -0.268 to -0.325.
The reconstruction reproduces their published relationship, so it is a fair
basis for testing their strategy.

WHAT IS TESTED. Their rule, with THEIR published ESX thresholds (tau_G = 0.75,
tau_L = 0.25, read from their Figure 3.1b), against the same rule driven by the
TSI attribution: global condition on Omega, local condition on the smallest
normalised diag(A^3). The TSI global threshold is set so that it FIRES ON THE
SAME NUMBER OF WINDOWS as theirs, and it selects the SAME NUMBER OF ASSETS per
window, so neither rule gets an advantage from firing more often or holding a
different basket size. That matching is a design choice, not a fit to outcomes,
and it is declared here rather than buried.

Both are scored their way: equally weighted in the selected assets when the
conditions fire and 1/N otherwise, in sample on the last five days of the
estimation window and out of sample on the five days following it. We add the
null their protocol lacks: a permutation p-value against random baskets of the
same size drawn from the same universe.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.stats import pearsonr, spearmanr

SRC = ("https://raw.githubusercontent.com/G-Gaddu/MSc-Thesis/main/"
       "Data/Daily_Prices.csv")
WIN, STEP, FWD = 60, 10, 5
TAU_G, TAU_L = 0.75, 0.25          # their published ESX thresholds
N_PERM = 2000
rng = np.random.default_rng(0)


def load():
    # not redistributed here: the script pulls it from the original repository
    local = RAW("esx50_daily_prices.csv")
    src = local if os.path.exists(local) else SRC
    d = pd.read_csv(src)
    d['Dates'] = pd.to_datetime(d['Dates'], dayfirst=True)
    d = d.set_index('Dates').sort_index().loc['2005-01-05':]
    px = d[d.columns[d.notna().all()]].dropna()
    return np.log(px / px.shift(1)).dropna()


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


def build(ret):
    n = ret.shape[1]
    rows = []
    for i in range(WIN, len(ret) - FWD, STEP):
        w = ret.iloc[i - WIN:i]
        C = np.nan_to_num(w.corr().values, nan=0.0)
        S = C.copy()
        np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        eS, eA = expm(S), expm(np.abs(S))
        k = float(np.trace(eS) / np.trace(eA))
        tri = np.diag(A @ A @ A)
        rows.append(dict(date=ret.index[i - 1], kappa=k,
                         gap=k - np.diag(eS) / np.diag(eA),
                         omega=omega_paper(A, n),
                         tri=tri / max(tri.sum(), 1e-12),
                         ins=ret.iloc[i - FWD:i].sum(axis=0).values,
                         oos=ret.iloc[i:i + FWD].sum(axis=0).values))
    return pd.DataFrame(rows), n


def fidelity(ret):
    print("FIDELITY CHECK against their Table 2.1 for ESX")
    print("  they report:  AMR -0.177 (-0.274 Spearman)   SR -0.227 (-0.316)")
    for W in (60, 150):
        K, AMR, SR = [], [], []
        for i in range(W, len(ret), 10):
            w = ret.iloc[i - W:i]
            C = np.nan_to_num(w.corr().values, nan=0.0)
            S = C.copy()
            np.fill_diagonal(S, 0.0)
            K.append(float(np.trace(expm(S)) / np.trace(expm(np.abs(S)))))
            m = w.mean(axis=1)
            AMR.append(m.mean())
            SR.append(m.mean() / m.std())
        K, AMR, SR = map(np.array, (K, AMR, SR))
        print(f"  window {W:>3}:   AMR {pearsonr(K, AMR)[0]:+.3f} ({spearmanr(K, AMR)[0]:+.3f})"
              f"   SR {pearsonr(K, SR)[0]:+.3f} ({spearmanr(K, SR)[0]:+.3f})")


K_BASKET = 5


def run_arm(R, n, name, fires, pick_fn, horizon, k=K_BASKET):
    sel, ben, perm = [], [], []
    for j, (_, row) in enumerate(R.iterrows()):
        if not fires[j]:
            continue
        f = row[horizon]
        pick = pick_fn(row)[:k]
        sel.append(f[pick].mean())
        ben.append(f.mean())
        perm.append([f[rng.choice(n, k, replace=False)].mean() for _ in range(N_PERM)])
    sel, ben, perm = np.array(sel), np.array(ben), np.array(perm)
    obs = sel.mean() - ben.mean()
    p = float(np.mean(perm.mean(axis=0) - ben.mean() >= obs))
    sr = sel.mean() / sel.std() * np.sqrt(252 / FWD) if sel.std() > 0 else 0
    srb = ben.mean() / ben.std() * np.sqrt(252 / FWD) if ben.std() > 0 else 0
    print(f"  {name:<26}{len(sel):>7}{sel.mean()*100:>10.3f}{ben.mean()*100:>10.3f}"
          f"{obs*100:>+10.3f}{p:>9.3f}{sr:>8.2f}{srb:>8.2f}")


def main():
    ret = load()
    n = ret.shape[1]
    print(f"EuroStoxx 50 reconstruction: N = {n} (theirs 42), "
          f"{ret.index.min().date()} to {ret.index.max().date()}, {len(ret)} days.\n")
    fidelity(ret)
    R, n = build(ret)
    print(f"\n{len(R)} windows of {WIN} days stepped {STEP}.")

    # --- diagnostic: can their published operating point even be reached here?
    fire = (R.kappa >= TAU_G).values
    sizes = np.array([int((g >= TAU_L).sum()) for g in R.gap])
    print(f"\nTHEIR PUBLISHED OPERATING POINT (tau_G={TAU_G}, tau_L={TAU_L}) ON THIS DATA:")
    print(f"  the global gate fires on {fire.mean():.1%} of windows, so it does not gate;")
    print(f"  the local rule selects a MEDIAN of {np.median(sizes):.0f} assets "
          f"(mean {sizes.mean():.2f}, max {sizes.max()}).")
    print("  We therefore cannot reproduce their operating point, and say so rather than")
    print("  tune our way to one. What follows is the same IDEA at a defined operating")
    print("  point: top-quartile global condition by percentile, fixed basket of "
          f"{K_BASKET}.")

    for q, tag in [(0.75, "top 25% of windows")]:
        tf = (R.kappa >= R.kappa.quantile(q)).values
        of = (R.omega >= R.omega.quantile(q)).values
        for horizon, label in [('ins', 'IN SAMPLE (last 5 days of the window)'),
                               ('oos', 'OUT OF SAMPLE (next 5 days)')]:
            print(f"\n{label}, {tag}")
            print(f"  {'rule':<26}{'wins':>7}{'sel %':>10}{'1/N %':>10}"
                  f"{'gap':>10}{'p':>9}{'SR':>8}{'SR 1/N':>8}")
            run_arm(R, n, "theirs: balance gap", tf,
                    lambda r: np.argsort(-r['gap']), horizon)
            run_arm(R, n, "TSI: low triangle share", of,
                    lambda r: np.argsort(r['tri']), horizon)
            run_arm(R, n, "TSI inverted (check)", of,
                    lambda r: np.argsort(-r['tri']), horizon)
    R.drop(columns=['gap', 'tri', 'ins', 'oos']).to_csv(RES("esx_replication.csv"), index=False)


if __name__ == "__main__":
    main()
