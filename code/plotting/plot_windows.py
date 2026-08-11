import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt

w20 = pd.read_csv(RES('omega_w20.csv'), parse_dates=['date'])
w30 = pd.read_csv(RES('omega_w30.csv'), parse_dates=['date'])
w90 = pd.read_csv(RES('omega_timeseries.csv'), parse_dates=['date'])

fig, axes = plt.subplots(2, 1, figsize=(13, 8))

def plot_period(ax, start, end, title, shock_date, shock_label):
    for res, label, color in [(w20,'20-day window','#e67e22'), (w30,'30-day window','#c0392b'), (w90,'90-day window','#7f8c8d')]:
        m = res[(res.date>=start)&(res.date<=end)]
        ax.plot(m['date'], m['Omega'], label=label, color=color, marker='o', ms=3)
    ax.axvline(pd.Timestamp(shock_date), color='black', linestyle='--', alpha=0.7)
    ax.text(pd.Timestamp(shock_date), ax.get_ylim()[1] if ax.get_ylim()[1]>0 else 1, shock_label, rotation=0, fontsize=9)
    ax.set_title(title)
    ax.set_ylabel('Omega')
    ax.legend(fontsize=8)

plot_period(axes[0], "2008-07-15", "2008-11-15", "Lehman Brothers (colapso: 15 sept 2008)", "2008-09-15", " Lehman")
plot_period(axes[1], "2019-12-15", "2020-04-01", "COVID (crash inicia: 20-24 feb 2020)", "2020-02-20", " Crash S&P")

plt.tight_layout()
plt.savefig(FIG("omega_windows_comparison.png"), dpi=140)
print("ok")
