"""Split-sample calibration of both selection rules on the EuroStoxx reconstruction.

The previous script imposed one operating point on both rules. That was neither
rule's own best, and it also handicapped theirs, whose whole design is a pair of
tuned thresholds. Their paper is explicit that calibration per dataset is
required. So calibrate, but calibrate honestly:

  * The windows are split in time. The FIRST half chooses the parameters, the
    SECOND half is touched once, to evaluate.
  * Both rules get the SAME parameter grid and therefore the same number of
    degrees of freedom: a global percentile g on their own state variable, and a
    basket size m taken from the top of their own local score.
  * The permutation null is unchanged: random baskets of size m from the same
    universe, 2000 draws per window.
  * We also report the in-sample-chosen number on the evaluation half, i.e. what
    you would claim if you calibrated and evaluated on the same data. The gap
    between the two is the size of the selection effect.

PRE-REGISTERED CRITERION: a rule works if, on the held-out half at the
parameters chosen on the calibration half, its mean excess over 1/N is positive
AND the permutation p is below 0.025 (two rules tested).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esx_replication import load, build, FWD  # noqa: E402

GRID_G = [0.0, 0.25, 0.50, 0.70, 0.85]
GRID_M = [3, 5, 10, 15]
N_PERM = 2000
rng = np.random.default_rng(0)


def excess(R, state, score, g, m, idx):
    thr = R[state].iloc[idx].quantile(g) if g > 0 else -np.inf
    d = []
    for j in idx:
        row = R.iloc[j]
        if row[state] < thr:
            continue
        pick = np.argsort(score(row))[:m]
        d.append(row['oos'][pick].mean() - row['oos'].mean())
    return np.array(d)


def perm_p(R, state, score, g, m, idx, n):
    thr = R[state].iloc[idx].quantile(g) if g > 0 else -np.inf
    obs, null = [], []
    for j in idx:
        row = R.iloc[j]
        if row[state] < thr:
            continue
        f = row['oos']
        pick = np.argsort(score(row))[:m]
        obs.append(f[pick].mean() - f.mean())
        null.append([f[rng.choice(n, m, replace=False)].mean() - f.mean()
                     for _ in range(N_PERM)])
    obs, null = np.array(obs), np.array(null)
    return obs.mean(), float(np.mean(null.mean(axis=0) >= obs.mean())), len(obs)


def main():
    ret = load()
    R, n = build(ret)
    half = len(R) // 2
    cal, ev = np.arange(half), np.arange(half, len(R))
    print(f"N={n}, {len(R)} windows. Calibration on the first {len(cal)}, "
          f"evaluation on the last {len(ev)} (touched once).\n")

    rules = {"theirs: balance gap": ('kappa', lambda r: -r['gap']),
             "TSI: low triangle": ('omega', lambda r: r['tri'])}

    for name, (state, score) in rules.items():
        best, bg, bm = -np.inf, None, None
        for g in GRID_G:
            for m in GRID_M:
                d = excess(R, state, score, g, m, cal)
                if len(d) >= 20 and d.mean() > best:
                    best, bg, bm = d.mean(), g, m
        obs, p, k = perm_p(R, state, score, bg, bm, ev, n)
        cheat_best, cg, cm = -np.inf, None, None
        for g in GRID_G:
            for m in GRID_M:
                d = excess(R, state, score, g, m, ev)
                if len(d) >= 20 and d.mean() > cheat_best:
                    cheat_best, cg, cm = d.mean(), g, m
        print(f"{name}")
        print(f"  chosen on calibration half: global percentile {bg}, basket {bm}"
              f"   (excess there {best * 100:+.3f}%)")
        print(f"  HELD-OUT half at those parameters: {k} windows, "
              f"excess {obs * 100:+.3f}%, permutation p = {p:.3f}"
              f"   -> {'WORKS' if (obs > 0 and p < 0.025) else 'does not reach the bar'}")
        print(f"  for reference, best achievable ON the held-out half "
              f"(g={cg}, m={cm}): {cheat_best * 100:+.3f}%  <- what tuning on the test set buys\n")


if __name__ == "__main__":
    main()
