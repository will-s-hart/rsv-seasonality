# UDE types considered for integrating several datasets

Working note, 21 November 2026. Read alongside the [modelling methodology](modelling-methodology.md); [introduction-to-udes.pdf](introduction-to-udes.pdf) introduces the general approach of fitting unknown functions with universal function approximators.

## Setting

We have $N$ datasets, indexed by $r = 1, \ldots, N$ (countries, Japanese prefectures, or US HHS regions). Each has its own surveillance data and its own environmental time series, $\boldsymbol{E}_{r,t}$, which is either temperature alone, $\boldsymbol{E}_{r,t} = T_{r,t}$, or temperature and specific humidity, $\boldsymbol{E}_{r,t} = (T_{r,t}, q_{r,t})$. The unknown function maps the environment to transmission. Leaving out the other terms of the renewal model (susceptibility, intercepts, calendar covariates), dataset $r$ has the reproduction potential

$$
\mathcal{R}_{r,t} = f_r(\boldsymbol{E}_{r,t}),
$$

and the question is how the functions $f_1, \ldots, f_N$ relate to each other. Each is fitted as a neural network, $U(\,\cdot\,;\boldsymbol{\theta})$, with a positive output (e.g. through an exponential link, as in the methodology note). The three options below differ only in what is shared across datasets.

## Option 1: one shared function

All datasets use the same function, $f_r = f$ for every $r$, fitted as one network $U(\boldsymbol{E};\boldsymbol{\theta})$ to all data jointly.

- Every dataset informs the same function, so this uses the data most efficiently. Datasets with different climates also cover different parts of the function's domain, and the shared function joins these into one curve (or surface).
- It predicts directly for a new location, given only its weather.
- It assumes the climate response is the same everywhere. Real differences (local adaptation, housing, heating and cooling use) are either absorbed by other dataset-specific parameters, such as the location intercepts $\alpha_r$ of the methodology note, or appear as misfit.

With location intercepts, $\mathcal{R}_{r,t} = \exp\{\alpha_r + U(\boldsymbol{E}_{r,t};\boldsymbol{\theta})\}$, the datasets share the shape of the response but not its level. This is the methodology note's current main model.

## Option 2: one function per dataset

Each dataset has its own network, $f_r = U(\,\cdot\,;\boldsymbol{\theta}_r)$, with separate parameters $\boldsymbol{\theta}_1, \ldots, \boldsymbol{\theta}_N$.

- This is the most flexible option and assumes nothing about how the responses are related.
- It has $N$ times as many network parameters, and each network is fitted to one dataset only, so each is less well determined, and overfitting is more likely.
- Each $f_r$ is learnt only over the climate range that location experiences. Two locations with little climate overlap give two functions that cannot be compared where it matters, and neither says anything about the other's climate.
- It cannot predict for a new location, and it tests the hypothesis of a common climate response only indirectly (by comparing fitted curves afterwards).

It is a useful reference with a few large datasets (e.g. one per country), but not with many small ones. The methodology note also advises against a separate unconstrained network per location.

## Option 3: conditional UDEs

The network takes two kinds of input: the environmental variables, and a condition variable, $c_r$, which is a free scalar parameter for each dataset:

$$
f_r(\boldsymbol{E}) = U(\boldsymbol{E}, c_r;\boldsymbol{\theta}).
$$

The network parameters $\boldsymbol{\theta}$ are shared and fitted to all data, and $c_1, \ldots, c_N$ are fitted alongside them. Each dataset gets its own function, but all the functions belong to one family, traced out as $c$ varies, so they share structure without being identical.

### Does this make sense?

Yes, I think it is a sensible approach, and probably the most promising of the three for this project. It is the standard way in machine learning to learn a family of related functions: a shared network takes a small, per-task "context" input that is fitted for each task. Examples are CAVIA ([Zintgraf et al., 2019](https://arxiv.org/abs/1810.03642)), which fits a few context parameters per task as extra network inputs, and CoDA ([Kirchmeyer et al., 2022](https://arxiv.org/abs/2202.01889)), which conditions learnt dynamical systems on a context vector per environment, fitted jointly with the shared parameters. In statistical terms, the $c_r$ play the part of random effects in a mixed-effects model.

It also sits naturally between the other two options. Fixing every $c_r$ to the same value gives option 1. Option 1 with location intercepts is the simplest conditional UDE, with $c_r = \alpha_r$ only able to scale the response up or down. A full conditional network lets $c_r$ change the shape of the response too.

### Points to watch

- **The amount of structure depends on $N$.** All $N$ functions must lie in a one-parameter family. With only two datasets this is hardly a constraint: a network with enough nodes can produce any two functions at $c = 0$ and $c = 1$, so option 3 then behaves much like option 2, restrained only by the network's size and regularisation. The constraint becomes real when there are many datasets, as with Japanese prefectures and US regions fitted jointly.
- **The values of $c_r$ have no meaning on their own.** The network can absorb any rescaling or other increasing transformation of $c$, so only the resulting functions can be interpreted. Fix $c$ for one reference dataset at 0, and keep the rest on a fixed scale with a penalty (e.g. on $\sum_r c_r^2$) or a bounded range. Once fitted, whether $c_r$ correlates with known location properties (mean temperature, latitude, housing) is a useful check.
- **$c_r$ can absorb any difference between datasets.** Like the intercepts, but more flexibly, it can take up differences in reporting, ascertainment or immunity and present them as differences in climate response. The synthetic recovery experiments in the analysis plan should include this case: data generated with one shared response but different observation processes, to check whether option 3 then invents differences.
- **A new location needs only $c$.** Transfer then means fitting one scalar (and an intercept) to the target data, which fits the analysis plan's "transfer allowing calibration" test. Without target data, $c$ must be guessed, e.g. from similar locations.
- **One condition variable to start with.** A vector $\boldsymbol{c}_r$ allows more variation between datasets but constrains them less. A scalar is the natural first choice.

### Structured variants

The condition variable can also enter in a fixed way, which constrains the family more and makes $c_r$ interpretable:

- **A shift**, $f_r(T) = U(T - c_r;\boldsymbol{\theta})$: the whole response, including both temperature peaks, is moved by $c_r$ degrees. This expresses local adaptation (a location used to cold winters responds to colder temperatures than one used to mild ones) and is close to the methodology note's "modest adaptation shifts".
- **A known covariate in place of a free parameter**: $c_r$ is set to a measured location property, such as mean annual temperature or a housing index, which corresponds to the context input $c_r$ of the methodology note. This predicts for new locations without target data, but only if the right covariate is chosen.
- **A shared function plus a penalised deviation**, $f_r = U(\,\cdot\,;\boldsymbol{\theta}) + U(\,\cdot\,;\boldsymbol{\theta}_r)$, with a penalty that keeps each deviation small. This is the approach of LEADS ([Yin et al., 2021](https://arxiv.org/abs/2106.04546)) and of the methodology note's "shrinkage-regularized deviations". It is an alternative to option 3 rather than a form of it: the deviations need not form a family.

## Several environmental variables

All three options apply unchanged to functions of several environmental variables, $\boldsymbol{E} = (T, q)$, or with precipitation added. In option 3 the network then has one more input than the number of environmental variables. Two points differ from the single-variable case:

- Within one location, temperature and humidity move together through the year, so each dataset covers only a narrow band of the $(T, q)$ plane. The surface is learnt only near these bands, and the methodology note's support maps are needed to show where. Locations with different climates cover different bands, which favours options 1 and 3 over option 2: a shared or conditional surface combines the bands, while separate surfaces stay confined to them.
- More inputs need more data to learn the same level of detail. With two inputs, the comparison of temperature alone, humidity alone and the joint surface in the methodology note matters even more, since collinearity can make the separate effects unidentifiable.

The two-peak hypothesis may in fact need humidity: a high-temperature peak could be a hot and humid peak, which a function of temperature alone would show only where temperature and humidity are strongly correlated.

## Summary

| Option | Network parameters | Shared across datasets | New location | Main risk |
| --- | --- | --- | --- | --- |
| 1. Shared function | one set | the whole response (with intercepts: its shape) | weather only | real differences absorbed elsewhere |
| 2. One function per dataset | $N$ sets | nothing | not possible | overfitting; functions confined to each location's climate |
| 3. Conditional UDE | one set, plus $c_1, \ldots, c_N$ | a one-parameter family | fit $c$ | little constraint when $N$ is small; $c_r$ absorbs observation differences |

A natural order is to fit option 1 (with intercepts) first, option 3 as the main extension, with the shift variant as its interpretable form, and option 2 only as a reference at the country level.
