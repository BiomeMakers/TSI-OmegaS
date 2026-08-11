import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np
from core.persistent_homology import rips_persistence

def takens_embedding(series, dim=3, delay=1):
    """Takens reconstruction: turns a scalar series into a point cloud
    in R^dim using time delays. Methodology of Gidea and Katz (2018)."""
    n = len(series) - (dim - 1) * delay
    return np.array([series[i:i + dim * delay:delay] for i in range(n)])

def h1_landscape_norm(points):
    """Euclidean distance between embedded points, persistent H1 homology,
    and the L1 persistence norm (total lifetime of the loops)."""
    n = len(points)
    D = np.sqrt(((points[:, None, :] - points[None, :, :])**2).sum(-1))
    pairs = rips_persistence(D, max_dim=2)
    h1 = [(b, d) for (dim_, b, d) in pairs if dim_ == 1]
    return sum(d - b for b, d in h1), len(h1)

def process(csv_path, out_name, is_wide_ofr=False, window=20, step=3, embed_dim=3, embed_delay=2):
    if is_wide_ofr:
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        # scalar series: the headline OFR FSI column
        series = df['OFR FSI'].diff().dropna().values
        dates = df['Date'].iloc[1:].reset_index(drop=True)
    else:
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        wide = df.pivot(index='Date', columns='Ticker', values='Close').sort_index()
        # scalar series: equally weighted mean portfolio return (a synthetic index)
        rets = np.log(wide).diff().dropna()
        series = rets.mean(axis=1).values
        dates = rets.index

    # points required per window after the embedding
    needed = window
    records = []
    for i in range(window + embed_dim*embed_delay, len(series), step):
        raw_win = series[i-needed-embed_dim*embed_delay:i]
        pts = takens_embedding(raw_win, dim=embed_dim, delay=embed_delay)
        if len(pts) < 4:
            continue
        h1norm, nloops = h1_landscape_norm(pts)
        d = dates.iloc[i-1] if hasattr(dates, 'iloc') else dates[i-1]
        records.append({'date': d, 'H1_takens': h1norm, 'n_loops': nloops})
    res = pd.DataFrame(records)
    res.to_csv(RES(f"{out_name}_h1_takens.csv"), index=False)
    print(out_name, "listo,", len(res), "filas")
    return res

process(RAW("ofr_financial_stress_index.csv"), 'ofr', is_wide_ofr=True, window=20, step=5)
