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

## Results on the pinned CDC export

The baseline includes all 3,650 expected PCR region-weeks across the ten HHS regions. Every year has full calendar-year support by Saturday ending, with 52 Saturdays in six years and 53 in 2016. There were no absent or zero-test rows. The analysis retained 257 tested rows with zero detections and 11 CDC-flagged rows.

| Year | A (%) | B (%) | C (%) | Within region (pp) | Region mix (pp) | C − A (pp) | Matched C − A (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2013 | 6.193 | 9.373 | 9.740 | +3.180 | +0.367 | +3.547 | +3.547 |
| 2014 | 5.397 | 6.653 | 6.675 | +1.256 | +0.022 | +1.278 | +1.278 |
| 2015 | 5.374 | 7.272 | 7.406 | +1.898 | +0.134 | +2.031 | +2.031 |
| 2016 | 5.645 | 7.369 | 7.312 | +1.725 | −0.057 | +1.667 | +1.541 |
| 2017 | 5.125 | 7.471 | 7.550 | +2.346 | +0.079 | +2.425 | +2.425 |
| 2018 | 5.164 | 7.650 | 7.779 | +2.487 | +0.129 | +2.615 | +2.615 |
| 2019 | 5.674 | 8.066 | 7.823 | +2.392 | −0.243 | +2.149 | +2.149 |

Global count pooling raised annual reported positivity by 1.278–3.547 percentage points in every year. Weighting weeks by reported test volume within each region accounted for the larger component in all seven years (+1.256 to +3.180 pp). Weighting regions by annual test totals reinforced that increase in five years and partially offset it in 2016 and 2019 (−0.243 to +0.367 pp overall).

Matching retained the first 52 Saturday ordinals in all ten regions and seven years. It removed ten tested rows at ordinal 53 in 2016 and left the other six annual estimates identical. For 2016, C fell to 6.981% and A to 5.440%. The gap stayed positive at +1.541 pp, with +1.631 pp from within-region weighting and −0.090 pp from region mix. The direction of the total gap and the larger absolute contribution of within-region weighting held in every year on matched support.

## Reproduce the annual table and independent replay

From the repository root, use Python 3.9 or later and set `NREVSS_CSV` to the path of the preserved CDC export if it is stored outside `data/raw/surveillance-audit/nrevss.csv`. Both commands check the file against the repository's `nrevss.csv` SHA-256 pin before parsing. The verifier reads the source independently and uses SQLite window totals to calculate the baseline weighting directly at the row level. The output contains annual aggregates.

```sh
source_csv=${NREVSS_CSV:-data/raw/surveillance-audit/nrevss.csv}
summary_csv=$(mktemp results/nrevss-annual-weighting.XXXXXX)
python -B scripts/summarize_nrevss_weighting.py "$source_csv" > "$summary_csv" &&
    python -B scripts/verify_nrevss_weighting.py "$source_csv" "$summary_csv" &&
    mv "$summary_csv" results/nrevss-annual-weighting-2013-2019.csv
```

The CLI and baseline verifier ran against the restored 544,023-byte export with SHA-256 `157893051636c43a29b7a881e6d031dc2381ce157c553b33c3586f992e7348cc`. A separate SQLite calculation reconstructed the calendar, matched eligible ordinals across all 70 region-years, and reproduced the coverage, counts, rates, and gaps for all 14 year-and-support rows.
