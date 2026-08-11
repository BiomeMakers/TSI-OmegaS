import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import pandas as pd
import numpy as np

def correlation_surprise(win):
    """
    Kinlaw & Turkington (2013), 'Correlation Surprise', State Street.
    Decomposes financial turbulence (Mahalanobis distance) into:
    - magnitude surprise: the turbulence there would be if assets were independent
    - correlation surprise: turbulencia_total / magnitude_surprise
      (isolates the contribution of correlation as such, not of the volatility level)
    """
    mu = win.mean().values
    cov = win.cov().values
    y = win.iloc[-1].values - mu
    try:
        turbulence = y @ np.linalg.pinv(cov) @ y
        cov_diag = np.diag(np.diag(cov))
        magnitude = y @ np.linalg.pinv(cov_diag) @ y
        corr_surprise = turbulence / magnitude if magnitude > 0 else np.nan
    except np.linalg.LinAlgError:
        turbulence, magnitude, corr_surprise = np.nan, np.nan, np.nan
    return turbulence, magnitude, corr_surprise

def process(csv_path, out_name, window=20, step=3, is_wide_ofr=False):
    if is_wide_ofr:
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        nodes = ['Credit', 'Equity valuation', 'Safe assets', 'Funding', 'Volatility',
                 'United States', 'Other advanced economies', 'Emerging markets']
        rets = df[nodes].diff().dropna().reset_index(drop=True)
        dates = df['Date'].iloc[1:].reset_index(drop=True)
    else:
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        wide = df.pivot(index='Date', columns='Ticker', values='Close').sort_index()
        rets = np.log(wide).diff().dropna()
        dates = rets.index

    records = []
    for i in range(window, len(rets), step):
        win = rets.iloc[i-window:i]
        turb, mag, cs = correlation_surprise(win)
        records.append({'date': dates.iloc[i-1] if hasattr(dates,'iloc') else dates[i-1],
                         'Turbulence': turb, 'MagnitudeSurprise': mag, 'CorrelationSurprise': cs})
    res = pd.DataFrame(records)
    res.to_csv(RES(f"{out_name}_corrsurprise.csv"), index=False)
    print(out_name, "listo,", len(res), "filas")
    return res

process(RAW("ofr_financial_stress_index.csv"), 'ofr', window=20, step=3, is_wide_ofr=True)
process(RAW("banks_2006_2011.csv"), 'banks', window=20, step=3)
process(RAW("ai_sector_2021_2026.csv"), 'ai', window=20, step=3)
