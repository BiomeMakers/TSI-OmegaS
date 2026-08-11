import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt

w90 = pd.read_csv(RES("ai_omega_w90.csv"), parse_dates=['date'])
w20 = pd.read_csv(RES("ai_omega_w20.csv"), parse_dates=['date'])

fig, axes = plt.subplots(2, 1, figsize=(13, 9))

ax = axes[0]
ax2 = ax.twinx()
l1, = ax.plot(w90['date'], w90['Omega'], color='#c0392b', lw=1, label='Omega (90d window)')
l2, = ax2.plot(w90['date'], w90['AbsorptionRatio'], color='#16a085', lw=1, label='Absorption Ratio (90d)')
ax.set_ylabel('Omega', color='#c0392b')
ax2.set_ylabel('Absorption Ratio', color='#16a085')
ax.set_title('Red de 11 acciones de IA (NVDA, MSFT, GOOGL, META, AMZN, AVGO, PLTR, MU, ORCL, AMD, TSM) 2021-2026')
events = [("Fondo bear 2022", "2022-10-13"), ("ChatGPT launch", "2022-11-30"),
          ("DeepSeek shock", "2025-01-27"), ("Tarifas Trump", "2025-04-02"), ("Hoy", "2026-07-20")]
for name, d in events:
    ax.axvline(pd.Timestamp(d), color='gray', linestyle='--', alpha=0.5)
    ax.text(pd.Timestamp(d), ax.get_ylim()[1]*0.92, name, rotation=90, fontsize=7, va='top')
ax.legend(handles=[l1, l2], fontsize=8, loc='upper right')

ax3 = axes[1]
ax4 = ax3.twinx()
start, end = "2026-01-01", "2026-07-20"
m20 = w20[(w20.date>=start)&(w20.date<=end)]
l3, = ax3.plot(m20['date'], m20['Omega'], color='#c0392b', marker='o', ms=3, label='Omega (20d)')
l4, = ax4.plot(m20['date'], m20['AbsorptionRatio'], color='#16a085', marker='s', ms=3, label='Absorption Ratio (20d)')
ax3.set_ylabel('Omega', color='#c0392b')
ax4.set_ylabel('Absorption Ratio', color='#16a085')
ax3.set_title('Detail for 2026 (the year of the Burry warnings): 20-day window')
ax3.legend(handles=[l3, l4], fontsize=8, loc='upper right')

plt.tight_layout()
plt.savefig(FIG("ai_omega_full.png"), dpi=140)
print("ok")
