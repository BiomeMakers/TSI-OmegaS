"""
Lead-lag analysis (Section 3.6d): is Omega a leading indicator or a coincident
state index?

The F1-at-90th-percentile criterion used elsewhere in this repository asks
whether Omega is *elevated during* documented stress windows. That is a
contemporaneous classification test and says nothing about whether Omega rises
*before* stress. Since "fragility index" invites the stronger reading, this
script tests the stronger claim directly.

Method: cross-correlate each signal against the OFR Financial Stress Index at
lags k in [-15, +30] observations (each step ~3 business days). k > 0 means the
signal leads. Reported both on levels and on first differences, because both
series are strongly autocorrelated in levels and the absolute rho there is not
the object of interest -- the informative feature is the SHAPE of the
cross-correlation function.

Headline: Omega peaks at k = 0 and decays symmetrically. It is a coincident
state index, not a leading indicator. This does not affect the F1 result (always
contemporaneous) but it does constrain the permissible framing.

Usage:
    python leadlag_analysis.py
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DATA = os.path.join(os.path.dirname(RAW("x")), "..")


def load() -> pd.DataFrame:
    mem = pd.read_csv(os.path.join(DATA, "results", "ofr_full_history_memory.csv"),
                      parse_dates=["date"])
    ar = pd.read_csv(os.path.join(DATA, "results", "ofr_AR_full_history.csv"),
                     parse_dates=["date"])
    fsi = pd.read_csv(os.path.join(DATA, "raw", "ofr_financial_stress_index.csv"),
                      parse_dates=["Date"])
    d = (mem.merge(ar, on="date")
            .merge(fsi[["Date", "OFR FSI"]], left_on="date", right_on="Date")
            .dropna().sort_values("date").reset_index(drop=True))
    return d


def cross_correlation(signal: np.ndarray, target: np.ndarray,
                      lo: int = -15, hi: int = 31) -> dict:
    """rho(k) for k in [lo, hi). k > 0 means the signal leads the target."""
    out = {}
    for k in range(lo, hi):
        if k >= 0:
            a, b = signal[:len(signal) - k], target[k:]
        else:
            a, b = signal[-k:], target[:len(signal) + k]
        m = np.isfinite(a) & np.isfinite(b)
        out[k] = spearmanr(a[m], b[m])[0]
    return out


def summarise(name: str, xc: dict, n: int) -> None:
    peak = max(xc, key=lambda k: abs(xc[k]))
    thr = 1.96 / np.sqrt(n)
    verdict = ("leads" if peak > 2 else
               "coincident" if abs(peak) <= 2 else "lags")
    print(f"  {name:22s} peak k={peak:+3d} (rho={xc[peak]:+.3f}) | "
          f"k=0 {xc[0]:+.3f} | k=+1 {xc.get(1, float('nan')):+.3f} | {verdict}")
    if abs(xc.get(1, 0.0)) < thr:
        print(f"{'':24s}(rho at k=+1 is within the +/-{thr:.3f} noise band)")


def main():
    d = load()
    print(f"n = {len(d)} | {d.date.min().date()} -> {d.date.max().date()}")
    print("each observation step is ~3 business days\n")

    print("=== LEVELS ===")
    for label, col in [("Omega with memory", "Omega_memory"),
                       ("Omega raw", "Omega"),
                       ("Absorption Ratio", "AbsorptionRatio")]:
        summarise(label, cross_correlation(d[col].values, d["OFR FSI"].values), len(d))

    print("\n=== FIRST DIFFERENCES (the rigorous version) ===")
    dd = d.copy()
    for c in ["Omega_memory", "Omega", "AbsorptionRatio", "OFR FSI"]:
        dd[c] = dd[c].diff()
    dd = dd.dropna()
    for label, col in [("d(Omega with memory)", "Omega_memory"),
                       ("d(Omega raw)", "Omega"),
                       ("d(Absorption Ratio)", "AbsorptionRatio")]:
        summarise(label, cross_correlation(dd[col].values, dd["OFR FSI"].values), len(dd))

    print("\nInterpretation: a leading indicator would peak at k > 0 with an "
          "asymmetric\ncross-correlation function. Omega peaks at k ~ 0 and decays "
          "symmetrically,\nwhich is the signature of a coincident relationship.")


if __name__ == "__main__":
    main()
