import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

df = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"), parse_dates=['Date'])
wide = df.pivot(index='Date', columns='Ticker', values='Close').sort_index()
tickers = list(wide.columns)
n = len(tickers)
print(f"n = {n} activos: {tickers}")

rets = np.log(wide).diff().dropna()
dates = rets.index

def fsri(A, n):
    A2 = A @ A
    A3 = A2 @ A
    T = np.trace(A3)
    denom = A2.sum() - np.trace(A2)
    C = T / denom if denom > 0 else 0.0
    deg = A.sum(axis=1)
    D = A.sum() / (n * (n - 1))
    Lap = np.diag(deg) - A
    eigvals = np.sort(np.linalg.eigvalsh(Lap))
    gap = eigvals[1] if len(eigvals) > 1 else 1e-9
    M = 1.0 / max(gap, 1e-6)
    Coex = np.var(deg)
    Omega = (C * D / M) * Coex if M > 0 else np.nan
    return Omega, C

def absorption_ratio(win, k):
    cov = win.cov().values
    eigvals = np.sort(np.linalg.eigvalsh(cov))[::-1]
    return eigvals[:k].sum() / eigvals.sum()

k_ar = max(1, round(n / 5))  # convencion estandar Kritzman & Li
print(f"k for the Absorption Ratio (n/5, rounded): {k_ar}")

window, step = 20, 3
records = []
for i in range(window, len(rets), step):
    win = rets.iloc[i - window:i]
    corr = win.corr().values
    A = np.abs(corr)
    np.fill_diagonal(A, 0.0)
    Omega, C = fsri(A, n)
    AR = absorption_ratio(win, k_ar)
    records.append({'date': dates[i - 1], 'Omega': Omega, 'Clustering': C, 'AbsorptionRatio': AR})

res = pd.DataFrame(records)

# Omega with persistence memory (the hyperparameters validated earlier)
omega = res['Omega'].values
mem = np.zeros_like(omega)
alpha_up, alpha_down = 0.6, 0.08
mem[0] = omega[0]
for i in range(1, len(omega)):
    if omega[i] > mem[i-1]:
        mem[i] = alpha_up*omega[i] + (1-alpha_up)*mem[i-1]
    else:
        mem[i] = alpha_down*omega[i] + (1-alpha_down)*mem[i-1]
res['Omega_memory'] = mem

res.to_csv(RES("large_network_full.csv"), index=False)
print("\nlisto,", len(res), "ventanas")
print(res.describe())
