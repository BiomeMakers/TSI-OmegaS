"""TSI attribution as a stock-selection signal, against the balance-gap rule.

PRE-REGISTERED. Criterion and outcomes written before the script was first run.

THE RULE WE ARE COPYING. Bartesaghi, Grassi and Uberti (arXiv:2512.10606,
q-fin.PM) propose this: in a crisis every asset moves together, the global
balance of the signed correlation network approaches its maximum, and ordinary
diversification stops working. So concentrate the portfolio in the few assets
that are NOT behaving like the rest. They identify those as the nodes whose
LOCAL balance departs most from the global balance, select
SA = {i : kappa(G) >= tau_G and kappa(G) - kappa_i >= tau_L}, hold them equally
weighted when the conditions fire and hold 1/N otherwise, and score by the
average return over the five days FOLLOWING the estimation window.

THE TRANSLATION TO TSI. The logic transfers directly, because diag(A^3) is a
per-node reading of exactly the same kind. The global condition becomes "Omega
is in its upper tail", i.e. the index says the market is in a stressed state.
The local condition becomes "this asset carries little of the triangle
pressure", i.e. the smallest normalised diag(A^3): the assets that are not part
of the stressed cluster. Same shape, different primitive.

WHAT THIS SCRIPT ADDS TO THEIR PROTOCOL, and it is the same thing our paper
adds to their detection work: a null. They compare the selected stocks against a
random equal-sized draw from the remainder and read the moments. We keep that
comparison and attach a permutation p-value to it, so that "the selected assets
did better" can be distinguished from "any five assets would have".

DESIGN. 42-asset diversified network, 2006-2026, daily log returns. Note the
coincidence of size: their ESX dataset also has N = 42. Rolling windows of 60
days (>= N, so the correlation matrix is full rank, their condition) stepped by
10 days (their step). Forward horizon 5 days (their horizon). Both selection
signals are given the SAME cardinality k and the SAME global-condition
percentile, so the only thing that differs is which assets get picked.

PRE-REGISTERED CRITERION. A selection rule works if, over the windows where its
global condition fires, the mean forward return of the selected basket exceeds
the 1/N basket AND the permutation p-value against random baskets of the same
size is below 0.05. Both conditions, not either.

PRE-REGISTERED OUTCOMES.
  (a) Both rules work    -> two independent confirmations of the same idea, and
                            the comparison is about which is stronger.
  (b) Only theirs works  -> the balance gap carries selection information that
                            triangle share does not; report and stop.
  (c) Only ours works    -> the attribution advantage measured on synthetic
                            epicentres transfers to a real decision.
  (d) Neither works      -> the effect is not reproducible on this universe.
                            Report the null; do NOT go looking for a window
                            length or a threshold that rescues it.

DECLARED LIMITATION, stated before running rather than after. Their thresholds
are calibrated per dataset, which their own text says is required for the
strategy to outperform. We avoid that free parameter by fixing the cardinality
k and sweeping the global percentile, but a sweep is still a sweep: the honest
reading of any positive result here is "survives a small grid", not "validated".
No transaction costs are modelled, and concentrating in five assets carries a
risk that a Sharpe ratio over 5-day windows does not capture.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

WIN, STEP, FWD = 60, 10, 5
K_SELECT = 5
N_PERM = 2000
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


def build():
    d = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"), parse_dates=['Date'])
    px = d.pivot(index='Date', columns='Ticker', values='Close').dropna(how='any')
    ret = np.log(px / px.shift(1)).dropna()
    n = ret.shape[1]
    rows = []
    for i in range(WIN, len(ret) - FWD, STEP):
        w = ret.iloc[i - WIN:i]
        fwd = ret.iloc[i:i + FWD].sum(axis=0).values      # 5-day forward log return
        C = np.nan_to_num(w.corr().values, nan=0.0)
        S = C.copy()
        np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        eS, eA = expm(S), expm(np.abs(S))
        kappa = float(np.trace(eS) / np.trace(eA))
        kappa_i = np.diag(eS) / np.diag(eA)
        tri = np.diag(A @ A @ A)
        rows.append(dict(date=ret.index[i - 1], omega=omega_paper(A, n), kappa=kappa,
                         gap=kappa - kappa_i,                 # theirs: large = deviates
                         tri_share=tri / max(tri.sum(), 1e-12),  # ours: small = decoupled
                         fwd=fwd))
    return pd.DataFrame(rows), n, list(ret.columns)


def evaluate(R, n, global_col, score, k=K_SELECT, pct=0.75, label=""):
    """score: (row -> array) larger value = more likely to be selected."""
    thr = R[global_col].quantile(pct)
    fired = R[R[global_col] >= thr]
    sel_r, bench_r, perm = [], [], []
    for _, row in fired.iterrows():
        s = np.asarray(score(row), float)
        pick = np.argsort(-s)[:k]
        f = row['fwd']
        sel_r.append(f[pick].mean())
        bench_r.append(f.mean())
        perm.append([f[rng.choice(n, k, replace=False)].mean() for _ in range(N_PERM)])
    sel_r, bench_r = np.array(sel_r), np.array(bench_r)
    perm = np.array(perm)                       # windows x N_PERM
    obs = sel_r.mean() - bench_r.mean()
    null = perm.mean(axis=0) - bench_r.mean()
    p = float(np.mean(null >= obs))
    sharpe = sel_r.mean() / sel_r.std() * np.sqrt(252 / FWD) if sel_r.std() > 0 else 0
    sharpe_b = bench_r.mean() / bench_r.std() * np.sqrt(252 / FWD) if bench_r.std() > 0 else 0
    print(f"  {label:<22}{len(fired):>7}{sel_r.mean() * 100:>11.3f}{bench_r.mean() * 100:>11.3f}"
          f"{obs * 100:>+10.3f}{p:>9.3f}{sharpe:>9.2f}{sharpe_b:>9.2f}")
    return obs, p


def main():
    R, n, tickers = build()
    print(f"{n} assets, {len(R)} windows of {WIN} days stepped {STEP}, "
          f"forward horizon {FWD} days, basket of {K_SELECT}.\n")
    print(f"  correlation(omega, kappa) = {np.corrcoef(R.omega, R.kappa)[0, 1]:+.3f}\n")
    for pct in (0.50, 0.75, 0.90):
        print(f"global condition: top {100 * (1 - pct):.0f}% of windows")
        print(f"  {'rule':<22}{'windows':>7}{'sel %':>11}{'1/N %':>11}{'gap':>10}"
              f"{'p':>9}{'SR sel':>9}{'SR 1/N':>9}")
        evaluate(R, n, 'kappa', lambda r: r['gap'], pct=pct,
                 label="theirs: balance gap")
        evaluate(R, n, 'omega', lambda r: -r['tri_share'], pct=pct,
                 label="ours: low triangle")
        evaluate(R, n, 'omega', lambda r: r['tri_share'], pct=pct,
                 label="ours inverted (check)")
        evaluate(R, n, 'kappa', lambda r: -r['tri_share'], pct=pct,
                 label="cross: kappa + triangle")
        print()
    R.drop(columns=['fwd', 'gap', 'tri_share']).to_csv(RES("investment_rule.csv"), index=False)


if __name__ == "__main__":
    main()
