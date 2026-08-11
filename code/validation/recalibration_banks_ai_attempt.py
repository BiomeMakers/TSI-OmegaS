import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

def memory(omega, alpha_up, alpha_down):
    mem = np.zeros_like(omega)
    mem[0] = omega[0]
    for i in range(1, len(omega)):
        if omega[i] > mem[i-1]:
            mem[i] = alpha_up*omega[i] + (1-alpha_up)*mem[i-1]
        else:
            mem[i] = alpha_down*omega[i] + (1-alpha_down)*mem[i-1]
    return mem

def score(mem, crisis, mask, pct):
    m, c = mem[mask], crisis[mask]
    thr = np.quantile(m, pct)
    alarm = m >= thr
    tp = np.sum(alarm & c); fp = np.sum(alarm & ~c); fn = np.sum(~alarm & c)
    p = tp/(tp+fp) if (tp+fp)>0 else 0
    r = tp/(tp+fn) if (tp+fn)>0 else 0
    f1 = 2*p*r/(p+r) if (p+r)>0 else 0
    return f1, p, r

def in_windows(d, windows):
    d = pd.Timestamp(d)
    return any(pd.Timestamp(s)<=d<=pd.Timestamp(e) for _,s,e in windows)

# --- BANKS: corrected list, including the true banking trough (spring 2009) ---
banks = pd.read_csv(RES('banks_full_comparison.csv'), parse_dates=['date'])
bank_crisis_windows = [
    ("New Century / subprime inicio","2007-02-15","2007-04-15"),
    ("Bear Stearns","2008-02-01","2008-04-15"),
    ("Lehman + minimo bancario","2008-08-01","2009-05-31"),
    ("Deuda europea","2011-06-01","2011-12-01"),
]
banks['crisis'] = banks['date'].apply(lambda d: in_windows(d, bank_crisis_windows))
train_mask_b = (banks['date'] < "2010-01-01").values
test_mask_b  = (banks['date'] >= "2010-01-01").values
omega_b = banks['Omega'].values
crisis_b = banks['crisis'].values
print("Filas en crisis (train):", banks.loc[train_mask_b,'crisis'].sum(), "/ (test):", banks.loc[test_mask_b,'crisis'].sum())

# --- AI sector: unchanged ---
ai = pd.read_csv(RES('ai_full_comparison.csv'), parse_dates=['date'])
ai_crisis_windows = [("Selloff 2022","2022-01-01","2022-12-01"),
                      ("DeepSeek","2025-01-20","2025-02-10"),
                      ("Tarifas","2025-03-15","2025-05-01")]
ai['crisis'] = ai['date'].apply(lambda d: in_windows(d, ai_crisis_windows))
train_mask_a = (ai['date'] < "2025-01-01").values
test_mask_a  = (ai['date'] >= "2025-01-01").values
omega_a = ai['Omega'].values
crisis_a = ai['crisis'].values
print("Filas en crisis IA (train):", ai.loc[train_mask_a,'crisis'].sum(), "/ (test):", ai.loc[test_mask_a,'crisis'].sum())

grid_up = [0.4, 0.5, 0.6, 0.7]
grid_down = [0.05, 0.08, 0.12, 0.16]
thresholds = [0.85, 0.90, 0.95]

for label, omega, crisis, train_mask, test_mask in [
    ("BANKS", omega_b, crisis_b, train_mask_b, test_mask_b),
    ("IA", omega_a, crisis_a, train_mask_a, test_mask_a)]:
    print(f"\n=== {label} ===")
    for pct in thresholds:
        results = []
        for au in grid_up:
            for ad in grid_down:
                mem = memory(omega, au, ad)
                f1_tr,_,_ = score(mem, crisis, train_mask, pct)
                f1_te,p_te,r_te = score(mem, crisis, test_mask, pct)
                results.append((au, ad, f1_tr, f1_te, p_te, r_te))
        df_r = pd.DataFrame(results, columns=['au','ad','f1_train','f1_test','prec_test','rec_test'])
        corr = df_r['f1_train'].corr(df_r['f1_test'])
        best = df_r.loc[df_r['f1_train'].idxmax()]
        print(f"  p{int(pct*100)}: corr(train,test)={corr:.2f} | mejor train: au={best.au},ad={best.ad} -> f1_train={best.f1_train:.3f}, f1_test={best.f1_test:.3f} (prec={best.prec_test:.2f}, rec={best.rec_test:.2f})")
