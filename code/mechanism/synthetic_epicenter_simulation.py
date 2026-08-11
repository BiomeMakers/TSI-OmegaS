import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RES  # noqa: E402
import numpy as np
import pandas as pd

np.random.seed(7)

# Modelo de un factor: r_i(t) = beta * F(t) + epsilon_i(t)
# F(t): factor de crisis comun (sube y decae)
# Epicentre group: after the shock, idiosyncratic variance GROWS (differentiation:
#   the market starts to tell apart who survives, who is rescued and who fails)
# Non-epicentre group: idiosyncratic variance stays low and constant
#   (those assets simply tracked the macro factor, with no specific differentiation)

T = 260
shock_start, shock_peak, shock_end = 50, 60, 90
F = np.zeros(T)
for t in range(T):
    if t < shock_start:
        F[t] = np.random.normal(0, 0.3)
    elif t <= shock_end:
        F[t] = np.random.normal(3.0, 0.3)  # factor de crisis elevado
    else:
        decay = np.exp(-(t - shock_end) / 40)
        F[t] = np.random.normal(3.0 * decay, 0.3)

s = 10  # assets per group
beta = 0.85

def gen_group(idiosync_growth):
    R = np.zeros((T, s))
    for t in range(T):
        if idiosync_growth and t > shock_end:
            sigma = 0.3 + 0.04 * (t - shock_end)  # differentiation grows after the shock
        else:
            sigma = 0.3
        R[t] = beta * F[t] + np.random.normal(0, sigma, s)
    return R

epicentro = gen_group(idiosync_growth=True)
no_epicentro = gen_group(idiosync_growth=False)
diverse = np.hstack([epicentro[:, :5], no_epicentro[:, :5]])  # half and half, same size as one group

def tr_a3_series(R, window=20, step=2):
    n = R.shape[1]
    rec = []
    for i in range(window, len(R), step):
        win = R[i-window:i]
        corr = np.corrcoef(win.T)
        A = np.abs(corr); np.fill_diagonal(A, 0)
        A2 = A @ A; A3 = A2 @ A
        rec.append({'t': i, 'TrA3': np.trace(A3) / (n**3)})  # normalised by n^3 so sizes are comparable
    return pd.DataFrame(rec)

res_epi = tr_a3_series(epicentro)
res_noepi = tr_a3_series(no_epicentro)
res_div = tr_a3_series(diverse)

for label, res in [("Epicentro (diferenciacion post-shock)", res_epi),
                    ("Non-epicentre (no differentiation)", res_noepi),
                    ("Diverso (mitad y mitad)", res_div)]:
    peak = res['TrA3'].max()
    peak_t = res.loc[res['TrA3'].idxmax(), 't']
    post = res[res['t'] > shock_end + 60]['TrA3'].mean()  # level well after the shock
    print(f"{label:40s}: pico={peak:.4f} (t={peak_t}), nivel tardio (t>150)={post:.4f}, retencion={post/peak*100:.1f}%")

res_epi.to_csv(RES('mech_epicenter.csv'), index=False)
res_noepi.to_csv(RES('mech_no_epicenter.csv'), index=False)
res_div.to_csv(RES('mech_diverse.csv'), index=False)
