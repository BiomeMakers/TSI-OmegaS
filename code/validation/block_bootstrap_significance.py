import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

np.random.seed(42)

mem_df = pd.read_csv(RES('ofr_full_history_memory.csv'), parse_dates=['date'])
ar_df = pd.read_csv(RES('ofr_AR_full_history.csv'), parse_dates=['date'])
df = mem_df.merge(ar_df, on='date')

crisis_windows = [
    ("Dot-com/11-S", "2000-03-01", "2002-10-01"),
    ("Crisis financiera global", "2007-08-01", "2009-06-01"),
    ("Deuda griega (inicio)", "2009-12-01", "2010-05-01"),
    ("Flash Crash 2010", "2010-08-01", "2010-10-15"),
    ("Deuda europea", "2011-06-01", "2012-09-01"),
    ("Taper tantrum", "2013-06-01", "2013-09-01"),
    ("Crimea/Rusia", "2014-02-15", "2014-04-15"),
    ("Grexit", "2015-06-15", "2015-07-15"),
    ("Yuan/China", "2015-08-01", "2015-11-10"),
    ("Brexit", "2016-06-01", "2016-09-01"),
    ("Deutsche Bank", "2016-09-10", "2016-10-10"),
    ("Francia/Comey", "2017-04-15", "2017-05-30"),
    ("Corea Norte", "2017-08-01", "2017-09-30"),
    ("Cataluna", "2017-10-01", "2017-10-10"),
    ("Volmageddon", "2018-01-15", "2018-02-15"),
    ("Guerra comercial/Italia/Lira", "2018-03-15", "2018-08-31"),
    ("Selloff Q4 2018", "2018-09-01", "2018-12-31"),
    ("Repo crisis", "2019-08-01", "2019-09-30"),
    ("COVID", "2020-02-01", "2020-07-31"),
    ("Delta/Evergrande", "2021-07-15", "2021-09-30"),
    ("Selloff tasas 2022", "2022-01-01", "2022-12-01"),
    ("SVB/Credit Suisse", "2023-03-01", "2023-04-15"),
    ("Carry trade yen", "2024-07-15", "2024-09-30"),
]

def is_crisis(d):
    d = pd.Timestamp(d)
    for name, s, e in crisis_windows:
        if pd.Timestamp(s) <= d <= pd.Timestamp(e):
            return True
    return False

df['crisis'] = df['date'].apply(is_crisis)
crisis = df['crisis'].values
omega_mem = df['Omega_memory'].values
ar = df['AbsorptionRatio'].values
n = len(df)

def f1_at_pct(x, crisis, pct=0.90):
    thr = np.quantile(x, pct)
    alarm = x >= thr
    tp = np.sum(alarm & crisis); fp = np.sum(alarm & ~crisis); fn = np.sum(~alarm & crisis)
    p = tp/(tp+fp) if (tp+fp)>0 else 0
    r = tp/(tp+fn) if (tp+fn)>0 else 0
    return 2*p*r/(p+r) if (p+r)>0 else 0

f1_mem = f1_at_pct(omega_mem, crisis)
f1_ar  = f1_at_pct(ar, crisis)
observed_diff = f1_mem - f1_ar
print(f"F1 Omega-with-memory: {f1_mem:.4f}")
print(f"F1 Absorption Ratio: {f1_ar:.4f}")
print(f"Observed difference (memory - AR): {observed_diff:.4f}")

# BLOCK bootstrap (preserves temporal autocorrelation): blocks of ~60 windows (~1 quarter)
block_len = 60
n_blocks = n // block_len
B = 2000
diffs_boot = []
for _ in range(B):
    idx = []
    for _ in range(n_blocks + 1):
        start = np.random.randint(0, n - block_len)
        idx.extend(range(start, start + block_len))
    idx = np.array(idx[:n])
    f1_m = f1_at_pct(omega_mem[idx], crisis[idx])
    f1_a = f1_at_pct(ar[idx], crisis[idx])
    diffs_boot.append(f1_m - f1_a)

diffs_boot = np.array(diffs_boot)
ci_low, ci_high = np.percentile(diffs_boot, [2.5, 97.5])
p_value = np.mean(diffs_boot <= 0) if observed_diff > 0 else np.mean(diffs_boot >= 0)

print(f"\nBlock bootstrap (B={B}, block={block_len} windows ~ 1 quarter):")
print(f"95% CI of the difference (memory - AR): [{ci_low:.4f}, {ci_high:.4f}]")
print(f"p-value (one sided, H0: difference <= 0): {p_value:.4f}")
