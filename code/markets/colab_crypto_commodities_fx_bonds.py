# Paste this into a Google Colab cell and run it.
# It downloads the four additional markets (crypto, commodities, FX, sovereign debt),
# computes Omega, Omega with memory, the Absorption Ratio and the culprit asset per window,
# and writes one CSV per scenario in the same format used elsewhere in this repository.

!pip install yfinance --quiet

import yfinance as yf
import pandas as pd
import numpy as np
import time

def descargar_precios(tickers, start, end):
    """Download one ticker at a time: slower, but it avoids the inconsistent
    MultiIndex that yf.download returns for lists of tickers."""
    frames = {}
    for t in tickers:
        try:
            df = yf.download(t, start=start, end=end, progress=False)
            if df.empty:
                print(f"WARNING: no data for {t}, skipping")
                continue
            close_col = 'Close' if 'Close' in df.columns else df.columns[0]
            s = df[close_col]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            frames[t] = s
            print(f"OK: {t} ({len(s)} filas)")
        except Exception as e:
            print(f"ERROR en {t}: {e}")
        time.sleep(0.3)
    return pd.DataFrame(frames)

def calculate_omega(corr_matrix):
    n = corr_matrix.shape[0]
    if n < 3:
        return np.nan
    A = np.abs(corr_matrix.values)
    np.fill_diagonal(A, 0)
    A3 = np.linalg.matrix_power(A, 3)
    C = np.trace(A3)
    D = np.sum(A) / (n * (n - 1))
    degrees = np.sum(A, axis=1)
    Coex = np.var(degrees)
    Lap = np.diag(degrees) - A
    eigenvalues = np.sort(np.linalg.eigvalsh(Lap))  # eigvalsh: mas estable, Laplaciano es simetrico
    spectral_gap = eigenvalues[1] if len(eigenvalues) > 1 and eigenvalues[1] > 1e-10 else 1e-5
    M = 1.0 / spectral_gap
    if Coex == 0 or M == 0:
        return np.nan
    return (C * D) / (M * Coex)

def calculate_absorption_ratio(returns_window, k=None):
    n = returns_window.shape[1]
    if k is None:
        k = max(2, int(np.round(n / 5)))
    cov = returns_window.cov().values
    eigvals = np.sort(np.linalg.eigvalsh(cov))[::-1]
    return eigvals[:k].sum() / eigvals.sum()

def run_scenario(tickers, start, end, nombre, window=20, step=3):
    print(f"\n=== {nombre}: descargando {len(tickers)} tickers ===")
    data = descargar_precios(tickers, start, end)
    data = data.dropna(axis=1, how='all').ffill().bfill()
    returns = np.log(data / data.shift(1)).dropna()

    alpha_up, alpha_down = 0.6, 0.08
    results = []
    mem = None
    for i in range(0, len(returns) - window, step):
        win = returns.iloc[i:i + window]
        date = returns.index[i + window - 1]
        corr = win.corr().fillna(0)
        A = np.abs(corr.values)
        np.fill_diagonal(A, 0)
        # Native attribution: the per-node decomposition of Tr(A^3).
        # Validated against synthetic ground truth; it beats both degree and
        # fixed-k spectral attribution when the number of epicentres is unknown
        # (see code/validation/node_attribution_epicenter_test.py and the paper).
        triangles = np.diag(A @ A @ A)
        culprit = corr.columns[np.argmax(triangles)] if triangles.sum() > 0 else None

        omega = calculate_omega(corr)
        ar = calculate_absorption_ratio(win)

        val = omega if not np.isnan(omega) else (mem if mem is not None else 0)
        mem = val if mem is None else (alpha_up*val + (1-alpha_up)*mem if val > mem
                                        else alpha_down*val + (1-alpha_down)*mem)

        results.append({'date': date, 'Omega': omega, 'Omega_memory': mem,
                         'AbsorptionRatio': ar, 'Culprit_asset': culprit})

    res = pd.DataFrame(results)
    fname = f"{nombre}.csv"
    res.to_csv(fname, index=False)
    print(f"Guardado: {fname} ({len(res)} filas)")
    return res

# --- The four additional scenarios ---
run_scenario(['BTC-USD','ETH-USD','BNB-USD','XRP-USD','ADA-USD','SOL-USD','DOGE-USD','DOT-USD','MATIC-USD','AVAX-USD'],
             '2021-01-01', '2024-01-01', 'crypto')

run_scenario(['GC=F','CL=F','NG=F','HG=F','ZC=F','ZW=F','ZS=F'],
             '2021-01-01', '2024-01-01', 'materias_primas')

run_scenario(['EURUSD=X','JPY=X','GBPUSD=X','AUDUSD=X','USDCAD=X','USDCHF=X','USDCNY=X','USDMXN=X','USDINR=X','USDBRL=X'],
             '2021-01-01', '2024-05-01', 'forex')

run_scenario(['TLT','IEF','SHY','BNDX','EMB','VWOB','IGOV','FLOT','TIP','MBB'],
             '2021-01-01', '2024-01-01', 'deuda_soberana')

print("\n\nDone. Four CSVs written: crypto, commodities, fx, sovereign_debt.")
print("Move them to data/raw/ to reproduce the cross-market table.")
