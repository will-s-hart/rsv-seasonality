# Japan and US ERA5 provenance handoff

28 November 2026 · Issue #22 · Source commit `010ddf42ac05e902fd8cfab49d19d8ef0be930cd`

Will asked where to find the ERA5 inventory for Japan and the US. The country-by-country gap table is on `main`. The input manifest marks climate as missing. For neither country does it identify an acquired release, confirm the variables and units from a file, give the first and last hourly timestamps, or record a verified SHA-256 digest. [Country gap table](../notes/data-sources.md#era5-inventory-gap-check-27-november-2026) · [Input manifest](../data/analysis-inputs.toml)

Both countries plan to use ERA5 hourly data on single levels for the 2013–2019 surveillance years, with 2 m air temperature and 2 m dewpoint temperature in K and surface pressure in Pa. Precipitation remains undecided. The first local observation week starts on 31 December 2012 in Japan and 30 December 2012 in the US, so a January 2013 start would leave both first weeks incomplete. [Climate source notes](../notes/data-sources.md#era5-inventory-gap-check-27-november-2026)

Torkel’s next action is to locate any existing files and verify each country’s release, native variable names and units, hourly coverage and SHA-256 digests against those files. If neither acquisition exists, obtain a documented pilot for each country. Will and Torkel still need to agree the UTC hours required for local weeks and any earlier lag period. [Analysis plan](../notes/analysis-plan.md#decision-gates-and-immediate-actions)

## Publication record

Starting commit `010ddf42ac05e902fd8cfab49d19d8ef0be930cd`.

Documentation/data-only change. Public-path, text, and Git whitespace checks passed.

- Added `Reports/2026-11-28_torkel_codex.md`
