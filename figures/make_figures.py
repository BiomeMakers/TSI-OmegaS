"""
Generates the figures in the preprint.

Figure 1 is computed directly from the released result files in data/, so it is
reproducible from this repository alone. Figures 2 and 3 render the values
reported in Sections 3.6b and 3.6c.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200})
BLUE, RED, GREY, GREEN = "#1f4e79", "#c0504d", "#7f7f7f", "#4f7942"
D = os.path.join(os.path.dirname(__file__), "..", "data")

# ------------------------------------------------- Figure 1: lead-lag
mem = pd.read_csv(os.path.join(D, "results", "ofr_full_history_memory.csv"),
                  parse_dates=["date"])
ar = pd.read_csv(os.path.join(D, "results", "ofr_AR_full_history.csv"),
                 parse_dates=["date"])
fsi = pd.read_csv(os.path.join(D, "raw", "ofr_financial_stress_index.csv"),
                  parse_dates=["Date"])
d = (mem.merge(ar, on="date")
        .merge(fsi[["Date", "OFR FSI"]], left_on="date", right_on="Date")
        .dropna().sort_values("date").reset_index(drop=True))


def xcorr(sig, tgt, lo=-15, hi=31):
    ks, rs = [], []
    for k in range(lo, hi):
        if k >= 0:
            a, b = sig[:len(sig) - k], tgt[k:]
        else:
            a, b = sig[-k:], tgt[:len(sig) + k]
        m = np.isfinite(a) & np.isfinite(b)
        ks.append(k)
        rs.append(spearmanr(a[m], b[m])[0])
    return np.array(ks), np.array(rs)


series = [("TSI (with memory)", "Omega_memory", BLUE, "o"),
          ("TSI (raw)", "Omega", GREEN, "s"),
          ("Absorption Ratio", "AbsorptionRatio", RED, "^")]

fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4))

for label, col, c, mk in series:                      # levels
    k, r = xcorr(d[col].values, d["OFR FSI"].values)
    ax[0].plot(k, r, marker=mk, ms=2.6, lw=1.2, color=c, label=label)
ax[0].axhline(0, color="0.75", lw=.8)
ax[0].axvline(0, color="0.85", lw=.8, ls="--")
ax[0].set_title("(a) Levels", fontsize=9.5, loc="left")
ax[0].set_xlabel("lag $k$ (observations); $k>0$ means the signal leads")
ax[0].set_ylabel(r"Spearman $\rho$")
ax[0].legend(frameon=False, fontsize=8)

dd = d.copy()
for c_ in ["Omega_memory", "Omega", "AbsorptionRatio", "OFR FSI"]:
    dd[c_] = dd[c_].diff()
dd = dd.dropna()
thr = 1.96 / np.sqrt(len(dd))
for label, col, c, mk in series:                      # first differences
    k, r = xcorr(dd[col].values, dd["OFR FSI"].values)
    ax[1].plot(k, r, marker=mk, ms=2.6, lw=1.2, color=c, label=label)
ax[1].axhspan(-thr, thr, color="0.85", alpha=.5, lw=0)
ax[1].text(20, thr * 1.25, "noise band", fontsize=7.5, color="0.45")
ax[1].axhline(0, color="0.75", lw=.8)
ax[1].axvline(0, color="0.85", lw=.8, ls="--")
ax[1].set_title("(b) First differences", fontsize=9.5, loc="left")
ax[1].set_xlabel("lag $k$ (observations)")
ax[1].set_ylabel(r"Spearman $\rho$")

fig.tight_layout()
fig.savefig("figure1_leadlag.png", bbox_inches="tight")
fig.savefig("figure1_leadlag.pdf", bbox_inches="tight")
print("figure1_leadlag written")

# ------------------------------------------------- Figure 2: benchmarks
names = ["TSI", "Effective\nrank", "Vendi\nscore",
         "Absorption\nRatio", "Effective rank\n(returns)"]
f1_raw = [0.367, 0.347, 0.347, 0.174, 0.179]
f1_flt = [0.447, 0.377, 0.377, 0.134, 0.174]
cols = [BLUE, GREY, GREY, RED, RED]
x = np.arange(len(names))
w = 0.38

fig2, ax2 = plt.subplots(figsize=(6.4, 3.3))
b1 = ax2.bar(x - w / 2, f1_raw, w, color=cols, alpha=.45, edgecolor="white",
             lw=.6, label="raw")
b2 = ax2.bar(x + w / 2, f1_flt, w, color=cols, edgecolor="white", lw=.6,
             label="with the same persistence filter")
for bars, vals in ((b1, f1_raw), (b2, f1_flt)):
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + .008, f"{v:.3f}",
                 ha="center", fontsize=7, color="0.3")
ax2.plot([0, 1, 2], [.50, .50, .50], color="0.4", lw=.9)
ax2.text(1, .508, "statistically indistinguishable", ha="center",
         fontsize=7.5, color="0.4")
ax2.set_xticks(x)
ax2.set_xticklabels(names, fontsize=8)
ax2.set_ylabel("F1 at 90th percentile")
ax2.set_ylim(0, .56)
ax2.legend(frameon=False, fontsize=7.5, loc="upper right")
ax2.set_title("Out-of-sample crisis detection, 2016-2026 (897 windows)",
              fontsize=9.5, loc="left")
fig2.tight_layout()
fig2.savefig("figure2_benchmarks.png", bbox_inches="tight")
fig2.savefig("figure2_benchmarks.pdf", bbox_inches="tight")
print("figure2_benchmarks written")

# ------------------------------------------------- Figure 3: attribution
epi = [1, 2, 3, 4]
tri = [0.994, 0.978, 0.980, 0.975]
spec_k2 = [0.756, 0.999, 0.946, 0.948]
spec_mp = [0.997, 0.978, 0.962, 0.959]
spec_kai = [0.000, 0.071, 0.457, 0.808]
deg = [0.933, 0.940, 0.952, 0.961]
x = np.arange(len(epi))
w = 0.17

fig3, ax3 = plt.subplots(figsize=(6.6, 3.4))
ax3.bar(x - 2 * w, tri, w, label="triangles $\\mathrm{diag}(A^3)$", color=BLUE)
ax3.bar(x - w, spec_mp, w, label="spectral, adaptive $k$ (Marchenko-Pastur)",
        color=GREEN)
ax3.bar(x, spec_k2, w, label="spectral, fixed $k=2$", color=RED)
ax3.bar(x + w, spec_kai, w, label="spectral, adaptive $k$ (Kaiser)",
        color=RED, alpha=.35)
ax3.bar(x + 2 * w, deg, w, label="degree", color=GREY)
ax3.annotate("misspecified $k$", xy=(0, .756), xytext=(0.30, .55),
             fontsize=8, color=RED,
             arrowprops=dict(arrowstyle="->", lw=.8, color=RED))
ax3.set_xticks(x)
ax3.set_xticklabels([f"{e} epicentre{'s' if e > 1 else ''}" for e in epi], fontsize=8)
ax3.set_ylabel("top-$k$ hit rate")
ax3.set_ylim(0, 1.18)
ax3.legend(frameon=False, fontsize=7, loc="lower right", ncol=2)
ax3.set_title("Node attribution: the triangle rule against every way of choosing $k$",
              fontsize=9.5, loc="left")
fig3.tight_layout()
fig3.savefig("figure3_attribution.png", bbox_inches="tight")
fig3.savefig("figure3_attribution.pdf", bbox_inches="tight")
print("figure3_attribution written")
