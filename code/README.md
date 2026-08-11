# Code index

Every script resolves inputs and outputs through `repo_paths.py` (`RAW` -> `data/raw/`,
`RES` -> `data/results/`, `PFIG` -> `preprint/figures/`), so it can be run from any
working directory.

All scripts are plain Python (pandas, numpy, scipy, matplotlib). No external persistent-
homology library (ripser/GUDHI) was available in the original compute environment, so
`core/persistent_homology.py` is a from-scratch implementation of Vietoris-Rips
persistent homology (boundary-matrix reduction, Z2 coefficients), validated against an
analytical test case (a 6-point circle, which must yield exactly one H1 generator; see
the `__main__` block).

## core/
- **`persistent_homology.py`**, Vietoris-Rips persistent homology from scratch (H0/H1).
  Used by both the negative correlation-network test (§3.8) and the positive
  Takens-embedding test (§3.8, §3.9).

## markets/, one pipeline per dataset, corresponding to preprint §3.1-3.9
- **`run_ofr_fsi.py`**, Ω / Absorption Ratio over the OFR Financial Stress Index,
  2000-2026 (26-year out-of-sample validation series, §3.5).
- **`run_banks_2008_2011.py`**, 10-bank network, 2006-2011 (Bear Stearns, Lehman,
  European debt crisis; §3.1-3.4).
- **`run_ai_sector.py`**, 11-stock AI/semiconductor network, 2021-2026 (§4).
- **`run_large_diversified_network.py`**, 42-asset, 7-sector network, 2006-2026 (the
  central large-network / disentangled size-vs-diversity result, §3.9).
- **`run_takens_embedding_h1.py`**, literature-faithful persistent homology (Takens
  embedding of the OFR FSI's scalar series, following Gidea & Katz 2018; §3.8).
- **`colab_crypto_commodities_fx_bonds.py`**, Colab-ready downloader + full pipeline for
  the four additional markets (crypto, commodities, FX, sovereign debt; §3.10). Produces
  the four result CSVs in `data/raw/` directly (includes the "responsible asset"
  explainability feature).

## validation/
- **`out_of_sample_calibration.py`**, grid search over the memory filter's
  hyperparameters (`α_up`, `α_down`) with a genuine temporal train/test split (§3.5).
- **`block_bootstrap_significance.py`**, block-bootstrap significance test (95% CI,
  p-value) of the F1 gap between Ω-with-memory and the Absorption Ratio, restricted to
  the out-of-sample period (§3.6).
- **`recalibration_banks_ai_attempt.py`**, the attempted (and informative) replication
  of the calibration on the shorter bank/AI series; documents why ground-truth-window
  definition dominates the result on short series (§3.7).
- **`leadlag_analysis.py`**, cross-correlation of Ω against the OFR stress index
  at lags −15 to +30 (§3.6d), on levels and first differences. **Headline: Ω peaks
  at k = 0 and decays symmetrically, it is a coincident *state index*, not a
  leading indicator.** At k = +1 on first differences the correlation is inside the
  noise band. This does not affect the F1 result (always a contemporaneous test)
  but it constrains the framing: read Ω the way a meteorologist reads CAPE, as a
  statement about the present configuration, not a forecast.
- **`samefilter_benchmarks.py`**, the like-for-like version of the spectral benchmark
  and the one the preprint table reports (§3.4). Scores every metric twice, raw and
  under the *same* asymmetric persistence filter, because filtering Ω and not its
  rivals would flatter Ω on an F1 criterion that rewards sustained plateaux.
  Self-validating: its filtered Ω column reproduces the released
  `ofr_full_history_memory.csv` to machine precision. **Headline: the tie against
  effective rank / Vendi survives the fair comparison (ΔF1 +0.038, 95% CI
  [−0.010, +0.111]), and the win over the Absorption Ratio grows (ΔF1 +0.219).**
- **`spectral_benchmarks_erank_vendi.py`**, the earlier version of the same benchmark,
  kept for provenance. It re-fits the memory as a *symmetric* EMA inside the replica
  rather than using the paper's asymmetric filter, which is why its Ω scores 0.362
  where the paper's own filter scores 0.447; the verdicts are unchanged. It benchmarks
  Ω against *sharper* spectral
  baselines (effective rank, Vendi score, and effective rank on the return matrix) using
  the identical pipeline, crisis labels and block bootstrap (§3.6b). Self-validating: it
  reproduces the published Ω and AR series exactly (n = 2,232, correlation 1.0000) before
  running the comparison. **Headline: Ω beats the Absorption Ratio but ties effective
  rank / Vendi**, reported explicitly in the preprint.
- **`node_attribution_epicenter_test.py`**, validates the culprit-asset attribution
  against synthetic ground truth, including a two-simultaneous-epicentre regime, and
  benchmarks it against eigenvector-loading attribution (§3.6c). Attribution works
  (top-3 hit rate 1.00 vs. chance 0.25).
- **`node_attribution_robustness_k.py`**, the decisive attribution test (§3.6c):
  robustness when the *number* of epicentres is unknown. Triangle attribution
  `diag(A³)`, native to Ω, is hyperparameter-free and holds 0.978-0.997 across 1-4
  epicentres, while fixed-k spectral attribution collapses to 0.747 when k is
  misspecified (paired Wilcoxon, 120 sims/regime). This motivated switching the
  culprit-asset rule from `argmax(degree)` to `argmax(diag(A³))` in
  `markets/colab_crypto_commodities_fx_bonds.py`.
- **`correlation_surprise_benchmark.py`**, Kinlaw & Turkington's Correlation Surprise,
  tested as an additional benchmark; too noisy day-to-day to serve as a comparable
  sustained-stress index (mentioned in Limitations, not a headline result).

## mechanism/
- **`disentangle_size_vs_diversity.py`**, builds the tech-only and diverse-small
  subsets from the 42-asset universe to separate network size from sector
  concentration (§3.9).
- **`synthetic_epicenter_simulation.py`**, toy single-factor model testing whether
  post-shock idiosyncratic differentiation in the "epicenter" sector explains the
  size/diversity finding; a partial, honestly-reported mechanistic account (§3.9).

## plotting/
One script per figure in the preprint; each reads a CSV from `data/results/` and writes
a PNG to `preprint/figures/`. These consume the per-window intermediates written by
`markets/run_ofr_fsi.py`, `markets/run_banks_2008_2011.py` and
`markets/run_ai_sector.py`, so run those first.

## repo_paths.py
Path resolution shared by every script. Not an analysis.

## validation/ — comparisons added after the first release

Head-to-head comparisons and pre-registered tests from the second review round.
Each carries its criterion in its docstring, written before the script was run.

| script | what it settles |
|---|---|
| `multiple_comparisons.py` | Holm-Bonferroni over the family of 24 detection tests |
| `ollivier_ricci_headtohead.py` | TSI against Ollivier-Ricci curvature, exact optimal transport |
| `signed_balance_headtohead.py` | the signed variant of the triangle count, and the global balance index |
| `balance_fidelity_and_attribution.py` | our balance implementation against the authors' own code, and attribution |
| `balance_own_regime.py` | the balance index at the window lengths its authors use |
| `balance_saturation_sp500.py` | where the balance index saturates and where it does not, 447 and 464 assets |
| `balance_detection_largeN.py` | detection head-to-head on 464 assets, under the original authors' own event definition |
| `triangle_residual.py` | what is left in diag(A^3) once the degree is removed |
| `label_robustness_and_alarm_quality.py` | the same verdict under all three crisis lists, and unexplained-alarm rates |
| `node_attribution_adaptive_k.py` | attribution when the spectral rule chooses its own number of components |

## What is NOT here

Experiments asking whether the index can drive an investment rule or a
forecasting engine are in [`../explorations/`](../explorations/). **None of them
is claimed by the preprint**, all seven closed with a null, and they are kept
separate so that no result there can be mistaken for one the paper reports.

## A note on column names

The code writes the index to a column named `Omega`, which is the symbol used in
the theoretical framework. The preprint calls it TSI. They are the same
quantity; the column names were left unchanged so that the released result CSVs
remain byte-identical to the ones the preprint reports.
