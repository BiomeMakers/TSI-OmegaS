# Introduction

TSI began as a descriptor of microbial co-occurrence networks in
agricultural soils, where resilience indices were derived from network
transitivity and competitive exclusion , and where the same four
quantities, clustering, density, modularity and the proportion of
exclusion edges, were observed to move together along a management
gradient. The accompanying theoretical work  formalises that
construction and establishes that its central quantity, the trace of the
cube of the adjacency matrix, proportional to the number of closed
triangles in the graph, is domain-agnostic: any system representable as
a weighted network admits the same computation.

This motivates a natural question. If the four factors that separate a
managed soil community from an undisturbed one are computed instead on
the correlation network among financial assets, do they register the
kind of structural concentration that characterises a system under
systemic stress, the configuration Minsky described as fragility built
up in plain sight ? We call the resulting quantity the **Triadic Stress
Index**, TSI, and write it that way throughout, in prose and in
equations.

A note on which factor is active, because that does not travel between
constructions and it is the first thing a reader should check. The
theoretical work  reports a direct measurement in a setting where the
adjacency matrix is obtained by passing weight correlations through a
bounded sigmoidal map. There the clustering factor $C$ is driven against
a constant and is numerically inert, and the operative factor is the
degree-variance term $\mathrm{Coex}$. That is a property of how $A$ is
built, not of the index. Here $A$ is a correlation matrix among assets,
built without any saturating nonlinearity, so $C$ is free to vary and
contributes to TSI as defined; we checked this rather than assumed it,
and the excess ratio $C/D$ departs from unity on these matrices, whereas
under a sigmoidal construction it equals unity to four decimal places.
The two settings are therefore consistent: the same four factors, with
the clustering channel inert in one construction and active in the
other.

We are deliberate about the verb. This paper tests whether TSI
*registers* such a state, not whether it *forecasts* its onset.
Section <a href="#sec:leadlag" data-reference-type="ref"
data-reference="sec:leadlag">6.7</a> reports a lead–lag analysis showing
the distinction matters: TSI is a coincident state index, not a leading
indicator, and we frame every claim accordingly.

Three claims are made and each is stated so that it can fail. **H1,
detection**: the index separates labelled crisis windows from calm ones
at least as well as the sharpest spectral measures available, at an
equal alarm budget. It fails if a baseline beats it with an interval
excluding zero. **H2, attribution**: the per-node decomposition names
the asset carrying the concentration without any parameter to select. It
fails if a rule with a parameter beats it, or if a published per-node
alternative does. **H3, register**: the index is coincident with stress
rather than leading it. It fails if the cross-correlation with an
external stress measure peaks at a negative lag.

The order of what follows is deliberate: first what the index does that
the alternatives do not, then where it merely equals them, then the
boundary of what it can be asked to do at all. Results that did not
survive testing are reported alongside those that did, including the
scope boundaries and the questions that remain open.

# Hypotheses and What Would Falsify Them

The three claims of
Section <a href="#sec:intro" data-reference-type="ref"
data-reference="sec:intro">1</a> are operationalised as follows, and the
criteria were fixed before the corresponding experiments were run.

- **H1, detection at parity.** Scored by $F_1$ at the 90th percentile of
  each series against labelled crisis windows, so that every metric
  spends the same alarm budget, with block-bootstrap intervals on the
  difference. Falsified if any baseline’s advantage has an interval
  excluding zero. Three independent crisis definitions are used and
  reported separately, because a result that holds only under one
  labelling is not a result.

- **H2, attribution without a parameter.** Scored by the hit rate in the
  top-$|$epicentres$|$ on a synthetic benchmark where ground truth
  exists, across regimes with one to four simultaneous epicentres.
  Falsified if a spectral rule with a well-chosen $k$, or a published
  per-node alternative, scores higher across regimes.

- **H3, coincident register.** Scored by the cross-correlation between
  the index and an external stress index across lags. Falsified if the
  peak sits at a negative lag, which would make it a leading indicator.

A fourth question is not a hypothesis but a scope condition, and it is
answered in
Section <a href="#sec:large_network" data-reference-type="ref"
data-reference="sec:large_network">6.9</a>: on what kind of network does
the raw index work, and where does it need the persistence filter?

# The Index

## Construction on a Financial Network

For a rolling window of $W$ days of daily log-returns of $n$ assets, we
build the correlation matrix $\rho$, define the adjacency matrix
$A = |\rho|$ (absolute value, zero diagonal), and compute:
$$\mathrm{TSI} = \frac{C \cdot D}{M} \cdot \mathrm{Coex},
\label{eq:omega}$$ where $C$ is the weighted clustering coefficient
(normalised $\operatorname{Tr}(A^3)$), $D$ is connection density, $M$ is
the inverse spectral gap of the graph Laplacian (a modularity proxy),
and $\mathrm{Coex}$ is the variance of the degree sequence. The
construction descends from prior work on co-inclusion and co-exclusion
networks in agricultural microbiomes, where resilience indices were
derived from network transitivity , following the original definition
in . Because $C$, $D$, $M$, and $\mathrm{Coex}$ all scale with $n$ in
different ways, raw TSI magnitudes are **not comparable across networks
of different size**; only within-series dynamics (z-scores, percentiles)
are.

#### The name.

We call the quantity in <a href="#eq:omega" data-reference-type="eqref"
data-reference="eq:omega">[eq:omega]</a> the **Triadic Stress Index**
(TSI). Each part of the name records something that the rest of this
paper either establishes or bounds. *Triadic*, because the
closed-triangle count is the only one of the four factors that is not a
function of the degree sequence alone, and because the per-node
attribution of Section <a href="#sec:attrib" data-reference-type="ref"
data-reference="sec:attrib">6.1</a> is the triangle count read per node
rather than summed. *Stress*, because in this domain the index rises
under stress, which is the reverse of the orientation the same
construction carries in the ecological setting it comes from, for the
reason set out immediately below. And *index* rather than signal or
forecast, because
Section <a href="#sec:leadlag" data-reference-type="ref"
data-reference="sec:leadlag">6.7</a> establishes that it is coincident
with stress and does not lead it.

#### A note on notation, because the names in this family are easy to confuse.

The accompanying theoretical work writes this quantity $\Omega$, and the
machine-learning line built on the same trace carries the Omega name as
well. To keep the financial instrument distinct from both, we write TSI
throughout this paper, in prose and in equations, and reserve the other
names for what they denote: **FSRI** for the theoretical framework,
**Omega-S** for the machine-learning line, and **TSI** for the index
defined here.

#### Relation to the composition fixed in the framework paper.

Equation <a href="#eq:omega" data-reference-type="eqref"
data-reference="eq:omega">[eq:omega]</a> places $\mathrm{Coex}$ in the
numerator, whereas Definition 1 of the framework paper  places it in the
denominator, so that a high degree variance lowers the index there and
raises it here. The two agree on the other three factors, including the
orientation of $M$ as an inverse spectral gap. We keep the composition
above, and we give the reason rather than leaving the difference to be
found by comparing code.

The reason is that the two domains do not agree on what the same
structure means. Under stress, correlations rise, the network becomes
denser and more connected, and every factor moves in the same direction:
$C$ rises, $D$ rises, $\mathrm{Coex}$ rises, and $M$, being an inverse
spectral gap, falls. A stress indicator should therefore place the three
that rise in the numerator and the one that falls in the denominator,
which is what <a href="#eq:omega" data-reference-type="eqref"
data-reference="eq:omega">[eq:omega]</a> does; the composition of
Definition 1 places $\mathrm{Coex}$ against the other three. The
underlying asymmetry is that a densely interconnected, weakly modular
community is the healthy configuration in the ecological setting the
index derives from, and is the crisis configuration in a market, where
it means that everything falls together. The difference between the two
papers is thus a deliberate reorientation by domain and not an
unreconciled discrepancy.

We also tested it rather than only arguing it, on the same windows and
with the same detection protocol used throughout this paper. Over a
portfolio of large US banks from 2006 to 2011, with the crisis window
labelled as 2007-08 to 2009-06, the filtered $F_1$ at the ninetieth
percentile is $0.275$ for the composition
of <a href="#eq:omega" data-reference-type="eqref"
data-reference="eq:omega">[eq:omega]</a> and $0.157$ for that of
Definition 1, against a chance level of $0.152$ for an alarm rate of ten
percent at the observed crisis frequency. The composition used here
detects at roughly $1.8\times$ chance while the alternative sits at
chance. Two limits should be read alongside that. Block-bootstrap
confidence intervals on the paired difference are wide and include zero
($+0.054$, $[-0.229, +0.315]$), so the comparison is directional rather
than conclusive; and on this particular portfolio and period the
Absorption Ratio also sits near chance ($0.167$), which indicates that
the test itself discriminates weakly rather than that the alternative
composition is uniquely poor. The argument from domain orientation above
is the stronger of the two and does not depend on this measurement.

A third composition deserves reporting because its outcome is a
limitation of the index rather than a point in its favour. The framework
paper shows that $\mathrm{Coex} = \operatorname{Var}(k)$ carries units
of degree squared and proposes a shape-normalised variant that replaces
it by the Gini coefficient of the degree sequence and the density by the
mean degree, removing the dependence on the scale of the degree
sequence. On the same test that variant scores $0.098$, that is *below*
chance. The implication is uncomfortable and we state it: a substantial
part of what TSI detects in this setting is the level of correlation
rather than the shape of its distribution, and removing the scale
dependence removes the signal with it. This does not affect the
comparisons reported below, which are all against external baselines
computed on the same windows, but it does bound what the index should be
claimed to measure.

#### The closest structural precedent, and we do benchmark against it.

Sandhu, Georgiou and Tannenbaum  compute Ollivier-Ricci curvature on
correlation networks of equities and report it as an indicator of market
fragility and systemic risk. That is the same graph construction and the
same purpose as the present work, reached from discrete geometry rather
than from triadic structure, and it is the nearest precedent to what
follows. Earlier versions of this paper named it and declined to
benchmark against it, on the grounds that per-edge Ollivier-Ricci
requires a Wasserstein computation for every edge and therefore sits in
a different cost regime from a stochastic trace estimate. That was a
reason not to have done the work, not a reason for it not to be done, so
we have now done it:
Section <a href="#sec:ricci" data-reference-type="ref"
data-reference="sec:ricci">6.5</a> reports the head-to-head on the same
windows, under the same filter and the same alarm budget as every other
benchmark here. We note in passing that a subsequent analysis  argues
the curvature identifies the size and duration of a crisis accurately
without leading it, which is the same register we establish for TSI in
Section <a href="#sec:leadlag" data-reference-type="ref"
data-reference="sec:leadlag">6.7</a>.

#### Other network-structural indicators, and where this sits.

Systemic risk has been approached through exposure and connectedness
models  and through random-matrix cleaning of correlation matrices . The
present work belongs to neither: it fixes a single composite index in
advance, taken from an external domain, and asks how it scores against
spectral baselines on the same windows. Three lines of work are close
enough that we state the relation explicitly rather than let a reader
find it. Samal, Kumar, Yadav and Chakraborti  evaluate a battery of
network-centric indicators, including edge curvatures, clique number and
community counts, on threshold networks over minimum spanning trees of
69 global indices, and conclude that network measures are useful for
monitoring fragility. That is the same question as ours; what differs is
that they survey measures and we commit to one in advance. Bartesaghi,
Diaz-Diaz, Grassi and Uberti  use the global balance index of the
*signed* correlation network as a systemic-risk measure and derive a
local, per-node version of it, developed further into an
investment-decision rule in follow-up work . That is the closest
existing work to the signed extension this paper leaves open, and we
state the position plainly: our $A = |\rho|$ discards precisely the
information their index is built from, their global balance is already
benchmarked against spectral risk measures as ours is, and their local
balance is a per-node attribution of the same kind as ours. Rather than
list the signed variant as future work, we ran it, and report three
findings in Section <a href="#sec:signed" data-reference-type="ref"
data-reference="sec:signed">6.13</a>. Zhang, Wang, Zheng and Cartlidge 
pair a correlation fragility indicator computed on time-varying
correlation networks with a risk contribution score that attributes
systemic risk to categories of protocol; a structural index plus a
per-node decomposition is the same shape as what is reported here, on a
different asset universe. None of the three is used as a running
benchmark, for the cost-regime reason given above, and we regard a
comparison against the signed balance index as the most informative of
the three left undone.

# Benchmarks

Four families of comparison are used, and the reason for each differs.

- **The Absorption Ratio**, described below. It is the industry standard
  and therefore the measure a practitioner would already have running.
  It is a weak baseline on this data, which the results below make
  plain.

- **The effective rank and the Vendi score**, spectral entropies of the
  correlation eigenvalues. These are the *sharpest* baselines we could
  find rather than the most common ones, and they are the honest test of
  H1. They are described and scored in
  Section <a href="#sec:spectral" data-reference-type="ref"
  data-reference="sec:spectral">6.2</a>.

- **Per-node alternatives**: spectral attribution under four different
  rules for choosing the number of components, the node degree, and the
  local balance index of Bartesaghi et al. All are scored in
  Section <a href="#sec:attrib" data-reference-type="ref"
  data-reference="sec:attrib">6.1</a>.

- **The global balance index** of the signed correlation network,
  treated separately below because it cannot be scored fairly on the
  networks used here.

## Benchmark: the Absorption Ratio

The Absorption Ratio  is the fraction of total variance explained by the
first $k$ principal components of the return covariance matrix
($k = \lfloor n/5 \rfloor$). It is the de facto standard in
systemic-risk management, used by MSCI and central banks, and is
computed on the same rolling windows as TSI for direct comparability.

**Additional spectral benchmarks.** The Absorption Ratio summarises the
eigenvalue spectrum through the mass of its leading components. Because
TSI is itself partly a spectral object, benchmarking against the AR
alone risks comparing against a deliberately coarse summary. We
therefore add two sharper spectral baselines on the same windows: the
*effective rank* , $\exp(H)$ with $H$ the Shannon entropy of the
correlation eigenvalues normalised to sum to one; and the *Vendi
score* , the exponential of the von Neumann entropy of the normalised
correlation kernel, which on a correlation matrix is *mathematically
identical* to the effective rank, an equivalence we state explicitly
rather than presenting the two as independent evidence. We additionally
report an effective rank computed on the return matrix itself (entropy
of the singular-value spectrum), a genuinely distinct quantity.

## The Global Balance Index, and Why It Is Not in the Main Table

The nearest published rival is the global balance index of the signed
correlation network , $\kappa = \operatorname{tr}(e^A) /
\operatorname{tr}(e^{|A|})$, with a per-node counterpart used for
investment decisions in follow-up work . It belongs in this list on
merit: it is built on the same object, aims at the same target, and is
published in a peer-reviewed venue. We reimplemented it and verified our
version against the authors’ own public code, obtaining agreement to
machine precision over 2 232 windows.

It does not appear as a column in the detection table for a reason we
measured rather than assumed. On small networks the index *saturates*:
with eight nodes it sits at its maximum of 1 on 26% of windows in its
weighted form and 70% in the binary form the same authors report,
because a small correlation network is close to balanced whatever the
market is doing. Any ranking produced under those conditions describes a
degenerate regime, not the index, so we produce none.
Section <a href="#sec:signed" data-reference-type="ref"
data-reference="sec:signed">6.13</a> reports what we did measure
instead, including the regime in which the index is well behaved, a
check that its own published relationship reproduces on our data, and a
head-to-head on a 464-asset universe where it does not saturate.

# Data and Protocol

## Data

<div id="tab:data">

| Scenario                               | Assets ($n$)         | Period    | Source   |
|:---------------------------------------|:---------------------|:----------|:---------|
| Banking crises (Bear Stearns, Lehman,  | 10 banks             | 2006–2011 | yfinance |
| European debt crisis)                  |                      |           |          |
| AI sector                              | 11 stocks            | 2021–2026 | yfinance |
| Out-of-sample validation               | 8 OFR components     | 2000–2026 | OFR      |
| Large-network robustness               | 42 stocks, 7 sectors | 2006–2026 | yfinance |
| Cross-market (crypto, FX, commodities, | 10+7+10+10           | 2021–2024 | yfinance |
| sovereign debt)                        |                      |           |          |

Datasets used in this study.

</div>

All windows: 20 trading days, recomputed every 3 days.

## TSI with Persistence Memory

We apply an asymmetric exponential filter: $$\begin{aligned}
\mathrm{mem}(t) &= \alpha_{\uparrow}\,\mathrm{TSI}(t) +
  (1-\alpha_{\uparrow})\,\mathrm{mem}(t-1)
  \quad \text{if } \mathrm{TSI}(t) > \mathrm{mem}(t-1), \label{eq:mem_up}\\
\mathrm{mem}(t) &= \alpha_{\downarrow}\,\mathrm{TSI}(t) +
  (1-\alpha_{\downarrow})\,\mathrm{mem}(t-1)
  \quad \text{if } \mathrm{TSI}(t) \leq \mathrm{mem}(t-1), \label{eq:mem_down}
\end{aligned}$$ with $\alpha_{\uparrow} = 0.6$ and
$\alpha_{\downarrow} = 0.08$, chosen by inspection and later validated
by grid search (Section <a href="#sec:oos" data-reference-type="ref"
data-reference="sec:oos">5.3</a>).

## Out-of-Sample Calibration and Significance Testing

Hyperparameters were calibrated via grid search
($\alpha_{\uparrow} \in [0.3, 0.8]$,
$\alpha_{\downarrow} \in [0.02, 0.20]$) with a genuine temporal
train/test split on the 2000–2026 OFR Financial Stress Index series
(train 2000–2015, test 2016–2026). Statistical significance of the F1
gap between TSI with memory and the Absorption Ratio was assessed via
block bootstrap (block length $\approx$ 1 quarter, $B = 2{,}000$
resamples), restricted to the out-of-sample period only.

## Persistent Homology

We implemented Vietoris-Rips persistent homology from scratch
(boundary-matrix reduction, $\mathbb{Z}_2$ coefficients), validated
against an analytical test case (a 6-point circle, which yields exactly
one H1 generator). We tested two constructions:

**Correlation-network H1** (negative result): Vietoris-Rips filtration
on the asset correlation-distance matrix
$d_{ij} = \sqrt{2(1-\rho_{ij})}$ .

**Takens-embedding H1** (positive result): following Gidea & Katz , a
scalar stress series is reconstructed as a point cloud in $\mathbb{R}^d$
via time-delay embedding, and persistent homology is computed on that
point cloud within each rolling window.

# Results

What follows is ordered by argument rather than by chronology: first the
layer that has no equivalent among the baselines, then the layer where
the index merely matches them, then the comparison it wins and the one
it does not, then the boundary of what it can be asked to do, and
finally the robustness checks and the extension we closed with a null.

## On the Node-Attribution Layer

Detection says the system is stressed. Attribution says *where*. The two
are not equally hard, and the difference is not that spectral methods
cannot attribute, because they can: the loading on the leading
eigenvector, directly available to any Absorption-Ratio user, recovers a
single epicentre perfectly. The difference is that they need to be told
how many places to look, or given a rule for deciding it. Reading
eigenvectors requires committing to $k$, the number of components to
inspect, and in deployment $k$ is either fixed in advance, before anyone
knows how many epicentres the next episode will have, or selected per
window by a rule that can itself be wrong. The per-node decomposition
$\mathrm{diag}(A^3)$, which is the alarm itself read per node rather
than summed, has no such parameter. How much that is worth is the
question this section answers, and the answer is more modest than the
framing above suggests.

We tested this on synthetic networks with a known epicentre, in two
steps. First, whether the attribution works at all: over 80 simulations
the culprit rule recovers the true epicentre in essentially every run
(top-3 hit rate 1.00 against a chance level of 0.25), and under two
simultaneous uncorrelated epicentres it recovers 0.93 of the six
affected nodes (chance 0.50). Then the question that decides the
comparison, which is robustness when the number of epicentres is
unknown. We ran regimes of one to four simultaneous epicentres, holding
the spectral method at a fixed $k=2$ as it would be held in deployment
(120 simulations per regime, paired Wilcoxon):

<div class="center">

|                |      Triangles       |        | Spectral, by how $k$ is chosen |       |        |        |
|:---------------|:--------------------:|:------:|:------------------------------:|:-----:|:------:|:------:|
| 5-7 Epicentres | $\mathrm{diag}(A^3)$ | Degree |          fixed $k=2$           |  MP   | Kaiser | oracle |
| 1              |      **0.994**       | 0.933  |             0.756              | 0.997 | 0.000  | 0.989  |
| 2              |        0.978         | 0.940  |             0.999              | 0.978 | 0.071  | 0.999  |
| 3              |      **0.980**       | 0.952  |             0.946              | 0.962 | 0.457  | 0.981  |
| 4              |      **0.975**       | 0.961  |             0.948              | 0.959 | 0.808  | 0.989  |

</div>

Top-$|\text{epicentres}|$ hit rate, 120 simulations per regime, 16 nodes
and 40-observation windows. *MP* selects $k$ per window as the number of
eigenvalues above the Marchenko-Pastur edge  $(1+\sqrt{n/T})^2 = 2.665$,
the standard random-matrix rule; it picks $k = 1.71$ on average.
*Kaiser* selects the eigenvalues above 1 and picks $k = 5.87$. *Oracle*
is given the true number of epicentres and is not available in practice;
it is the ceiling.

<figure id="fig:attribution">
<embed src="figure3_attribution.pdf" style="width:72.0%" />
<figcaption>Attribution accuracy as the number of simultaneous
epicentres varies. The triangle rule is flat across regimes because it
has no parameter to misspecify. The spectral rule depends entirely on
how <span class="math inline"><em>k</em></span> is chosen: the
Marchenko-Pastur rule ties the triangle rule everywhere, a fixed <span
class="math inline"><em>k</em> = 2</span> costs a quarter of the
accuracy when it is wrong, and the equally standard Kaiser rule
collapses. The spread between those three, not the gap to the triangle
rule, is the result.</figcaption>
</figure>

The triangle rule is flat, 0.975 to 0.994 across every regime, because
there is no parameter in it to misspecify. Fixed $k=2$ matches it
exactly where that value happens to be right (two epicentres) and loses
a quarter of its accuracy where it is not (0.756 with a single
epicentre).

**The adaptive-$k$ control, and what it costs the claim.** An earlier
version of this section stopped there. It should not have, because the
obvious objection is that a practitioner would not hold $k$ fixed but
read it off the spectrum window by window, and we had not tested it. We
have now, and the result is against us: with $k$ chosen by the
Marchenko-Pastur edge the spectral rule scores 0.959 to 0.997 and ties
the triangle rule across all four regimes. The oracle ties it as well.
The gap in the fixed-$k$ column is therefore not evidence that triangles
see something eigenvectors cannot; it is evidence that $k$ matters, and
a good rule for choosing $k$ closes it.

What the control does not do is make the choice free. The three
selection rules in the table span 0.000 to 0.997 on the single-epicentre
regime: Marchenko-Pastur lands near the ceiling, a fixed $k=2$ costs a
quarter of the accuracy, and the Kaiser rule ($\lambda > 1$), which is
equally standard and equally defensible a priori, collapses completely,
because it selects roughly six eigenvectors and the epicentre stops
being separable in their combined loading. The spectral route can match
$\mathrm{diag}(A^3)$, but only conditional on a selection decision whose
wrong answers are catastrophic and are not identifiable without the
ground truth we have here and a practitioner does not.

So we state the claim at the size the evidence supports, which is
smaller than the one we set out to make. TSI’s attribution is not more
accurate than spectral attribution; against a well-chosen adaptive rule
it is exactly as accurate. What it is, is unconditional: it arrives with
the index, ranks the nodes with no parameter to select and no way to
select it wrongly, and it also beats the simpler degree rule in all four
regimes (0.933–0.961), which is why we adopt it over a generic
centrality. That is a robustness and simplicity argument, not a
resolution argument, and it should be read as one.

Two further limits bound even that. The evidence is synthetic, with a
controlled ground truth real markets do not provide, so it is a
mechanism result and not a field validation. And it does not overturn
the detection tie of
Section <a href="#sec:spectral" data-reference-type="ref"
data-reference="sec:spectral">6.2</a>: on discriminating stressed
windows from calm ones, TSI and the effective rank remain statistically
indistinguishable, and nothing here changes that.

## Benchmarking Against Sharper Spectral Baselines

Because the Absorption Ratio is a deliberately coarse spectral summary,
we re-ran the identical protocol (same windows, crisis labels,
F1-at-90th-percentile criterion and block bootstrap) against the sharper
baselines of Section <a href="#sec:ar" data-reference-type="ref"
data-reference="sec:ar">4.1</a>. One design point decides this
comparison and we handle it explicitly: the persistence filter of
Section <a href="#sec:mem" data-reference-type="ref"
data-reference="sec:mem">5.2</a> helps any series that is elevated in
bursts, so filtering TSI and not its rivals would flatter TSI. We
therefore report every metric twice, raw and under the same asymmetric
filter, and run the bootstrap on the like-for-like column. Out of sample
(2016–2026, 897 windows):

<div class="center">

|                          | F1@p90 |           |            |                    |           |          |
|:-------------------------|:------:|:---------:|:----------:|:------------------:|:---------:|:--------:|
| 2-3 Metric               |  raw   | filtered  | $\Delta$F1 |       95% CI       |    $p$    | Verdict  |
| TSI                      | 0.367  | **0.447** |            |                    |           |          |
| Effective rank (corr.)   | 0.347  |   0.377   |  $+0.038$  | $[-0.010, +0.111]$ |   0.10    |   tie    |
| Vendi score              | 0.347  |   0.377   |  $+0.037$  | $[-0.009, +0.104]$ |   0.12    |   tie    |
| Absorption Ratio         | 0.174  |   0.134   |  $+0.219$  | $[+0.070, +0.410]$ | $<0.0005$ | TSI wins |
| Effective rank (returns) | 0.179  |   0.174   |  $+0.227$  | $[+0.097, +0.393]$ | $<0.0005$ | TSI wins |

</div>

$\Delta$F1 and its interval come from the block bootstrap on the
filtered column and need not equal the difference of the two point
estimates. The filter is the same asymmetric map for every row, applied
to the stress-oriented signal (the effective rank and the Vendi score
fall under stress, so they enter negated).

<figure id="fig:benchmarks">
<embed src="figure2_benchmarks.pdf" style="width:72.0%" />
<figcaption>Out-of-sample crisis detection, each metric read raw (pale)
and under the same persistence filter (solid). TSI outperforms the
Absorption Ratio by a wide margin in both readings, but the sharper
spectral baselines sit within its confidence interval in both. The
advantage over the industry standard is real; the advantage over a
properly sharpened spectral measure is not, and giving the rivals the
same filter does not change that verdict.</figcaption>
</figure>

The verdict does not depend on which column is read. Raw, TSI leads the
effective rank by 0.020; filtered, by 0.070; in neither case does the
bootstrap interval exclude zero. Over the full history (2000–2026, 2,232
windows) the pattern repeats: under the same filter TSI scores 0.389
against 0.342 for the effective rank (tie, $p = 0.07$) and 0.175 for the
Absorption Ratio (TSI wins, $p < 0.0005$).

**Does the verdict depend on the crisis list?** For one comparison, yes.
Re-running the same protocol under each of the three lists of
Section <a href="#sec:oos_results" data-reference-type="ref"
data-reference="sec:oos_results">6.3</a>, on both the hold-out period
and the full history, with every series filtered:

<div class="center">

| Sample        | List            |  TSI  | Eff. rank |  Absorption R.  | Eff. rank (ret.) |
|:--------------|:----------------|:-----:|:---------:|:---------------:|:----------------:|
| Out of sample | 16 ep. (21.9%)  | 0.434 | 0.343 $=$ |    0.168 $=$    | 0.224 $\bullet$  |
| 2016–2026     | 23 win. (34.9%) | 0.447 | 0.377 $=$ | 0.134 $\bullet$ | 0.174 $\bullet$  |
|               | 25 ep. (33.0%)  | 0.451 | 0.383 $=$ | 0.135 $\bullet$ | 0.181 $\bullet$  |
| Full history  | 16 ep. (27.7%)  | 0.340 | 0.363 $=$ |    0.204 $=$    |    0.192 $=$     |
| 2000–2026     | 23 win. (40.6%) | 0.389 | 0.342 $=$ | 0.175 $\bullet$ | 0.165 $\bullet$  |
|               | 25 ep. (39.8%)  | 0.386 | 0.343 $=$ | 0.164 $\bullet$ | 0.167 $\bullet$  |

</div>

$=$ tie, $\bullet$ TSI wins, by block bootstrap on the F1 gap.
Percentages are the share of windows the list labels as stress.

Two readings follow. The tie against the effective rank is *robust*: it
holds in all six cells. Its direction is consistent, with TSI ahead in
five of the six, and in the sixth the effective rank leads by 0.023,
well inside the noise ($p = 0.59$). The win over the Absorption Ratio is
*not* robust: it disappears in both cells of the narrowest list, where
the gap remains positive ($+0.170$ and $+0.121$) but the interval
touches zero. We report this because the Absorption Ratio is the
benchmark this work set out to beat and the one a practitioner would
already have in production. The correct statement is that TSI beats it
clearly under the two broader labellings and falls short of conventional
significance under the narrowest, which is also the one with the fewest
labelled windows and the least power.

**Why the tie happens, and what it is not.** The four baselines are not
four independent objects. The Vendi score and the effective rank are
identical by construction on a correlation matrix, as noted in
Section <a href="#sec:ar" data-reference-type="ref"
data-reference="sec:ar">4.1</a>, and empirically the Absorption Ratio
and the effective rank computed on the return matrix are near-duplicates
as well (Pearson 0.91, Spearman 0.97), which is why they score alike.
That leaves two distinct baselines, not four. Against them TSI is far
from equidistant: it correlates 0.85 (Spearman 0.93) with the effective
rank and only 0.54 (Spearman 0.61) with the Absorption Ratio, and it
shares 53% of its alarm windows with the former against 34% with the
latter. TSI is therefore a close relative of the effective rank and a
distant one of the Absorption Ratio, which is exactly what the companion
theoretical work predicts: the global scalar $\operatorname{Tr}(A^3)$ is
the third spectral moment and belongs to the same family as the spectral
entropies , whereas the Absorption Ratio reads leading-eigenvalue mass.
The tie is not an awkward null result to be explained away; it is the
predicted outcome, and the 47% of alarms TSI does not share with its
nearest relative is the measure of how far a different construction of
the same spectrum can move.

**Alarm quality on a common criterion.**
Section <a href="#sec:oos_results" data-reference-type="ref"
data-reference="sec:oos_results">6.3</a> gave an unexplained-alarm rate
for TSI alone. Computed for every metric on the same 25-episode list, at
the same top-decile alarm budget (full history, all series filtered):
TSI 4.0% (9 of 224), effective rank and Vendi 14.7% (33), effective rank
on returns 58.5% (131), Absorption Ratio 59.4% (133). Out of sample the
ordering is the same (3.3%, 17.8%, 61.1%, 71.1%). TSI’s alarms are
therefore the cleanest of any metric tested, by a wide margin over the
industry standard and by roughly a factor of four over the effective
rank.

One qualification prevents that from being read as an independent
result, and it is the reason we ran the comparison rather than quoting
the 4% on its own. With the alarm budget fixed at the top decile, the
unexplained-alarm rate is exactly $1 - \text{precision}$, and F1 at a
fixed alarm count is a monotone function of the same quantity. The two
comparisons are one comparison in two presentations. The verdict from
the bootstrap therefore carries over unchanged: against the effective
rank the difference in alarm quality is real in point estimate and not
separable from zero at this sample size, exactly as the F1 comparison
found.

We read this as the honest and more informative result. TSI’s advantage
over the Absorption Ratio is real, reproducible and statistically
significant but the gap is largely explained by the AR being a weak
baseline on this data (F1 $\approx 0.17$–$0.19$, roughly half of every
other measure tested), not by TSI accessing information the spectrum
lacks. **Against a properly sharpened spectral baseline, TSI ties.** It
does not lose, and retains a small positive point estimate in every
comparison, but the difference is not statistically distinguishable from
zero. The defensible claim is therefore not that TSI dominates spectral
methods, but that it matches the best of them while being constructed
from a different primitive, network topology rather than variance
decomposition, and while carrying an attribution layer that arrives with
the index and needs no selection rule
(Section <a href="#sec:attrib" data-reference-type="ref"
data-reference="sec:attrib">6.1</a>, which also reports what that is and
is not worth). A lead–lag analysis
(Section <a href="#sec:leadlag" data-reference-type="ref"
data-reference="sec:leadlag">6.7</a>) establishes the correct register
for all of these claims: the cross-correlation with the stress index
peaks at zero lag and decays symmetrically, so TSI is a *coincident
state index*, reporting that the network is presently in a concentrated
and stressed configuration, and not a leading indicator. We frame every
claim accordingly.

## Out-of-Sample Calibration and False-Alarm Rate

Over the full 2000–2026 OFR series (2,232 windows), the correlation
between in-sample and out-of-sample F1 across the full 36-combination
grid is $\mathbf{0.96}$. The optimum ($\alpha_{\downarrow} = 0.08$,
robust for $\alpha_{\uparrow} \in [0.5, 0.7]$) matches the values chosen
by inspection.

**Three ground-truth lists, and which figure uses which.** The episodes
that count as stress were labelled at three points in this project and
the lists are not identical. We set them out rather than let a reader
assume a single list throughout, because each headline number below is
attached to a different one.

- A *16-episode* list with narrow windows, used for the hyperparameter
  calibration of Section <a href="#sec:oos" data-reference-type="ref"
  data-reference="sec:oos">5.3</a>. On it, out of sample (2016–2026),
  TSI with memory gives **69% precision and 32% recall** at the
  90th-percentile threshold.

- A *23-window* list with wider windows, used for every F1 figure in
  Sections <a href="#sec:signif" data-reference-type="ref"
  data-reference="sec:signif">6.4</a>
  and <a href="#sec:spectral" data-reference-type="ref"
  data-reference="sec:spectral">6.2</a>. On it, out of sample, the same
  series gives precision 1.00 and recall 0.29 (90 alarms, none falling
  outside a labelled window).

- A *25-episode* list used to ask a different question: not whether an
  alarm falls inside a pre-drawn window, but whether it corresponds to
  any documented episode at all. Across the full history 9 of 224 alarms
  have no such correspondence, a **4.0% unexplained-alarm rate**.

Three caveats bound that last figure and we state all three. It is
computed over the full 2000–2026 history rather than the hold-out
period, so it is not an out-of-sample result. Its list is broader than
the 23-window one, so it is a laxer test by construction. And we have
not computed the same quantity for the Absorption Ratio or for the
spectral baselines, so it characterises TSI and does not separate it
from them. Rather than pick one list and discard the others, we re-ran
every comparison under all three.
Section <a href="#sec:spectral" data-reference-type="ref"
data-reference="sec:spectral">6.2</a> reports the result: one verdict in
this paper does depend on which list is used, and it is not the one we
expected.

## Statistical Significance

Restricted to 2016–2026 (897 windows), the F1 gap between TSI with
memory and the Absorption Ratio is 0.273 (0.447 vs. 0.174).
Block-bootstrap ($B=2{,}000$, block $\approx$ 1 quarter): **95% CI
$[0.095,\, 0.392]$**, does not cross zero, one-sided $p < 0.0005$.

TSI with memory here is the asymmetric filter of
Section <a href="#sec:mem" data-reference-type="ref"
data-reference="sec:mem">5.2</a> ($\alpha_{\uparrow} = 0.6$,
$\alpha_{\downarrow} = 0.08$) applied to raw TSI, which is the form used
throughout this paper. We say so explicitly because the next section
compares against spectral rivals and the choice of filter moves the
number materially.

*Caveat.* This metric rewards sustained-plateau behaviour, which is
precisely what the memory filter was built to produce. The test confirms
the filter achieves its design goal with statistical confidence, not
that TSI with memory is superior on some independent criterion.

#### The head-to-head, run where the index is well behaved.

On 464 S&P 500 constituents with a complete ten-year history the balance
index does not saturate: it takes distinct values in every window, and
at the 90th percentile it flags 10.2% of them, as do TSI, the binary
balance index and the effective rank. The Absorption Ratio cannot be
scored in this configuration at all, and for a reason worth stating:
with a 60-day window and 464 assets the covariance matrix has rank 59,
so the top $n/5 = 93$ eigenvalues capture the entire trace by
construction and the ratio is identically one. That is a limitation of
the configuration, not of the measure.

Ground truth here is *theirs*, not ours: a window is labelled systemic
when the cross-sectional mean return falls below a threshold over a
20-day span, which is the definition used in the original work. Adopting
it removes our own episode judgement from the comparison entirely.

**The result is a tie, at every threshold and under both readings of the
label.** Scoring against the contemporaneous span, TSI reaches $F_1$ of
$0.160$–$0.161$ and the balance index $0.184$–$0.187$, with every paired
difference’s interval crossing zero ($p$ from $0.43$ to $0.63$); the
binary variant and the effective rank land in the same place. No measure
separates itself, and none is far above the chance level of roughly
$0.14$ at this alarm budget and base rate. We read that as a property of
the label rather than of the measures: a return-based event is a coarse
proxy for a structural one, and this is the price of using someone
else’s definition rather than our own.

**One thing did fall out of it, and it corroborates the central claim of
this paper from an unexpected direction.** Orientation was measured
rather than assumed in every cell. Against the *contemporaneous* span
TSI enters positively, rising as returns deteriorate. Against the
*forward* span its orientation reverses. An index that reads the present
correctly and inverts when asked about the future is precisely a
coincident state index, which is what
Section <a href="#sec:leadlag" data-reference-type="ref"
data-reference="sec:leadlag">6.7</a> establishes by a different route.
These tests use a different universe and a different ground truth from
Section <a href="#sec:spectral" data-reference-type="ref"
data-reference="sec:spectral">6.2</a>, so they form their own family and
are not folded into the correction of
Section <a href="#sec:multiplicity" data-reference-type="ref"
data-reference="sec:multiplicity">6.6</a>.

## Head-to-Head Against Ollivier–Ricci Curvature

Correlations are mapped to the Mantegna distance
$d_{ij} = \sqrt{2(1-\rho_{ij})}$, each node carries a measure over its
neighbours proportional to the absolute correlation, and the curvature
of an edge is $\kappa_{ij} = 1 - W_1(m_i,m_j)/d_{ij}$ with the
earth-mover distance computed exactly by linear programming. The
market-level scalar is the mean edge curvature; a correlation-weighted
mean was also computed and behaves almost identically. Everything else
is unchanged: same windows, same asymmetric filter applied to the
curvature series as to every other, $F_1$ at the 90th percentile, block
bootstrap, all three labellings.

Orientation was measured rather than assumed. Mean curvature is $0.711$
in labelled crisis windows against $0.678$ in calm ones, so it rises
under stress, which is the direction the original work reports.

<div class="center">

| Sample         | Labels      | $F_1$ TSI | $F_1$ curvature | $\Delta F_1$ ($p$) |
|:---------------|:------------|:---------:|:---------------:|:------------------:|
| OOS 2016–2026  | 16 episodes |   0.434   |      0.301      |  $+0.126$ (0.011)  |
| OOS 2016–2026  | 23 windows  |   0.447   |      0.337      |  $+0.087$ (0.007)  |
| OOS 2016–2026  | 25 episodes |   0.451   |      0.321      |  $+0.101$ (0.003)  |
| FULL 2000–2026 | 16 episodes |   0.340   |      0.335      |  $+0.023$ (0.388)  |
| FULL 2000–2026 | 23 windows  |   0.389   |      0.317      |  $+0.074$ (0.018)  |
| FULL 2000–2026 | 25 episodes |   0.386   |      0.316      |  $+0.073$ (0.023)  |

</div>

Curvature lands where a reader familiar with this literature would
expect it to land: clearly above the Absorption Ratio, which scores 0.13
to 0.17 on the same windows, and somewhat below the effective rank,
which scores 0.34 to 0.38. It is a mid-strength baseline rather than a
weak one, and the honest summary is that TSI is ahead of it in all six
cells but not by the margin it holds over the Absorption Ratio.
Section <a href="#sec:multiplicity" data-reference-type="ref"
data-reference="sec:multiplicity">6.6</a> reports what survives once
this comparison is folded into the corrected family, and only one of the
five nominally significant cells does.

## Correcting for Multiple Comparisons

This paper runs many related tests, and reporting each in isolation
would overstate the evidence. We therefore define the family in advance
and correct over all of it. Hypothesis H1 is tested by comparing TSI
against every *distinct* baseline (the effective rank, which is
identical to the Vendi score on a correlation matrix and so is counted
once; the Absorption Ratio; and the effective rank computed on the
return matrix), on both samples, under all three crisis labellings. With
the Ollivier–Ricci curvature of
Section <a href="#sec:ricci" data-reference-type="ref"
data-reference="sec:ricci">6.5</a> included, that is
$4 \times 2 \times 3 = 24$ tests, and all twenty-four enter the family,
including those that were never going to be reported as wins: choosing
which tests belong is precisely the manoeuvre the correction exists to
prevent. We apply Holm–Bonferroni at a family-wise error rate of $0.05$,
which is uniformly more powerful than plain Bonferroni and assumes no
independence between tests.

**Sixteen of the twenty-four are significant before the correction and
nine after it.** The nine that survive are the eight wins over the
Absorption Ratio and over the effective rank on returns, under the
23-window and 25-episode labellings, on both samples, all with bootstrap
$p$ below $0.0001$ against Holm thresholds between $0.0028$ and
$0.0045$; plus one of the six comparisons against curvature. The six
comparisons against the effective rank were ties before the correction
and remain ties after it, so the central finding of this paper is
untouched: a correction cannot turn a tie into anything else.

**Three results are lost, and all three sit on the same labelling.** The
win over the effective rank on returns out of sample under the
16-episode list ($\Delta F_1 = +0.179$, $p = 0.0060$ against a threshold
of $0.0050$), and the wins over the Absorption Ratio and the effective
rank on returns over the full history under the same list ($p = 0.040$
and $p = 0.044$). This is the narrowest of the three labellings and the
one with the least power, and the paper already identified it as the
weakest support for the Absorption Ratio result before the correction
was applied. The correction did not reveal a new weakness; it quantified
one that was already declared.

The practical reading is that the advantage over the Absorption Ratio is
real under the two broader labellings and does not reach family-wise
significance under the narrowest. We state the claim at that strength
and no higher.

## Lead–Lag Analysis: a Coincident Index, Not a Forecast

The F1-at-90th-percentile criterion used throughout asks whether TSI is
*elevated during* documented stress windows. It is a contemporaneous
classification test, and it says nothing about whether TSI rises
*before* stress. Because the framing of a “fragility index” invites the
stronger reading, we test the stronger claim directly.

We cross-correlate TSI against the OFR Financial Stress Index  at lags
$k \in [-15, +30]$ observations (each step $\approx$ 3 business days),
where $k > 0$ means TSI leads. Results on the full history
($n = 2{,}232$):

<div class="center">

| Signal           | Peak $|\rho|$ at | $\rho$ at $k=0$ |             Reading             |
|:-----------------|:----------------:|:---------------:|:-------------------------------:|
| TSI raw          |     $k = 0$      |    $+0.203$     |       exactly coincident        |
| TSI with memory  |     $k = -2$     |    $+0.195$     | coincident (marginally lagging) |
| Absorption Ratio |    $k = -15$     |    $+0.063$     |             lagging             |

</div>

<figure id="fig:leadlag">
<embed src="figure1_leadlag.pdf" />
<figcaption>Cross-correlation against the OFR Financial Stress Index.
TSI with its persistence filter is in dark blue, raw TSI in green, and
the Absorption Ratio in red. <strong>(a)</strong> In levels, TSI peaks
at or just before zero lag and decays symmetrically.
<strong>(b)</strong> In first differences the same conclusion sharpens:
at positive lags, where a leading indicator would show its peak, the
correlation lies inside the noise band. The shape identifies a
coincident state index rather than a forecast.</figcaption>
</figure>

Both series are strongly autocorrelated, so the absolute $\rho$ values
in levels are not the object of interest; the informative feature is the
*shape* of the cross-correlation function, which decays symmetrically
about $k \approx 0$, the signature of a contemporaneous relationship
rather than a leading one. Repeating the analysis on first differences
sharpens the same conclusion: $\Delta\mathrm{TSI}$ raw peaks exactly at
$k = 0$ ($\rho = +0.094$), and at $k = +1$, with TSI leading by a single
step, the correlation is statistically indistinguishable from zero
($\rho = -0.009$ and $+0.008$ for the memory and raw forms respectively,
against a significance threshold of $\pm 0.041$ at $n = 2{,}231$). The
memory filter, being an exponential moving average, introduces a small
lag rather than an anticipation, peaking at $k = -4$.

**What this does and does not change.** It does not affect the paper’s
principal result: the F1 comparison was always a contemporaneous test,
it reproduces, and TSI outperforms the Absorption Ratio at every lag
examined ($\rho \approx 0.20$ versus $0.06$). What it does change is the
permissible framing. TSI should be read as a *state index*, closer in
spirit to Convective Available Potential Energy in meteorology, which
reports that the atmosphere is presently primed for severe weather
without predicting when or where a storm will form, than as an
early-warning signal. A high reading says the correlation network is
presently in a concentrated, stressed configuration. It does not say
that stress is coming. We adopt that language throughout and recommend
that practitioners do the same.

## Four Original Scenarios

**Bear Stearns (March 2008).** Raw TSI peaks *before* the rescue and
falls afterward, while the Absorption Ratio keeps rising; TSI with
memory tracks the AR’s sustained trajectory.

**Lehman Brothers (September 2008).** Raw TSI jumps sharply within days
of the collapse, a much sharper reaction than the AR, and TSI with
memory preserves this signal through October.

**European debt crisis (2011): the original failure case.** Raw TSI
falls to 0.17–0.30 during the crisis on the 10-bank network while the AR
stays elevated; TSI with memory corrects this.
Section <a href="#sec:large_network" data-reference-type="ref"
data-reference="sec:large_network">6.9</a> shows this failure does not
replicate on a larger, diversified network.

**AI sector: the 2025 tariff shock.** The same failure-and-correction
pattern recurs on the tech-stock network ($n=11$).

## Large-Network Robustness and the Central Finding

Running the full pipeline on a 42-asset network diversified across seven
sectors, 2006–2026, and normalising to z-scores:

<div id="tab:zscores">

|              |                     |                  |                 |                 |
|:-------------|--------------------:|-----------------:|----------------:|----------------:|
|              |          Financials |             Tech |         Diverse |            Full |
|              | ($n=10$, epicentre) | ($n=8$, non-ep.) |  ($n=9$, mixed) |        ($n=42$) |
| Bear Stearns |             $-0.28$ |          $-0.42$ |         $-0.26$ |         $-0.12$ |
| Lehman       |              $0.10$ |           $1.20$ |          $1.27$ | $\mathbf{2.61}$ |
| Euro debt    |             $-1.09$ |           $2.18$ | $\mathbf{5.35}$ |          $2.13$ |

Ending z-scores by network composition.

</div>

The pattern sits in the epicentre column. During the European debt
crisis the ten-bank basket, which *is* the epicentre sector, ends at
$z = -1.09$, below its own historical mean while the crisis is still
running, whereas the diverse and full baskets end at $+5.35$ and
$+2.13$; the same ordering holds at Lehman. That collapse of the reading
during the episode is the forgetting behaviour the memory filter was
built to repair, and it appears only where the basket is concentrated on
the epicentre.

Node count alone does not explain it: the 8-node tech-only basket does
**not** exhibit the forgetting pattern. **The variable that matters is
whether the tested basket is concentrated in the sector that is the
actual epicentre of the crisis.** Any basket that avoids that
concentration, whether small-and-diverse or large-and-diverse, retains
an elevated reading.

Replication in COVID (z = 1.35, Feb–Apr 2020) and the 2022 rate-hike
selloff (z = 1.41, Jan–Oct 2022) confirms the pattern in two independent
episodes.

## Cross-Market Test: Crypto, Commodities, FX, and Sovereign Debt

**Two clear successes.** The all-time peak in the crypto series (z =
3.9) falls in May–June 2022, the Terra/Luna collapse, with MATIC-USD
flagged as the most-connected asset. The all-time peak in sovereign debt
(z = 3.6, August–December 2023) coincides with the historic bond
selloff, with MBB (the highest-duration instrument) flagged as
responsible.

**Two episodes outside what TSI is built to measure.** The September
2022 pound sterling / UK gilt crisis: TSI with memory stayed negative
throughout, because the crisis was largely contained to sterling-linked
instruments rather than reorganising the broader FX correlation
structure. The 2022 Ukraine invasion: a $\sim$<!-- -->3-month lag before
TSI rose, consistent with geopolitical shocks propagating through price
co-movement over weeks rather than instantaneously.

These are not detection errors but *scope boundaries*: TSI detects
correlation-structure breaks (episodes where normally semi-independent
assets suddenly co-move), not directional price events. This yields a
precise, falsifiable scope claim.

## Attempted Replication on Shorter Series

We attempted to repeat the calibration on the bank network (train: Bear
Stearns + Lehman 2008; test: European debt crisis 2011) and the AI
network. Both failed to reproduce the OFR result, and not because the
filter stopped working, but because the highest TSI with memory readings
in the training period systematically fell *outside* our defined crisis
windows (they clustered on real but undocumented events).

**Finding.** With short series (5 years, 2–3 labelled episodes), the
definition of the ground-truth event list dominates the calibration
result far more than the choice of hyperparameters. The 26-year,
20+-episode OFR series has enough independent events to support reliable
out-of-sample calibration; 5-year, 2–3-episode series do not.

## Persistent Homology

The correlation-network H1 construction showed no discriminative pattern
(mean 0.03–0.07 across all scenarios; calm and crisis periods
indistinguishable). We attribute this to insufficient topological
richness in an 8–11-node graph.

The Takens-embedding construction tells a different story. The all-time
maximum (30 March 2020, COVID) sits $\sim$<!-- -->12 standard deviations
above the historical mean (0.104 $\pm$ 0.110). **Fifteen of the twenty
highest readings fall inside documented crises**, including
October–November 2011, exactly the episode the small-network raw TSI
missed.

## The signed channel, and a head-to-head against the balance index

Three questions follow from the previous paragraph, and we answer them
on the same windows, with code in the repository.

**First: does the sign of the triangle carry independent information?
No.** Replacing $\operatorname{Tr}(A^3)$ by $\operatorname{Tr}(\rho^3)$,
which counts balanced minus frustrated triangles, changes nothing: the
two series correlate at $1.000$ across all 2,232 windows, and the
resulting $F_1$ moves by $0.000$ (95% CI $[-0.005, +0.005]$). The reason
is structural rather than particular to this data. Positive
semi-definiteness bounds how frustrated a triangle in a correlation
matrix can be, so signed and unsigned triangle counts are nearly
collinear by construction; the measured ratio averages $0.92$. The sign
channel that the balance literature exploits is not reachable through
the triangle count alone, and we retire this extension rather than carry
it forward.

**Second: the balance index as an attribution rule.** The local balance
of Bartesaghi et al. shares with $\mathrm{diag}(A^3)$ the property of
having no $k$ to select, so it belongs in the comparison above on merit.
On the same benchmark it scores $0.329$, $0.552$, $0.724$ and $0.841$
for one to four epicentres, against $0.992$, $0.996$, $0.972$ and
$0.966$ for the triangle rule, with chance at $0.188$ to $0.750$.
Because the generator contains no sign structure, which is precisely
what a balance index is built to read, we repeated it with half of each
stressed block loading negatively on its factor, so that frustrated
triangles are present by construction. The ordering does not move:
$0.992$, $0.988$, $0.979$, $0.968$ against $0.350$, $0.567$, $0.719$,
$0.838$.

**Third: detection, where we decline to claim a win.** On our windows
the balance index scores poorly, but the reason disqualifies the
comparison rather than settling it. The index *saturates*: with 20-day
windows over eight nodes it sits at its maximum of $1$ on 26% of windows
in its weighted form and 70% in the binary form the same authors report,
because short-window correlation matrices are almost entirely positive
and an all-positive network is perfectly balanced. On the 42-asset
network of
Section <a href="#sec:large_network" data-reference-type="ref"
data-reference="sec:large_network">6.9</a> lengthening the window makes
it worse rather than better, the fraction of windows at $\kappa = 1$
rising from 10% at 45 days to 24% at 100 and 63% at 400.

That last observation, however, is a statement about small networks and
not about the index, and the distinction decides who the finding is
about. Repeating the measurement on 447 S&P 500 constituents, and again
on 464 over a ten-year panel, the saturation disappears: $\kappa$ ranges
over almost the whole unit interval, with a median of $0.44$ on the
first panel and $0.03$ on the second at a 60-day window, and at most
$2.0\%$ of windows sit at the maximum at any window length from 45 to
500 days. The measurement is reproduced by
`code/validation/balance_saturation_sp500.py`. The reason is
combinatorial. The number of triangles grows as $n^3$, so in a large
network a modest fraction of negative correlations already produces
enough frustration to move the index, whereas a network of a few dozen
nodes is close to balanced whatever the market is doing. Saturation is
therefore a property of *small* correlation networks, and the regime the
original authors work in, 199 to 385 assets, is not one of them.

Two consequences follow, and neither favours us. Our own networks of
eight and 42 nodes are exactly the regime where their index cannot be
evaluated, so no ranking produced on them would be informative about it,
and none is given here. And the level of $\kappa$ is not portable: the
median moves from $0.44$ to $0.03$ between two panels of the same market
a few years apart, so a fixed threshold calibrated on one dataset need
not fire at all on another. What we do report is a check in the other
direction: on our data their headline association reproduces, with the
Spearman correlation between the balance index and mean absolute
correlation at $0.94$, $0.89$ and $0.71$ for the three window lengths
against the $0.877$ they report, and with the conditional mean of
forward average returns decreasing monotonically across balance
quintiles at 45-day windows, as they describe.

**A methodological note that this exercise forced, and that applies to
the like-for-like table of
Section <a href="#sec:spectral" data-reference-type="ref"
data-reference="sec:spectral">6.2</a>.** $F_1$ at a fixed percentile is
a fixed alarm budget only if the metric takes distinct values near the
threshold. A saturating metric flags far more than the intended fraction
of windows and scores an inflated $F_1$ through recall alone; the binary
balance index flags 70% of windows at its 90th percentile and reaches
$F_1 = 0.537$ with a precision of $0.425$ against a base rate of
$0.406$, which is no better than chance. We verified that no benchmark
reported in this paper has this property. Every series in that table,
raw and filtered, takes distinct values throughout and flags exactly
10.0% of windows at its 90th percentile; the check is printed by
`code/validation/samefilter_benchmarks.py` in the repository.

# Discussion

**What the index is worth, stated as a package.** No single comparison
in this paper is decisive on its own, and we do not present one as such.
Taken together they describe something narrower and, we think, more
useful than a win. On detection, TSI matches the best spectral measure
available: a tie in all six labelling-by-sample cells, with the point
estimate in TSI’s favour in five of them, which is a consistent
direction that never separates from zero at this sample size. At the
same alarm budget its alarms are the cleanest of any metric tested, 4.0%
unexplained against 14.7% for the effective rank and roughly 59% for the
Absorption Ratio, though that is the same comparison re-expressed and
carries the same verdict. It reaches that level from a different
primitive, network topology rather than variance decomposition, sharing
only half its alarms with its nearest relative. And it arrives with a
node-attribution layer that requires no selection rule, ties the best
adaptive spectral rule, and cannot be misconfigured the way a fixed or
badly chosen $k$ can be.

None of those four is a headline on its own. The defensible claim is the
conjunction: *equal detection performance, cleaner alarms in point
estimate, a different construction, and attribution included at no extra
parameter*. A practitioner already running an effective-rank monitor
would not switch on the strength of the detection numbers alone, and we
do not suggest they should. What they would gain is the attribution
layer, which their current tool supplies only after they commit to a
component count and get it right.

The central methodological lesson is that **whether a tested basket is
concentrated in the sector at the epicentre of a given crisis, not raw
network size, determines whether raw TSI needs a memory correction.** On
a network concentrated in the epicentre sector (10 banks during banking
crises), raw TSI behaves as a sharp but forgetful alarm. On a network
that avoids that concentration, whether large-and-diverse (42 assets) or
small-but-diverse (9 assets spanning seven sectors), raw TSI already
exhibits sustained-elevation behaviour, replicated across three
independent crises.

# Limitations

#### On real matrices the attribution reduces to the degree.

The per-node layer is defended in this paper on a synthetic benchmark
where the ground truth is known, and there $\mathrm{diag}(A^3)$ scores
0.966 to 0.996 against 0.933 to 0.961 for the far simpler node degree,
$\sum_j |\rho_{ij}|$. That gap does not survive contact with real data.
Across 245 windows of 464 S&P 500 constituents, the cross-sectional rank
correlation between $\mathrm{diag}(A^3)$ and the degree averages
**0.996**, and a cubic in the degree explains $R^2 = 0.992$ of the
triangle count. We then asked whether the remaining 0.8% carries
anything of its own, since that residual is the only part of the
quantity that is not a restatement of the degree. It does not: its rank
correlation with forward five-day returns is $+0.002$ with a bootstrap
interval spanning zero, and its apparent association with forward
volatility ($+0.187$) disappears once current volatility is partialled
out ($+0.016$, interval $[-0.003, +0.035]$), while the degree itself
retains a small but non-zero effect there. The practical reading is that
on correlation networks of real assets, naming the culprit with
$\mathrm{diag}(A^3)$ and naming it with the degree give the same answer,
and a practitioner should use the degree, which costs one matrix
row-sum. What the triangle count buys is what
Section <a href="#sec:attrib" data-reference-type="ref"
data-reference="sec:attrib">6.1</a> claims and no more: no parameter to
misspecify, and a measured advantage in a regime where the ground truth
can be checked.

- The large-network result
  (Section <a href="#sec:large_network" data-reference-type="ref"
  data-reference="sec:large_network">6.9</a>) is a single test on one
  42-asset universe; it has not been repeated with different sector
  compositions or other crises.

- The attempted short-series recalibration is a negative methodological
  result; we did not re-derive “correct” crisis windows to avoid
  indefinitely re-tuning ground truth.

- The Takens-embedding H1 result uses one embedding dimension and delay,
  chosen once; a proper replication would test robustness to these
  choices.

- The statistical significance test evaluates the memory filter against
  the exact objective it was designed for; it is not independent
  evidence of general superiority.

- Three different ground-truth lists are in use across the paper
  (Section <a href="#sec:oos_results" data-reference-type="ref"
  data-reference="sec:oos_results">6.3</a>). Every F1 figure uses one of
  them consistently, but the precision, recall and unexplained-alarm
  figures do not come from the same list as the F1 figures, and no
  result should be quoted as if they did.

- The attribution result of
  Section <a href="#sec:attrib" data-reference-type="ref"
  data-reference="sec:attrib">6.1</a> is established on synthetic
  networks. Against a spectral comparator with an adaptive $k$ it is a
  tie, not an advantage; the advantage claimed is the absence of a
  selection rule, not accuracy.

- The win over the Absorption Ratio does not survive the narrowest of
  the three crisis lists
  (Section <a href="#sec:spectral" data-reference-type="ref"
  data-reference="sec:spectral">6.2</a>), and it is one of the three
  results that a Holm–Bonferroni correction over the family of eighteen
  tests removes
  (Section <a href="#sec:multiplicity" data-reference-type="ref"
  data-reference="sec:multiplicity">6.6</a>). The tie against the
  effective rank survives all three lists and is unaffected by the
  correction, as a tie must be.

- Nothing in this document constitutes investment advice.

# Where This Stands

Several questions that a reader would reasonably raise have already been
answered, and it is more useful to say so than to list them as future
work.

**Settled, and reported above.** Whether the conclusions survive a
correction for multiple comparisons:
Section <a href="#sec:multiplicity" data-reference-type="ref"
data-reference="sec:multiplicity">6.6</a> defines the family of
twenty-four tests and applies Holm–Bonferroni, and reports what does not
survive it. Whether the index beats the nearest structural precedent,
Ollivier–Ricci curvature:
Section <a href="#sec:ricci" data-reference-type="ref"
data-reference="sec:ricci">6.5</a> runs that head-to-head, which earlier
versions declared and did not perform. Whether declining to rank the
global balance index on small networks was concealing a loss: it was
not, and Section <a href="#sec:signed" data-reference-type="ref"
data-reference="sec:signed">6.13</a> reports the tie on a 464-asset
universe where the index is well behaved, under the original authors’
own definition of a systemic event. Whether the attribution advantage
survives a spectral rule that chooses its own number of components: it
does not, and the claim was reduced accordingly to robustness rather
than resolution. Whether the alarm-quality figure holds for the
competitors too: computed for all of them. Whether the results depend on
which list of crisis episodes is used: all three are reported. Whether
signing the correlation recovers the single-asset blind spot: it does
not, and the reason is structural. Whether the per-node layer sees
something the node degree does not: on real matrices it does not, and
Section <a href="#sec:limits" data-reference-type="ref"
data-reference="sec:limits">8</a> says so with the numbers.

**Open, and worth doing.** A systematic sweep of the Takens embedding
parameters, which would not change any conclusion here. And an
attribution test on real data, which needs a partial ground truth, for
instance from regulatory post-mortems of documented episodes; we note
that after the degree result of
Section <a href="#sec:limits" data-reference-type="ref"
data-reference="sec:limits">8</a> the expected outcome of that test is
fairly clear, which lowers its value.

**Not attempted here, deliberately.** Everything in this paper is a
backtest of a state reading. Turning that into an allocation rule is a
different exercise with a different evidential standard, and mixing the
two would weaken both.

Issues, pull requests and replication attempts are welcome at
<https://github.com/BiomeMakers/TSI-OmegaS>. For production licensing:
`acedo@biomemakers.com`.

# Conclusion

TSI’s apparent need for a memory correction turns out to be largely a
property of small, sector-homogeneous, or crisis-epicentre-concentrated
networks, not of TSI itself. On a large, diversified network, raw TSI
already tracks sustained stress correctly. The memory filter remains a
validated, statistically significant, out-of-sample-tested fix for the
small or concentrated-network case, which is the realistic case for many
practical applications (a single sector, a single portfolio, a single
institution’s counterparties).

Across all tests in this paper, namely four original scenarios,
out-of-sample calibration, statistical significance testing, the
like-for-like spectral benchmark under three crisis labellings, the
adaptive-$k$ attribution control, the lead–lag analysis, the
disentangled large-network robustness check and the persistent-homology
extension, the evidence supports a specific and bounded conclusion. TSI
matches a properly sharpened spectral measure at detecting stress rather
than beating it. It equals one, from a different construction, with the
cleanest alarms of anything we tested, and it brings with it an
attribution of each reading to a specific asset that needs no component
count to be chosen and therefore cannot be chosen wrongly. That
combination is what we would ask a practitioner to weigh, complementary
to and not a replacement for established indices such as the Absorption
Ratio.

<div class="thebibliography">

99

Acedo A. (2026). The Functional Symbiotic Resilience Index: Topological
Entropy, Wasserstein Curvature Bounds, and Non-Equilibrium
Thermodynamics of Complex Networks. *Preprint*.
<https://github.com/BiomeMakers/OmegaS-fsri>

Ortiz-Álvarez R, Ortega-Arranz H, Ontiveros V J, de Celis M, Ravarani C,
Acedo A, Belda I. (2021). Network properties of local fungal communities
reveal the anthropogenic disturbance consequences of farming practices
in vineyard soils. *mSystems*, 6(3), e00344-21.

Saati-Santamaría Z, Pérez-Gorjón S, Abel-Schaad D, Acedo-Bécares A, et
al. (2026). Soil microbial diversity and network organization respond to
land use and agricultural inputs worldwide. *Global Change Biology*,
32(7), e70984.

Acedo A, Ortega-Arranz H, Almonacid D, Ferrero A (2022). Methods and
systems for generating and applying agronomic indices from
microbiome-derived parameters. US Patent Application Publication
No. US 2022/0268756 A1 (Appl. No. 17/665,332, filed 4 February 2022),
Biome Makers Inc.

Sandhu R S, Georgiou T T, Tannenbaum A R. (2016). Ricci curvature: an
economic indicator for market fragility and systemic risk. *Science
Advances*, 2(5), e1501495.

Sánchez García J, Gherghe S. (2024). On the Ollivier-Ricci curvature as
fragility indicator of the stock markets. arXiv:2405.07134.

Kritzman M, Li Y. (2010). Skulls, Financial Turbulence, and Risk
Management. *Financial Analysts Journal*, 66(5).

Gidea M, Katz Y. (2018). Topological Data Analysis of Financial Time
Series: Landscapes of Crashes. *Physica A*, 491.

Mantegna R N. (1999). Hierarchical structure in financial markets.
*European Physical Journal B*, 11(1).

Billio M, Getmansky M, Lo A W, Pelizzon L. (2012). Econometric measures
of connectedness and systemic risk in the finance and insurance sectors.
*Journal of Financial Economics*, 104(3).

Minsky H P. (1992). The Financial Instability Hypothesis. *Levy
Economics Institute Working Paper* No. 74.

Monin P J. (2019). The OFR Financial Stress Index. *Risks*, 7(1), 25.

Roy O, Vetterli M. (2007). The effective rank: a measure of effective
dimensionality. *Proceedings of the 15th European Signal Processing
Conference (EUSIPCO)*, 606–610.

Friedman D, Dieng A B. (2023). The Vendi Score: a diversity evaluation
metric for machine learning. *Transactions on Machine Learning
Research*. arXiv:2210.02410.

Marchenko V A, Pastur L A. (1967). Distribution of eigenvalues for some
sets of random matrices. *Matematicheskii Sbornik*, 72(4), 507–536.

Laloux L, Cizeau P, Bouchaud J-P, Potters M. (1999). Noise dressing of
financial correlation matrices. *Physical Review Letters*, 83(7),
1467–1470.

Plerou V, Gopikrishnan P, Rosenow B, Amaral L A N, Guhr T, Stanley H E.
(2002). Random matrix approach to cross correlations in financial data.
*Physical Review E*, 65, 066126.

Diebold F X, Yilmaz K. (2014). On the network topology of variance
decompositions: measuring the connectedness of financial firms. *Journal
of Econometrics*, 182(1), 119–134.

Acemoglu D, Ozdaglar A, Tahbaz-Salehi A. (2015). Systemic risk and
stability in financial networks. *American Economic Review*, 105(2),
564–608.

Samal A, Kumar S, Yadav Y, Chakraborti A. (2021). Network-centric
indicators for fragility in global financial indices. *Frontiers in
Physics*, 8, 624373. arXiv:2102.00070.

Bartesaghi P, Diaz-Diaz F, Grassi R, Uberti P. (2025). Global balance
and systemic risk in financial correlation networks. arXiv:2407.14272.

Bartesaghi P, Grassi R, Uberti P. (2025). Local and global balance in
financial correlation networks: an application to investment decisions.
arXiv:2512.10606.

Zhang S, Wang Z, Zheng J, Cartlidge J. (2026). Systemic risk in DeFi: a
network-based fragility analysis of TVL dynamics. arXiv:2601.08540.

</div>

*Correspondence:* Alberto Acedo, Biome Makers Inc.
(`acedo@biomemakers.com`). The author declares no competing financial
interests beyond patent applications filed by Biome Makers Inc. relating
to the index described here.
