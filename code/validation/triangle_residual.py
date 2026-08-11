"""Is there anything in diag(A^3) that is not the degree?

On real correlation matrices the two rank assets almost identically: the
cross-sectional Spearman between diag(A^3) and the degree, sum |rho|, averages
0.996. That is close enough to an identity that the per-node attribution claim
has to be re-examined, because degree is free and everyone can compute it.

This script asks the only question that remains, and it is the Corollary 1
question applied to the node level: strip out the part that IS the degree and
see whether anything is left that does work.

The residual is formed within each window, cross-sectionally, by regressing the
rank of diag(A^3) on the rank of the degree and keeping what the degree does not
explain. Then two tests.

REAL DATA. Does the residual rank next week's returns, or next week's realised
variance, better than chance? Block bootstrap over windows for the interval.

SYNTHETIC. On the epicentre benchmark of the preprint, where ground truth
exists, does the residual identify the stressed nodes at all? Degree and
triangles both score high there; the question is whether the part of triangles
that is NOT degree carries any of that.

PRE-REGISTERED: the residual carries information only if its mean rank
correlation with a forward quantity has a 95% interval excluding zero, OR if on
the synthetic benchmark it beats chance by more than the interval width. If
neither, the node-level line closes without ambiguity.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
WIN, STEP, FWD = 60, 10, 5
rng = np.random.default_rng(0)


def residualise(tri, deg):
    """Part of the triangle count that the degree does not explain, in ranks."""
    x, y = rankdata(deg), rankdata(tri)
    x = (x - x.mean()) / x.std()
    y = (y - y.mean()) / y.std()
    return y - (x @ y / (x @ x)) * x


def block_ci(v, block=8, B=4000):
    m = len(v)
    out = []
    for _ in range(B):
        idx = []
        while len(idx) < m:
            s = rng.integers(0, max(1, m - block))
            idx.extend(range(s, min(s + block, m)))
        out.append(np.mean(np.array(v)[np.array(idx[:m])]))
    return np.percentile(out, 2.5), np.percentile(out, 97.5)


def real_data():
    px = pd.read_pickle(PANEL).dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    Rv, n = ret.values, ret.shape[1]
    r_ret, r_var, d_ret, t_ret = [], [], [], []
    for i in range(WIN, len(Rv) - FWD, STEP):
        C = np.nan_to_num(np.corrcoef(Rv[i - WIN:i], rowvar=False), nan=0.0)
        A = np.abs(C.copy())
        np.fill_diagonal(A, 0.0)
        tri = np.diag(A @ A @ A)
        deg = A.sum(1)
        res = residualise(tri, deg)
        fwd = Rv[i:i + FWD].sum(axis=0)
        fvar = Rv[i:i + FWD].var(axis=0)
        r_ret.append(spearmanr(res, fwd).statistic)
        r_var.append(spearmanr(res, fvar).statistic)
        d_ret.append(spearmanr(deg, fwd).statistic)
        t_ret.append(spearmanr(tri, fwd).statistic)
    print(f"REAL DATA, {len(r_ret)} windows, {n} assets")
    print(f"  {'signal':<34}{'mean Spearman':>15}{'95% CI':>22}")
    for name, v in [("residual of triangles vs return", r_ret),
                    ("residual of triangles vs variance", r_var),
                    ("degree vs return", d_ret),
                    ("raw triangles vs return", t_ret)]:
        lo, hi = block_ci(v)
        flag = "  informative" if (lo > 0 or hi < 0) else ""
        print(f"  {name:<34}{np.mean(v):>+15.4f}{f'[{lo:+.4f}, {hi:+.4f}]':>22}{flag}")


def gen(n=16, T=200, epis=None, t0=100, seed=0):
    r = np.random.default_rng(seed)
    Fs = [r.normal(0, 1, T) for _ in epis]
    bg = r.normal(0, 1, T)
    R = np.zeros((T, n))
    memb = {i: g for g, grp in enumerate(epis) for i in grp}
    for t in range(T):
        for i in range(n):
            if t < t0:
                R[t, i] = r.normal(0, 1)
            elif i in memb:
                R[t, i] = 0.9 * Fs[memb[i]][t] + np.sqrt(1 - 0.81) * r.normal(0, 1)
            else:
                R[t, i] = 0.25 * bg[t] + np.sqrt(1 - 0.0625) * r.normal(0, 1)
    return R


def synthetic():
    print("\nSYNTHETIC BENCHMARK, hit rate in the top |epicentres|, 80 sims per regime")
    print(f"  {'epicentres':>10}{'chance':>8}{'degree':>8}{'triangles':>11}{'residual':>10}")
    g = np.random.default_rng(0)
    for nf in (1, 2, 3, 4):
        acc = {'deg': [], 'tri': [], 'res': []}
        for s in range(80):
            idx = g.permutation(16)
            epis = [tuple(idx[3 * j:3 * j + 3]) for j in range(nf)]
            nodes = set(i for grp in epis for i in grp)
            win = gen(epis=epis, seed=400 + s)[120:160]
            C = np.corrcoef(win.T)
            A = np.abs(C)
            np.fill_diagonal(A, 0)
            tri, deg = np.diag(A @ A @ A), A.sum(1)
            res = residualise(tri, deg)
            k = len(nodes)
            for key, sc in [('deg', deg), ('tri', tri), ('res', res)]:
                acc[key].append(len(set(np.argsort(-sc)[:k]) & nodes) / k)
        print(f"  {nf:>10}{3*nf/16:>8.3f}{np.mean(acc['deg']):>8.3f}"
              f"{np.mean(acc['tri']):>11.3f}{np.mean(acc['res']):>10.3f}")


if __name__ == "__main__":
    real_data()
    synthetic()
