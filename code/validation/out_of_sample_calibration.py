import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

res = pd.read_csv(RES('omega_w20.csv'), parse_dates=['date'])
omega_raw = res['Omega'].values
dates = res['date'].values

crisis_windows = [
    ("Dot-com/11-S", "2000-03-01", "2002-10-01"),
    ("Deuda griega (inicio)", "2009-12-01", "2010-05-01"),
    ("Flash Crash 2010", "2010-08-01", "2010-10-15"),
    ("Deuda europea", "2011-06-01", "2012-09-01"),
    ("Taper tantrum", "2013-06-01", "2013-09-01"),
    ("Crimea/Rusia", "2014-02-15", "2014-04-15"),
    ("Devaluacion yuan", "2015-08-01", "2015-09-30"),
    ("Brexit", "2016-06-01", "2016-08-15"),
    ("Volmageddon", "2018-01-15", "2018-02-15"),
    ("Guerra comercial (inicio)", "2018-03-15", "2018-04-30"),
    ("Selloff Q4 2018", "2018-10-01", "2018-12-31"),
    ("Repo crisis", "2019-08-01", "2019-09-30"),
    ("COVID", "2020-02-01", "2020-05-01"),
    ("Selloff tasas 2022", "2022-01-01", "2022-12-01"),
    ("SVB/Credit Suisse", "2023-03-01", "2023-04-15"),
    ("Carry trade yen", "2024-07-15", "2024-09-15"),
]

def is_crisis(d):
    d = pd.Timestamp(d)
    for name, s, e in crisis_windows:
        if pd.Timestamp(s) <= d <= pd.Timestamp(e):
            return True
    return False

crisis_flag = np.array([is_crisis(d) for d in dates])

def memory(omega, alpha_up, alpha_down):
    mem = np.zeros_like(omega)
    mem[0] = omega[0]
    for i in range(1, len(omega)):
        if omega[i] > mem[i-1]:
            mem[i] = alpha_up*omega[i] + (1-alpha_up)*mem[i-1]
        else:
            mem[i] = alpha_down*omega[i] + (1-alpha_down)*mem[i-1]
    return mem

def score(mem, crisis_flag, mask, pct=0.90):
    m = mem[mask]
    c = crisis_flag[mask]
    thr = np.quantile(m, pct)
    alarm = m >= thr
    tp = np.sum(alarm & c)
    fp = np.sum(alarm & ~c)
    fn = np.sum(~alarm & c)
    precision = tp / (tp+fp) if (tp+fp) > 0 else 0
    recall = tp / (tp+fn) if (tp+fn) > 0 else 0
    f1 = 2*precision*recall/(precision+recall) if (precision+recall) > 0 else 0
    return precision, recall, f1

# split temporal: train = 2000-2015, test = 2016-2026 (fuera de muestra real)
train_mask = pd.Series(dates).apply(lambda d: pd.Timestamp(d) < pd.Timestamp("2016-01-01")).values
test_mask = ~train_mask

print(f"Ventanas train (2000-2015): {train_mask.sum()}, test (2016-2026): {test_mask.sum()}")

grid_up = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
grid_down = [0.02, 0.05, 0.08, 0.12, 0.16, 0.20]

results = []
for au in grid_up:
    for ad in grid_down:
        mem = memory(omega_raw, au, ad)
        p_tr, r_tr, f1_tr = score(mem, crisis_flag, train_mask)
        p_te, r_te, f1_te = score(mem, crisis_flag, test_mask)
        results.append({'alpha_up': au, 'alpha_down': ad,
                         'f1_train': f1_tr, 'f1_test': f1_te,
                         'precision_test': p_te, 'recall_test': r_te})

df = pd.DataFrame(results)
df.to_csv(RES('calibration_grid.csv'), index=False)

# selection is by best F1 on TEST (out of sample), not on train
best_test = df.loc[df['f1_test'].idxmax()]
best_train = df.loc[df['f1_train'].idxmax()]

print("\nMejor combinacion optimizando F1 en TRAIN (2000-2015):")
print(best_train)
print("\nF1 de esa combinacion en TEST (fuera de muestra):", 
      df[(df.alpha_up==best_train.alpha_up)&(df.alpha_down==best_train.alpha_down)]['f1_test'].values)

print("\nBest combination optimising F1 on TEST directly (reference only; not the valid choice):")
print(best_test)

print("\nParametros originales (0.6, 0.08) -- evaluados en train y test:")
mem_orig = memory(omega_raw, 0.6, 0.08)
print("train:", score(mem_orig, crisis_flag, train_mask))
print("test:", score(mem_orig, crisis_flag, test_mask))
