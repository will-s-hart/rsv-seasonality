# Tentative analysis plan and responsibilities

Working plan, 18 November 2026. Will leads epidemiological inference and renewal models; Torkel leads differentiable mechanistic modelling and the neural climate component. Proposed responsibilities and effort below remain to be agreed between collaborators. See the [literature review](literature-review.md), [data sources](data-sources.md), and [methodology](modelling-methodology.md).

## Scope and first decision

Primary question: does a shared climate response improve out-of-sample RSV transmission modelling across locations, and which aspects of its shape are identifiable? Secondary question: can different climate trajectories, susceptibility, and childhood mixing explain England's mainly winter outbreaks and Japan's changing warm-season activity?

The focal [Park et al. paper](https://doi.org/10.1038/s41467-025-66184-y) already supplies a mechanistic explanation involving climate and mixing. Start by reproducing it, then test the value of joint climate-driven inference and cross-country validation. A nonlinear curve alone is not the novelty claim.

The intended UK comparator starts with England, not an aggregate labelled UK. Public dashboard positivity currently provides only a short pre-COVID overlap with Japan; the availability of a sufficiently long, interpretable England series is unresolved. If archived DataMart counts/testing denominators cannot be obtained, develop on Japan first, consider Scotland after an equivalent audit, and describe England as a restricted external validation case. This gate can change the study design before model development expands.

## Stages, deliverables, and ownership

Effort bands are indicative active working weeks, with overlap and no calendar deadlines. Data access delays and compute costs are not included.

| Stage | Deliverable and completion criterion | Will | Torkel | Effort |
| --- | --- | --- | --- | --- |
| 0. Agree scope and provenance | Reproduce one focal-paper figure from versioned author data/code; settle outcomes, units, calendar, permissions, causal diagram, and initial held-out split | Lead literature/epidemiology audit; check interpretation of sentinel counts and positivity | Review code, numerical assumptions, and replication route | 1–2 weeks |
| 1. Build the data panel | Versioned acquisition scripts, checksums, missingness/denominator report, regional climate trajectories, surveillance change log; UK feasibility decision recorded | Lead surveillance acquisition, observation definitions, population/births and intervention metadata | Lead climate ingestion, humidity derivation, aggregation, reusable Julia pipeline; Will reviews geography | 2–3 weeks |
| 2. Implement benchmarks | Renewal likelihood plus constant/harmonic/quadratic/spline comparators; reproduce key qualitative seasonal patterns on a small panel | Lead renewal dynamics, susceptible bookkeeping, delays, and likelihood | Review differentiability and implement response interface/optimization harness | 2–3 weeks |
| 3. Demonstrate recoverability | Synthetic experiments quantify curve recovery, false extra peaks, and immunity/reporting confounding under observed weather; freeze model complexity rules | Design epidemiological misspecification and observation scenarios | Lead neural training, gradient checks, identifiability diagnostics, repeated fits | 2–3 weeks |
| 4. Fit and validate | Frozen comparison of shared climate models on held-out years/regions; external transfer only if data gate passed | Lead validation design, epidemiological diagnostics, uncertainty checks | Lead neural fits, regularization tuning within training folds, compute/reproducibility | 3–4 weeks |
| 5. Explain seasonal differences | Supported climate surfaces/trajectories, conditional extrema analysis, mixing/immunity scenarios; optional matched UDE robustness comparison | Lead epidemiological interpretation and contact/susceptibility counterfactuals | Lead matched continuous-time UDE if justified, numerical robustness, response visualization | 2–3 weeks |
| 6. Synthesize | Reproducible figures, sensitivity appendix, limitations, manuscript outline, and public analysis release | Lead epidemiology/methods narrative | Lead numerical/neural methods narrative | 1–2 weeks |

Both review each other's core model and acquisition code. Meet weekly around one concrete diagnostic or figure; record decisions in these notes or short linked decision files. Neither person needs to wait for a complete UDE implementation to establish the initial renewal benchmarks.

## Initial datasets and validation design

1. **Replication:** pin the [authors' repository](https://github.com/parksw3/perturbation) by commit and trace its raw inputs. Keep upstream code/data attribution and licensing distinct from this repository. Reproduce the published analysis before changing its assumptions.
2. **Primary development:** target Japan prefectures, 2012–2019 subject to completeness and the testing-policy audit; the authors' currently inspected CSV starts in 2013, so a 2013–2019 panel is the immediate fallback. Reproduce the focal publication's full analysis window separately, including its pandemic terms; 2013–2019 is our selected pre-COVID subset. Begin with a small geographically diverse panel, then include all usable prefectures. Include Hokkaido, central Honshu, southern Japan, and Okinawa to expose climate-support differences.
3. **Provisional splits:** for a 2012–2019 panel, train 2012–2016, tune on 2017, and hold 2018–2019 for final temporal evaluation; use 2013 as the training start if earlier data are unavailable. Also use prespecified leave-region-out folds. For a separate forward test of the 2016/17 phase shift, train through 2015 only and fix tuning choices without post-2015 outcomes. Reserve geography/splits before outcome-driven model tuning; revise dates once data completeness is known and record the revision. Keep full prior history for latent-state filtering without fitting parameters to future outcomes.
4. **UK comparator:** target pre-2020 England counts and tested denominators plus compatible climate. Do not promise a 2012–2019 England panel from the current dashboard. Use nation/region-specific observation models; additional UK nations are distinct replications, not interchangeable observations.
5. **Stress tests:** reserve 2020–2024 for COVID disruption/recovery analysis. Treat Japan's 2025 sentinel redesign and later prevention/reporting changes as separate epochs requiring additional observation/intervention assumptions. Do not force a climate network to explain those discontinuities.

Use ERA5-family temperature/dewpoint/pressure with precipitation, matched to the epidemiological geography; compare population-weighted gridded estimates with selected stations. Freeze transformations, train-only standardization, lag choices, and the data vintage before final evaluation. Every outcome must retain its count/rate/positivity identity.

## Main comparisons and required checks

- Compare non-climate calendar forcing, simple climate regressions, penalized smooths, and a small shared neural climate response under the same observation/susceptibility assumptions. Apply comparable tuning budgets and evaluate complete epidemic simulations, not only one-step fits.
- Assess predictive log score and calibration, peak/onset timing, seasonal center of gravity, epidemic size when scale is identifiable, and warm-season fraction with a season definition fixed per hemisphere/location. Retain annual and semiannual summaries to avoid reducing all seasonality to one peak.
- Challenge the humid branch with precipitation and temperature-only/humidity-only alternatives; challenge apparent curve complexity with altered generation intervals, immunity duration, importation, surveillance epochs, and restricted residual forcing.
- Show whether shared versus country-deviating responses change held-out performance, and distinguish uncertainty outside climate support from evidence of no climate effect. Check observation residuals, state positivity/mass balance, optimizer convergence, and finite-difference gradients.
- Estimate supported response features across bootstrap refits. Climate/mixing swaps must be run from explicit comparable histories or re-equilibrated states; distinguish immediate weather substitution from a long-run dynamical scenario. Report how incidence timing differs from the timing of transmission potential.

## Decision gates and minimum publishable outcome

**Data gate:** if UK observations do not support incidence/susceptibility inference, narrow the primary mechanistic analysis to Japan and state the limit of the UK comparison. **Recovery gate:** if simulated data with actual weather cannot distinguish temperature from humidity, or climate shape from reporting/immunity, reduce the estimand to a supported joint climate index or predictive comparison. **Complexity gate:** retain the neural model only if its added flexibility is justified by recovery and held-out performance; an interpretable spline may be the better result.

A credible first outcome is a reproducible joint renewal/climate comparison with uncertainty and explicit limits on curve identification. Evidence for multiple supported transmission opportunities would strengthen it; evidence that the available observations cannot identify a unique curve is also a substantive result. Global climate-change projections, full age-structured vaccine policy analysis, and unrestricted pathogen-interaction models are outside this first phase.

## Immediate next actions

- **Will:** audit the focal paper's observation model and obtain a small England DataMart export with counts, tested denominators, age definition, geography, and historical availability; an enquiry to UKHSA would be a next project action, not an action already taken here.
- **Torkel:** prototype a common `climate_response(parameters, weather)` interface and a differentiable daily renewal simulator on synthetic weather, then benchmark gradient methods on a short trajectory.
- **Joint:** agree the causal target, replication window, climate representation, observation-scale constraints, and recovery criteria before fitting a neural model to real outcomes.
