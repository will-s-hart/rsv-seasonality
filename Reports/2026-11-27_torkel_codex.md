# Japan and US ERA5 provenance gaps

Date: 27 November 2026

Task: answer the public ERA5 inventory request in issue #22.

Source commit: `9ace6eb332cd601d57254ad3faf9757593fbf05d`.

## Result

No acquired Japan or US ERA5 inventory is documented in the supplied snapshot. The [manifest](../data/analysis-inputs.toml) explicitly records `unresolved.climate.status = "missing"` and no locked ERA5 artifacts. The [country gap table](../notes/data-sources.md#era5-inventory-gap-check-27-november-2026) distinguishes planned inputs from verified acquisitions. Stage 1 remains open.

For both countries, the planned source is ERA5 hourly single levels, targeting 2013–2019, with 2 m temperature and dewpoint in K and surface pressure in Pa. Acquired release/version, actual variable metadata, exact timestamp coverage and artifact SHA-256 digests remain undocumented. Precipitation inclusion, native units and accumulation handling require agreement. These are planning specifications, not empirical climate findings.

The manifest's inclusive local observation intervals start on 31 December 2012 for Japan and 30 December 2012 for the US. A January 2013 climate start would omit part of each first observation week. Hourly UTC coverage, local-time handling and any earlier lag/initialisation buffer remain to be frozen.

## Evidence and overlap check

- The [climate source notes](../notes/data-sources.md#climate-same-exposure-pipeline-across-countries) document the candidate catalogue and state that no climate retrieval has been performed.
- The [manifest audit summary](../notes/analysis-plan.md#audited-analysis-input-manifest) separates the epidemiological inventory from missing climate inputs.
- The [latest merged country comparison](../notes/japan-us-annual-reporting-directions-2013-2019.md#interpretation-and-provenance) identifies the same climate provenance dependency.
- The supplied branch list contains no apparent ERA5 inventory branch, and no open pull requests were listed. Only this report is available in the staged `Reports/` directory; earlier reports from other branches were not supplied. Branch contents were not independently inspected, so overlapping work on other branches or outside the snapshot cannot be excluded.

The [README layout](../README.md#layout) links to `Reports/` and explains how to find reports on unmerged `torkel/` branches. The [analysis plan](../notes/analysis-plan.md#decision-gates-and-immediate-actions) records the inventory gaps and next action.

## Blockers and next action

Both countries lack documented acquired release metadata, exact coverage and verified artifact digests in this snapshot. This does not establish whether Torkel holds acquisitions elsewhere.

Torkel should locate any existing acquisitions and supply publishable dataset/release, variables and native units, coverage, retrieval date, licence and SHA-256 digests verified against preserved bytes. Keep original acquisition receipts private. If no acquisitions exist, obtain a documented two-country pilot in the existing project environment. Agree edge-week coverage and precipitation handling with Will, and pin spatial boundaries, weights and Julia transformations before panel assembly. Package installation and updates remain with Torkel.

## Validation scope

Documentation and manifest inspection only. No climate retrieval, empirical analysis, synthetic experiment or Julia/Python execution was performed. The report was rewritten to remove trailing spaces. Validation here is limited to text-level whitespace and evidence-link checks. Git staged-diff validation remains with the runner.

## Publication record

Starting commit `9ace6eb332cd601d57254ad3faf9757593fbf05d`.

Documentation/data-only change. Public-path, text, and Git whitespace checks passed.

- Edited `README.md`
- Added `Reports/2026-11-27_torkel_codex.md`
- Edited `notes/analysis-plan.md`
- Edited `notes/data-sources.md`
