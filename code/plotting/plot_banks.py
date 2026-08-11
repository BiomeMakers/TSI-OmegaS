import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt

b20 = pd.read_csv(RES("banks_omega_w20.csv"), parse_dates=['date'])
b30 = pd.read_csv(RES("banks_omega_w30.csv"), parse_dates=['date'])
b90 = pd.read_csv(RES("banks_omega_w90.csv"), parse_dates=['date'])

o20 = pd.read_csv(RES("omega_w20.csv"), parse_dates=['date'])
o30 = pd.read_csv(RES("omega_w30.csv"), parse_dates=['date'])

fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=False)

# Panel 1: full Omega series for the bank network, 2006-2011, with events
ax = axes[0]
ax.plot(b90['date'], b90['Omega'], color='#7f8c8d', lw=1, label='90-day window')
ax.plot(b30['date'], b30['Omega'], color='#c0392b', lw=0.8, alpha=0.7, label='30-day window')
events = [("Bear Stearns", "2008-03-14"), ("Lehman", "2008-09-15"), ("TARP", "2008-10-03"), ("Fondo mercado", "2009-03-09")]
for name, d in events:
    ax.axvline(pd.Timestamp(d), color='gray', linestyle='--', alpha=0.6)
    ax.text(pd.Timestamp(d), ax.get_ylim()[1]*0.95 if ax.get_ylim()[1]>0 else 1.5, name, rotation=90, fontsize=8, va='top')
ax.set_title('Omega on the correlation network of 10 real banks (JPM, BAC, C, GS, MS, WFC, USB, PNC, COF, AIG), 2006-2011')
ax.set_ylabel('Omega')
ax.legend(fontsize=8)

# Panel 2: bank network vs OFR FSI around Lehman, 20-day window
ax2 = axes[1]
start, end = "2008-07-15", "2008-11-01"
mb = b20[(b20.date>=start)&(b20.date<=end)]
mo = o20[(o20.date>=start)&(o20.date<=end)]
ax2.plot(mb['date'], mb['Omega'], color='#c0392b', marker='o', ms=3, label='Omega, bank network (real prices)')
ax2.plot(mo['date'], mo['Omega'], color='#2980b9', marker='o', ms=3, label='Omega, OFR FSI network (stress index)')
ax2.axvline(pd.Timestamp("2008-09-15"), color='black', linestyle='--', alpha=0.7)
ax2.text(pd.Timestamp("2008-09-15"), ax2.get_ylim()[1]*0.9, ' Lehman', fontsize=9)
ax2.set_title('Which moves first, the bank price network or the stress index? (20-day window)')
ax2.set_ylabel('Omega')
ax2.legend(fontsize=8)

plt.tight_layout()
plt.savefig(FIG("banks_omega_full.png"), dpi=140)
print("ok")
