"""Like-for-like spectral benchmark (Section 3.4 of the preprint).

Rebuilds Omega, the Absorption Ratio, the effective rank and the Vendi score
from the raw OFR series with the paper pipeline (window=20, step=3,
Omega = (C*D/M)*Var(deg) on A=|corr|, AR on the covariance with k=n/5), and
then scores every metric TWICE:

  * raw, with no persistence filter;
  * under the SAME asymmetric filter used for Omega in Section 2.3
    (alpha_up=0.6, alpha_down=0.08), applied to the stress-oriented signal.

The second column is the like-for-like comparison. Filtering Omega and not its
rivals would flatter Omega, because the F1-at-90th-percentile criterion rewards
sustained plateaux, which is exactly what the filter produces.

Reproduces (23-window crisis list):

    OOS 2016-2026, n=897        raw     filtered
      Omega                     0.367   0.447
      effective rank / Vendi    0.347   0.377   tie   (dF1 +0.038, p=0.10)
      Absorption Ratio          0.174   0.134   Omega wins (dF1 +0.219)
      effective rank (returns)  0.179   0.174   Omega wins (dF1 +0.227)

    FULL 2000-2026, n=2232      raw     filtered
      Omega                     0.308   0.389
      effective rank / Vendi    0.310   0.342   tie   (dF1 +0.046, p=0.067)
      Absorption Ratio          0.191   0.175   Omega wins

The filtered Omega column reproduces the released series
data/results/ofr_full_history_memory.csv exactly, which is the check that the
replica is faithful.

Run from code/validation/.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, FIG  # noqa: E402
import numpy as np
import pandas as pd

np.random.seed(42)
D = os.path.join(os.path.dirname(RAW("x")), "..") + os.sep

NODES = ['Credit', 'Equity valuation', 'Safe assets', 'Funding', 'Volatility',
         'United States', 'Other advanced economies', 'Emerging markets']
N_NODES = len(NODES)
WIN, STEP = 20, 3
ALPHA_UP, ALPHA_DOWN = 0.6, 0.08

CRISIS = [("2000-03-01", "2002-10-01"), ("2007-08-01", "2009-06-01"),
          ("2009-12-01", "2010-05-01"), ("2010-08-01", "2010-10-15"),
          ("2011-06-01", "2012-09-01"), ("2013-06-01", "2013-09-01"),
          ("2014-02-15", "2014-04-15"), ("2015-06-15", "2015-07-15"),
          ("2015-08-01", "2015-11-10"), ("2016-06-01", "2016-09-01"),
          ("2016-09-10", "2016-10-10"), ("2017-04-15", "2017-05-30"),
          ("2017-08-01", "2017-09-30"), ("2017-10-01", "2017-10-10"),
          ("2018-01-15", "2018-02-15"), ("2018-03-15", "2018-08-31"),
          ("2018-09-01", "2018-12-31"), ("2019-08-01", "2019-09-30"),
          ("2020-02-01", "2020-07-31"), ("2021-07-15", "2021-09-30"),
          ("2022-01-01", "2022-12-01"), ("2023-03-01", "2023-04-15"),
          ("2024-07-15", "2024-09-30")]

# sign convention: +1 if the metric RISES under stress, -1 if it falls
SIGN = {'Omega': 1, 'AR': 1, 'erank': -1, 'vendi': -1, 'erank_data': -1}


def omega(A):
    A2 = A @ A
    den = A2.sum() - np.trace(A2)
    C = np.trace(A2 @ A) / den if den > 0 else 0.0
    deg = A.sum(1)
    dens = A.sum() / (N_NODES * (N_NODES - 1))
    ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
    M = 1.0 / max(ev[1], 1e-6)
    return (C * dens / M) * np.var(deg)


def absorption_ratio(win, k):
    ev = np.sort(np.linalg.eigvalsh(win.cov().values))[::-1]
    return ev[:k].sum() / ev.sum()


def asymmetric_filter(x, a_up=ALPHA_UP, a_down=ALPHA_DOWN):
    out = np.zeros_like(x, dtype=float)
    out[0] = x[0]
    for i in range(1, len(x)):
        a = a_up if x[i] > out[i - 1] else a_down
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def f1_at_pct(x, crisis, pct=0.90):
    thr = np.quantile(x, pct)
    alarm = x >= thr
    tp = (alarm & crisis).sum()
    fp = (alarm & ~crisis).sum()
    fn = (~alarm & crisis).sum()
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    return 2 * p * r / (p + r) if p + r else 0


def block_bootstrap(sub, col_a, col_b, B=2000, block=60):
    a, b = sub[col_a].values, sub[col_b].values
    c = sub['crisis'].values
    n = len(sub)
    out = []
    for _ in range(B):
        idx = []
        for _ in range(n // block + 1):
            s = np.random.randint(0, n - block)
            idx.extend(range(s, s + block))
        idx = np.array(idx[:n])
        out.append(f1_at_pct(a[idx], c[idx]) - f1_at_pct(b[idx], c[idx]))
    out = np.array(out)
    return out.mean(), np.percentile(out, 2.5), np.percentile(out, 97.5), np.mean(out <= 0)


def build():
    df = (pd.read_csv(D + "raw/ofr_financial_stress_index.csv", parse_dates=['Date'])
            .sort_values('Date').reset_index(drop=True))
    diffs = df[NODES].diff().dropna().reset_index(drop=True)
    dates = df['Date'].iloc[1:].reset_index(drop=True)
    k_ar = max(1, round(N_NODES / 5))
    rows = []
    for i in range(WIN, len(diffs), STEP):
        w = diffs.iloc[i - WIN:i]
        A = np.abs(w.corr().values)
        np.fill_diagonal(A, 0.0)
        corr = np.nan_to_num(w.corr().values, nan=0.0)
        ev = np.clip(np.linalg.eigvalsh(corr), 1e-9, None)
        p = ev / ev.sum()
        erank = float(np.exp(-(p * np.log(p)).sum()))
        sv = np.linalg.svd(w.values - w.values.mean(0), compute_uv=False)
        q = sv / sv.sum()
        q = q[q > 1e-12]
        rows.append(dict(date=dates.iloc[i - 1], Omega=omega(A),
                         AR=absorption_ratio(w, k_ar), erank=erank, vendi=erank,
                         erank_data=float(np.exp(-(q * np.log(q)).sum()))))
    R = pd.DataFrame(rows)
    R['crisis'] = R.date.apply(
        lambda x: any(pd.Timestamp(s) <= x <= pd.Timestamp(e) for s, e in CRISIS))
    for col, sgn in SIGN.items():
        R[col + '_filtered'] = asymmetric_filter(sgn * R[col].values)
    return R


def saturation_check(R):
    """F1 at a fixed percentile is a fixed alarm budget only if the metric takes
    distinct values near the threshold. A metric that saturates at its maximum
    flags far more than the intended fraction and inflates F1 through recall
    alone. This prints the check for every series in the table."""
    print("\nSaturation check (each series must flag 10.0% at its 90th percentile):")
    print(f"  {'series':<24}{'flagged @p90':>14}{'at its max':>12}{'distinct':>10}")
    for col in SIGN:
        for suffix in ('', '_filtered'):
            x = (SIGN[col] * R[col].values) if not suffix else R[col + suffix].values
            thr = np.quantile(x, 0.90)
            name = col + (' (filtered)' if suffix else '')
            print(f"  {name:<24}{(x >= thr).mean():>13.1%}"
                  f"{(x >= x.max() - 1e-12).mean():>12.2%}"
                  f"{len(np.unique(np.round(x, 12))) / len(x):>10.1%}")


def main():
    R = build()
    saturation_check(R)
    released = pd.read_csv(D + "results/ofr_full_history_memory.csv", parse_dates=['date'])
    chk = R.merge(released[['date', 'Omega', 'Omega_memory']], on='date', suffixes=('', '_rel'))
    print(f"replica: n={len(R)}, overlap={len(chk)}, "
          f"corr(Omega)={np.corrcoef(chk.Omega, chk.Omega_rel)[0, 1]:.4f}, "
          f"max|filtered - released memory|={np.abs(chk.Omega_filtered - chk.Omega_memory).max():.2e}")

    for label, sub in [("OOS 2016-2026", R[R.date >= pd.Timestamp("2016-01-01")].reset_index(drop=True)),
                       ("FULL 2000-2026", R)]:
        c = sub['crisis'].values
        print(f"\n=== {label} (n={len(sub)}) ===")
        print(f"{'metric':<24}{'raw':>8}{'filtered':>10}{'dF1':>9}{'95% CI':>22}{'p':>8}  verdict")
        print(f"{'Omega':<24}{f1_at_pct(SIGN['Omega']*sub.Omega.values, c):>8.3f}"
              f"{f1_at_pct(sub.Omega_filtered.values, c):>10.3f}")
        for col in ['erank', 'vendi', 'AR', 'erank_data']:
            raw = f1_at_pct(SIGN[col] * sub[col].values, c)
            filt = f1_at_pct(sub[col + '_filtered'].values, c)
            d, lo, hi, p = block_bootstrap(sub, 'Omega_filtered', col + '_filtered')
            verdict = "Omega wins" if lo > 0 else ("Omega loses" if hi < 0 else "tie")
            print(f"{col:<24}{raw:>8.3f}{filt:>10.3f}{d:>+9.3f}"
                  f"{f'[{lo:+.3f}, {hi:+.3f}]':>22}{p:>8.4f}  {verdict}")


if __name__ == "__main__":
    main()
