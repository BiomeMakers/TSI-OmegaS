[![arXiv](https://img.shields.io/badge/arXiv-2608.10788-red)](https://arxiv.org/abs/2608.10788)
# TSI: the Triadic Stress Index

The **Triadic Stress Index** (TSI) is a structural index of a weighted
network: the number of closed triangles, `Tr(A³)`, together with density, modularity
and degree variance. Its four factors come from co-occurrence networks in agricultural
soil microbiomes, and are formalised in the companion theoretical work,
[OmegaS-fsri](https://github.com/BiomeMakers/OmegaS-fsri). This repository takes that
construction, reorients it for the financial domain (degree variance moves to the
numerator, because a densely interconnected, weakly modular market is the crisis
configuration and not the healthy one), and tests it on correlation networks of real
assets across five markets: equities, cryptocurrencies, commodities, foreign exchange,
and sovereign debt.

**On the name:** *triadic* because the closed-triangle count is the only one of the
four factors that is not a function of the degree sequence alone; *stress* because here
the index rises under stress; *index* rather than signal, because the lead-lag test says
it is coincident with stress and does not lead it.

**Three names, three things.** The theoretical framework is the **FSRI**, and it writes
this quantity Ω. The machine-learning line built on the same trace is **Omega-S**. This
index, the financial instrument, is the **TSI**. The preprint uses TSI throughout, in
prose and in equations; the code keeps `Omega` as a column name so that the released
result CSVs stay byte-identical to the ones the preprint reports.

## Headline result

Benchmarked against the Absorption Ratio (Kritzman & Li, 2010, the industry standard
used by MSCI and central banks), Ω with its persistence filter is a **statistically
significant improvement** at sustaining a signal through prolonged stress (F1 gap
0.273 out of sample, 95% CI [0.10, 0.39], p < 0.0005). Against **sharper** spectral
baselines (effective rank, Vendi score) Ω **ties**, in all six
labelling-by-sample cells tested, with the point estimate in Ω's favour in five of
them. That win over the Absorption Ratio, in turn, does not survive the narrowest of
the three crisis lists. We report both rather than lead with the gap over a weak
baseline.

The contribution is therefore a conjunction, not a single result:

- **Detection on a par with the best spectral measure.** A tie, robust to labelling.
- **The cleanest alarms of anything tested**, at the same alarm budget: 4.0%
  unexplained against 14.7% for the effective rank and ~59% for the Absorption Ratio.
  Same caveat as above: at a fixed alarm budget this is 1 − precision, so it is the F1
  comparison re-expressed, not independent evidence.
- **A different primitive.** Ω correlates 0.85 with the effective rank and 0.54 with
  the Absorption Ratio, and shares only half its alarm windows with the former. It is a
  close relative of the spectral entropies, exactly as the FSRI theory predicts, and
  the alarms it does *not* share measure how far a different construction moves.
- **Node attribution included, with no parameter to select.** It names *which* asset is
  responsible. A spectral rule can do this too and ties it when the component count k is
  chosen well (Marchenko-Pastur), but costs a quarter of its accuracy at a fixed k=2 and
  collapses entirely under the equally standard Kaiser rule. Ω has no such decision to
  get wrong. Synthetic ground truth; Section 3.5 of the preprint.

A separate, central methodological finding, developed in full in the preprint, is that
Ω's apparent need for a memory correction is largely a property of small,
sector-concentrated networks, not of Ω itself.

Full results, methodology, and an explicit account of what Ω does *not* detect (by
construction, not by error) are in [`preprint/`](preprint/).

## Repository structure

```
├── preprint/              # The paper: markdown, PDF, HTML, figures, executive summary
├── code/                  # All analysis code, organized by purpose (see code/README.md)
├── data/
│   ├── raw/                # Input data (prices / pre-aggregated results) used in the paper
│   └── results/            # Derived CSVs (Ω, Ω-with-memory, Absorption Ratio, per test)
└── LICENSE                 # Dual license: AGPL-3.0 (research) / commercial (production)
```

## What is in this repository, and what is not

`code/` and `data/results/` contain everything the preprint claims, and the
result CSVs are byte-identical to the ones it reports.

[`explorations/`](explorations/) contains lines that were opened, tested against
a pre-registered criterion, and **closed with a null**: whether the index can
drive an investment rule, and whether it can drive a forecasting or scenario
engine. **None of that is claimed by the preprint**, which says so explicitly.
They are kept because a negative anyone can rerun is worth more than one that is
asserted, and they are kept separate so that nothing there can be mistaken for a
result the paper reports.

## Reproducing the results

Every script resolves its own paths through `code/repo_paths.py`, so it runs from any
working directory and needs no editing:

```bash
python code/markets/run_ofr_fsi.py          # writes data/results/omega_w{20,30,90}.csv
python code/validation/samefilter_benchmarks.py
python code/plotting/plot_omega.py          # writes preprint/figures/
```

Each script in `code/` is a standalone analysis matching one section of the preprint
(see `code/README.md` for the map). Inputs come from `data/raw/`, derived series go to
`data/results/`, plots go to `preprint/figures/`. The plotting scripts consume the
intermediates written by `code/markets/`, so run those first. Every script in the
repository has been executed end to end from a clean checkout, and the regenerated
result CSVs reproduce the released ones to machine precision.
Market data (`data/raw/*.csv`) was originally pulled via `yfinance`; the Colab-ready
download scripts are included in `code/markets/` for anyone who wants to refresh or
extend the dataset.

## Patent and licensing

Built on the Functional Symbiotic Resilience Index (FSRI, Ω), USPTO Patent Pending
Serial No. 64/121,656, filed 29 July 2026 (the number assigned on electronic filing,
pending the official receipt).

- **Software** (`code/`, `figures/`): AGPL-3.0 for research and non-commercial use; a
  commercial licence is available for production use. See [`LICENSE`](LICENSE).
- **Preprint text and figures** (`preprint/`, `arxiv/`): CC BY-NC-ND 4.0, the same
  licence as the companion papers.
- **Data** (`data/raw/`): redistributed for reproducibility only, subject to the terms
  of the original providers.

## Status

Working preprint, actively tested against adversarial checks (out-of-sample
calibration, statistical significance, cross-market replication, a persistent-homology
extension). Known open items are listed in the preprint's Roadmap section, contributions
and replications welcome, see below.

## Contributing / Open Collaboration

This is exploratory, applied research from a small team, released openly because we
think the falsifiable, adversarially-tested approach benefits more from outside scrutiny
than from staying private. Concrete places to contribute are listed in the preprint's
"Roadmap and Open Collaboration" section (Section 7), among them: a signed-correlation
variant to close the single-asset-divergence blind spot, a Takens-embedding parameter
sweep, and repeating the large-network test with different sector compositions. Issues
and pull requests are welcome; for licensing a production use case, contact
acedo@biomemakers.com.

## Citation

@misc{acedo2026tsi,
  title         = {The Triadic Stress Index in Financial Markets},
  author        = {Acedo, Alberto},
  year          = {2026},
  eprint        = {2608.10788},
  archivePrefix = {arXiv},
  primaryClass  = {physics.soc-ph},
  url           = {https://arxiv.org/abs/2608.10788}
}
