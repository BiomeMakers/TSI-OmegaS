import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt

res = pd.read_csv(RES("omega_vs_ar.csv"), parse_dates=['date'])

fig, axes = plt.subplots(3, 1, figsize=(12, 11))

def panel(ax, start, end, title, event_date=None, event_label=""):
    m = res[(res.date>=start)&(res.date<=end)]
    ax2 = ax.twinx()
    l1, = ax.plot(m['date'], m['Omega'], color='#c0392b', marker='o', ms=3, label='Omega (TSI)')
    l2, = ax2.plot(m['date'], m['AbsorptionRatio'], color='#16a085', marker='s', ms=3, label='Absorption Ratio')
    ax.set_ylabel('Omega', color='#c0392b')
    ax2.set_ylabel('Absorption Ratio', color='#16a085')
    ax.set_title(title)
    if event_date:
        ax.axvline(pd.Timestamp(event_date), color='gray', linestyle='--', alpha=0.6)
        ax.text(pd.Timestamp(event_date), ax.get_ylim()[1]*0.9, event_label, fontsize=8)
    ax.legend(handles=[l1, l2], fontsize=8, loc='upper left')

panel(axes[0], "2008-02-15", "2008-04-01", "Bear Stearns", "2008-03-16", " rescate JPM")
panel(axes[1], "2008-08-15", "2008-10-01", "Lehman Brothers", "2008-09-15", " colapso")
panel(axes[2], "2011-07-01", "2011-11-15", "Crisis deuda europea", "2011-08-05", " downgrade EEUU")

plt.tight_layout()
plt.savefig(FIG("omega_vs_ar.png"), dpi=140)
print("ok")
