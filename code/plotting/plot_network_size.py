import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repo_paths import RAW, RES, PFIG as FIG  # noqa: E402
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

small = pd.read_csv(RES("banks_full_comparison.csv"), parse_dates=['date'])
large = pd.read_csv(RES("large_network_full.csv"), parse_dates=['date'])

def zscore(x):
    return (x - x.mean()) / x.std()

small['Omega_z'] = zscore(small['Omega'])
large['Omega_z'] = zscore(large['Omega'])

fig, ax = plt.subplots(figsize=(12, 6))
start, end = "2011-06-01", "2011-12-15"
ms = small[(small.date>=start)&(small.date<=end)]
ml = large[(large.date>=start)&(large.date<=end)]

ax.plot(ms['date'], ms['Omega_z'], color='#c0392b', lw=2, marker='o', ms=4, label='Raw Omega, small network (n=10 banks)')
ax.plot(ml['date'], ml['Omega_z'], color='#2980b9', lw=2, marker='s', ms=4, label='Raw Omega, large diversified network (n=42)')
ax.axhline(0, color='gray', lw=0.5, linestyle=':')
ax.axvline(pd.Timestamp("2011-08-05"), color='gray', linestyle='--', alpha=0.6)
ax.text(pd.Timestamp("2011-08-05"), ax.get_ylim()[1]*0.9, ' downgrade EEUU', fontsize=9)
ax.set_ylabel('Raw Omega (z-score within its own history)')
ax.set_title('2011 European debt crisis: network size and diversity decide whether raw Omega needs the memory filter')
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig(FIG("network_size_comparison.png"), dpi=140)
print("ok")
