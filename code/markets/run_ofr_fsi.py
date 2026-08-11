import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

df = pd.read_csv(RAW("ofr_financial_stress_index.csv"), parse_dates=['Date'])
df = df.sort_values('Date').reset_index(drop=True)

nodes = ['Credit', 'Equity valuation', 'Safe assets', 'Funding', 'Volatility',
         'United States', 'Other advanced economies', 'Emerging markets']
n = len(nodes)

# daily changes (first differences): we measure co-movement of stress, not levels
diffs = df[nodes].diff().dropna().reset_index(drop=True)
dates = df['Date'].iloc[1:].reset_index(drop=True)

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
    # A: weighted, non-negative, symmetric adjacency matrix with zero diagonal
    A2 = A @ A
    A3 = A2 @ A
    T = np.trace(A3)
    # weighted clustering coefficient, Tr(A^3) / (sum(A^2) - Tr(A^2))
    denom = A2.sum() - np.trace(A2)
    C = T / denom if denom > 0 else 0.0
    deg = A.sum(axis=1)
    D = A.sum() / (n * (n - 1))
    # modularity proxy: inverse spectral gap of the Laplacian
    Lap = np.diag(deg) - A
    eigvals = np.sort(np.linalg.eigvalsh(Lap))
    gap = eigvals[1] if len(eigvals) > 1 else 1e-9
    M = 1.0 / max(gap, 1e-6)
    Coex = np.var(deg)
    Omega = (C * D / M) * Coex if M > 0 else np.nan
    # per-edge topological pressure and its Gini coefficient
    pressure = 3 * A2 * A
    iu = np.triu_indices(n, k=1)
    G = gini(pressure[iu])
    return Omega, C, G, T

# The paper's headline configuration is (window=20, step=3); the 30- and 90-day
# windows are the robustness checks reported alongside it. All three are written
# out, because the plotting and calibration scripts consume them by name.
for window, step in [(20, 3), (30, 3), (90, 5)]:
    records = []
    for i in range(window, len(diffs), step):
        win = diffs.iloc[i - window:i]
        corr = win.corr().values
        A = np.abs(corr)
        np.fill_diagonal(A, 0.0)
        Omega, C, G, T = fsri(A)
        records.append({
            'date': dates.iloc[i - 1],
            'Omega': Omega,
            'Clustering': C,
            'Gini_pressure': G,
            'Tr_A3': T
        })

    res = pd.DataFrame(records)
    res.to_csv(RES(f"omega_w{window}.csv"), index=False)
    if window == 90:
        # kept under its historical name for code/plotting/plot_omega.py
        res.to_csv(RES("omega_timeseries.csv"), index=False)
    print(f"\n=== window={window}, step={step} ===")
    print(res.describe())
    print(res.tail(5))
