# Tentative modelling methodology

Working proposal, 18 November 2026. Read alongside the [literature review](literature-review.md), [data audit](data-sources.md), and [analysis plan](analysis-plan.md). Equations and design choices below are proposals, not fitted results.

## Central hypothesis and estimand

The central hypothesis is that **climate-dependent behaviour amplifies transmission**: cold and hot/humid conditions can change indoor time, crowding, ventilation, heating, and air-conditioning use. These responses may depend on the combination of temperature and humidity and on local adaptation and infrastructure. They are a hypothesized explanation for contrasting epidemic timing, not an established universal behavioural rule.

Estimate the **combined climate-associated multiplier**, including behavioural and direct biological pathways, within a renewal model fitted jointly to at least two countries. Japan and a well-observed winter-seasonal comparator are the minimum initial design; cross-country explanation is a primary aim. Separate this multiplier from susceptibility, non-climatic contact changes, and surveillance. A causal diagram should distinguish climate-mediated behaviour from confounding: adjusting for indoor time in the primary model would remove part of the effect we want to capture ([causal framework](https://doi.org/10.1038/s41559-024-02594-3)).

The neural response alone cannot identify how much of the fitted effect is behavioural versus biological. Independent behaviour measurements can test mediation later; without them, interpret the surface as a combined response consistent or inconsistent with the behavioural hypothesis.

## Daily renewal backbone; weekly observation

For location r and day t, use a normalized generation-interval mass function g and daily infection incidence i:

```math
\Lambda_{r,t}=\sum_{a=1}^{A}g_a i_{r,t-a}+\eta_{r,t},
\qquad \sum_a g_a=1,
```

```math
\mathcal R_{r,t}=\exp\{\alpha_r+f_\theta(T_{r,t},q_{r,t};c_r)+
                         \gamma^\top z_{r,t}+u_{r,t}\},
\qquad E[i_{r,t}]\approx(S_{r,t}/N_r)\mathcal R_{r,t}\Lambda_{r,t}.
```

Here eta is imported infectious pressure in incidence-equivalent units; c describes limited local context; z contains non-climatic calendar/intervention covariates; u is a strongly regularized residual, added only in sensitivity analyses. Climate-mediated contacts belong inside f, not in a covariate adjustment that removes them. R calligraphic is reproduction potential in a fully susceptible population; the effective reproduction number also includes susceptibility. A bounded daily hazard, `S * (1 - exp(-R * Lambda / N))`, is an alternative if the linear approximation would exhaust susceptible individuals.

Track susceptibility within the renewal model using births, recoveries, waning immunity, and population turnover, maintaining nonnegative states and mass balance. Derive infectious prevalence/recoveries consistently from infection-age distributions; do not identify the generation interval with the surveillance interval. Treat prehistory, import pressure, initial immunity, generation interval, and immunity duration as sensitivity parameters with external information. Allow reinfection; extend to first/repeat infection or child/adult strata only if data and recovery experiments justify the additional parameters.

For a count observation stream o in epidemiological week w:

```math
Y_{r,w,o}\sim\operatorname{NegBin}(\mu_{r,w,o},\phi_o),\qquad
\mu_{r,w,o}=\sum_{t\in w}\rho_{r,t,o}\sum_{\ell\ge0}d_{o,\ell}i_{r,t-\ell}.
```

Use the NB2 convention `Var(Y) = mu + mu^2 / phi`. Observation-specific delays d and ascertainment/severity rho separate infections from sentinel consultations, laboratory detections, and admissions. Reporting-site counts can supply coverage offsets where available; constrain remaining ascertainment changes to documented epochs. Sentinel counts do not directly identify population attack rates. If only rounded cases-per-sentinel rates are available, use a suitable rate likelihood and explicit measurement uncertainty, rather than treating the rates as counts.

Positivity needs positive and tested counts with a binomial/beta-binomial observation model and assumptions about selection into testing, including non-RSV illness where relevant. Denominators help quantify testing but do not identify infection attack rates. Use source-specific observation models, including age composition where possible: paediatric sentinel consultations and all-age laboratory detections are not interchangeable. Choose a second country with usable observations before joint empirical fitting; unresolved access should trigger a different comparator, not a single-country primary analysis.

## Climate response and comparators

Fit the same observation and susceptibility backbone with a staged response family:

| Model | Role |
| --- | --- |
| Constant and annual/semiannual harmonic forcing | Non-climate predictive reference; semiannual forcing does not demonstrate a climatic mechanism |
| Linear and quadratic temperature or specific humidity, fitted separately | Simple climate benchmarks |
| Penalized additive smooths, then a low-rank temperature–humidity interaction | Interpretable flexible benchmark |
| Small smooth neural network f(T,q), e.g. 2 inputs → 8 tanh units → 1 output | Main joint climate response, including behavioural pathways; tune complexity using blocked multi-country training folds |

**Represent joint behavioural responses from the outset.** The main network should permit temperature–humidity interactions, tilted response contours, and different cold and hot/humid branches. As a constrained hypothesis comparator, learn a region of lower estimated climate-associated transmission and a response to distance from it. A positive-semidefinite quadratic distance with an off-diagonal term permits correlated temperature–humidity responses. A monotone distance response imposes a trough and equal amplification at equal distance; compare these assumptions with the unrestricted network's potentially asymmetric surface. The fitted region has no identified behavioural meaning without measured mediators. Compare absolute weather with deviations from local seasonal climate, and allow only strongly pooled country shifts in response thresholds/context.

Center f over a fixed training reference distribution to separate it from the global intercept; standardize inputs using training data only. Location intercepts and adaptation shifts can still confound response levels across disconnected climate supports; centering does not replace overlap and within-location contrasts. Retain positivity of transmission through the exponential link. Penalize weights and roughness on the supported domain; let the main network estimate its shape freely, using the constrained comparator to test the trough hypothesis. Compare temperature alone, humidity alone, and their joint surface because collinearity can make partial effects unidentifiable. Relative humidity is a sensitivity alternative to specific humidity, not a third independent humidity input.

Include precipitation as a rival/additional behavioural or biological driver of the humid branch ([Baker et al.](https://doi.org/10.1038/s41467-019-13562-y)). Derive humidity before spatial/temporal averaging. Evaluate climate responses daily before summing observations into weeks. For large US regions, compare population-weighted local response values with the response to regional mean weather; these differ under nonlinearity and imply different mixing approximations. Compare contemporaneous weather with a short prespecified lag kernel; keep infection-to-observation delays separate from climate lags. Use within-location weather anomalies to check associations driven only by shared annual phase.

Allow location intercepts first; compare the shared response with prespecified, shrinkage-regularized island/region and country deviations. Within-Japan heterogeneity, including Hokkaido and Ryukyu, already motivates this check. Avoid a separate unconstrained network per location. Flexible calendar forcing, annual ascertainment, latent immunity, and a free time-varying residual can each absorb the same signal: introduce them separately and report which features cease to be identifiable.

## Julia implementation and joint inference

Use a single differentiable daily renewal implementation with interchangeable climate-response functions. Will leads renewal dynamics and the observation model; Torkel leads the neural component, automatic differentiation, and optimization. Both share responsibility for the behavioural assumptions and multi-country interpretation.

Proposed tools: CSV/DataFrames for tables, NCDatasets for climate, Lux/ComponentArrays for explicit neural parameters, and an optimization/automatic-differentiation combination tested on the renewal recursion. These are candidates, not dependencies installed in the skeleton; [Lux documentation](https://lux.csail.mit.edu/stable/) describes explicit parameter/state handling. Pin a tested environment when implementing it. Check gradients against finite differences on a short trajectory.

## Inference, identifiability, and interpretation

Begin with a joint penalized likelihood/MAP fit over the entire incidence trajectory, observation parameters, and climate response. A two-stage estimated-Rt/weather regression is a diagnostic benchmark with propagated uncertainty, not the final estimator. Use multiple starts; inspect ridges in baseline, ascertainment, and initial immunity. First fit deterministic expected incidence with observation noise; add a latent process model only if needed and computationally supportable.

Before empirical interpretation, simulate the actual locations' weather under null, monotone, U-shaped, and interacting climate mechanisms, including wrong immunity, changing testing, rainfall effects, and contact shifts. Measure recovery of function values and supported curve features, rather than individual neural weights. For flexible models, use block/parametric bootstrap refitting and independent initialization; an optimization ensemble alone is not a confidence interval. Use posterior sampling for manageable parametric benchmarks if feasible.

Fit the initial two-country panel jointly and evaluate held-out contiguous years and regions in both countries. Also test leave-country-out transfer in both directions. Separate transfer with no target epidemic calibration from transfer allowing a target intercept/observation calibration; neither may tune the shared curve on held-out outcomes. Use predictive log scores, interval coverage, timing, and epidemic size where scale is identifiable. Reserve COVID-era and later surveillance/prevention epochs for separate perturbation tests. Additional countries can strengthen climate overlap and test adaptation once this joint design works.

Report climate-support maps and uncertainty on the sampled trajectories. Elevated low/high ends of a U-shaped one-dimensional curve are not evidence of two interior local maxima. Two annual transmission peaks along a country's climate trajectory are also different from two incidence peaks: depletion and mixing can suppress or shift outbreaks. Assess extrema only within supported climate ranges; use counterfactual climate/mixing swaps with explicit extrapolation flags and label these as model-based scenarios. If different climate surfaces fit equally well, report the non-identifiability rather than selecting an attractive double peak.
