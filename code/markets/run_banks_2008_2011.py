import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

df = pd.read_csv(RAW("banks_2006_2011.csv"), parse_dates=['Date'])
wide = df.pivot(index='Date', columns='Ticker', values='Close').sort_index()
tickers = list(wide.columns)
n = len(tickers)

# daily log returns (the finance standard; better behaved than price levels)
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
    pressure = 3 * A2 * A
    iu = np.triu_indices(n, k=1)
    G = gini(pressure[iu])
    return Omega, C, G, T

results = {}
for window, step in [(20, 3), (30, 3), (90, 5)]:
    records = []
    for i in range(window, len(rets), step):
        win = rets.iloc[i - window:i]
        corr = win.corr().values
        A = np.abs(corr)
        np.fill_diagonal(A, 0.0)
        Omega, C, G, T = fsri(A)
        records.append({'date': dates[i - 1], 'Omega': Omega, 'Gini_pressure': G})
    res = pd.DataFrame(records)
    res.to_csv(RES(f"banks_omega_w{window}.csv"), index=False)
    results[window] = res

def w(label, start, end, window):
    res = results[window]
    m = res[(res.date>=start)&(res.date<=end)]
    print(f"\n--- banks w={window} {label} ---")
    print(m.to_string(index=False))

for win in [20, 30]:
    w("Pre/post Lehman", "2008-08-01", "2008-10-15", win)

print("\nTickers usados:", tickers)
