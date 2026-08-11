"""Holm-Bonferroni correction over the whole detection family.

This paper runs many related tests, and until now none of them was corrected
for that. The omission was declared rather than hidden, but declaring it is not
the same as fixing it, and a reader is entitled to know which conclusions
survive once the family is accounted for.

THE FAMILY, defined before computing anything so that it cannot be drawn around
a convenient subset. Hypothesis H1 is tested by comparing Omega against every
distinct baseline, on both samples, under all three crisis labellings:

  baselines   effective rank (identical to the Vendi score on a correlation
              matrix, so counted once), the Absorption Ratio, and the effective
              rank computed on the return matrix
  samples     out of sample 2016-2026, and the full history 2000-2026
  labellings  the 16-episode, 23-window and 25-episode lists

That is 3 x 2 x 3 = 18 tests. Every one of them is included, including those
that were never going to be reported as wins, because selecting which tests
enter the family is exactly the manoeuvre the correction exists to prevent.

METHOD. Holm-Bonferroni at a family-wise error rate of 0.05, which is uniformly
more powerful than plain Bonferroni and makes no independence assumption. The
p-values come from the same one-sided block bootstrap used throughout, with
blocks of 60 windows.

WHAT TO EXPECT. The comparisons against the effective rank were already ties
and stay ties, so nothing changes there. The question is which of the wins over
the weaker baselines survive, and in particular whether the win over the
Absorption Ratio survives on the narrowest labelling, which the paper already
flags as its most fragile result.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from samefilter_benchmarks import build, f1_at_pct, block_bootstrap, D  # noqa: E402

ALPHA = 0.05
CW16 = [("2000-03-01", "2002-10-01"), ("2009-12-01", "2010-05-01"),
        ("2010-08-01", "2010-10-15"), ("2011-06-01", "2012-09-01"),
        ("2013-06-01", "2013-09-01"), ("2014-02-15", "2014-04-15"),
        ("2015-08-01", "2015-09-30"), ("2016-06-01", "2016-08-15"),
        ("2018-01-15", "2018-02-15"), ("2018-03-15", "2018-04-30"),
        ("2018-10-01", "2018-12-31"), ("2019-08-01", "2019-09-30"),
        ("2020-02-01", "2020-05-01"), ("2022-01-01", "2022-12-01"),
        ("2023-03-01", "2023-04-15"), ("2024-07-15", "2024-09-15")]


def main():
    R = build()
    gt = pd.read_csv(D + "results/ofr_ground_truth_final.csv", parse_dates=['date'])
    R = R.merge(gt[['date', 'crisis']].rename(columns={'crisis': 'episode25'}),
                on='date', how='left')
    R['crisis23'] = R['crisis']
    R['crisis16'] = R.date.apply(
        lambda x: any(pd.Timestamp(a) <= x <= pd.Timestamp(b) for a, b in CW16))
    R['crisis25'] = R.episode25.notna()

    tests = []
    for sname, sel in [("OOS 2016-2026", R.date >= pd.Timestamp("2016-01-01")),
                       ("FULL 2000-2026", R.date == R.date)]:
        for lname in ['crisis16', 'crisis23', 'crisis25']:
            sub = R[sel].reset_index(drop=True).copy()
            sub['crisis'] = sub[lname]
            c = sub.crisis.values
            for col in ['erank', 'AR', 'erank_data']:
                d, lo, hi, p = block_bootstrap(sub, 'Omega_filtered', col + '_filtered')
                tests.append(dict(sample=sname, labels=lname, baseline=col,
                                  dF1=d, lo=lo, hi=hi, p=p,
                                  f1_omega=f1_at_pct(sub.Omega_filtered.values, c),
                                  f1_base=f1_at_pct(sub[col + '_filtered'].values, c)))
    T = pd.DataFrame(tests).sort_values('p').reset_index(drop=True)
    m = len(T)
    # Holm-Bonferroni, step-down
    T['threshold'] = [ALPHA / (m - i) for i in range(m)]
    surv, still = [], True
    for i in range(m):
        still = still and (T.p.iloc[i] <= T.threshold.iloc[i])
        surv.append(still)
    T['holm'] = surv

    print(f"Family of {m} tests, Holm-Bonferroni at FWER = {ALPHA}\n")
    print(f"  {'sample':<16}{'labels':<10}{'baseline':<12}{'dF1':>8}{'p':>9}"
          f"{'Holm thr':>10}  verdict")
    for i, r in T.iterrows():
        v = "SURVIVES" if r.holm else ("was significant, now not"
                                       if r.p < ALPHA else "tie, unchanged")
        print(f"  {r['sample']:<16}{r['labels']:<10}{r['baseline']:<12}"
              f"{r['dF1']:>+8.3f}{r['p']:>9.4f}{r['threshold']:>10.4f}  {v}")

    n_raw = int((T.p < ALPHA).sum())
    n_holm = int(T.holm.sum())
    print(f"\n  significant before correction: {n_raw} of {m}")
    print(f"  significant after Holm:        {n_holm} of {m}")
    lost = T[(T.p < ALPHA) & (~T.holm)]
    if len(lost):
        print("\n  LOST TO THE CORRECTION:")
        for _, r in lost.iterrows():
            print(f"    {r['sample']}, {r['labels']}, vs {r['baseline']}: "
                  f"dF1 {r['dF1']:+.3f}, p = {r['p']:.4f}")
    T.to_csv(RES("multiple_comparisons.csv"), index=False)


if __name__ == "__main__":
    main()
