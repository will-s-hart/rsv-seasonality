# RSV seasonality

Research project with Will and Torkel Loman on the relationship between climate and respiratory syncytial virus (RSV) transmission, combining renewal equation models with neural climate response functions in Julia.

The initial comparison is Japan and England, with other UK nations included when compatible surveillance data are available. We will test whether a shared climate response can explain different epidemic timing after accounting for susceptibility, mixing, and observation processes. Multiple transmission peaks are a hypothesis to evaluate, rather than a constraint to impose.

## Planning notes

- [Literature review](notes/literature-review.md)
- [Data sources and feasibility](notes/data-sources.md)
- [Tentative modelling methodology](notes/modelling-methodology.md)
- [Analysis plan and Will/Torkel responsibilities](notes/analysis-plan.md)

These are provisional research notes dated 18 November 2026. No empirical models have been fitted and no source datasets have been downloaded into this repository.

## Julia setup

The skeleton targets Julia 1.10 or later and currently has no external dependencies. It has been checked locally on Julia 1.11.2.

```sh
julia --startup-file=no --project=. scripts/check_setup.jl
```

`src/RSVSeasonality.jl` is the package entry point. Add dependencies and substantive modelling code as the design becomes concrete. Commit the generated `Manifest.toml` when establishing the first analysis environment; retain exact versions and random seeds for reported results.

## Layout

| Path | Purpose |
| --- | --- |
| `notes/` | Consolidated evidence, methodological decisions, and analysis plan |
| `src/` | Reusable Julia model, observation, and inference components |
| `scripts/` | Reproducible command-line entry points |
| `data/` | Data conventions and local raw/processed data, excluded from Git |
| `results/` | Local generated figures, tables, and fitted objects, excluded from Git |
| `.github/workflows/` | Julia package-loading smoke check |

For each downloaded dataset, record provenance, access date, source version, licence, units, and a checksum before using it. Data redistribution remains subject to the original provider's terms; the repository licence covers original project material only.
