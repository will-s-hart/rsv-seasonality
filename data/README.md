# Data conventions

Keep downloaded source files under `data/raw/` and derived tables under `data/processed/`. These directories are ignored by Git; create them when acquiring data. Never overwrite a source file with transformed data.

Record each acquisition in a provenance manifest, including source URL, dataset/version, download timestamp, licence/attribution, file checksum, spatial unit, coverage dates, time zone, calendar/week convention, variable units, and transformation script. Commit the manifest only after checking that its contents are suitable for this public repository.

Suggested epidemiology fields: `location_id`, `period_start`, `period_end`, `outcome_type`, `age_group`, `value`, `tests`, `sentinel_count`, `population`, `source_version`, and `quality_flag`. Preserve unavailable denominators as missing, never zero. Store raw counts, rates per sentinel, positivity, and hospital admissions as distinct outcome types. Do not reconstruct counts from rounded rates without validated denominators.

Suggested daily climate fields: `location_id`, `date`, `temperature_c`, `dewpoint_c`, `surface_pressure_pa`, `specific_humidity_g_kg`, `relative_humidity_pct`, and `precipitation_mm`. Derive humidity at the native temporal resolution before aggregation and record spatial weights. Use source-defined epidemiological weeks when aggregating observations.

See [data sources](../notes/data-sources.md) for access routes, limitations, and the initial feasibility gate. No data files are bundled in the skeleton.

See [annual demographic sources, 2013–2019](../notes/demographic-sources-2013-2019.md) for the source contract, staging commands, US state/DC build, and remaining official-file checks.
