"""Head-to-head on 447 S&P 500 stocks: the regime where THEIR rule is defined.

Everything before this was run on universes of 46 (EuroStoxx) or 18 (crypto)
assets, and in both the balance index saturates: kappa sits at 1 because a small
correlation network is almost balanced by combinatorics alone. That made their
published operating point (tau_G = 0.75, tau_L = 0.25) unreachable, which is a
fact about the test bench, not about their index.

With 447 assets it does not saturate. Kappa runs from 0.00 to 0.98 with a median
of 0.45 on 60-day windows, only 1.7% of windows sit at the maximum, and the
local rule selects 2 to 3 assets per window, which is the regime they describe.
So this is the first fair test of their rule, and of ours against it.

DATA. Daily closes of S&P 500 constituents, 2012-08 to 2017-08, from the public
mirror at github.com/liorsidi/sp500-stock-similarity-time-series. Restricted to
the 447 tickers with a complete history. Not redistributed here.

DECLARED LIMITATION. Their methodology asks for a window at least as long as the
number of assets, so that the correlation matrix is full rank. With 447 assets
and five years that is impossible, and we use 60-day windows. Every
eigenvalue-based quantity here is therefore computed on a rank-deficient matrix.
Their own stated advantage is that the balance index does not require full rank,
so this penalises us, not them: Omega's modularity term and the effective rank
are the ones that suffer.

RULES, all with the same basket size per window so none can win by
concentrating more: theirs at their published thresholds; the TSI holding the
same number of assets chosen by smallest normalised diag(A^3); the inverted TSI
as a direction control; and 1/N.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

SRC = ("https://raw.githubusercontent.com/liorsidi/sp500-stock-similarity-"
       "time-series/master/sandp500/all_stocks_5yr.csv")
WIN, STEP, FWD = 60, 10, 5
TAU_G, TAU_L = 0.75, 0.25
N_PERM = 1000
CAPITAL, COST = 100_000, 0.0010
HORIZON, START_EVERY = 25, 6
rng = np.random.default_rng(0)


def load():
    local = RAW("sp500_5yr.csv")
    d = pd.read_csv(local if os.path.exists(local) else SRC)
    d['Date'] = pd.to_datetime(d['Date'])
    px = d.pivot(index='Date', columns='Name', values='Close')
    px = px[px.columns[px.notna().all()]]
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
    for i in range(WIN, len(ret) - max(FWD, HORIZON * STEP), STEP):
        w = ret.iloc[i - WIN:i]
        C = np.nan_to_num(w.corr().values, nan=0.0)
        S = C.copy()
        np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        eS, eA = expm(S), expm(np.abs(S))
        k = float(np.trace(eS) / np.trace(eA))
        tri = np.diag(A @ A @ A)
        rows.append(dict(i=i, date=ret.index[i - 1], kappa=k,
                         gap=k - np.diag(eS) / np.diag(eA),
                         omega=omega_paper(A, n),
                         tri=tri / max(tri.sum(), 1e-12),
                         ins=ret.iloc[i - FWD:i].sum(axis=0).values,
                         oos=ret.iloc[i:i + FWD].sum(axis=0).values))
    return pd.DataFrame(rows), n


def arm(R, n, name, sizes, pick, hz):
    port, bench, sel, ben, perm = [], [], [], [], []
    for j, (_, row) in enumerate(R.iterrows()):
        f = row[hz]
        m = sizes[j]
        if m == 0:
            port.append(f.mean())
        else:
            p = pick(row, m)
            port.append(f[p].mean())
            sel.append(f[p].mean())
            ben.append(f.mean())
            perm.append([f[rng.choice(n, m, replace=False)].mean() for _ in range(N_PERM)])
        bench.append(f.mean())
    port, bench, sel, ben, perm = map(np.array, (port, bench, sel, ben, perm))
    obs = sel.mean() - ben.mean()
    p = float(np.mean(perm.mean(axis=0) - ben.mean() >= obs))
    sr = port.mean() / port.std() * np.sqrt(252 / FWD)
    srb = bench.mean() / bench.std() * np.sqrt(252 / FWD)
    print(f"  {name:<28}{np.exp(port.sum()):>9.2f}{np.exp(bench.sum()):>9.2f}"
          f"{obs*100:>+11.3f}{p:>9.3f}{sr:>8.2f}{srb:>8.2f}")


def main():
    ret = load()
    R, n = build(ret)
    print(f"{n} S&P 500 stocks, {ret.index.min().date()} to {ret.index.max().date()}, "
          f"{len(ret)} days, {len(R)} windows of {WIN} days.\n")
    fire = (R.kappa >= TAU_G).values
    sizes = np.array([int((g >= TAU_L).sum()) if f else 0 for g, f in zip(R.gap, fire)])
    print(f"THEIR OPERATING POINT IS REACHABLE HERE: the global gate fires on "
          f"{fire.mean():.1%} of windows,\n  it selects assets in {(sizes>0).mean():.1%} of "
          f"them, median basket {int(np.median(sizes[sizes>0])) if (sizes>0).any() else 0}, "
          f"mean {sizes[sizes>0].mean():.1f}.")
    print(f"  kappa range {R.kappa.min():.4f} to {R.kappa.max():.4f}, "
          f"median {R.kappa.median():.4f}.")

    for hz, lab in [('ins', 'IN SAMPLE (last 5 days of the window)'),
                    ('oos', 'OUT OF SAMPLE (next 5 days)')]:
        print(f"\n{lab}")
        print(f"  {'rule':<28}{'value':>9}{'1/N':>9}{'basket-1/N':>11}{'p':>9}{'SR':>8}{'SR 1/N':>8}")
        arm(R, n, "theirs: their thresholds", sizes,
            lambda r, m: np.argsort(-r['gap'])[:m], hz)
        arm(R, n, "TSI: same basket size", sizes,
            lambda r, m: np.argsort(r['tri'])[:m], hz)
        arm(R, n, "TSI inverted (control)", sizes,
            lambda r, m: np.argsort(-r['tri'])[:m], hz)
        # The control that decides whether this is network information or just
        # short-horizon mean reversion: pick the worst in-window performers,
        # using no network at all.
        arm(R, n, "worst performers (no network)", sizes,
            lambda r, m: np.argsort(r['ins'])[:m], hz)

    # money, one-year horizons from quarterly starts
    def wts(j, rule):
        w = np.full(n, 1.0 / n)
        row = R.iloc[j]
        m = sizes[j]
        if m == 0 or rule == 'equal':
            return w
        if rule == 'theirs':
            p = np.argsort(-row['gap'])[:m]
        elif rule == 'tsi':
            p = np.argsort(row['tri'])[:m]
        else:
            p = np.argsort(-row['tri'])[:m]
        w = np.zeros(n)
        w[p] = 1.0 / m
        return w

    rules = ['equal', 'theirs', 'tsi', 'tsi_inv']
    starts = list(range(0, len(R) - HORIZON, START_EVERY))
    res = {r: [] for r in rules}
    for s in starts:
        for r in rules:
            eq, wp = 1.0, None
            for j in range(s, s + HORIZON):
                w = wts(j, r)
                turn = np.abs(w - wp).sum() if wp is not None else 1.0
                a, b = int(R.i.iloc[j]), int(R.i.iloc[j + 1])
                eq *= (1 - COST * turn) * np.exp((ret.iloc[a:b].values @ w).sum())
                wp = w
            res[r].append(eq * CAPITAL)
    print(f"\n100,000 FOR ONE YEAR, {len(starts)} quarterly start dates "
          f"(few and heavily overlapping, so read as indicative)")
    print(f"  {'rule':<12}{'median':>12}{'p10':>12}{'p90':>12}{'worst':>12}{'beats 1/N':>11}")
    base = np.array(res['equal'])
    for r in rules:
        v = np.array(res[r])
        b = f"{(v > base).mean():>11.0%}" if r != 'equal' else f"{'-':>11}"
        print(f"  {r:<12}{np.median(v):>12,.0f}{np.percentile(v,10):>12,.0f}"
              f"{np.percentile(v,90):>12,.0f}{v.min():>12,.0f}{b}")
    pd.DataFrame(res, index=[R.date.iloc[s].date() for s in starts]).to_csv(
        RES("sp500_backtest.csv"))


if __name__ == "__main__":
    main()
