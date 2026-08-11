"""Attribution with an ADAPTIVE k: does choosing k per window close the gap?

Section 3.5 compares the triangle rule diag(A^3) against spectral attribution
held at a fixed k = 2, which is how k is set in deployment. The obvious
objection is that a practitioner could choose k per window from the eigenvalue
spectrum instead. This script runs that control.

Three spectral variants are added to the fixed-k rule:

  * Marchenko-Pastur: k = number of eigenvalues above the upper edge of the
    MP distribution, lambda+ = (1 + sqrt(n/T))^2, the standard random-matrix
    rule in finance;
  * Kaiser: k = number of eigenvalues above 1 (the mean eigenvalue of a
    correlation matrix);
  * oracle: k = the true number of epicentres. Not available in practice; it is
    the ceiling the adaptive rules are trying to reach.

Same generator, same regimes and same hit-rate criterion as
node_attribution_robustness_k.py, 120 simulations per regime.

Run from code/validation/.
"""
import numpy as np

N_NODES, T_OBS, N_SIMS = 16, 200, 120
WINDOW = slice(120, 160)          # 40 observations
GROUP = 3                          # nodes per epicentre


def generate(epicentres, seed):
    r = np.random.default_rng(seed)
    factors = [r.normal(0, 1, T_OBS) for _ in epicentres]
    background = r.normal(0, 1, T_OBS)
    R = np.zeros((T_OBS, N_NODES))
    member = {i: gi for gi, g in enumerate(epicentres) for i in g}
    for t in range(T_OBS):
        for i in range(N_NODES):
            if t < 100:
                R[t, i] = r.normal(0, 1)
            elif i in member:
                b = 0.90
                R[t, i] = b * factors[member[i]][t] + np.sqrt(1 - b ** 2) * r.normal(0, 1)
            else:
                b = 0.25
                R[t, i] = b * background[t] + np.sqrt(1 - b ** 2) * r.normal(0, 1)
    return R


def hit(score, nodes):
    return len(set(np.argsort(score)[::-1][:len(nodes)]) & set(nodes)) / len(nodes)


def run():
    rng = np.random.default_rng(0)
    n_obs = WINDOW.stop - WINDOW.start
    mp_edge = (1 + np.sqrt(N_NODES / n_obs)) ** 2
    print(f"n = {N_NODES} nodes, T = {n_obs} observations per window, "
          f"Marchenko-Pastur upper edge = {mp_edge:.3f}")
    print(f"\n{'epicentres':>11} {'chance':>7} {'triangles':>10} {'degree':>8} "
          f"{'fixed k=2':>10} {'adapt. MP':>10} {'adapt. Kaiser':>14} {'oracle k':>9}")
    ks = {'mp': [], 'kaiser': []}
    for n_foci in (1, 2, 3, 4):
        acc = {k: [] for k in ('tri', 'deg', 'k2', 'mp', 'kaiser', 'oracle')}
        for s in range(N_SIMS):
            idx = rng.permutation(N_NODES)
            epicentres = [tuple(idx[GROUP * j:GROUP * (j + 1)]) for j in range(n_foci)]
            nodes = [i for g in epicentres for i in g]
            win = generate(epicentres, seed=400 + s)[WINDOW]
            C = np.corrcoef(win.T)
            A = np.abs(C)
            np.fill_diagonal(A, 0)
            ev, V = np.linalg.eigh(C)
            k_mp = max(1, int((ev > mp_edge).sum()))
            k_kaiser = max(1, int((ev > 1.0).sum()))
            ks['mp'].append(k_mp)
            ks['kaiser'].append(k_kaiser)
            acc['tri'].append(hit(np.diag(A @ A @ A), nodes))
            acc['deg'].append(hit(A.sum(1), nodes))
            for tag, k in (('k2', 2), ('mp', k_mp), ('kaiser', k_kaiser), ('oracle', n_foci)):
                acc[tag].append(hit(np.abs(V[:, -k:]).sum(axis=1), nodes))
        print(f"{n_foci:>11} {GROUP * n_foci / N_NODES:>7.2f} {np.mean(acc['tri']):>10.3f} "
              f"{np.mean(acc['deg']):>8.3f} {np.mean(acc['k2']):>10.3f} "
              f"{np.mean(acc['mp']):>10.3f} {np.mean(acc['kaiser']):>14.3f} "
              f"{np.mean(acc['oracle']):>9.3f}")
    print(f"\nk selected by Marchenko-Pastur: mean {np.mean(ks['mp']):.2f}, "
          f"range {min(ks['mp'])}-{max(ks['mp'])}")
    print(f"k selected by Kaiser:           mean {np.mean(ks['kaiser']):.2f}, "
          f"range {min(ks['kaiser'])}-{max(ks['kaiser'])}")


if __name__ == "__main__":
    run()
