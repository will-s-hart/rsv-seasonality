# Tentative analysis plan and responsibilities

Working plan, 18 November 2026. Will leads renewal modelling and epidemiological inference; Torkel leads the neural climate component, differentiation, and optimization. Both develop the behavioural hypothesis and multi-country interpretation. See [literature](literature-review.md), [data sources](data-sources.md), and [methodology](modelling-methodology.md).

## Scientific aim and initial country pair

The initial study will fit **Japan and the United States jointly**, using a renewal model with a neural climate component. The main aim is to explain contrasting seasonal transmission across countries, with climate-dependent behaviour as a central hypothesis: conditions that alter indoor time, crowding, ventilation, or heating/cooling use may amplify transmission at both cold and hot/humid ends of the climate range. Model the joint temperature–humidity response and allow limited local adaptation, without declaring a universal behavioural threshold.

The US is the leading winter-seasonal comparator because the [official historical NREVSS dataset](https://data.cdc.gov/Laboratory-Surveillance/Respiratory-Syncytial-Virus-Laboratory-Data-NREVSS/52kb-ccu2/about_data) provides weekly positives and tested counts by diagnostic method across ten HHS regions, July 2010–June 2020. [CDC describes predominantly winter peaks in most US regions](https://www.cdc.gov/rsv/php/surveillance/index.html), with important geographical exceptions. The data audit verified this file's accessibility and overlap with Japan; it has not established that laboratory sampling can identify population attack rates.

The first panel should include diverse Japanese prefectures and winter-dominant US HHS regions (provisionally 1, 2, and 5), selected on geography and surveillance quality before model comparison. Broader US regions can subsequently add climate contrast. Canada is the strongest alternative under further archive audit; the UK is optional. If a candidate's observation process proves unusable, replace it before joint empirical fitting and maintain at least two countries in the primary analysis.

## Stages, deliverables, and ownership

Indicative effort is active working weeks, with overlap and no calendar deadlines; access delays and compute costs remain uncertain.

| Stage | Deliverable and completion criterion | Will | Torkel | Effort |
| --- | --- | --- | --- | --- |
| 0. Define hypotheses and observations | Causal diagram distinguishing climate-mediated behaviour, direct biological effects, immunity, calendars, and testing; country/region selection and observation assumptions recorded | Lead epidemiological definitions, age/catchment comparability, external information on immunity | Lead candidate joint climate surfaces and adaptation parameterization | 1–2 weeks |
| 1. Build a two-country panel | Official Japan and US inputs, provenance/checksums, denominator/missingness report, climate-support maps, and surveillance change log; usable observations from both countries | Lead epidemiology acquisition, population/births, and source-specific observation models | Lead ERA5 ingestion, humidity derivation, spatial aggregation, and Julia pipeline | 2–3 weeks |
| 2. Build one renewal implementation | Differentiable simulator and likelihood, with simple, spline, and neural climate responses sharing identical dynamics and observation interfaces | Lead renewal dynamics, susceptibility bookkeeping, delays, and likelihood | Lead neural interface, gradient checks, training, and regularization | 2–3 weeks |
| 3. Test recovery and behavioural structures | Synthetic experiments using both countries' weather quantify recovery, false extra peaks, and observation/immunity confounding; freeze complexity/tuning rules | Lead epidemiological and reporting misspecification scenarios | Lead joint-interaction and behaviour-informed neural structures, repeated fits, and recovery diagnostics | 2–3 weeks |
| 4. Joint fitting and validation | Joint Japan–US fit, held-out years/regions in both countries, and leave-country-out transfer in both directions | Lead validation design, epidemiological diagnostics, and calibrated uncertainty | Lead fitting, tuning within training folds, compute, and reproducibility | 3–4 weeks |
| 5. Explain contrasts and assess expansion | Supported climate surfaces, annual climate trajectories, transmission/incidence timing, and climate/context scenarios; ranked next-country options | Lead behavioural interpretation and susceptibility/contact scenarios | Lead interaction/adaptation diagnostics and response visualization | 2–3 weeks |
| 6. Synthesize | Reproducible figures, limitations, sensitivity appendix, manuscript outline, and public analysis release | Lead epidemiological and renewal methods narrative | Lead neural and numerical methods narrative | 1–2 weeks |

Both review each other's core acquisition/model code. Meet weekly around one diagnostic or figure and record decisions in these notes or short linked decision files. The deliverable is one neural renewal model, with interchangeable response functions for hypothesis testing.

## Initial data and held-out design

1. **Common baseline window:** target 2013–2019 Japan prefecture-week surveillance and US HHS-region-week NREVSS, paired with ERA5 temperature, dewpoint, pressure, and precipitation. Acquire Japan from official IDWR archives. Keep US PCR and antigen series separate; begin with PCR after checking reporting completeness. Harmonize local week definitions and outcome delays without relabelling either stream as population incidence.
2. **Provisional joint splits:** train on 2013–2016 in both countries, tune on 2017, and hold 2018–2019 for final temporal evaluation. Reserve geographical folds before tuning and use prior history for state initialization without fitting to held-out outcomes. For a separate Japan 2016/17 timing-shift test, train through 2015 and freeze choices without post-2015 outcomes.
3. **Cross-country tests:** compare joint fitting with Japan-only and US-only training, evaluating transfer to the held-out country in both directions. Report separately transfer without target outcomes and transfer allowing prespecified baseline/observation calibration. Each test must keep the shared climate function fixed with respect to its held-out outcomes.
4. **Behaviour and local context:** compile school/childcare calendars, housing/heating/cooling information, and any suitable time-use/contact data. Weather-mediated behaviours are part of the target response, so do not regress them away as routine confounders. Use independent measurements to challenge the proposed pathway where feasible; sparse context data should support modest pooled modifiers, not unconstrained country functions.
5. **Later countries and epochs:** rank Canada and other well-observed countries by historical coverage, observation quality, climate overlap/contrast, and measured behavioural context. Add countries through the same data/model interfaces. Pandemic years and later prevention/surveillance regimes are separate tests requiring additional inputs; the verified historical US file ends in June 2020.

Freeze climate transformations, train-only scaling, lag choices, input vintages, outcome likelihoods, and tuning budgets before final evaluation. Large US regions require a spatial-aggregation sensitivity check: average local climate response values versus responding to region-average weather, with explicit assumptions about mixing.

### Annual demographics

The [2013–2019 source contract and workflow](demographic-sources-2013-2019.md) covers resident totals and ages 0–4. The US states/DC build is verified with synthetic fixtures. The Cloud environment blocks official downloads. Will's next step is to acquire the official files, run the US controls, and verify the Japan and Puerto Rico file layouts and counts before pinning the inputs. Natality remains a separate source audit.

## Comparisons and interpretation

- Compare simple climate curves and splines against the main joint neural response and a behaviour-informed response with a learned low-amplification region. Include a calendar-forcing reference within the same renewal backbone. Test temperature–humidity interactions and modest adaptation shifts; do not require a double peak in every country.
- Evaluate predictive log scores, interval coverage, onset/peak timing, seasonal center of gravity, and warm-season fraction in both countries. Compare epidemic size only where its scale is identifiable. Report gains or failures by country, rather than allowing a much larger surveillance dataset to hide failure in the other; retain genuine likelihood weights and add country-balanced evaluation summaries.
- Challenge the response with rainfall, weather anomalies, generation intervals, waning immunity, importation, age composition, testing epochs, and limited residual forcing. Distinguish a weather→behaviour pathway from calendar-driven contact changes and from direct biological effects; surveillance alone will not fully separate the first and last.
- Use bootstrap refitting and simulation recovery to assess supported surface features. For climate/context swaps, specify epidemic history and whether the scenario changes weather immediately or re-equilibrates the system. Report climate-support/extrapolation flags. Transmission opportunities and incidence peaks need not coincide.

## Decision gates and immediate actions

**Two-country data gate:** usable, interpretable streams from both Japan and a winter-seasonal comparator before substantive empirical claims; replace the comparator if needed. **Recovery gate:** if weather support cannot distinguish marginal temperature/humidity effects, report a supported joint response rather than force separate effects. **Behaviour gate:** describe evidence as consistent with a behavioural pathway unless independent data identify mediation. **Complexity gate:** justify extra neural/context parameters using recovery and held-out performance.

A first substantive result should explain what a shared or partially pooled climate response can account for across the initial two countries, how behavioural interpretations stand up to alternatives, and which features remain uncertain. Further countries strengthen this aim without being prerequisites for the first analysis.

- **Will:** audit official Japan IDWR and US NREVSS definitions, reporting changes, age composition, and the minimum observation assumptions needed for joint inference.
- **Torkel:** prototype `climate_response(parameters, weather, context)` and the differentiable daily renewal recursion; compare an unrestricted joint response with one small behaviour-informed architecture on synthetic two-country data.
- **Joint:** fix the first regions, behavioural hypotheses, baseline period, held-out design, and recovery criteria before fitting real outcomes.
