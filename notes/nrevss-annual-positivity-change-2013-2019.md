# Year-over-year changes in US NREVSS PCR positivity, 2013–2019

Changes in the mix of reported PCR tests reversed the direction of the matched cell-positivity component in two of six calendar-year pairs. The mix component was larger in absolute magnitude in four pairs. Matching preserved the direction of the pooled change in all six pairs.

## Support and decomposition

The source is CDC's historical public-use NREVSS export `52kb-ccu2`, pinned at SHA-256 `157893051636c43a29b7a881e6d031dc2381ce157c553b33c3586f992e7348cc`. The analysis pools the ten HHS reporting regions as the US surveillance aggregate. It uses PCR rows with positive test denominators and retains tested rows with zero detections and CDC-flagged PCR rows. [Source coverage, fields and reporting calendar](surveillance-audit-2013-2019.md#us-historical-nrevss).

A cell is an HHS region and a Saturday's ordinal within the calendar year of the reported week-ending date. The first Saturday is ordinal 1. The all-years intersection retains the first 52 ordinals in all ten regions, for 520 matched cells per year. Full-calendar pooling uses all 3,650 tested rows across the seven years. Matching excludes ten rows from 2016, the only year with 53 Saturdays. The matched analyses use the same cells for every pair. [Calendar convention from the annual weighting analysis](nrevss-annual-weighting-2013-2019.md).

For an adjacent pair, let `p0` and `p1` be each cell's share of tests that were positive, and let `w0` and `w1` be its shares of the earlier and later year's total matched tests. Matched pooled positivity changes by `sum(w1*p1 - w0*p0)`, which is exactly the sum of two terms.

- **Cell positivity** is `sum(((w0 + w1)/2) * (p1 - p0))`. It measures the observed change in positivity in matched cells at fixed midpoint test shares.
- **Test mix** is `sum(((p0 + p1)/2) * (w1 - w0))`. It measures the change from reallocating the shares of reported tests at fixed midpoint cell positivity.

The equal-weight change is the mean of `p1 - p0` over the 520 matched cells. The leave-one-region-out check recomputes all shares on the remaining cells and reports only the minimum and maximum across omissions.

## Annual changes

Effects are later minus earlier in percentage points. The two component estimates sum to the matched pooled change before rounding.

| Calendar years | Full pooled | Matched pooled | Cell positivity | Test mix | Equal weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2013→2014 | −3.066 | −3.066 | −1.174 | −1.892 | −0.797 |
| 2014→2015 | +0.731 | +0.731 | +0.157 | +0.574 | −0.022 |
| 2015→2016 | −0.094 | −0.425 | −0.216 | −0.209 | +0.065 |
| 2016→2017 | +0.238 | +0.569 | −0.364 | +0.934 | −0.315 |
| 2017→2018 | +0.229 | +0.229 | −0.154 | +0.384 | +0.039 |
| 2018→2019 | +0.044 | +0.044 | +0.430 | −0.386 | +0.510 |

In 2016→2017 and 2017→2018, positive test-mix terms outweighed negative cell-positivity terms, yielding pooled increases. Test mix also contributed the larger absolute term in 2013→2014 and 2014→2015, when both terms pointed in the same direction. The terms were similar in magnitude in 2015→2016. In 2018→2019 the negative mix term offset most of the positive cell term. Equal weighting gave the opposite direction from matched pooling in 2014→2015, 2015→2016 and 2016→2017. Matching changed the two pooled differences involving 2016 by 0.331 percentage points in opposite directions. The other four pooled differences were identical on both supports.

| Calendar years | Matched pooled range | Cell positivity range | Test mix range |
| --- | ---: | ---: | ---: |
| 2013→2014 | [−3.749, −2.576] | [−1.532, −0.731] | [−2.226, −1.553] |
| 2014→2015 | [+0.369, +1.039] | [+0.020, +0.332] | [+0.349, +0.753] |
| 2015→2016 | [−0.639, −0.061] | [−0.443, +0.153] | [−0.246, −0.104] |
| 2016→2017 | [−0.133, +1.110] | [−1.137, +0.134] | [+0.806, +1.004] |
| 2017→2018 | [−0.097, +0.327] | [−0.508, −0.003] | [+0.289, +0.431] |
| 2018→2019 | [−0.180, +0.410] | [+0.286, +0.784] | [−0.466, −0.231] |

The sign of the mix term held in every omission for all six pairs. The matched pooled sign held in every omission for the first three pairs. The pooled ranges for both national reversals crossed zero, so those reversals depended on the set of regions included. These effects describe reported tests. Changes within cells can reflect shifts in who was tested and which laboratories reported. Inference about incidence, transmission or assay performance would require additional data.

## Reproduce and verify

Point `NREVSS_CSV` at the original pinned CSV and run this command from the repository root.

```sh
python3 -B scripts/summarize_nrevss_annual_change.py "$NREVSS_CSV"
```

The command verifies the input hash and prints six country-level rows to standard output. The fixture checks the exact identity by hand, including a direction reversal, calendar-year boundaries, the all-years intersection and normalization after excluding a region. An independent SQLite replay indexed the raw PCR Saturday rows in date order and rebuilt the matched support. It recovered each component from four pooled rates formed by crossing the two years' shares and cell positivities. The replay agreed with all 96 output fields, including the omission ranges, to the CLI's displayed precision.
