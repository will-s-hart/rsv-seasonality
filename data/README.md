# Data conventions

Keep downloaded source files under `data/raw/` and derived tables under `data/processed/`. These directories are ignored by Git; create them when acquiring data. Never overwrite a source file with transformed data.

Record each acquisition in a provenance manifest, including source URL, dataset/version, download timestamp, licence/attribution, file checksum, spatial unit, coverage dates, time zone, calendar/week convention, variable units, and transformation script. Commit the manifest only after checking that its contents are suitable for this public repository.

Suggested epidemiology fields: `location_id`, `period_start`, `period_end`, `outcome_type`, `age_group`, `value`, `tests`, `sentinel_count`, `population`, `source_version`, and `quality_flag`. Preserve unavailable denominators as missing, never zero. Store raw counts, rates per sentinel, positivity, and hospital admissions as distinct outcome types. Do not reconstruct counts from rounded rates without validated denominators.

Suggested daily climate fields: `location_id`, `date`, `temperature_c`, `dewpoint_c`, `surface_pressure_pa`, `specific_humidity_g_kg`, `relative_humidity_pct`, and `precipitation_mm`. Derive humidity at the native temporal resolution before aggregation and record spatial weights. Use source-defined epidemiological weeks when aggregating observations.

See [data sources](../notes/data-sources.md) for access routes, limitations, and the initial feasibility gate. No data files are bundled in the skeleton.

See [annual demographic sources, 2013–2019](../notes/demographic-sources-2013-2019.md) for the source contract, staging commands, US state/DC build, and remaining official-file checks.

## Audited analysis inputs, 2013–2019

The [analysis input manifest](analysis-inputs.toml) describes the epidemiological source artifacts already covered by the surveillance, natality and population audits. Print the public coverage, provenance, source filenames and referenced SHA-256 pins without local inputs. The command uses Python 3.11 or later.

```sh
python3 -B scripts/check_analysis_inputs.py inventory
```

On department, put the original artifacts under `data/raw/` using the relative paths reported by `inventory`. Use `--raw-root PATH` for an alternate cache. The pinned NCHS report and supplement PDFs use the basenames of their official URLs. The two WONDER TSVs must match the dated original exports, including their query notes. Population sources use the existing `demography/<source-id>/source` and `manifest.json` pairs.

The US Census national and county population control pins come from the original department audit receipts. Save those two verified hashes under the TOML keys `us-national-control` and `us-county-control` in a private file, such as `data/raw/population-control-pins.toml`. Keep this file and the raw cache outside Git. The auditor compares staged control bytes and receipts with those pins. Will should confirm the original receipt provenance before supplying them.

```sh
python3 -B scripts/check_analysis_inputs.py verify \
  --population-control-pins data/raw/population-control-pins.toml
```

`verify` exits nonzero for missing or unmatched bytes, pins or population receipts. A successful run checks file identity against the expected digests, verifies population receipt source metadata, size, capture time and existing format checks, and reports counts of verified artifacts. It has no writes and does not load outcome rows. The source audits describe the coverage reconciliations and supporting documents. Official verification on department also needs the original WONDER acquisition records and any documented retrieval metadata. The CLI verifies the WONDER TSV bytes against the published pins. Other historical captures, control transcriptions and manual spot checks are audit evidence outside the raw artifact check.

The report keeps analysis readiness false. ERA5 and other climate inputs are missing. The analysis-wide source and date freeze, joint geography and holdout settings remain open. State/DC does not establish full HHS Region 2 coverage. Puerto Rico's annual population has a separate validation, while US Virgin Islands annual population and monthly territorial residence births remain unresolved.
