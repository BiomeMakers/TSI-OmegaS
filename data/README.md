# Data

## raw/
Input data as used in the preprint.
- `ofr_financial_stress_index.csv`, Office of Financial Research Financial Stress
  Index, 2000-2026 (8 sub-components + composite).
- `banks_2006_2011.csv`, daily OHLCV, 10 banks (JPM, BAC, C, GS, MS, WFC, USB, PNC,
  COF, AIG), 2006-2011.
- `ai_sector_2021_2026.csv`, daily OHLCV, 11 AI/semiconductor stocks, 2021-2026.
- `diversified_network_42assets_2006_2026.csv`, daily OHLCV, 42 stocks across 7 sectors,
  2006-2026 (the large-network test).
- `crypto_results.csv`, `commodities_results.csv`, `fx_results.csv`,
  `sovereign_debt_results.csv`, these four are **already-computed** results (Ω,
  Ω-with-memory, Absorption Ratio, responsible asset per window), produced by
  `code/markets/colab_crypto_commodities_fx_bonds.py`, not raw prices.

## results/
Derived series (Ω, Ω-with-memory, Absorption Ratio, and test-specific outputs) used to
produce every figure and table in the preprint. File names indicate the source market /
test; see `code/README.md` for which script produces which file.
