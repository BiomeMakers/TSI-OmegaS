# explorations/

**Nothing in this folder is claimed by the preprint.** It contains lines of work
that were opened, tested against a pre-registered criterion, and closed. They
live in the repository because a negative result that anyone can rerun is worth
more than one that is merely asserted, and because several of them are the
evidence behind sentences in the paper's *Limitations* and *Where This Stands*.

If you arrived here looking for what the paper claims, you want `code/` and
`data/results/` instead.

## Why these are separate

The preprint is about the TSI as a **coincident state index**: it reads how
structurally concentrated a market is right now, and it names which asset is
carrying that concentration. It makes no claim about allocation, and it says so
explicitly. The experiments below ask whether the index can be turned into an
investment rule or a forecasting engine. **The answer, seven pre-registered
tests in, is no**, and keeping those tests next to the paper's own results
would invite exactly the confusion this folder exists to prevent.

In particular: `sp500_headtohead.py` reports a $+1.6\%$ out-of-sample excess
with $p = 0.005$ on a 2012--2017 panel. **That result does not replicate.**
`sp500_10y.py` runs the same test on ten years and 464 assets, and the effect
changes sign between halves. Do not quote the first without the second.

## The investment line, closed

| script | question | answer |
|---|---|---|
| `investment_rule_headtohead.py` | does either index pick assets that beat 1/N over 5 days? | no, for both |
| `esx_replication.py`, `esx_literal_rule.py`, `esx_calibrated.py` | does the published balance rule work on a reconstruction of its own dataset? | in sample yes, out of sample no, and honest calibration removes it |
| `sp500_headtohead.py`, `sp500_10y.py` | does it work on 447 and then 464 S&P 500 assets? | positive on five years, does not replicate on ten |
| `crypto_headtohead.py` | and on 18 crypto assets? | the balance rule is undefined there; ours adds nothing |
| `exposure_rule.py` | can the index size exposure better than volatility targeting? | it ties, and correlates 0.85 with it |
| `euro_backtest.py` | what would 100,000 have done, from many start dates? | the apparent edge vanishes with more independent windows |

## The forecasting and scenario line, closed

| script | question | answer |
|---|---|---|
| `structure_forecast.py` | does the index predict next month's correlation structure beyond persistence? | no |
| `scenario_engine.py` | can it generate calibrated risk scenarios? | yes, and it ties the EWMA Gaussian default |
| `scenario_generality.py` | does that hold across portfolios and horizons? | no: it fails on dollar-neutral books, where the default passes |
| `scenario_repair.py` | is the failure the factor truncation? | no, and the per-node state turns out to be the node degree |
| `corr_forecast_rival.py` | how good is the rival? | DCC beats persistence by 9-13%, so the dynamics are already modelled |
| `shrinkage_target.py` | is a triadic covariance target better than the standard ones? | no: it loses to constant correlation, to the identity and to nonlinear shrinkage |

### On `shrinkage_target.py`

This was the last well-typed question in the whole line. Portfolio construction
consumes a matrix and the index produces a scalar, so every earlier attempt was a
category error; a shrinkage *target* is a matrix, and `A@A` normalised to a unit
diagonal is a valid correlation matrix that encodes triadic closure and is
positive semi-definite by construction. It was worth one experiment.

It lost. On 464 assets with p/T = 0.93, out-of-sample realised volatility of the
global minimum-variance portfolio was 13.68% for the triadic target against
12.27% for constant correlation, 11.66% for Ledoit-Wolf analytical nonlinear
shrinkage and 11.33% for a scaled identity. The linear targets were given a
shrinkage intensity tuned on a calibration half and the nonlinear estimator was
not, so the comparison was tilted toward the triadic target, and it still lost.
The implementation self-check passed: nonlinear shrinkage cut realised risk from
40.2% to 16.4% against the raw sample covariance, which is the behaviour that
estimator is supposed to have.

## Running them

`explorations/code/repo_paths.py` resolves inputs to the shared `data/raw/` and
writes outputs to `explorations/results/`, so nothing here can overwrite a
result the preprint reports. Several scripts download their own data (S&P 500
panels, Coin Metrics, a public EuroStoxx mirror); none of it is redistributed
here, and each script names its source in its docstring.

Every script carries its pre-registered criterion and its possible outcomes in
its docstring, written before it was first run.
