"""Path resolution for explorations/, which sits one level deeper than code/.

RAW  -> data/raw/           (shared with the paper's code)
RES  -> explorations/results/  (kept apart, so nothing here can be mistaken
                                for a result the preprint claims)
FIG  -> explorations/results/
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")


def RAW(name):
    return os.path.join(DATA, "raw", name)


def RES(name):
    d = os.path.join(ROOT, "explorations", "results")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def FIG(name):
    return RES(name)


def PFIG(name):
    return RES(name)
