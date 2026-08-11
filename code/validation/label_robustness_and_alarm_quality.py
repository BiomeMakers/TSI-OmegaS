"""Robustness of every verdict to the choice of crisis list, plus alarm quality.

Two controls that the preprint reports in Section 3.4.

(1) LABEL ROBUSTNESS. Three crisis lists were used at different points in this
    project: 16 narrow episodes (the calibration list), 23 wider windows (the
    list behind every F1 figure) and 25 episodes (the list behind the
    unexplained-alarm rate). Every comparison is re-run under all three, so no
    verdict rests on one labelling. Headline: the tie against effective rank
    holds under all three; the win over the Absorption Ratio does NOT survive
    the narrowest list (p = 0.055 there, against p < 0.0005 on the other two).

(2) ALARM QUALITY. The unexplained-alarm rate, computed for every metric on the
    same 25-episode list rather than for Omega alone. Headline: Omega's alarms
    are the cleanest of any metric tested (4.0% unexplained against 14.7% for
    the effective rank and ~59% for the Absorption Ratio), BUT with the alarm
    budget fixed at the top decile this quantity is exactly 1 - precision, and
    therefore a monotone transform of the F1 already reported. It is the same
    comparison re-expressed, not independent evidence, so the tie against the
    effective rank applies to it too.

Run from code/validation/.
"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
from samefilter_benchmarks import build, f1_at_pct, block_bootstrap, SIGN, asymmetric_filter, D
R=build()
gt=pd.read_csv(D+"results/ofr_ground_truth_final.csv",parse_dates=['date'])
R=R.merge(gt[['date','crisis']].rename(columns={'crisis':'episode25'}),on='date',how='left')

print("="*70)
print("TASK 3: unexplained-alarm rate, same 25-episode list, for every metric")
print("="*70)
for label,sub in [("FULL 2000-2026",R),("OOS 2016-2026",R[R.date>=pd.Timestamp("2016-01-01")])]:
    print(f"\n{label} (n={len(sub)})")
    print(f"{'metrica':<22}{'alarms':>9}{'sin episodio':>14}{'tasa':>9}")
    for col in ['Omega','erank','vendi','AR','erank_data']:
        for mode in ['filtered','raw']:
            x = sub[col+'_filtered'].values if mode=='filtered' else SIGN[col]*sub[col].values
            al = x>=np.quantile(x,0.90)
            n_al=al.sum(); n_un=sub.episode25[al].isna().sum()
            print(f"{col+' ('+mode+')':<22}{n_al:>9}{n_un:>14}{n_un/n_al:>8.1%}")

print()
print("="*70)
print("TASK 1: same verdict under both window lists (all series filtered)")
print("="*70)
cw16=[("2000-03-01","2002-10-01"),("2009-12-01","2010-05-01"),("2010-08-01","2010-10-15"),("2011-06-01","2012-09-01"),
("2013-06-01","2013-09-01"),("2014-02-15","2014-04-15"),("2015-08-01","2015-09-30"),("2016-06-01","2016-08-15"),
("2018-01-15","2018-02-15"),("2018-03-15","2018-04-30"),("2018-10-01","2018-12-31"),("2019-08-01","2019-09-30"),
("2020-02-01","2020-05-01"),("2022-01-01","2022-12-01"),("2023-03-01","2023-04-15"),("2024-07-15","2024-09-15")]
R['crisis23']=R['crisis']
R['crisis16']=R.date.apply(lambda x: any(pd.Timestamp(s)<=x<=pd.Timestamp(e) for s,e in cw16))
# 25-episode list: a window is labelled if it carries an episode name
R['crisis25']=R.episode25.notna()
for lname in ['crisis16','crisis23','crisis25']:
    sub=R[R.date>=pd.Timestamp("2016-01-01")].reset_index(drop=True).copy()
    sub['crisis']=sub[lname]
    c=sub.crisis.values
    print(f"\n--- list {lname}: {c.mean():.1%} of windows labelled as crisis (OOS n={len(sub)}) ---")
    fo=f1_at_pct(sub.Omega_filtered.values,c)
    print(f"   Omega F1={fo:.3f}")
    for col in ['erank','AR','erank_data']:
        f=f1_at_pct(sub[col+'_filtered'].values,c)
        d,lo,hi,p=block_bootstrap(sub,'Omega_filtered',col+'_filtered')
        v='GANA Omega' if lo>0 else ('PIERDE' if hi<0 else 'empate')
        print(f"   {col:<12} F1={f:.3f}  dF1 {d:+.3f} IC[{lo:+.3f},{hi:+.3f}] p={p:.4f} -> {v}")
