"""What would 100,000 euros have done? Walk-forward, from many starting dates.

This is the money version of the comparison, and it is deliberately run from
MANY starting dates rather than one. A single equity curve is a single draw: it
tells you what happened to someone who started on one particular Monday, and
with 5-year horizons the choice of start date moves the answer more than the
strategy does. The distribution across start dates is the evidence; one path is
an anecdote.

SETUP. EuroStoxx reconstruction, N = 46, 2005-2019. Correlation window 60 days,
rebalance every 10 days, position held until the next rebalance. Costs of 10
basis points on each unit of exposure traded, charged at every rebalance.

RULES
  equal       1/N in everything, always. The benchmark they use.
  theirs      their published ESX operating point: hold the assets whose
              balance gap is at least 0.25 in windows where the global balance
              is at least 0.75, and 1/N otherwise.
  tsi         the parameters chosen on the FIRST HALF of the sample in
              esx_calibrated.py, applied here unchanged: fire when Omega is in
              the top 30% of its trailing history, then hold the 5 assets with
              the smallest normalised diag(A^3), and 1/N otherwise.
  tsi_inv     the same with the selection reversed, as a direction control.

NO LOOK-AHEAD. The Omega percentile uses only windows up to the decision date.

WHAT IS REPORTED. For every start date, the terminal value of 100,000 invested
for five years, plus the worst drawdown along the way. Then the distribution
over start dates: median, 10th and 90th percentiles, and the share of start
dates on which each rule finished above 1/N. That last number is the one that
matters: a rule that beats the benchmark on 55% of start dates is noise, one
that beats it on 85% is a finding.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from esx_replication import load, build  # noqa: E402

CAPITAL = 100_000
COST = 0.0010
HORIZON = int(os.environ.get("HORIZON", 126))      # decision points, 10 trading days each
START_EVERY = int(os.environ.get("START_EVERY", 12))
TAU_G, TAU_L = 0.75, 0.25
TSI_PCT, TSI_K = 0.70, 5


def weights(R, j, rule, hist):
    n = len(R.tri.iloc[j])
    w = np.full(n, 1.0 / n)
    row = R.iloc[j]
    if rule == 'equal':
        return w
    if rule == 'theirs':
        if row['kappa'] >= TAU_G:
            pick = np.where(row['gap'] >= TAU_L)[0]
            if len(pick):
                w = np.zeros(n)
                w[pick] = 1.0 / len(pick)
        return w
    if rule in ('tsi', 'tsi_inv'):
        past = hist[:j + 1]
        if len(past) > 30 and row['omega'] >= np.quantile(past, TSI_PCT):
            s = row['tri'] if rule == 'tsi' else -row['tri']
            pick = np.argsort(s)[:TSI_K]
            w = np.zeros(n)
            w[pick] = 1.0 / TSI_K
        return w
    raise ValueError(rule)


def simulate(R, ret, idx_start, rules, hist):
    out = {}
    for rule in rules:
        eq, w_prev = [1.0], None
        for j in range(idx_start, min(idx_start + HORIZON, len(R) - 1)):
            w = weights(R, j, rule, hist)
            turn = np.abs(w - w_prev).sum() if w_prev is not None else 1.0
            a, b = int(R.i.iloc[j]), int(R.i.iloc[j + 1])
            seg = ret.iloc[a:b].values @ w
            v = eq[-1] * (1 - COST * turn)
            for r in seg:
                v *= np.exp(r)
                eq.append(v)
            eq[-1] = v
            w_prev = w
        eq = np.array(eq)
        dd = float((eq / np.maximum.accumulate(eq) - 1).min())
        out[rule] = (eq[-1], dd)
    return out


def main():
    ret = load()
    R, n = build(ret)
    R['i'] = [ret.index.get_loc(d) for d in R.date]
    hist = R.omega.values
    rules = ['equal', 'theirs', 'tsi', 'tsi_inv']
    starts = list(range(30, len(R) - HORIZON, START_EVERY))
    print(f"N={n}, {len(R)} decision points. {len(starts)} start dates, "
          f"{HORIZON} rebalances each (~{HORIZON*10/252:.1f} years), {COST*1e4:.0f} bp per unit traded.\n")

    res = {r: [] for r in rules}
    dds = {r: [] for r in rules}
    for s in starts:
        o = simulate(R, ret, s, rules, hist)
        for r in rules:
            res[r].append(o[r][0] * CAPITAL)
            dds[r].append(o[r][1])
    print(f"  {'rule':<10}{'median':>12}{'p10':>12}{'p90':>12}{'worst':>12}"
          f"{'med. drawdown':>15}{'beats 1/N':>11}")
    base = np.array(res['equal'])
    for r in rules:
        v = np.array(res[r])
        beats = (v > base).mean() if r != 'equal' else np.nan
        print(f"  {r:<10}{np.median(v):>12,.0f}{np.percentile(v,10):>12,.0f}"
              f"{np.percentile(v,90):>12,.0f}{v.min():>12,.0f}"
              f"{np.median(dds[r]):>14.1%}"
              + (f"{beats:>11.0%}" if r != 'equal' else f"{'-':>11}"))
    # Overlapping start dates are not independent observations. The moving-block
    # bootstrap below uses blocks the length of the overlap, so the interval
    # reflects the effective sample size rather than the nominal one.
    overlap = max(1, HORIZON // START_EVERY)
    rngb = np.random.default_rng(0)
    print(f"\n  Paired differences across the {len(starts)} start dates, "
          f"moving-block bootstrap with blocks of {overlap} (the overlap length):")
    print(f"  {'contrast':<24}{'median EUR diff':>17}{'share > 0':>11}{'95% CI of share':>20}")
    for a, b in [('tsi', 'equal'), ('theirs', 'equal'), ('tsi', 'tsi_inv'), ('tsi', 'theirs')]:
        d = np.array(res[a]) - np.array(res[b])
        m = len(d)
        sh = []
        for _ in range(4000):
            idx = []
            while len(idx) < m:
                st = rngb.integers(0, max(1, m - overlap))
                idx.extend(range(st, min(st + overlap, m)))
            sh.append((d[np.array(idx[:m])] > 0).mean())
        lo, hi = np.percentile(sh, [2.5, 97.5])
        print(f"  {a + ' - ' + b:<24}{np.median(d):>17,.0f}{(d > 0).mean():>11.0%}"
              f"{f'[{lo:.0%}, {hi:.0%}]':>20}")
    pd.DataFrame({r: res[r] for r in rules},
                 index=[R.date.iloc[s].date() for s in starts]).to_csv(
        RES(f"euro_backtest_h{HORIZON}.csv"))
    print(f"\n  (first start {R.date.iloc[starts[0]].date()}, "
          f"last {R.date.iloc[starts[-1]].date()})")


if __name__ == "__main__":
    main()
