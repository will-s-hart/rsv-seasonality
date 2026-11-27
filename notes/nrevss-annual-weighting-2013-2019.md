# Weighting annual reported PCR positivity in NREVSS, 2013–2019

For each calendar year, the analysis measures how weighting by reported test volume changes the estimated PCR positivity across the ten HHS reporting regions. It separates the contribution of weighting weeks within each region from the contribution of weighting regions by their annual reported test totals. The input is the [SHA-pinned historical CDC aggregate export](surveillance-audit-2013-2019.md#us-historical-nrevss).

## Support and contrasts

Use the calendar year of the Saturday week ending, as in the audit's annual testing totals. Assign the full Sunday–Saturday count to that year, including weeks crossing 1 January. The expected annual grid is all ten regions by every Saturday ending in the year. The study window comprises calendar years 2013–2019. The remainder of the source release lies outside this window.

The baseline includes each source-present PCR row with at least one reported test. A zero detection count on a tested row contributes zero positivity. An absent row or zero-test row supplies no rate. Retain CDC-flagged observations. The pinned loader requires complete tested PCR coverage on the audited grid and fails on a violation. Annual coverage columns count expected cells, absent rows, zero-test rows and eligible rows. The annual calculation uses the available eligible rows, gives each region with at least one eligible row equal weight in A and B, and applies no scaling to partial support. With empty support, the CSV leaves the rates and gaps blank.

Within each year and support, calculate all three rates on the same observations.

| Rate | Calculation |
| --- | --- |
| A | Mean of weekly positivity within each region, then the mean of those regional means |
| B | Sum of detections divided by sum of tests within each region, then the mean of those pooled rates |
| C | Sum of detections divided by sum of tests across all retained regions and weeks |

The total gap `C − A` is the sum of `B − A` and `C − B`. The first component reflects the association between weekly test volume and reported positivity within regions. The second reflects the association between a region's share of reported tests and its pooled reported positivity. Positive components raise the pooled rate and negative components lower it. Compare their absolute sizes and report when they offset each other. Rates are percentages and gaps are percentage points. The code computes the differences from exact fractions before rounding each output independently.

The matched sensitivity uses only Saturday ordinals, counted from each calendar year's first Saturday, with eligible rows in all ten regions in every study year. This drops an extra ordinal in a 53-Saturday year and would drop any ordinal lacking eligible support in any region-year. The output counts tested rows excluded by matching. This controls the number and ordinal positions of weeks contributing to each annual estimate. It cannot establish stable laboratory participation, test indications or catchments. The contrasts describe redistribution of weight among reported tests and reporting units. The aggregate file lacks the sampling information needed to infer population incidence, population weights or assay performance.

## Reproduce the annual table and independent replay

From the repository root, use Python 3.9 or later and place the exact original CDC export at `data/raw/surveillance-audit/nrevss.csv`. Both commands check the file against the repository's `nrevss.csv` SHA-256 pin before parsing. The verifier reads the source independently and uses SQLite window totals to calculate the baseline weighting directly at the row level. The published table format exposes only annual aggregates.

```sh
source_csv=data/raw/surveillance-audit/nrevss.csv
summary_csv=$(mktemp results/nrevss-annual-weighting.XXXXXX)
python -B scripts/summarize_nrevss_weighting.py "$source_csv" > "$summary_csv" &&
    python -B scripts/verify_nrevss_weighting.py "$source_csv" "$summary_csv" &&
    mv "$summary_csv" results/nrevss-annual-weighting-2013-2019.csv
```

The empirical run awaits the original CSV in the analysis workspace. The expected SHA-256 is `157893051636c43a29b7a881e6d031dc2381ce157c553b33c3586f992e7348cc`.
