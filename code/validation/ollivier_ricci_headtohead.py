"""The comparison this paper has owed since its first version: Ollivier--Ricci.

Sandhu, Georgiou and Tannenbaum proposed Ricci curvature on the correlation
network as an indicator of market fragility~\\cite{sandhu2016}, and this paper
has named it as the closest structural precedent while declining to benchmark
against it. That was defensible when the comparison had not been run; it is not
a reason to keep not running it. Here it is.

CONSTRUCTION, following the standard used in that literature. Correlations are
mapped to the Mantegna distance $d_{ij} = \\sqrt{2(1-\\rho_{ij})}$, which is the
transformation the financial network literature uses and the one Sandhu et al.
adopt. Each node carries a probability measure over its neighbours proportional
to the absolute correlation. The Ollivier--Ricci curvature of an edge is
$\\kappa_{ij} = 1 - W_1(m_i, m_j)/d_{ij}$, with $W_1$ the earth-mover distance
computed exactly by linear programming on the distance matrix as ground metric.
The market-level scalar is the average edge curvature, reported in both the
unweighted and the correlation-weighted form.

ORIENTATION IS MEASURED, NOT ASSUMED. The declared finding in that literature
is that curvature rises with fragility, but we make the same mistake only once:
both orientations are computed and the one whose crisis-window mean exceeds its
calm-window mean is the one used, with both printed.

PROTOCOL. Identical to every other benchmark in this paper: the same windows,
the same asymmetric persistence filter applied to every series, $F_1$ at the
90th percentile so that all metrics spend the same alarm budget, block
bootstrap for the interval, and all three crisis labellings.

THE FAMILY GROWS. Adding a fourth distinct baseline turns the 18 tests of
Section~\\ref{sec:multiplicity} into 24, so the Holm thresholds tighten. This
script reports the corrected verdict over the enlarged family, because keeping
the old family after adding a test would be the exact manoeuvre the correction
exists to prevent.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from samefilter_benchmarks import (build, f1_at_pct, block_bootstrap,
                                   asymmetric_filter, D, NODES, WIN, STEP)  # noqa: E402

ALPHA = 0.05
CW16 = [("2000-03-01", "2002-10-01"), ("2009-12-01", "2010-05-01"),
        ("2010-08-01", "2010-10-15"), ("2011-06-01", "2012-09-01"),
        ("2013-06-01", "2013-09-01"), ("2014-02-15", "2014-04-15"),
        ("2015-08-01", "2015-09-30"), ("2016-06-01", "2016-08-15"),
        ("2018-01-15", "2018-02-15"), ("2018-03-15", "2018-04-30"),
        ("2018-10-01", "2018-12-31"), ("2019-08-01", "2019-09-30"),
        ("2020-02-01", "2020-05-01"), ("2022-01-01", "2022-12-01"),
        ("2023-03-01", "2023-04-15"), ("2024-07-15", "2024-09-15")]


def w1(mi, mj, dist):
    """Exact earth-mover distance between two distributions on the same nodes."""
    n = len(mi)
    diff = mi - mj
    if np.abs(diff).sum() < 1e-12:
        return 0.0
    c = dist.ravel()
    A_eq, b_eq = [], []
    for i in range(n):                       # row sums = mi
        r = np.zeros((n, n)); r[i, :] = 1
        A_eq.append(r.ravel()); b_eq.append(mi[i])
    for j in range(n):                       # column sums = mj
        r = np.zeros((n, n)); r[:, j] = 1
        A_eq.append(r.ravel()); b_eq.append(mj[j])
    res = linprog(c, A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                  bounds=(0, None), method='highs')
    return float(res.fun) if res.success else np.nan


def curvature(C):
    n = C.shape[0]
    d = np.sqrt(np.clip(2 * (1 - C), 0, None))
    np.fill_diagonal(d, 0.0)
    A = np.abs(C.copy())
    np.fill_diagonal(A, 0.0)
    m = A / np.clip(A.sum(1, keepdims=True), 1e-12, None)
    ks, ws = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if d[i, j] < 1e-9:
                continue
            k = 1.0 - w1(m[i], m[j], d) / d[i, j]
            ks.append(k); ws.append(A[i, j])
    ks, ws = np.array(ks), np.array(ws)
    return float(ks.mean()), float((ks * ws).sum() / max(ws.sum(), 1e-12))


def main():
    R = build()
    df = (pd.read_csv(D + "raw/ofr_financial_stress_index.csv", parse_dates=['Date'])
            .sort_values('Date').reset_index(drop=True))
    diffs = df[NODES].diff().dropna().reset_index(drop=True)
    plain, weighted = [], []
    for i in range(WIN, len(diffs), STEP):
        C = np.nan_to_num(diffs.iloc[i - WIN:i].corr().values, nan=0.0)
        a, b = curvature(C)
        plain.append(a); weighted.append(b)
    R['ricci'] = plain[:len(R)]
    R['ricci_w'] = weighted[:len(R)]

    gt = pd.read_csv(D + "results/ofr_ground_truth_final.csv", parse_dates=['date'])
    R = R.merge(gt[['date', 'crisis']].rename(columns={'crisis': 'episode25'}),
                on='date', how='left')
    R['crisis23'] = R['crisis']
    R['crisis16'] = R.date.apply(
        lambda x: any(pd.Timestamp(a) <= x <= pd.Timestamp(b) for a, b in CW16))
    R['crisis25'] = R.episode25.notna()

    print("ORIENTATION CHECK (mean in labelled crisis windows vs calm, 23-window list)")
    for col in ('ricci', 'ricci_w'):
        c = R.crisis23.values
        print(f"  {col:<10} crisis {R[col][c].mean():+.4f}   calm {R[col][~c].mean():+.4f}   "
              f"-> rises under stress: {R[col][c].mean() > R[col][~c].mean()}")
    sgn = {}
    for col in ('ricci', 'ricci_w'):
        c = R.crisis23.values
        sgn[col] = 1 if R[col][c].mean() > R[col][~c].mean() else -1
        R[col + '_filtered'] = asymmetric_filter(sgn[col] * R[col].values)
    print(f"  signs used: {sgn}\n")

    rows = []
    for sname, sel in [("OOS 2016-2026", R.date >= pd.Timestamp("2016-01-01")),
                       ("FULL 2000-2026", R.date == R.date)]:
        for lname in ['crisis16', 'crisis23', 'crisis25']:
            sub = R[sel].reset_index(drop=True).copy()
            sub['crisis'] = sub[lname]
            c = sub.crisis.values
            for col in ['erank', 'AR', 'erank_data', 'ricci', 'ricci_w']:
                d_, lo, hi, p = block_bootstrap(sub, 'Omega_filtered', col + '_filtered')
                rows.append(dict(sample=sname, labels=lname, baseline=col, dF1=d_,
                                 p=p, f1=f1_at_pct(sub[col + '_filtered'].values, c),
                                 f1_omega=f1_at_pct(sub.Omega_filtered.values, c)))
    T = pd.DataFrame(rows)

    print("HEAD-TO-HEAD AGAINST OLLIVIER-RICCI CURVATURE (filtered, same protocol)")
    print(f"  {'sample':<16}{'labels':<10}{'F1 Omega':>10}{'F1 ricci':>10}"
          f"{'F1 ricci_w':>12}{'dF1 vs ricci':>14}{'p':>9}")
    for sname in T['sample'].unique():
        for lname in ['crisis16', 'crisis23', 'crisis25']:
            a = T[(T['sample'] == sname) & (T.labels == lname)]
            r = a[a.baseline == 'ricci'].iloc[0]
            rw = a[a.baseline == 'ricci_w'].iloc[0]
            print(f"  {sname:<16}{lname:<10}{r.f1_omega:>10.3f}{r.f1:>10.3f}"
                  f"{rw.f1:>12.3f}{r.dF1:>+14.3f}{r.p:>9.4f}")

    # ---- Holm over the enlarged family: 4 distinct baselines x 2 x 3 = 24
    fam = T[T.baseline.isin(['erank', 'AR', 'erank_data', 'ricci'])].copy()
    fam = fam.sort_values('p').reset_index(drop=True)
    m = len(fam)
    fam['threshold'] = [ALPHA / (m - i) for i in range(m)]
    keep, still = [], True
    for i in range(m):
        still = still and (fam.p.iloc[i] <= fam.threshold.iloc[i])
        keep.append(still)
    fam['holm'] = keep
    print(f"\nHOLM OVER THE ENLARGED FAMILY ({m} tests, curvature included)")
    print(f"  significant before correction: {int((fam.p < ALPHA).sum())} of {m}")
    print(f"  significant after Holm:        {int(fam.holm.sum())} of {m}")
    print("\n  surviving comparisons:")
    for _, r in fam[fam.holm].iterrows():
        print(f"    {r['sample']:<16}{r['labels']:<10}vs {r['baseline']:<12}"
              f"dF1 {r['dF1']:+.3f}  p {r['p']:.4f}")
    fam.to_csv(RES("ollivier_ricci.csv"), index=False)


if __name__ == "__main__":
    main()
