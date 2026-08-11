"""The saturation measurement cited in Section 4.2 and Section 5.6.

The global balance index saturates on small correlation networks and does not
on large ones. That claim is made in the preprint with numbers, so the numbers
are computed here: the fraction of windows in which the index sits at its
maximum, at several window lengths, on two S&P 500 panels of 447 and 464
constituents.

The panels are not redistributed. The 447-asset one is 2012-2017 and comes from
the public mirror at github.com/liorsidi/sp500-stock-similarity-time-series;
the 464-asset one is 2015-2025 and is assembled from per-ticker CSVs. Point
PANEL5Y and PANEL10Y at them, or run with neither and the script explains what
is missing.

Nothing about investment is measured here. Those experiments live in
explorations/ and are not claimed by the preprint.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

SRC5 = ("https://raw.githubusercontent.com/liorsidi/sp500-stock-similarity-"
        "time-series/master/sandp500/all_stocks_5yr.csv")
PANEL10Y = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")


def kappa(C, binary=False):
    S = C.copy()
    if binary:
        B = np.zeros_like(S)
        B[S > 0.25] = 1
        B[S < -0.25] = -1
        S = B
    np.fill_diagonal(S, 0.0)
    return float(np.trace(expm(S)) / np.trace(expm(np.abs(S))))


def table(ret, label):
    n = ret.shape[1]
    print(f"\n{label}: {n} assets, {len(ret)} days")
    print(f"  {'window':>8}{'windows':>9}{'k min':>9}{'k median':>10}"
          f"{'at max':>9}{'binary at max':>15}")
    for W in (45, 60, 100, 250, 500):
        if W >= len(ret) - 10:
            continue
        K, KB = [], []
        for i in range(W, len(ret), 15):
            C = np.nan_to_num(np.corrcoef(ret[i - W:i], rowvar=False), nan=0.0)
            K.append(kappa(C))
            KB.append(kappa(C, True))
        K, KB = np.array(K), np.array(KB)
        print(f"  {W:>8}{len(K):>9}{K.min():>9.4f}{np.median(K):>10.4f}"
              f"{(K >= K.max() - 1e-12).mean():>9.1%}{(KB >= KB.max() - 1e-12).mean():>15.1%}")


def main():
    try:
        d = pd.read_csv(SRC5)
        d['Date'] = pd.to_datetime(d['Date'])
        px = d.pivot(index='Date', columns='Name', values='Close')
        px = px[px.columns[px.notna().all()]]
        table(np.log(px / px.shift(1)).dropna().values, "S&P 500, 2012-2017")
    except Exception as e:
        print(f"[5-year panel unavailable: {e}]")
    if os.path.exists(PANEL10Y):
        px = pd.read_pickle(PANEL10Y).dropna(axis=1, how='any')
        table(np.log(px / px.shift(1)).dropna().values, "S&P 500, 2015-2025")
    else:
        print(f"\n[10-year panel not found at {PANEL10Y}; set PANEL to its path]")
    print("\nFor contrast, the same measurement on the networks used in the paper is in")
    print("balance_own_regime.py (42 assets) and signed_balance_headtohead.py (8 nodes).")


if __name__ == "__main__":
    main()
