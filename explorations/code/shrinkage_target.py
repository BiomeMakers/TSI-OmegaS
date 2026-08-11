"""A triadic shrinkage target, against Ledoit-Wolf. PRE-REGISTERED.

WHY THIS AND NOT ANOTHER SIGNAL. Every previous attempt to take the index into
portfolio construction failed for the same structural reason: portfolio
construction consumes a MATRIX and the index produces a SCALAR, plus a per-node
vector that turns out to be the degree. A scalar cannot improve a covariance
estimate; it is not the same kind of object.

There is exactly one place where the triadic structure is the right TYPE. A
shrinkage estimator pulls the noisy sample eigenvalues toward a structured
target, and the choice of target is where prior structure enters. The standard
targets are the identity, the constant-correlation matrix and a single factor.
None of them knows anything about triangles.

THE TRIADIC TARGET. Let A be the absolute correlation matrix with a zero
diagonal. Then A@A is a Gram matrix, hence positive semi-definite, and
normalising it to a unit diagonal gives a valid correlation matrix whose entry
(i,j) is large when i and j connect to the SAME OTHER ASSETS. That is triadic
closure written as a matrix: it is the structure diag(A^3) reads per node,
expressed pairwise. It is PSD by construction, which most hand-built targets are
not, and it is exactly the object the rest of this project has been unable to
reach with a scalar.

The degree target is included as the control that matters. If the triadic target
only reproduces the degree sequence, it will not beat a rank-one target built
from degrees alone, and we already know that on real matrices the per-node
triangle count and the degree agree at 0.996. This comparison is the matrix-level
version of that question.

ESTIMATORS COMPARED, all feeding the same global minimum-variance portfolio:
  sample        the sample covariance, no shrinkage
  identity      linear shrinkage toward a scaled identity
  const_corr    linear shrinkage toward the constant-correlation matrix, the
                standard strong linear target
  degree        linear shrinkage toward the rank-one degree target
  triadic       linear shrinkage toward the target described above
  nonlinear     Ledoit-Wolf analytical nonlinear shrinkage (2020), the actual
                state of the art and the thing to beat

PROTOCOL. 464 S&P 500 constituents, ten years. Estimation window 500 days so
that p/T = 0.93, the concentrated regime where nonlinear shrinkage is designed
to win and where the sample covariance is nearly singular. Rebalance every 21
days, hold, and record the realised return of the global minimum-variance
portfolio. The metric is out-of-sample realised volatility, which is the metric
this literature uses, because a minimum-variance portfolio makes no claim about
returns and should not be judged on them.

The shrinkage intensity for the linear targets is chosen on the FIRST HALF of
the rebalance dates and the second half is touched once.

PRE-REGISTERED CRITERION. The triadic target works only if, on the held-out
half, its realised volatility is lower than the constant-correlation target's
AND no higher than nonlinear shrinkage's, with a bootstrap interval on the
variance ratio excluding one. Both conditions.

PRE-REGISTERED OUTCOMES.
  (a) triadic beats const_corr and ties or beats nonlinear -> the structure is
      worth something at the matrix level, and this is the first place it is.
  (b) triadic beats const_corr but loses to nonlinear -> a better target than
      the linear defaults, not competitive with the state of the art. Report
      as such, claim nothing more.
  (c) triadic ties or loses to degree -> the target is the degree target in
      disguise, which is what the 0.996 predicts. Line closed.
  (d) nonlinear wins outright -> the expected outcome. Line closed.

SELF-CHECK BEFORE ANY VERDICT. If the nonlinear estimator does not beat the
sample covariance in this regime, the implementation is wrong and no comparison
here means anything. That check is printed first and stated plainly.

STATED PRIOR: low. Nonlinear shrinkage is asymptotically optimal in this regime,
and the per-node result predicts the triadic target collapses onto the degree
one. This is run because it is the last well-typed question, not because it is
expected to work.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd

PANEL = os.environ.get("PANEL", "/tmp/sp500_10y.pkl")
T_EST, STEP = 500, 21
rng = np.random.default_rng(0)


def corr_from_cov(S):
    d = np.sqrt(np.clip(np.diag(S), 1e-16, None))
    return S / np.outer(d, d)


def lin_shrink(S, target, alpha):
    return (1 - alpha) * S + alpha * target


def target_identity(S):
    return np.eye(S.shape[0]) * np.mean(np.diag(S))


def target_const_corr(S):
    d = np.sqrt(np.clip(np.diag(S), 1e-16, None))
    R = corr_from_cov(S)
    n = S.shape[0]
    rbar = (R.sum() - n) / (n * (n - 1))
    T = np.full((n, n), rbar)
    np.fill_diagonal(T, 1.0)
    return T * np.outer(d, d)


def _rescale(T, S):
    """Give a correlation-shaped target the volatilities of the sample."""
    d = np.sqrt(np.clip(np.diag(S), 1e-16, None))
    return T * np.outer(d, d)


def target_degree(S):
    A = np.abs(corr_from_cov(S))
    np.fill_diagonal(A, 0.0)
    deg = A.sum(1)
    G = np.outer(deg, deg)
    G = G / np.sqrt(np.outer(np.diag(G), np.diag(G)))
    np.fill_diagonal(G, 1.0)
    return _rescale(G, S)


def target_triadic(S):
    A = np.abs(corr_from_cov(S))
    np.fill_diagonal(A, 0.0)
    G = A @ A                      # Gram, hence PSD
    d = np.sqrt(np.clip(np.diag(G), 1e-16, None))
    G = G / np.outer(d, d)
    np.fill_diagonal(G, 1.0)
    return _rescale(G, S)


def nls_analytical(X):
    """Ledoit-Wolf analytical nonlinear shrinkage, p < n branch."""
    n, p = X.shape
    Xc = X - X.mean(0)
    S = Xc.T @ Xc / (n - 1)
    lam, U = np.linalg.eigh(S)
    lam = np.clip(lam, 0, None)
    c = p / n
    h = n ** (-1 / 3.0)
    L = np.tile(lam, (p, 1))                      # L[i, j] = lam[j]
    xi = (np.tile(lam, (p, 1)).T - L) / (h * L)   # (lam_i - lam_j)/(h lam_j)
    ind = np.abs(xi) < np.sqrt(5)
    ftilde = np.sum(np.where(ind, (3 / (4 * np.sqrt(5))) * (1 - xi ** 2 / 5) / (h * L), 0), axis=1) / p
    with np.errstate(divide='ignore', invalid='ignore'):
        Hf = np.where(ind,
                      (-3 * xi / (10 * np.pi) + (3 / (4 * np.sqrt(5) * np.pi))
                       * (1 - xi ** 2 / 5) * np.log(np.abs((np.sqrt(5) - xi) / (np.sqrt(5) + xi + 1e-300)))),
                      (1 / (np.pi * xi)))
    Htilde = np.sum(np.nan_to_num(Hf) / (h * L), axis=1) / p
    denom = (np.pi * c * lam * ftilde) ** 2 + (1 - c - np.pi * c * lam * Htilde) ** 2
    dtilde = lam / np.clip(denom, 1e-16, None)
    return U @ np.diag(dtilde) @ U.T


def gmv(S):
    n = S.shape[0]
    one = np.ones(n)
    try:
        x = np.linalg.solve(S + 1e-10 * np.eye(n), one)
    except np.linalg.LinAlgError:
        x = np.linalg.pinv(S) @ one
    return x / x.sum()


def main():
    px = pd.read_pickle(PANEL).dropna(axis=1, how='any')
    ret = np.log(px / px.shift(1)).dropna()
    R, p = ret.values, ret.shape[1]
    dates = list(range(T_EST, len(R) - STEP, STEP))
    print(f"{p} assets, {len(R)} days, estimation window {T_EST} (p/T = {p/T_EST:.2f}), "
          f"{len(dates)} rebalances of {STEP} days.\n")

    TARGETS = {'identity': target_identity, 'const_corr': target_const_corr,
               'degree': target_degree, 'triadic': target_triadic}
    ALPHAS = [0.1, 0.3, 0.5, 0.7, 0.9]
    half = len(dates) // 2

    fwd = {}
    for t in dates:
        X = R[t - T_EST:t]
        S = np.cov(X, rowvar=False)
        fwd[t] = R[t:t + STEP]
        rec = {'sample': gmv(S), 'nonlinear': gmv(nls_analytical(X))}
        for name, f in TARGETS.items():
            T_ = f(S)
            for a in ALPHAS:
                rec[f"{name}@{a}"] = gmv(lin_shrink(S, T_, a))
        fwd[str(t)] = rec

    def realised(key, idx):
        r = np.concatenate([fwd[t] @ fwd[str(t)][key] for t in idx])
        return float(r.std() * np.sqrt(252))

    cal, ev = dates[:half], dates[half:]
    print(f"SELF-CHECK on the calibration half ({len(cal)} rebalances), annualised realised vol")
    vs, vn = realised('sample', cal), realised('nonlinear', cal)
    print(f"  sample covariance {vs:.2%}   nonlinear shrinkage {vn:.2%}   "
          f"-> {'implementation behaves as expected' if vn < vs else 'NONLINEAR DOES NOT BEAT SAMPLE: implementation suspect'}")

    chosen = {}
    print(f"\n  shrinkage intensity chosen on the calibration half")
    for name in TARGETS:
        best = min(ALPHAS, key=lambda a: realised(f"{name}@{a}", cal))
        chosen[name] = best
        print(f"    {name:<12} alpha = {best}")

    print(f"\nHELD-OUT HALF ({len(ev)} rebalances), annualised realised volatility")
    print(f"  {'estimator':<14}{'realised vol':>14}{'vs const_corr':>15}{'vs nonlinear':>14}")
    base_c = realised(f"const_corr@{chosen['const_corr']}", ev)
    base_n = realised('nonlinear', ev)
    rows = []
    for key, label in ([('sample', 'sample'), ('nonlinear', 'nonlinear')] +
                       [(f"{n}@{chosen[n]}", n) for n in TARGETS]):
        v = realised(key, ev)
        rows.append(dict(estimator=label, vol=v))
        print(f"  {label:<14}{v:>14.2%}{v/base_c - 1:>+15.1%}{v/base_n - 1:>+14.1%}")
    pd.DataFrame(rows).to_csv(RES("shrinkage_target.csv"), index=False)
    print("\n  (negative means lower realised risk, which is better)")


if __name__ == "__main__":
    main()
