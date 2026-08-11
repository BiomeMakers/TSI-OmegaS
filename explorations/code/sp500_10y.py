"""Ten years, 464 S&P 500 stocks: the decisive run of the investment line.

The five-year panel gave the first positive result of this line: both the
balance rule and the TSI rule beat 1/N out of sample by about 1.5 to 1.6 points
over five days, and the effect survived a control that picks the worst in-window
performers with no network at all. The obvious objection was that 2012-2017 is
one bull market. This run answers it: 2015-12 to 2025-12, 464 tickers with a
complete history, and the same table computed on each half separately.

DATA. Per-ticker CSVs downloaded from Kaggle by the user (S&P 500, ten years,
yfinance format with the two-row header). Not redistributed. Point PANEL at the
assembled price matrix.

SURVIVORSHIP, declared. The ticker list is current index membership, so these
are firms that are in the index today and had ten years of history. That
inflates any long-equity strategy in absolute terms. It does not obviously bias
the comparison, since every arm trades the same names, and their own datasets
carry the same restriction by construction.

ARMS, all with the same basket size per window: their rule at their published
thresholds; the TSI on the smallest normalised diag(A^3); the inverted TSI as a
direction control; and the worst in-window performers, which is the control that
distinguishes network information from short-horizon reversal.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP, FWD = 60, 10, 5
TAU_G, TAU_L = 0.75, 0.25
N_PERM = 500
rng = np.random.default_rng(0)


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


def arm(R, n, name, sizes, pick, hz):
    sel, ben, perm = [], [], []
    for j, (_, row) in enumerate(R.iterrows()):
        m = sizes[j]
        if m == 0:
            continue
        f = row[hz]
        p = pick(row, m)
        sel.append(f[p].mean())
        ben.append(f.mean())
        perm.append([f[rng.choice(n, m, replace=False)].mean() for _ in range(N_PERM)])
    sel, ben, perm = np.array(sel), np.array(ben), np.array(perm)
    obs = sel.mean() - ben.mean()
    p = float(np.mean(perm.mean(axis=0) - ben.mean() >= obs))
    sr = sel.mean() / sel.std() * np.sqrt(252 / FWD) if sel.std() else 0
    srb = ben.mean() / ben.std() * np.sqrt(252 / FWD) if ben.std() else 0
    print(f"  {name:<32}{len(sel):>6}{obs*100:>+11.3f}{p:>9.3f}{sr:>8.2f}{srb:>8.2f}")


def table(R, n, sizes, label):
    print(f"\n{label}   ({(sizes>0).sum()} windows fire)")
    for hz, h in [('ins', 'in sample (last 5 days of window)'),
                  ('oos', 'OUT OF SAMPLE (next 5 days)')]:
        print(f"  -- {h}")
        print(f"  {'rule':<32}{'n':>6}{'basket-1/N':>11}{'p':>9}{'SR':>8}{'SR 1/N':>8}")
        arm(R, n, "theirs: their thresholds", sizes, lambda r, m: np.argsort(-r['gap'])[:m], hz)
        arm(R, n, "TSI: same basket", sizes, lambda r, m: np.argsort(r['tri'])[:m], hz)
        arm(R, n, "TSI inverted (control)", sizes, lambda r, m: np.argsort(-r['tri'])[:m], hz)
        arm(R, n, "worst performers (no network)", sizes, lambda r, m: np.argsort(r['ins'])[:m], hz)


def main():
    px = pd.read_pickle(PANEL) if PANEL.endswith('.pkl') else pd.read_csv(PANEL, index_col=0, parse_dates=True)
    px = px.dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    R, n = build(ret)
    print(f"{n} S&P 500 stocks, {ret.index.min().date()} to {ret.index.max().date()}, "
          f"{len(ret)} days, {len(R)} windows.")
    fire = (R.kappa >= TAU_G).values
    sizes = np.array([int((g >= TAU_L).sum()) if f else 0 for g, f in zip(R.gap, fire)])
    print(f"  kappa {R.kappa.min():.4f} to {R.kappa.max():.4f}, median {R.kappa.median():.4f}, "
          f"{(R.kappa >= R.kappa.max()-1e-12).mean():.1%} at its maximum")
    print(f"  their gate fires on {fire.mean():.1%} of windows, selects assets in "
          f"{(sizes>0).mean():.1%}, median basket "
          f"{int(np.median(sizes[sizes>0])) if (sizes>0).any() else 0}")

    table(R, n, sizes, "FULL PERIOD")
    mid = R.date.iloc[len(R) // 2]
    for lab, mask in [(f"FIRST HALF (to {mid.date()})", (R.date <= mid).values),
                      (f"SECOND HALF (from {mid.date()})", (R.date > mid).values)]:
        table(R, n, sizes * mask, lab)
    R.drop(columns=['gap', 'tri', 'ins', 'oos']).to_csv(RES("sp500_10y.csv"), index=False)


if __name__ == "__main__":
    main()
