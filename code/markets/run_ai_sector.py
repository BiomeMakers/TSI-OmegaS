import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

df = pd.read_csv(RAW("ai_sector_2021_2026.csv"), parse_dates=['Date'])
wide = df.pivot(index='Date', columns='Ticker', values='Close').sort_index()
tickers = list(wide.columns)
n = len(tickers)
rets = np.log(wide).diff().dropna()
dates = rets.index

def gini(x):
    x = np.array(x, dtype=float)
    x = x[x >= 0]
    if len(x) == 0 or x.sum() == 0:
        return 0.0
    x = np.sort(x)
    N = len(x)
    cum = np.cumsum(x)
    return (N + 1 - 2 * (cum.sum() / cum[-1])) / N

def fsri(A):
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
    return Omega

def absorption_ratio(win, k=2):
    cov = win.cov().values
    eigvals = np.linalg.eigvalsh(cov)
    eigvals = np.sort(eigvals)[::-1]
    return eigvals[:k].sum() / eigvals.sum()

for window, step in [(20, 3), (30, 3), (90, 5)]:
    records = []
    for i in range(window, len(rets), step):
        win = rets.iloc[i - window:i]
        corr = win.corr().values
        A = np.abs(corr)
        np.fill_diagonal(A, 0.0)
        Omega = fsri(A)
        AR = absorption_ratio(win, k=2)
        records.append({'date': dates[i-1], 'Omega': Omega, 'AbsorptionRatio': AR})
    res = pd.DataFrame(records)
    res.to_csv(RES(f"ai_omega_w{window}.csv"), index=False)

print("Tickers:", tickers)
print("listo")
