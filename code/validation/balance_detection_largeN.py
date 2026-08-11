"""The detection benchmark against the global balance index, in the regime where
it is defined.

Section~\\ref{sec:balancebench} declines to rank the global balance index on the
networks used in the main results, because on eight and 42 nodes it saturates
and any ranking would describe a degenerate regime. That was the right call and
it left an obvious gap: the index has never been benchmarked against ours
anywhere.

It can be, on a large universe. On 464 S&P 500 constituents the index does not
saturate: kappa runs over most of the unit interval and only a small fraction of
windows sit at the maximum. This script runs the comparison there.

GROUND TRUTH IS THEIRS, NOT OURS. A window is labelled systemic if the
cross-sectional mean return over the following 20 trading days falls below a
threshold, which is the definition used in the original work. Using their
labelling rather than our episode lists removes our own judgement from the
comparison entirely, and it is the single most important design choice here.
Two thresholds are reported.

EVERYTHING ELSE IS THE STANDARD PROTOCOL of this paper: the same 60-day windows,
the same asymmetric persistence filter applied to every series, F1 at the 90th
percentile so all metrics spend the same alarm budget, and a block bootstrap for
the interval. Orientation is measured for every series, not assumed.

THE SATURATION CHECK RUNS FIRST, because a fixed percentile is a fixed alarm
budget only when the metric takes distinct values there. Any series that flags
materially more than 10% of windows is disqualified before it is scored.

NOT INCLUDED: Ollivier--Ricci curvature. On 464 nodes it requires an exact
optimal transport solve on more than a hundred thousand edges per window, which
is a different cost regime; it is benchmarked on the main network instead.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP, EVENT = 60, 10, 20
ALPHA_UP, ALPHA_DOWN = 0.6, 0.08
rng = np.random.default_rng(0)


def asym(x, a_up=ALPHA_UP, a_dn=ALPHA_DOWN):
    o = np.zeros_like(x, dtype=float)
    o[0] = x[0]
    for i in range(1, len(x)):
        a = a_up if x[i] > o[i - 1] else a_dn
        o[i] = a * x[i] + (1 - a) * o[i - 1]
    return o


def f1(x, c, pct=0.90):
    thr = np.quantile(x, pct)
    al = x >= thr
    tp = (al & c).sum()
    p = tp / al.sum() if al.sum() else 0
    r = tp / c.sum() if c.sum() else 0
    return (2 * p * r / (p + r) if p + r else 0), al.mean()


def boot(a, b, c, B=2000, block=20):
    n = len(c)
    out = []
    for _ in range(B):
        idx = []
        while len(idx) < n:
            s = rng.integers(0, max(1, n - block))
            idx.extend(range(s, min(s + block, n)))
        idx = np.array(idx[:n])
        out.append(f1(a[idx], c[idx])[0] - f1(b[idx], c[idx])[0])
    out = np.array(out)
    return out.mean(), np.percentile(out, 2.5), np.percentile(out, 97.5), float(np.mean(out <= 0))


def omega(A, n):
    A2 = A @ A
    den = A2.sum() - np.trace(A2)
    if den <= 0:
        return 0.0
    C = np.trace(A2 @ A) / den
    deg = A.sum(1)
    dens = A.sum() / (n * (n - 1))
    ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
    return (C * dens * max(ev[1], 1e-6)) * np.var(deg)


def main():
    px = pd.read_pickle(PANEL).dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    Rv, n = ret.values, ret.shape[1]
    rows = []
    for i in range(WIN, len(Rv) - EVENT, STEP):
        w = Rv[i - WIN:i]
        C = np.nan_to_num(np.corrcoef(w, rowvar=False), nan=0.0)
        S = C.copy(); np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        B = np.zeros_like(S); B[S > 0.25] = 1; B[S < -0.25] = -1
        ev = np.clip(np.linalg.eigvalsh(C), 1e-9, None)
        p = ev / ev.sum()
        cov = np.sort(np.linalg.eigvalsh(np.cov(w, rowvar=False)))[::-1]
        rows.append(dict(
            Omega=omega(A, n),
            kappa=float(np.trace(expm(S)) / np.trace(expm(np.abs(S)))),
            kappa_bin=float(np.trace(expm(B)) / np.trace(expm(np.abs(B)))),
            erank=float(np.exp(-(p * np.log(p)).sum())),
            AR=cov[:max(1, round(n / 5))].sum() / cov.sum(),
            fwd=float(Rv[i:i + EVENT].mean()),
            now=float(Rv[i - EVENT:i].mean())))
    R = pd.DataFrame(rows)
    cols = ['Omega', 'kappa', 'kappa_bin', 'erank', 'AR']
    print(f"{n} S&P 500 stocks, {len(R)} windows of {WIN} days.\n")

    print("SATURATION CHECK (a fixed percentile is a fixed alarm budget only if the")
    print("metric takes distinct values there)")
    print(f"  {'series':<12}{'at its max':>12}{'distinct':>11}{'flagged @p90':>14}")
    ok = []
    for k in cols:
        x = R[k].values
        atmax = (x >= x.max() - 1e-12).mean()
        dis = len(np.unique(np.round(x, 12))) / len(x)
        fl = (x >= np.quantile(x, 0.90)).mean()
        print(f"  {k:<12}{atmax:>12.1%}{dis:>11.1%}{fl:>14.1%}")
        if fl <= 0.12:
            ok.append(k)
        elif k == 'AR':
            print("     (the Absorption Ratio is identically 1 here: with a 60-day window")
            print("      and 464 assets the covariance has rank 59, so the top n/5 = 93")
            print("      eigenvalues capture the whole trace by construction. That is a")
            print("      limitation of this configuration, not a property of the measure.)")
    print(f"  -> scored: {', '.join(ok)}\n")

    for tgt, tau in (('now', -0.0005), ('now', -0.001), ('fwd', -0.0005), ('fwd', -0.001)):
        c = (R[tgt] < tau).values
        if c.sum() < 10:
            print(f"tau={tau}: only {c.sum()} labelled windows, skipped\n")
            continue
        sg, filt = {}, {}
        for k in ok:
            s = 1 if R[k][c].mean() > R[k][~c].mean() else -1
            sg[k] = s
            filt[k] = asym(s * R[k].values)
        when = (f"the SAME {EVENT} days as the estimation window (detection)"
                if tgt == 'now' else f"the NEXT {EVENT} days (prediction)")
        print(f"GROUND TRUTH: mean return over {when}, below {tau:.4f} "
              f"-> {c.mean():.1%} of windows labelled ({c.sum()} of {len(c)})")
        print(f"  orientations measured: " +
              ", ".join(f"{k} {'+' if sg[k] > 0 else '-'}" for k in ok))
        print(f"  {'series':<12}{'F1':>8}{'vs Omega dF1':>14}{'95% CI':>22}{'p':>9}")
        for k in ok:
            v, _ = f1(filt[k], c)
            if k == 'Omega':
                print(f"  {k:<12}{v:>8.3f}")
                continue
            d, lo, hi, p = boot(filt['Omega'], filt[k], c)
            print(f"  {k:<12}{v:>8.3f}{d:>+14.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>22}{p:>9.4f}")
        print()
    R.to_csv(RES("balance_detection_largeN.csv"), index=False)


if __name__ == "__main__":
    main()
