# Tentative modelling methodology

Working proposal, 18 November 2026. Read alongside the [literature review](literature-review.md), [data audit](data-sources.md), and [analysis plan](analysis-plan.md). Equations and design choices below are proposals, not fitted results.

## Question and estimand

Estimate a climate-associated multiplier of transmission, shared initially across locations, while distinguishing it from susceptibility, contacts, and surveillance. Test whether this relationship improves prediction across years and countries and permits winter and summer transmission opportunities. A causal biological effect is a stronger claim than these observational data alone support: weather may also act through behaviour. Specify a causal diagram before deciding whether to adjust for childcare, indoor time, or other potential mediators ([Barrero Guevara et al.](https://doi.org/10.1038/s41559-024-02594-3)).

The starting paper already links a quadratic climate response and changing mixing to Japan's seasonal shift ([Park et al.](https://doi.org/10.1038/s41467-025-66184-y)). The proposed contribution is joint inference of a flexible response within transmission dynamics, with explicit recovery tests and external validation; neither a neural network nor a U-shaped curve alone establishes novelty.

## Daily renewal backbone; weekly observation

For location r and day t, use a normalized generation-interval mass function g and daily infection incidence i:

```math
\Lambda_{r,t}=\sum_{a=1}^{A}g_a i_{r,t-a}+\eta_{r,t},
\qquad \sum_a g_a=1,
```

```math
\mathcal R_{r,t}=\exp\{\alpha_r+f_\theta(T_{r,t},q_{r,t})+
                         \gamma^\top z_{r,t}+u_{r,t}\},
\qquad E[i_{r,t}]\approx(S_{r,t}/N_r)\mathcal R_{r,t}\Lambda_{r,t}.
```

Here eta is imported infectious pressure in incidence-equivalent units; z contains specified contact/intervention covariates; u is a strongly regularized residual, added only in sensitivity analyses. R calligraphic is the reproduction potential in a fully susceptible population under current contacts and climate; it is not an ODE beta rate. The effective reproduction number also includes susceptibility. A bounded daily hazard, `S * (1 - exp(-R * Lambda / N))`, is an alternative when the linear approximation would deplete more susceptibles than exist.

Model susceptibility explicitly with births, recoveries, waning immunity, and population turnover, maintaining nonnegative states and mass balance. Use an SIRS renewal formulation initially, with infectious prevalence/recoveries derived consistently from infection-age distributions. Do not identify the generation interval with the surveillance interval. Treat prehistory, import pressure, initial immunity, generation interval, and immunity duration as sensitivity parameters with external information. RSV reinfection makes a lifelong-immunity TSIR assumption a benchmark, not the default. Extend to first/repeat infection or child/adult strata only if data and recovery experiments justify the additional parameters.

For a count observation stream o in epidemiological week w:

```math
Y_{r,w,o}\sim\operatorname{NegBin}(\mu_{r,w,o},\phi_o),\qquad
\mu_{r,w,o}=\sum_{t\in w}\rho_{r,t,o}\sum_{\ell\ge0}d_{o,\ell}i_{r,t-\ell}.
```

Use the NB2 convention `Var(Y) = mu + mu^2 / phi`. Observation-specific delays d and ascertainment/severity rho separate infections from sentinel consultations, laboratory detections, and admissions. Reporting-site counts can supply coverage offsets where available; constrain remaining ascertainment changes to documented epochs. Sentinel counts do not directly identify population attack rates. If only rounded cases-per-sentinel rates are available, use a suitable rate likelihood and explicit measurement uncertainty, rather than treating the rates as counts.

Positivity needs positive and tested counts with a binomial/beta-binomial observation model and a model for selection into testing, including non-RSV illness where relevant. A percent-positivity curve alone cannot calibrate population infections or susceptible depletion. England's historical numerator/denominator availability is therefore a feasibility gate, not an assumed input. Start Japan-led if that gate fails.

## Climate response and comparators

Fit the same observation and susceptibility backbone with a staged response family:

| Model | Role |
| --- | --- |
| Constant and annual/semiannual harmonic forcing | Non-climate predictive reference; semiannual forcing does not demonstrate a climatic mechanism |
| Linear and quadratic temperature or specific humidity, fitted separately | Reproduce simple published relationships |
| Penalized additive smooths, then a low-rank temperature–humidity interaction | Interpretable flexible benchmark |
| Small smooth neural network f(T,q), e.g. 2 inputs → 8 tanh units → 1 output | Proposed shared climate response; tune complexity using blocked training folds |

Center f over a fixed training reference distribution to separate it from the global intercept; standardize inputs using training data only. Location intercepts can still confound response levels across disconnected climate supports; centering does not replace overlap and within-location contrasts. Retain positivity of transmission through the exponential link. Penalize weights and roughness on the supported climate domain; do not impose two peaks, a trough, or independent temperature/humidity effects. Compare temperature alone, humidity alone, and their joint surface because collinearity can make partial effects unidentifiable. Relative humidity is a sensitivity alternative to specific humidity, not a third independent humidity input.

Include precipitation as a prespecified rival explanation for the humid branch: [Baker et al.](https://doi.org/10.1038/s41467-019-13562-y) motivates this check. Derive humidity before spatial/temporal averaging. Evaluate climate responses daily before summing predicted observations into weeks, rather than evaluating a nonlinear response only at weekly mean weather. Compare contemporaneous weather with a short prespecified lag kernel; keep infection-to-observation delays separate from climate lags. Use within-location weather anomalies as an additional check on associations driven only by shared annual phase.

Allow location intercepts first; compare the shared response with prespecified, shrinkage-regularized island/region and country deviations. Within-Japan heterogeneity, including Hokkaido and Ryukyu, already motivates this check. Avoid a separate unconstrained network per location. Flexible calendar forcing, annual ascertainment, latent immunity, and a free time-varying residual can each absorb the same signal: introduce them separately and report which features cease to be identifiable.

## Connecting renewal models to UDEs in Julia

The neural renewal model is a hybrid mechanistic model with memory; it need not be relabelled as an ordinary differential equation. Torkel can implement a matched continuous-time SIRS/SEIRS UDE with the same climate network. Choose latent/infectious stages and stage-specific infectiousness to match the induced generation kernel (infectiousness at infection age times survival in infection), not simply the infectious-duration distribution. Match integrated infectivity/reproduction normalization, susceptibility assumptions, and observation aggregation before comparing engines. This checks robustness to the backbone rather than requiring both engines in the first analysis. The general mechanistic/neural approach follows [Rackauckas et al.](https://arxiv.org/abs/2001.04385).

Proposed tools: CSV/DataFrames for tabular data, NCDatasets for climate, Lux/ComponentArrays for explicit network parameters, Optimization for fitting, and OrdinaryDiffEq/SciMLSensitivity for the continuous-time branch. These are candidates, not dependencies installed in the skeleton; the [official SciML example](https://docs.sciml.ai/Overview/stable/showcase/missing_physics/) demonstrates this combination. Add and pin a tested environment when implementing it. Check gradients against finite differences on a small problem before large fits.

## Inference, identifiability, and interpretation

Begin with a joint penalized likelihood/MAP fit over the entire incidence trajectory, observation parameters, and climate response. A two-stage estimated-Rt/weather regression is a diagnostic benchmark with propagated uncertainty, not the final estimator. Use multiple starts; inspect ridges in baseline, ascertainment, and initial immunity. First fit deterministic expected incidence with observation noise; add a latent process model only if needed and computationally supportable.

Before empirical interpretation, simulate the actual locations' weather under null, monotone, U-shaped, and interacting climate mechanisms, including wrong immunity, changing testing, rainfall effects, and contact shifts. Measure recovery of function values and supported curve features, rather than individual neural weights. For flexible models, use block/parametric bootstrap refitting and independent initialization; an optimization ensemble alone is not a confidence interval. Use posterior sampling for manageable parametric benchmarks if feasible.

Evaluate held-out contiguous years, regions, and Japan→England transfer using predictive log scores, interval coverage, timing, and epidemic size. Separate transfer with no target epidemic calibration from transfer allowing a target intercept/observation calibration; neither may tune the shared curve on held-out outcomes. Fit 2020–2024 as a separate perturbation test and isolate later surveillance/prevention epochs.

Report climate-support maps and uncertainty on the sampled trajectories. Elevated low/high ends of a U-shaped one-dimensional curve are not evidence of two interior local maxima. Two annual transmission peaks along a country's climate trajectory are also different from two incidence peaks: depletion and mixing can suppress or shift outbreaks. Assess extrema only within supported climate ranges; use counterfactual climate/mixing swaps with explicit extrapolation flags and label these as model-based scenarios. If different climate surfaces fit equally well, report the non-identifiability rather than selecting an attractive double peak.
