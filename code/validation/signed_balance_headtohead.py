"""Head-to-head against the signed-network literature (PRE-REGISTERED).

Motivation. This paper builds its adjacency as A = |rho|, which discards the
sign of every correlation. Two published indices use exactly that discarded
information:

  * Bartesaghi, Diaz-Diaz, Grassi and Uberti, "Global balance and systemic risk
    in financial correlation networks", Physica A 674, 130698 (2025),
    arXiv:2407.14272. The global balance index of the SIGNED correlation
    network as a systemic-risk measure.
  * Bartesaghi, Grassi and Uberti, arXiv:2512.10606 (2025), the local, per-node
    version of the same object.

Tr(A^3) on a signed matrix counts balanced minus frustrated triangles, i.e. it
is the third-order term of the same walk family their index sums over all
lengths. So the two are mathematically adjacent and the comparison is owed.

ARMS (identical windows, identical persistence filter, identical F1 criterion):
  Omega          the published index, A = |rho|
  Omega_signed   same composite, but the triangle numerator computed on the
                 SIGNED matrix. Density, modularity and degree variance stay on
                 |rho|, so the ONLY thing that changes is the sign channel.
  balance_K      tr(exp(S)) / tr(exp(|S|)) with S the signed correlation matrix
                 and zero diagonal: the standard walk-based global balance
                 index. K = 1 is a fully balanced network.
  erank, AR      the baselines already in the paper, for scale.

SIGN CONVENTION, AND A DECLARED DEVIATION FROM THE FIRST RUN. We pre-registered
both signed arms with sign -1, on the reasoning that a balanced network is a
predictable one and that balance should therefore FALL under stress. THE DATA
SAYS THE OPPOSITE, and the reason is obvious in hindsight: under stress every
correlation turns positive, and an all-positive network is by definition
perfectly balanced. Mean balance in labelled crisis windows is 0.972 against
0.962 in calm windows on the OFR network, and 0.810 against 0.621 on the
diversified network. Both signed arms therefore enter with sign +1.

This is an orientation chosen after seeing the data, so we declare it: the
script prints BOTH orientations for balance_K, and the one used in the verdict
table is the one whose crisis-window mean exceeds its calm-window mean. That is
a property of the data and not a fitted parameter, but it is a degree of
freedom and it is reported rather than hidden.

PRE-REGISTERED CRITERION, written before the script was first run: an arm beats
another only if dF1 > 0.05 AND the 95% block-bootstrap CI excludes zero. Same
threshold used elsewhere in this project; not relaxed after seeing anything.

PRE-REGISTERED OUTCOMES:
  (a) Omega_signed beats Omega       -> the sign channel is real and the signed
                                        variant has to be developed properly,
                                        not listed as future work.
  (b) balance_K beats Omega          -> the published index wins on our own
                                        protocol and the paper must say so.
  (c) everything ties                -> the sign channel adds nothing on this
                                        data; the roadmap sentence stands as a
                                        comparison already run, with a null.
  (d) Omega beats both               -> discarding the sign is not a loss here,
                                        which is a positive result for A=|rho|.

CAVEAT OF SCOPE, to be stated wherever this is reported: balance_K here is the
standard combinatorial balance index computed on the full signed correlation
matrix of the same windows. The cited papers derive it from a diffusive process
and apply it to their own asset universe and filtering. This is a like-for-like
reimplementation on our data, not a replication of their results.

Run from anywhere:  python code/validation/signed_balance_headtohead.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

np.random.seed(42)

WIN, STEP = 20, 3
ALPHA_UP, ALPHA_DOWN = 0.6, 0.08
NODES = ['Credit', 'Equity valuation', 'Safe assets', 'Funding', 'Volatility',
         'United States', 'Other advanced economies', 'Emerging markets']

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

SIGN = {'Omega': 1, 'Omega_signed': 1, 'balance_K': 1, 'AR': 1, 'erank': -1}


def composite(A, S, n):
    """Omega on |rho| and the same composite with a signed triangle numerator."""
    A2 = A @ A
    den = A2.sum() - np.trace(A2)
    tri_abs = np.trace(A2 @ A)
    tri_sgn = np.trace(S @ S @ S)
    deg = A.sum(1)
    dens = A.sum() / (n * (n - 1))
    ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
    M = 1.0 / max(ev[1], 1e-6)
    v = np.var(deg)
    if den <= 0:
        return 0.0, 0.0
    return (tri_abs / den * dens / M) * v, (tri_sgn / den * dens / M) * v


def global_balance(S):
    """tr(exp(S)) / tr(exp(|S|)): the walk-based global balance index."""
    return float(np.trace(expm(S)) / np.trace(expm(np.abs(S))))


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


def block_bootstrap(sub, ca, cb, B=2000, block=60):
    a, b, c = sub[ca].values, sub[cb].values, sub['crisis'].values
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
    return out.mean(), np.percentile(out, 2.5), np.percentile(out, 97.5)


def build(values, dates, n):
    rows = []
    for i in range(WIN, len(values), STEP):
        w = values.iloc[i - WIN:i]
        corr = np.nan_to_num(w.corr().values, nan=0.0)
        S = corr.copy()
        np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        om, om_s = composite(A, S, n)
        ev = np.clip(np.linalg.eigvalsh(corr), 1e-9, None)
        p = ev / ev.sum()
        cov = np.sort(np.linalg.eigvalsh(w.cov().values))[::-1]
        rows.append(dict(date=dates.iloc[i - 1], Omega=om, Omega_signed=om_s,
                         balance_K=global_balance(S),
                         erank=float(np.exp(-(p * np.log(p)).sum())),
                         AR=cov[:max(1, round(n / 5))].sum() / cov.sum()))
    R = pd.DataFrame(rows)
    R['crisis'] = R.date.apply(
        lambda x: any(pd.Timestamp(s) <= x <= pd.Timestamp(e) for s, e in CRISIS))
    for col, sgn in SIGN.items():
        R[col + '_f'] = asymmetric_filter(sgn * R[col].values)
    return R


def report(R, title):
    for label, sub in [("OOS 2016-2026", R[R.date >= pd.Timestamp("2016-01-01")].reset_index(drop=True)),
                       ("FULL", R)]:
        if len(sub) < 200:
            continue
        c = sub['crisis'].values
        print(f"\n=== {title} / {label} (n={len(sub)}, {c.mean():.0%} labelled) ===")
        print(f"{'arm':<16}{'raw':>8}{'filtered':>10}   vs Omega: {'dF1':>8}{'95% CI':>22}  verdict")
        for col in ['Omega', 'Omega_signed', 'balance_K', 'erank', 'AR']:
            raw = f1_at_pct(SIGN[col] * sub[col].values, c)
            filt = f1_at_pct(sub[col + '_f'].values, c)
            if col == 'Omega':
                print(f"{col:<16}{raw:>8.3f}{filt:>10.3f}")
                continue
            d, lo, hi = block_bootstrap(sub, 'Omega_f', col + '_f')
            v = ("Omega wins" if (lo > 0 and d > 0.05) else
                 "Omega LOSES" if (hi < 0 and d < -0.05) else "tie")
            print(f"{col:<16}{raw:>8.3f}{filt:>10.3f}{'':>11}{d:>+8.3f}"
                  f"{f'[{lo:+.3f}, {hi:+.3f}]':>22}  {v}")
        for sgn, tag in [(1, 'crisis > calm'), (-1, 'crisis < calm')]:
            print(f"    [orientation check] balance_K sign {sgn:+d} ({tag}): "
                  f"raw {f1_at_pct(sgn*sub.balance_K.values, c):.3f}, "
                  f"filtered {f1_at_pct(asymmetric_filter(sgn*sub.balance_K.values), c):.3f}")
        print(f"    [orientation check] mean balance_K: crisis "
              f"{sub.balance_K[c].mean():.4f} vs calm {sub.balance_K[~c].mean():.4f}")
        print("  corr(Omega, Omega_signed) = "
              f"{np.corrcoef(sub.Omega, sub.Omega_signed)[0,1]:+.3f}   "
              f"corr(Omega, balance_K) = {np.corrcoef(sub.Omega, sub.balance_K)[0,1]:+.3f}   "
              f"balance_K range = [{sub.balance_K.min():.3f}, {sub.balance_K.max():.3f}]")


def main():
    df = (pd.read_csv(RAW("ofr_financial_stress_index.csv"), parse_dates=['Date'])
            .sort_values('Date').reset_index(drop=True))
    diffs = df[NODES].diff().dropna().reset_index(drop=True)
    R = build(diffs, df['Date'].iloc[1:].reset_index(drop=True), len(NODES))
    report(R, "OFR FSI network, n=8 nodes")
    R.to_csv(RES("signed_headtohead_ofr.csv"), index=False)

    try:
        d2 = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"),
                         parse_dates=['Date'])
        px = d2.pivot(index='Date', columns='Ticker', values='Close').dropna(how='any')
        ret = np.log(px / px.shift(1)).dropna()
        R2 = build(ret, pd.Series(ret.index), ret.shape[1])
        report(R2, f"Diversified network, n={ret.shape[1]} assets")
        R2.to_csv(RES("signed_headtohead_diversified.csv"), index=False)
    except Exception as e:
        print(f"\n[diversified network skipped: {e}]")


if __name__ == "__main__":
    main()
