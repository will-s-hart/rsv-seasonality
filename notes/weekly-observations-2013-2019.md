# Weekly RSV observations for Japan and the US, 2013–2019

The export covers 47 Japan NESID prefectures and 10 US NREVSS HHS regions for source week years 2013–2019. Each Japan row is a prefecture and diagnosis week. Each US row is an HHS region, reporting week and diagnostic method. National and annual NESID rows serve as audit controls. [Source audit and download instructions](surveillance-audit-2013-2019.md).

## Generate the CSV

From the repository root, download the 29 official audit inputs to `data/raw/surveillance-audit/`. Use Python 3.9 or later with the audit's `xlrd` and `openpyxl` workbook readers. [Official download commands](surveillance-audit-2013-2019.md#reproduce-the-tabulations).

```sh
mkdir -p data/processed
python -B scripts/export_weekly_observations.py data/raw/surveillance-audit \
    --output data/processed/weekly_observations.csv
```

With `--output`, the command replaces the destination atomically after generation and a successful close. If generation fails, any previous CSV stays in place. The destination must be separate from the audit inputs, and an existing destination must be a regular file. Its read, write and execute permission bits are preserved, and a new output starts with owner-only access. Omit `--output` to write the same CSV to stdout for a pipeline. Shell redirection with `>` truncates its destination before the exporter runs.

The command validates all inputs against the audit SHA-256 manifest and parses the weekly records before writing the CSV. It writes UTF-8 with LF line endings, a single header and empty fields for null values. Row order is Japan by diagnosis week then prefecture code, followed by US PCR then antigen, each by numeric HHS region then reporting week. Keep the output under the Git-ignored `data/processed/` directory. [Audit SHA-256 manifest](../scripts/surveillance_sources.sha256).

```sh
python -B -m unittest discover -s scripts -p 'test_*.py'
python -B scripts/check_surveillance_sources.py data/raw/surveillance-audit
```

## Columns

The row key is `source_id`, `region_id`, `source_week_year`, `source_week_code` and, for the US, `method`. Read IDs and week codes as strings to preserve their formatting.

| Column | Meaning |
| --- | --- |
| `source_id` | `NESID` or `NREVSS:52kb-ccu2` |
| `source_version` | `final_annual_YYYY` for the NESID workbooks or `historical_public_use_2022` for the NREVSS file |
| `source_vintage` | CDC catalogue data update date, `2022-10-21`. The exact snapshot dates of the NESID workbooks are unknown, so their fields are empty. |
| `source_calendar` | `japan_diagnosis` or `cdc_mmwr` |
| `source_week_year` | Year in the source calendar |
| `source_week_code` | NESID case workbook sheet name, e.g. `５３週`, or the four-character NREVSS `repweekcode`, e.g. `1453`. Absent antigen rows use the verified NREVSS code for the same HHS reporting week. |
| `week_start`, `week_end` | Inclusive calendar dates, `YYYY-MM-DD` |
| `region_id`, `region_label` | Japan e-Stat prefecture code `01`–`47` with the bilingual NESID label, or CDC `hhs_region` code `1`–`10` mapped to `HHS Region N` |
| `observation_type`, `method` | `rsv_case_notifications` with an empty method field for NESID, or `rsv_test_detections` with the native NREVSS `PCR` or `Antigen` method |
| `count` | NESID table 8-1 case notifications, both sexes combined, or NREVSS `rsvpos` |
| `denominator_kind`, `denominator` | `paediatric_sentinel_sites` from NESID table 14-1, sheet `小児科定点`, or `reported_tests` from NREVSS `rsvtest`. Values are integers where present. |
| `coverage` | `present` when the source has the weekly observation, including zero-test rows, and `absent` for missing antigen rows on the grid |
| `source_outlier` | Native CDC `outlier` value, `1` for a flagged observation and `0` for an unflagged observation. Empty for NESID and absent antigen rows. |
| `positivity` | NREVSS detections divided by reported tests as a fraction from 0 to 1. Defined for positive test totals, including when detections equal zero. Empty for NESID, zero-test rows and absent rows. |

The NESID denominator is the weekly number of sentinel clinics and hospitals in the paediatric reporting category for that prefecture. It describes the size of the paediatric sentinel network that week. RSV tests and the number of sites that tested for or reported RSV that week are unavailable in these tables. The NREVSS denominator counts reported tests in the specified method and region. Weekly lab participation is unavailable in the export. [JIHS final table archive](https://id-info.jihs.go.jp/surveillance/idwr/annual/2024/archive/index.html), [e-Stat prefecture codes](https://www.e-stat.go.jp/municipalities/cities/areacode), [HHS regional definitions](https://www.hhs.gov/about/agencies/iea/regional-offices/index.html), [CDC field definitions](https://data.cdc.gov/api/views/52kb-ccu2).

CDC's flag identifies extreme weekly counts of tests or detections under its three-standard-deviation rule within method, HHS region and surveillance year. Coverage records row presence independently of that flag. An absent row has empty count, denominator, flag and positivity fields. A present zero-test row retains the source's numeric zeros for detections and tests and its original flag. [CDC field definitions](https://data.cdc.gov/api/views/52kb-ccu2).

## Coverage in the pinned inputs

| Stream | Grid rows | Source-present rows | Absent rows | Zero-test rows | Flagged rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| NESID | 17,155 | 17,155 | 0 | — | — |
| NREVSS PCR | 3,650 | 3,650 | 0 | 0 | 11 |
| NREVSS antigen | 3,650 | 3,569 | 81 | 8 | 33 |
| Total | 24,455 | 24,374 | 81 | 8 | 44 |

All NESID observations have a numeric case count and a positive sentinel count. The antigen gaps comprise three weeks in HHS Region 2 and 78 weeks in Region 8. Four zero-test rows occur in each of Regions 2 and 7. [Audit coverage and dates](surveillance-audit-2013-2019.md#us-historical-nrevss).

For a table by source, method, region and source week year, use the [coverage summary command and provisional reporting QA](weekly-reporting-qa-2013-2019.md).

## Week boundaries and release timing

Japan diagnosis weeks run Monday through Sunday. They use the ISO week convention in this window. US MMWR reporting weeks run Sunday through Saturday, with week 1 containing the first Wednesday of the year. Dates belong to their respective source calendars. [JIHS 2014–2018 calendar](https://id-info.jihs.go.jp/surveillance/idwr/annual/2022/archive/14-18calendar.gif), [CDC MMWR week rules](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/MMWR_Week_overview.pdf), [CDC 2014–2015 calendar](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/W2014-15.pdf), [CDC 2018–2019 calendar](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/W2018-19.pdf).

| Source-labelled week | Inclusive start | Inclusive end |
| --- | --- | --- |
| Japan 2015 W53 (`５３週`) | 2015-12-28 | 2016-01-03 |
| US 2014 W53 (`1453`) | 2014-12-28 | 2015-01-03 |
| Japan 2017 W52 (`５２週`) | 2017-12-25 | 2017-12-31 |
| US 2018 W01 (`1801`) | 2017-12-31 | 2018-01-06 |

The fixtures check that Japan 2017 W52 and US 2018 W01 both include 31 December 2017, their only shared date. The export supports retrospective evaluation only. Establishing what data were available at a given week end requires historical release records. Japan's archived preliminary postings and annual compilation cutoffs document separate events. CDC provides catalogue timestamps for its historical public-use dataset. [Japan release provenance](surveillance-audit-2013-2019.md#japan-release-provenance), [US release provenance](surveillance-audit-2013-2019.md#us-release-provenance).

## Check candidate calendar cutoffs

Run the read-only diagnostic on an existing export or a CSV with the same calendar, row-key and coverage columns. This example uses the calendar dates corresponding to the provisional 2013–2016 training, 2017 tuning and 2018–2019 retrospective holdout years.

```sh
python -B scripts/check_weekly_cutoffs.py data/processed/weekly_observations.csv \
    --window-start 2013-01-01 \
    --train-through 2016-12-31 \
    --tune-through 2017-12-31 \
    --holdout-through 2019-12-31
```

The diagnostic compares `source_week_year` against those provisional label years and checks each complete inclusive observation interval against the supplied dates. Each period end belongs to that period. The following period starts the next day. An interval that ends on its period's last day can be assigned to that period. An interval that starts on that day and extends into the next period crosses the cutoff. With the dates above, Japan 2017 W52 is assigned to tune under both rules. US 2018 W01 has a holdout label and is unassigned under the complete-interval rule because it includes 31 December 2017.

The JSON report counts every input row by source, method, coverage and the two assignments. `affected_rows` lists each differing or strict-unassigned row with its native key, dates, coverage and any crossed cutoffs. A strict assignment of `null` has status `crosses_cutoff` for a row spanning a boundary or `outside_window` for a row wholly outside the supplied window. Coverage remains visible in the report, including absent antigen grid rows. Reported dates describe observation intervals. Period-end availability is unknown from the interval dates and source vintage. A prospective evaluation would require separate historical release records.

The final cutoff policy for the retrospective evaluation is a joint design decision.
