import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt

banks = pd.read_csv(RES("banks_full_comparison.csv"), parse_dates=['date'])
ai = pd.read_csv(RES("ai_full_comparison.csv"), parse_dates=['date'])

fig, axes = plt.subplots(2, 2, figsize=(14, 9))

def panel(ax, df, start, end, title, event_date=None, event_label=""):
    m = df[(df.date >= start) & (df.date <= end)]
    ax2 = ax.twinx()
    l1, = ax.plot(m['date'], m['Omega'], color='#e67e22', lw=1, alpha=0.6, label='Raw Omega')
    l2, = ax.plot(m['date'], m['Omega_memory'], color='#c0392b', lw=1.8, label='Omega with memory')
    l3, = ax2.plot(m['date'], m['AbsorptionRatio'], color='#16a085', lw=1.5, label='Absorption Ratio')
    ax.set_ylabel('Omega', color='#c0392b')
    ax2.set_ylabel('AR', color='#16a085')
    ax.set_title(title, fontsize=10)
    if event_date:
        ax.axvline(pd.Timestamp(event_date), color='gray', linestyle='--', alpha=0.6)
        ax.text(pd.Timestamp(event_date), ax.get_ylim()[1]*0.9, event_label, fontsize=7)
    ax.legend(handles=[l1, l2, l3], fontsize=7, loc='upper left')
    ax.tick_params(axis='x', labelrotation=30)

panel(axes[0,0], banks, "2008-02-01", "2008-04-15", "(A) Bear Stearns 2008", "2008-03-16", " rescate")
panel(axes[0,1], banks, "2008-08-01", "2008-11-01", "(B) Lehman Brothers 2008", "2008-09-15", " colapso")
panel(axes[1,0], banks, "2011-07-01", "2011-11-30", "(C) Crisis deuda europea 2011", "2011-08-05", " downgrade EEUU")
panel(axes[1,1], ai, "2025-01-01", "2025-06-01", "(D) Sector IA : tarifas Trump 2025", "2025-04-02", " Liberation Day")

plt.tight_layout()
plt.savefig(FIG("preprint_fig1.png"), dpi=150)
print("ok")
