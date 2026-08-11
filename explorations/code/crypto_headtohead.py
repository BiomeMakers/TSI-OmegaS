"""Both indices on crypto: the market where correlations are most extreme.

WHY CRYPTO. Everything measured so far on equities left the same open question:
the global balance index saturates because correlation networks are almost
entirely positive, and we could not tell how much of that was the asset class.
Crypto is the extreme case of the same phenomenon. If saturation is a property
of the construction rather than of a particular market, it should be worse here
than anywhere. It is also a fair second universe for the investment rule, with
frequent, sharp and well-separated stress episodes.

DATA. Daily PriceUSD from the Coin Metrics community dataset, a public
repository (github.com/coinmetrics/data). Assets are the 18 with a complete
history from 2018-07-01, which is the date at which the set stops shrinking.
Not redistributed here: the script downloads what it needs.

WHAT IS RUN
  1. Saturation of the balance index, weighted and binary, at four window
     lengths.
  2. Their Table 2.1 relationship: does a high balance still go with a poor
     average market return and a poor in-window Sharpe, as it does in equities?
  3. The investment head-to-head, on the design that survived scrutiny: 1-year
     horizons from quarterly start dates, costs charged, no look-ahead, and a
     moving-block bootstrap sized to the overlap.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.stats import pearsonr, spearmanr

BASE = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/"
ASSETS = ['btc', 'eth', 'ltc', 'xrp', 'bch', 'ada', 'xlm', 'xmr', 'dash', 'zec',
          'etc', 'doge', 'link', 'bnb', 'neo', 'eos', 'trx', 'xtz']
START = "2018-07-01"
WIN, STEP = 60, 10
CAPITAL, COST = 100_000, 0.0010
HORIZON, START_EVERY = 25, 6
TAU_G, TAU_L = 0.75, 0.25
TSI_PCT, TSI_K = 0.70, 5
rng = np.random.default_rng(0)


def load():
    cache = RAW("crypto_prices_coinmetrics.csv")
    if os.path.exists(cache):
        px = pd.read_csv(cache, index_col=0, parse_dates=True)
    else:
        cols = {}
        for a in ASSETS:
            d = pd.read_csv(BASE + a + ".csv", usecols=['time', 'PriceUSD'],
                            parse_dates=['time']).dropna().set_index('time')
            cols[a] = d['PriceUSD']
        px = pd.DataFrame(cols).loc[START:].dropna()
    return np.log(px / px.shift(1)).dropna()


def kappa(C, binary=False):
    S = C.copy()
    if binary:
        B = np.zeros_like(S)
        B[S > 0.25] = 1.0
        B[S < -0.25] = -1.0
        S = B
    np.fill_diagonal(S, 0.0)
    return float(np.trace(expm(S)) / np.trace(expm(np.abs(S)))), S


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


def main():
    ret = load()
    n = ret.shape[1]
    print(f"{n} crypto assets, {ret.index.min().date()} to {ret.index.max().date()}, "
          f"{len(ret)} days.\n")

    print("1) SATURATION OF THE BALANCE INDEX")
    print(f"   {'window':>7}{'windows':>9}{'k min':>8}{'k med':>8}{'at max':>9}"
          f"{'binary at max':>15}{'mean |corr|':>13}")
    for W in (30, 60, 100, 200):
        K, KB, MC = [], [], []
        for i in range(W, len(ret), 10):
            C = np.nan_to_num(ret.iloc[i - W:i].corr().values, nan=0.0)
            k, S = kappa(C)
            kb, _ = kappa(C, binary=True)
            K.append(k)
            KB.append(kb)
            MC.append(np.abs(S)[np.triu_indices(n, 1)].mean())
        K, KB = np.array(K), np.array(KB)
        print(f"   {W:>7}{len(K):>9}{K.min():>8.4f}{np.median(K):>8.4f}"
              f"{(K >= K.max() - 1e-12).mean():>9.1%}{(KB >= KB.max() - 1e-12).mean():>15.1%}"
              f"{np.mean(MC):>13.3f}")

    rows = []
    for i in range(WIN, len(ret) - HORIZON * STEP, STEP):
        w = ret.iloc[i - WIN:i]
        C = np.nan_to_num(w.corr().values, nan=0.0)
        k, S = kappa(C)
        A = np.abs(S)
        eS, eA = expm(S), expm(np.abs(S))
        tri = np.diag(A @ A @ A)
        m = w.mean(axis=1)
        rows.append(dict(i=i, date=ret.index[i - 1], kappa=k,
                         gap=k - np.diag(eS) / np.diag(eA),
                         omega=omega_paper(A, n),
                         tri=tri / max(tri.sum(), 1e-12),
                         amr=m.mean(), sharpe=m.mean() / m.std()))
    R = pd.DataFrame(rows)
    print(f"\n2) THEIR TABLE 2.1 RELATIONSHIP, on crypto ({len(R)} windows)")
    print(f"   balance vs average market return: {pearsonr(R.kappa, R.amr)[0]:+.3f} "
          f"Pearson ({spearmanr(R.kappa, R.amr)[0]:+.3f} Spearman)")
    print(f"   balance vs in-window Sharpe:      {pearsonr(R.kappa, R.sharpe)[0]:+.3f} "
          f"({spearmanr(R.kappa, R.sharpe)[0]:+.3f})")
    print("   for reference, on equities they report -0.177 (-0.274) and -0.227 (-0.316)")

    def w_of(j, rule, hist):
        w = np.full(n, 1.0 / n)
        row = R.iloc[j]
        if rule == 'equal':
            return w
        if rule == 'theirs' and row['kappa'] >= TAU_G:
            pick = np.where(row['gap'] >= TAU_L)[0]
            if len(pick):
                w = np.zeros(n)
                w[pick] = 1.0 / len(pick)
        if rule in ('tsi', 'tsi_inv'):
            past = hist[:j + 1]
            if len(past) > 30 and row['omega'] >= np.quantile(past, TSI_PCT):
                s = row['tri'] if rule == 'tsi' else -row['tri']
                pick = np.argsort(s)[:TSI_K]
                w = np.zeros(n)
                w[pick] = 1.0 / TSI_K
        return w

    rules = ['equal', 'theirs', 'tsi', 'tsi_inv']
    hist = R.omega.values
    starts = list(range(30, len(R) - HORIZON, START_EVERY))
    res = {r: [] for r in rules}
    for s in starts:
        for r in rules:
            eq, wp = 1.0, None
            for j in range(s, s + HORIZON):
                w = w_of(j, r, hist)
                turn = np.abs(w - wp).sum() if wp is not None else 1.0
                a, b = int(R.i.iloc[j]), int(R.i.iloc[j + 1])
                eq *= (1 - COST * turn) * np.exp((ret.iloc[a:b].values @ w).sum())
                wp = w
            res[r].append(eq * CAPITAL)
    print(f"\n3) 100,000 INVESTED FOR ONE YEAR, {len(starts)} quarterly start dates")
    print(f"   {'rule':<10}{'median':>12}{'p10':>12}{'p90':>12}{'worst':>12}{'beats 1/N':>11}")
    base = np.array(res['equal'])
    for r in rules:
        v = np.array(res[r])
        b = f"{(v > base).mean():>11.0%}" if r != 'equal' else f"{'-':>11}"
        print(f"   {r:<10}{np.median(v):>12,.0f}{np.percentile(v,10):>12,.0f}"
              f"{np.percentile(v,90):>12,.0f}{v.min():>12,.0f}{b}")
    ov = max(1, HORIZON // START_EVERY)
    print(f"\n   paired, moving-block bootstrap with blocks of {ov}:")
    for a, b in [('tsi', 'equal'), ('theirs', 'equal'), ('tsi', 'tsi_inv')]:
        d = np.array(res[a]) - np.array(res[b])
        m = len(d)
        sh = []
        for _ in range(4000):
            idx = []
            while len(idx) < m:
                st = rng.integers(0, max(1, m - ov))
                idx.extend(range(st, min(st + ov, m)))
            sh.append((d[np.array(idx[:m])] > 0).mean())
        lo, hi = np.percentile(sh, [2.5, 97.5])
        print(f"   {a + ' - ' + b:<20}{(d > 0).mean():>8.0%}   95% CI [{lo:.0%}, {hi:.0%}]")
    pd.DataFrame(res, index=[R.date.iloc[s].date() for s in starts]).to_csv(
        RES("crypto_backtest.csv"))


if __name__ == "__main__":
    main()
