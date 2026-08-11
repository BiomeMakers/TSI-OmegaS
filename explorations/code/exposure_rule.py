"""Omega as an EXPOSURE-SIZING signal, against volatility targeting.

PRE-REGISTERED. Criterion and outcomes written before the script was first run.

WHY THIS ONE. The only thing about Omega that is solidly established is that it
identifies the stressed state, contemporaneously. Exposure sizing is the use
that asks exactly that and nothing more: do not predict returns, do not pick
assets, just hold less of the market while the network says the market is
structurally concentrated. Two previous pre-registered attempts in this line
failed (asset selection on 5-day forward returns, and forecasting correlation
structure), and both failed for the same reason: they required anticipation.
This one does not.

RULES. All exposures are capped at 1, so no rule can win by leverage.
  hold        exposure 1 at all times.
  voltarget   exposure = min(1, 10% annual target / trailing realised vol).
              The serious rival: a standard, widely used risk control.
  omega       exposure = 1 - F(Omega), F the TRAILING empirical CDF of Omega.
  kappa       the same rule on their global balance index, head to head.
  omega_inv   the same rule with the sign flipped, as a direction check.

NO LOOK-AHEAD. Omega for a window ending at day i uses returns strictly before
i, the CDF uses only values up to i, and the resulting exposure is applied to
days i onward. A burn-in of 100 decision points is discarded so that the CDF is
estimated on something.

COSTS ARE MODELLED, because this is where exposure rules die: 5 basis points on
each unit of exposure traded, charged at every rebalance.

PRE-REGISTERED CRITERION, with the correction the situation requires. This is
the fourth test in the same family (selection, structure forecast, this, and the
portfolio-construction variant still unrun), so the threshold is Bonferroni
corrected: an arm beats a rival if its net-of-cost Sharpe ratio is higher AND
the block-bootstrap p-value is below 0.0125, not 0.05. The comparison that
counts is against VOLTARGET, not against buy-and-hold; beating buy-and-hold on
Sharpe is what any risk control does and proves nothing.

PRE-REGISTERED OUTCOMES.
  (a) omega beats voltarget      -> the state reading adds to plain volatility,
                                    which would be the first positive result in
                                    this line and worth a note of its own.
  (b) omega ties voltarget       -> Omega is a volatility proxy with extra
                                    steps. Report it as such and close the line.
  (c) omega loses to voltarget   -> same conclusion, more bluntly.
  (d) omega_inv beats omega      -> the direction is wrong and everything
                                    previously concluded about orientation needs
                                    revisiting.
In cases (b), (c) and (d) the investment line closes and is not reopened with a
different cost assumption, target volatility, or rebalancing frequency.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES  # noqa: E402
import numpy as np
import pandas as pd
from scipy.linalg import expm

WIN, STEP = 60, 10
TARGET_VOL = 0.10
COST = 0.0005            # 5 bp per unit of exposure traded
BURN = 100               # decision points discarded while the CDF is estimated
rng = np.random.default_rng(0)


def omega_paper(A, n):
    A2 = A @ A
    den = A2.sum() - np.trace(A2)
    if den <= 0:
        return 0.0
    C = np.trace(A2 @ A) / den
    deg = A.sum(1)
    dens = A.sum() / (n * (n - 1))
    ev = np.sort(np.linalg.eigvalsh(np.diag(deg) - A))
    return (C * dens / (1.0 / max(ev[1], 1e-6))) * np.var(deg)


def signals(ret, n):
    rows = []
    for i in range(WIN, len(ret), STEP):
        w = ret.iloc[i - WIN:i]
        S = np.nan_to_num(w.corr().values, nan=0.0)
        np.fill_diagonal(S, 0.0)
        A = np.abs(S)
        rows.append(dict(idx=i,
                         omega=omega_paper(A, n),
                         kappa=float(np.trace(expm(S)) / np.trace(expm(np.abs(S)))),
                         vol=w.mean(axis=1).std() * np.sqrt(252)))
    return pd.DataFrame(rows)


def trailing_cdf(v, k):
    """Rank of v[k] among v[:k+1], in [0, 1]. Uses no future information."""
    past = v[:k + 1]
    return float((past <= past[-1]).sum() - 1) / max(1, len(past) - 1)


def path(base, sig, rule):
    """Daily net returns of the rule, and its realised turnover."""
    r, e_prev, turn = [], 0.0, 0.0
    for k in range(BURN, len(sig)):
        i = int(sig.idx.iloc[k])
        j = int(sig.idx.iloc[k + 1]) if k + 1 < len(sig) else len(base)
        if rule == 'hold':
            e = 1.0
        elif rule == 'voltarget':
            e = min(1.0, TARGET_VOL / max(sig.vol.iloc[k], 1e-6))
        elif rule == 'omega':
            e = 1.0 - trailing_cdf(sig.omega.values, k)
        elif rule == 'omega_inv':
            e = trailing_cdf(sig.omega.values, k)
        elif rule == 'kappa':
            e = 1.0 - trailing_cdf(sig.kappa.values, k)
        seg = base[i:j] * e
        seg = seg.copy()
        if len(seg):
            seg[0] -= COST * abs(e - e_prev)
        turn += abs(e - e_prev)
        e_prev = e
        r.extend(seg)
    return np.array(r), turn


def stats(r):
    ann = r.mean() * 252
    vol = r.std() * np.sqrt(252)
    eq = np.exp(np.cumsum(r))
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    return ann, vol, (ann / vol if vol > 0 else 0), dd


def boot_sharpe_diff(a, b, B=4000, block=21):
    m = len(a)
    out = []
    for _ in range(B):
        idx = []
        while len(idx) < m:
            s = rng.integers(0, max(1, m - block))
            idx.extend(range(s, min(s + block, m)))
        idx = np.array(idx[:m])
        sa = a[idx].mean() / a[idx].std() if a[idx].std() > 0 else 0
        sb = b[idx].mean() / b[idx].std() if b[idx].std() > 0 else 0
        out.append(sa - sb)
    out = np.array(out) * np.sqrt(252)
    return out.mean(), np.percentile(out, 2.5), np.percentile(out, 97.5), float(np.mean(out <= 0))


def main():
    d = pd.read_csv(RAW("diversified_network_42assets_2006_2026.csv"), parse_dates=['Date'])
    px = d.pivot(index='Date', columns='Ticker', values='Close').dropna(how='any')
    ret = np.log(px / px.shift(1)).dropna()
    n = ret.shape[1]
    base = ret.mean(axis=1).values
    sig = signals(ret, n)
    print(f"{n} assets, {len(ret)} days, {len(sig)} decision points every {STEP} days, "
          f"{BURN} burned in.\nCost {COST*1e4:.0f} bp per unit traded, exposure capped at 1, "
          f"vol target {TARGET_VOL:.0%}.\n")

    P = {r: path(base, sig, r) for r in ['hold', 'voltarget', 'omega', 'omega_inv', 'kappa']}
    print(f"  {'rule':<12}{'ann ret':>9}{'ann vol':>9}{'Sharpe':>8}{'max DD':>9}{'turnover':>10}")
    for r, (x, t) in P.items():
        a, v, s, dd = stats(x)
        print(f"  {r:<12}{a:>8.2%}{v:>9.2%}{s:>8.2f}{dd:>9.1%}{t:>10.1f}")

    print(f"\n  Pre-registered comparison, threshold p < 0.0125 (Bonferroni over four tests)")
    print(f"  {'contrast':<26}{'dSharpe':>9}{'95% CI':>24}{'p':>9}  verdict")
    for a, b in [('omega', 'voltarget'), ('kappa', 'voltarget'),
                 ('omega', 'kappa'), ('omega', 'omega_inv'), ('omega', 'hold')]:
        d_, lo, hi, p = boot_sharpe_diff(P[a][0], P[b][0])
        v = "WINS" if (d_ > 0 and p < 0.0125) else ("loses" if (d_ < 0 and 1 - p < 0.0125) else "tie")
        print(f"  {a + ' vs ' + b:<26}{d_:>+9.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>24}{p:>9.4f}  {v}")

    print(f"\n  correlation between the omega exposure and the voltarget exposure: ", end="")
    eo = np.array([1 - trailing_cdf(sig.omega.values, k) for k in range(BURN, len(sig))])
    ev = np.array([min(1.0, TARGET_VOL / max(sig.vol.iloc[k], 1e-6)) for k in range(BURN, len(sig))])
    print(f"{np.corrcoef(eo, ev)[0,1]:+.3f}")
    pd.DataFrame(dict(omega_exposure=eo, voltarget_exposure=ev)).to_csv(
        RES("exposure_rule.csv"), index=False)


if __name__ == "__main__":
    main()
