import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

df = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"), parse_dates=['Date'])
wide_full = df.pivot(index='Date', columns='Ticker', values='Close').sort_index()

sectors = {
    'financials': ["JPM","BAC","C","GS","MS","WFC","USB","PNC","COF","AIG"],
    'tech': ["AAPL","MSFT","INTC","CSCO","IBM","ORCL","HPQ","TXN"],
    'industrials': ["GE","CAT","BA","MMM","HON","UPS"],
    'consumer': ["KO","PG","WMT","MCD","DIS","NKE"],
    'energy': ["XOM","CVX","COP"],
    'health': ["JNJ","PFE","UNH","MRK","ABT"],
    'other': ["VZ","T","SO","DD"],
}
# small but diverse subset: 1-2 representative tickers per sector (n=9)
diverse_small = ["JPM","AAPL","GE","KO","XOM","JNJ","VZ","MMM","WMT"]

def fsri(A, n):
    A2 = A @ A; A3 = A2 @ A
    T = np.trace(A3)
    denom = A2.sum() - np.trace(A2)
    C = T/denom if denom>0 else 0.0
    deg = A.sum(axis=1)
    D = A.sum()/(n*(n-1))
    Lap = np.diag(deg)-A
    eigvals = np.sort(np.linalg.eigvalsh(Lap))
    gap = eigvals[1] if len(eigvals)>1 else 1e-9
    M = 1.0/max(gap,1e-6)
    Coex = np.var(deg)
    return (C*D/M)*Coex if M>0 else np.nan

def run(tickers, label, window=20, step=3):
    wide = wide_full[tickers]
    n = len(tickers)
    rets = np.log(wide).diff().dropna()
    dates = rets.index
    records = []
    for i in range(window, len(rets), step):
        win = rets.iloc[i-window:i]
        corr = win.corr().values
        A = np.abs(corr); np.fill_diagonal(A,0.0)
        Omega = fsri(A, n)
        records.append({'date': dates[i-1], 'Omega': Omega})
    res = pd.DataFrame(records)
    res.to_csv(RES(f"subset_{label}.csv"), index=False)
    print(f"{label}: n={n}, {len(res)} windows")
    return res

run(sectors['tech'], 'tech_small_homogeneous')
run(diverse_small, 'diverse_small')
print("\nTickers diversos pequenos usados:", diverse_small)
