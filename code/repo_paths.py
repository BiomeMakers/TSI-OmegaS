"""Repository-relative paths.

Every script in this repository resolves its inputs and outputs through this
module, so it can be run from any working directory:

    python code/markets/run_ofr_fsi.py

RAW  -> data/raw/      (inputs shipped with the repository)
RES  -> data/results/  (derived CSVs; created on demand)
FIG  -> figures/       (plots; created on demand)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FIGURES = os.path.join(ROOT, "figures")


def RAW(name):
    return os.path.join(DATA, "raw", name)


def RES(name):
    os.makedirs(os.path.join(DATA, "results"), exist_ok=True)
    return os.path.join(DATA, "results", name)


def FIG(name):
    os.makedirs(FIGURES, exist_ok=True)
    return os.path.join(FIGURES, name)


def PFIG(name):
    """Figures embedded in preprint/omega_s_financial_sector.md."""
    d = os.path.join(ROOT, "preprint", "figures")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)
