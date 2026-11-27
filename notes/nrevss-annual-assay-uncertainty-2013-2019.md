# Test-count noise in annual NREVSS assay contrasts, 2013–2019

Four of the six observed differences between annual antigen and PCR positivity changes exceed the standard-deviation ceiling for hypothetical independent reported rows. The largest difference, +1.473 percentage points (pp) in 2014–2015, is 3.41 times that ceiling. Allowing arbitrary dependence across all rows within a reporting region puts every observed difference below the region-cluster ceiling. The archive leaves this dependence unresolved.

## Fixed annual contrast

Use the positive-denominator, equal-weight comparison from the [adjacent-year assay analysis](https://github.com/will-s-hart/rsv-seasonality/pull/18). In each pair, match by reporting region and the ordinal of the reporting Saturday in its calendar year. Keep a matched cell when PCR and antigen both report positive test denominators in each year. A source flag or zero positives with a positive denominator leaves the row eligible. Keep the same `m` matched cells and the same weight `1/m` for each of the four assay-year means. The contrast is the antigen change minus the PCR change, with each change taken as later minus earlier. Keep the observed denominators, support and weights fixed in every calculation. Each reported assay–region–date row contributes exactly once within a pair. Neighboring contrasts can reuse rows and are considered separately.

## Conditional variance ceilings

For a reported row `i` with `n_i` tests, hypothetical independent Bernoulli trials with common row probability `p_i` give variance `p_i(1−p_i)/n_i ≤ 1/(4n_i)` for the row positivity. The bound also holds with independent trials of different probabilities within the row, by summing their individual Bernoulli variance bounds. Neither calculation uses the observed positivity to estimate `p_i`. In percentage-point units the signed coefficient of each row is `±100/m`. Its weighted marginal SD ceiling is `s_i = 100 / (2m√n_i)`.

For a block `B` of arbitrarily dependent rows, Cauchy–Schwarz bounds the absolute covariance of two weighted rows by `s_i s_j`. Hence the block variance is at most `(Σ_{i∈B} s_i)²`, regardless of the coefficient signs. Add these squared sums for independent blocks, then take the square root for the SD ceiling. Use four nested partitions of the same rows.

- **Independent rows.** Every assay–region–date row is a separate block. The variance ceiling is `Σ_i s_i²`.
- **Independent region-dates.** The two assays from the same reporting region and date can depend arbitrarily. Distinct region-dates form independent blocks.
- **Independent regions.** Within each region, allow arbitrary dependence across assays and dates in both years. Distinct reporting regions form independent blocks.
- **Unrestricted cross-row dependence.** Put all rows in one block. This still retains the hypothetical within-row Bernoulli variance ceiling.

The block assumptions define sensitivity scenarios. They allow covariance signs that maximize the bound, and the resulting ceilings can be loose for dependent Bernoulli counts. The reported data do not justify any of the partitions as a sampling design.

## Annual results

Contrasts and SD ceilings are in pp. The last two columns give `|contrast| / row SD ceiling` and its square, the factors needed for the row SD or variance ceiling to reach the observed scale. A factor below one means the current row ceiling already exceeds the discrepancy. The CLI also reports all four variance ceilings in pp².

| Years | Matched cells / regions | Contrast | Independent rows | Independent region-dates | Independent regions | Unrestricted | SD factor | Variance factor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2013–2014 | 518 / 10 | −0.528 | 0.480 | 0.592 | 5.215 | 15.568 | 1.10 | 1.21 |
| 2014–2015 | 518 / 10 | +1.473 | 0.433 | 0.536 | 5.032 | 14.972 | 3.41 | 11.60 |
| 2015–2016 | 518 / 10 | −0.087 | 0.441 | 0.533 | 4.863 | 14.567 | 0.20 | 0.04 |
| 2016–2017 | 520 / 10 | +0.394 | 0.538 | 0.625 | 5.597 | 16.132 | 0.73 | 0.54 |
| 2017–2018 | 488 / 10 | +0.878 | 0.606 | 0.695 | 5.883 | 16.951 | 1.45 | 2.10 |
| 2018–2019 | 462 / 9 | −0.799 | 0.677 | 0.761 | 6.432 | 17.203 | 1.18 | 1.39 |

Allowing same-region, same-date assay dependence moves the 2013–2014 discrepancy below the ceiling. The 2014–2015, 2017–2018 and 2018–2019 gaps still exceed that ceiling by factors of 2.75, 1.26 and 1.05. When all rows within a reporting region may covary, the SD ceilings range from 4.86 to 6.43 pp. These are conditional comparisons of scales. P-values and confidence intervals would require a justified joint sampling distribution. Unbiased assay comparisons would require comparable testing populations, and diagnosing overdispersion would require a validated mean and reporting design. The matched, selected reported counts alone cannot establish those conditions.

## What would strengthen the observation comparison

The largest gap is 2014–2015. A credible variance upper bound below its break-even factor of about 11.60 times the independent-row ceiling would keep that gap above the resulting SD ceiling. Support for that bound would require aggregate evidence about both cross-assay reuse and persistence across reporting periods. Contributor retention summaries and totals restricted to contributors reporting both assays in both years could show changes in assay use and the distribution of testing volume across contributors. Counts of dual-tested specimens and their paired outcomes, with summaries of repeat testing, could constrain within-block covariance. Aggregate contributor or network overlap across reporting periods and regions, together with replicate totals or a defensible upper bound on covariance, could constrain dependence between blocks. Aggregate tabulations can provide those summaries while preserving contributor and patient privacy.

Comparable test eligibility, or standardized aggregates by broad age and care-setting strata, would help assess whether changes in the tested populations account for part of the gap. This remains an observation validation task for Will. The public counts alone leave both the conditional variance and any change in the underlying reporting means unresolved.

## Reproduce

Run with Python 3.11 or later from the repository root using the existing historical CDC export at SHA-256 `157893051636c43a29b7a881e6d031dc2381ce157c553b33c3586f992e7348cc`. The CLI checks the digest before parsing. Its six output rows contain only adjacent-year aggregates.

```sh
python3 -B scripts/summarize_nrevss_assay_uncertainty.py "$NREVSS_CSV"
python3 -B -m unittest discover -s scripts -p test_summarize_nrevss_assay_uncertainty.py
```

A hand-calculated fixture checks all four ceilings and both multipliers on unequal denominators and uneven region sizes. Calendar and support fixtures check absent and zero-test rows, flagged zero detections, and the unmatched 53rd Saturday. A separate SQLite replay computed the ordinal from the date's day of year, selected four distinct positive-denominator rows per key in long form, and aggregated by the four block definitions in SQL. It matched all 90 displayed fields to rounding precision. A direct comparison with the merged PR #18 CLI also matched support and observed contrasts at full displayed precision. A checksum mismatch exited before emitting a summary.
