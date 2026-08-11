"""Fidelity check against the authors' own implementation, and the attribution
head-to-head that the detection comparison did not cover.

Companion to signed_balance_headtohead.py. Two things are settled here.

PART 1. IS OUR REIMPLEMENTATION FAITHFUL?
Bartesaghi, Diaz-Diaz, Grassi and Uberti publish their code at
github.com/fernandodiazdiaz/Global_balance-and_Systemic_Risk. Their
global_balance is tr(expm(A)) / tr(expm(|A|)) and their local_balance is
diag(expm(A)) / diag(expm(|A|)). We reproduce both here verbatim and check our
version against them, including the diagonal-invariance result they prove
(a constant diagonal cancels, so it does not matter whether the correlation
matrix is passed with a unit or a zero diagonal). We also add the BINARY
variant they report, in which correlations above +0.25 become +1, below -0.25
become -1, and the rest become 0.

PART 2. LOCAL BALANCE AGAINST diag(A^3) AS AN ATTRIBUTION RULE.
The per-node claim in the preprint is that diag(A^3) needs no hyperparameter
and does not degrade when the number of stress epicentres is unknown, whereas
spectral attribution has to fix k. Local balance is a third rule with the same
property: it has no k either. This adds it to the same synthetic benchmark used
in the preprint (16 nodes, groups of 3 driven by their own factor, hit rate in
the top |epicentres|, 80 simulations per regime).

Orientation is reported in both directions rather than assumed, which is the
mistake made and declared in the companion script.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

NODES = ['Credit', 'Equity valuation', 'Safe assets', 'Funding', 'Volatility',
         'United States', 'Other advanced economies', 'Emerging markets']


# --- their code, transcribed from the public repository ----------------------
def their_global_balance(A):
    return np.trace(expm(A)) / np.trace(expm(np.abs(A)))


def their_local_balance(A):
    return np.diag(expm(A)) / np.diag(expm(np.abs(A)))


# --- ours, as used in signed_balance_headtohead.py ---------------------------
def our_global_balance(S):
    return float(np.trace(expm(S)) / np.trace(expm(np.abs(S))))


def binarise(C, thr=0.25):
    B = np.zeros_like(C)
    B[C > thr] = 1.0
    B[C < -thr] = -1.0
    np.fill_diagonal(B, 0.0)
    return B


def part1():
    df = (pd.read_csv(RAW("ofr_financial_stress_index.csv"), parse_dates=['Date'])
            .sort_values('Date'))
    diffs = df[NODES].diff().dropna().reset_index(drop=True)
    ours, theirs_diag0, theirs_diag1, binary = [], [], [], []
    for i in range(20, len(diffs), 3):
        C = np.nan_to_num(diffs.iloc[i - 20:i].corr().values, nan=0.0)
        S = C.copy()
        np.fill_diagonal(S, 0.0)
        ours.append(our_global_balance(S))
        theirs_diag0.append(their_global_balance(S))
        theirs_diag1.append(their_global_balance(C))
        binary.append(their_global_balance(binarise(C)))
    o, t0, t1, b = map(np.array, (ours, theirs_diag0, theirs_diag1, binary))
    print(f"PART 1 -- fidelity, {len(o)} windows of the OFR network")
    print(f"  ours vs THEIR code, same matrix : max|diff| = {np.abs(o - t0).max():.3e}")
    print(f"  zero vs unit diagonal           : max|diff| = {np.abs(o - t1).max():.3e}"
          "   (their Section 2.2 invariance, confirmed)")
    print(f"  weighted K range  {o.min():.4f} to {o.max():.4f}")
    print(f"  binary   K range  {b.min():.4f} to {b.max():.4f}"
          f"   corr with weighted = {np.corrcoef(o, b)[0, 1]:.4f}")
    return o, b


# --- Part 2: the synthetic epicentre benchmark of the preprint ---------------
def gen(n=16, T=200, epicentres=None, t0=100, seed=0, frustrated=False):
    """frustrated=True flips the loading of half of each epicentre group, so the
    stressed block contains negative correlations and therefore frustrated
    triangles. Without it the benchmark contains no sign structure at all, which
    would be an unfair test for a balance-based rule."""
    r = np.random.default_rng(seed)
    Fs = [r.normal(0, 1, T) for _ in epicentres]
    bg = r.normal(0, 1, T)
    R = np.zeros((T, n))
    memb, sgn = {}, {}
    for gi, g in enumerate(epicentres):
        for j, i in enumerate(g):
            memb[i] = gi
            sgn[i] = -1.0 if (frustrated and j % 2 == 1) else 1.0
    for t in range(T):
        for i in range(n):
            if t < t0:
                R[t, i] = r.normal(0, 1)
            elif i in memb:
                b = 0.90
                R[t, i] = sgn[i] * b * Fs[memb[i]][t] + np.sqrt(1 - b ** 2) * r.normal(0, 1)
            else:
                b = 0.25
                R[t, i] = b * bg[t] + np.sqrt(1 - b ** 2) * r.normal(0, 1)
    return R


def hit(s, focus, k):
    return len(set(np.argsort(s)[::-1][:k]) & set(focus)) / len(focus)


def part2(frustrated=False):
    rng = np.random.default_rng(0)
    tag = ("stress block carries BOTH SIGNS (frustrated triangles present)"
           if frustrated else "stress block all-positive (no sign structure)")
    print(f"\nPART 2 -- attribution, {tag}")
    print("hit rate in the top |epicentres|, 80 sims per regime")
    print(f"{'epicentres':>10} |{'chance':>7} |{'triangles':>10} |{'spec k=2':>9} |"
          f"{'spec ORACLE':>12} |{'local bal':>10} |{'-local bal':>11}")
    for nf in (1, 2, 3, 4):
        res = {k: [] for k in ('tri', 'sp2', 'spO', 'lb', 'lbneg')}
        for s in range(80):
            idx = rng.permutation(16)
            epis = [tuple(idx[3 * j:3 * j + 3]) for j in range(nf)]
            nodes = [i for g in epis for i in g]
            win = gen(epicentres=epis, seed=400 + s, frustrated=frustrated)[120:160]
            C = np.corrcoef(win.T)
            A = np.abs(C)
            np.fill_diagonal(A, 0.0)
            S = C.copy()
            np.fill_diagonal(S, 0.0)
            ev, V = np.linalg.eigh(C)
            kappa = their_local_balance(S)
            res['tri'].append(hit(np.diag(A @ A @ A), nodes, len(nodes)))
            res['sp2'].append(hit(np.sum(np.abs(V[:, -2:]), axis=1), nodes, len(nodes)))
            res['spO'].append(hit(np.sum(np.abs(V[:, -nf:]), axis=1), nodes, len(nodes)))
            res['lb'].append(hit(kappa, nodes, len(nodes)))
            res['lbneg'].append(hit(-kappa, nodes, len(nodes)))
        print(f"{nf:>10} |{3 * nf / 16:>7.3f} |{np.mean(res['tri']):>10.3f} |"
              f"{np.mean(res['sp2']):>9.3f} |{np.mean(res['spO']):>12.3f} |"
              f"{np.mean(res['lb']):>10.3f} |{np.mean(res['lbneg']):>11.3f}")


if __name__ == "__main__":
    part1()
    part2(frustrated=False)
    part2(frustrated=True)
