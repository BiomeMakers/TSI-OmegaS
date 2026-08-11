import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt

res = pd.read_csv(RES("omega_timeseries.csv"), parse_dates=['date'])

crises = [
    ("Dot-com", "2000-03-10"),
    ("11-Sep", "2001-09-11"),
    ("Lehman", "2008-09-15"),
    ("Deuda UE", "2011-08-05"),
    ("COVID", "2020-02-24"),
]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

ax1.plot(res['date'], res['Omega'], color='#c0392b', lw=1)
ax1.set_ylabel('Omega (TSI)')
ax1.set_title('Omega on the OFR FSI component network (90-day rolling window, weekly recomputation)')

ax2.plot(res['date'], res['Gini_pressure'], color='#2980b9', lw=1)
ax2.set_ylabel('Gini of the topological pressure')
ax2.set_xlabel('Fecha')

for name, d in crises:
    d = pd.Timestamp(d)
    for ax in (ax1, ax2):
        ax.axvline(d, color='gray', linestyle='--', alpha=0.6)
    ax1.text(d, ax1.get_ylim()[1]*0.95, name, rotation=90, fontsize=8, va='top')

plt.tight_layout()
plt.savefig(FIG("omega_fsi_timeseries.png"), dpi=140)
print("ok")
