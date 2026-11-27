# Adjacent-year NREVSS PCR and antigen positivity changes, 2013–2019

Native count pooling gave PCR and antigen changes with the same direction in five of six adjacent calendar-year pairs. Equal weighting of the very same region–Saturday cells reduced agreement to two of six. The mean absolute cross-assay gap fell only slightly, from 0.759 to 0.693 percentage points (pp). The two higher test-count screens recovered some equal-weight agreement as they changed which reports contributed.

## Matched comparisons

Each Sunday–Saturday reporting week belongs to the calendar year of its Saturday. For each adjacent pair, match on HHS region and the Saturday's ordinal within its calendar year. Ten 53rd-Saturday cells in 2016 have no calendar counterpart in 2015 or 2017. The remaining common calendar has 520 possible cells per year for every pair. Require reported tests above zero in both assays in both years at each matched cell. Positive-test rows with zero detections and rows with native outlier flags remain eligible.

For each assay and year, native pooling divides summed detections by summed tests. The equal-weight estimate averages the cell positivity ratios, giving each retained cell weight `1 / matched_cells_per_year` for all four assay-year combinations. Differences are later minus earlier. The discrepancy is antigen change minus PCR change. Signs use unrounded changes, with any exact zero counted separately. The support and weights are set within each adjacent pair, so the same year can contribute different cells to neighboring contrasts. The contrasts cannot be chained into a single annual series.

| Calendar years | Cells per year / regions | Pooled PCR / antigen change (pp) | Pooled gap (pp) | Equal PCR / antigen change (pp) | Equal gap (pp) | Same direction after omission, pooled / equal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2013→2014 | 518 / 10 | −3.059 / −3.860 | −0.801 | −0.800 / −1.327 | −0.528 | 10/10 · 10/10 |
| 2014→2015 | 518 / 10 | +0.730 / +2.078 | +1.348 | −0.025 / +1.448 | +1.473 | 10/10 · 3/10 |
| 2015→2016 | 518 / 10 | −0.427 / −0.925 | −0.498 | +0.067 / −0.020 | −0.087 | 10/10 · 6/10 |
| 2016→2017 | 520 / 10 | +0.569 / +1.377 | +0.808 | −0.315 / +0.080 | +0.394 | 9/10 · 3/10 |
| 2017→2018 | 488 / 10 | +0.182 / −0.666 | −0.848 | +0.024 / +0.902 | +0.878 | 1/10 · 7/10 |
| 2018→2019 | 462 / 9 | −0.075 / −0.327 | −0.252 | +0.438 / −0.360 | −0.799 | 6/9 · 0/9 |

Each omission removes one represented region from all four assay-year combinations and recomputes both estimators. The equal-weight opposition in 2018→2019 persisted in all nine omissions, with gaps from −1.234 to −0.545 pp. For 2015→2016, both equal-weight changes were within 0.067 pp of zero and the omission gaps ranged from −0.465 to +0.173 pp. These ranges describe sensitivity to omitting a represented region. Adjacent contrasts share years, and the omissions reuse cells, so their tallies are descriptive.

## Test-count sensitivity and coverage

The two screens reuse the existing paired-assay audit minima of 25 and 100 tests. A cell is retained only when all four assay-year denominators meet the minimum. The cutoffs are descriptive sensitivity checks. The positive-denominator support excludes 84 of the 3,120 possible pair-cells for a missing row and 12 for a present zero-test row. The count for a calendar key can recur across adjacent pairs. Missingness takes precedence if a cell also contains another row with zero tests. Relative to the positive-denominator support, the 25-test screen drops another 489 pair-cells and the 100-test screen drops 1,487. The latter leaves about half the cells and reduces coverage from 9–10 to 7–9 regions per pair.

| Minimum per assay and year | Retained pair-cells across six pairs | Cells per pair / regions | Direction agreement, pooled / equal | Mean absolute gap (pp), pooled / equal | Same direction across omissions, pooled / equal |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 3,024 | 462–520 / 9–10 | 5/6 · 2/6 | 0.759 · 0.693 | 46/59 · 29/59 |
| 25 | 2,535 | 356–466 / 9–10 | 5/6 · 4/6 | 0.774 · 0.571 | 47/59 · 33/59 |
| 100 | 1,537 | 213–298 / 7–9 | 5/6 · 5/6 | 0.645 · 0.656 | 41/50 · 40/50 |

Native pooling gave the same pairwise direction classifications at all three minima. Under equal weights, agreement in 2015→2016 and 2016→2017 appeared at 25 tests and persisted at 100. At 100 tests, 2014→2015 and 2018→2019 also moved to agreement, while 2017→2018 moved to opposition. The increase in equal-weight agreement describes progressively selected supports.

## Interpretation

The findings describe consistency in aggregate reported positivity. The reporting streams may overlap, and their tested populations are unknown. The release cannot identify how much of the discrepancy reflects changes in contributing laboratories, test eligibility, repeat testing or assay response. The unresolved observation check is whether the streams show similar changes among stable contributors under comparable testing eligibility, using linked contributor metadata or another overlapping reference. That check belongs to Will's epidemiological validation work and requires information beyond this export.

## Reproduce

Run with Python 3.11 or later from the repository root, using an existing copy of the historical CDC file at SHA-256 `157893051636c43a29b7a881e6d031dc2381ce157c553b33c3586f992e7348cc`. The standard output contains calendar-pair aggregates, coverage loss counts, and unlabeled omission ranges.

```sh
python3 -B scripts/summarize_nrevss_assay_changes.py "$NREVSS_CSV"
python3 -B -m unittest discover -s scripts -p test_summarize_nrevss_assay_changes.py
```

An independent SQLite replay generated a seven-day calendar and ranked Saturdays within calendar year. It joined the original CSV by date, region, and assay, then used SQL sums and means for full and leave-one-region-out estimates. It matched all 450 fields across the 18 pair-by-screen rows to the displayed precision. The documented CLI rejected a checksum mismatch before emitting a summary.

Related checks cover [paired PCR and antigen levels](nrevss-assay-comparability-2013-2019.md), [annual weighting of PCR levels](nrevss-annual-weighting-2013-2019.md), and [within-PCR changes on a balanced calendar](nrevss-annual-positivity-change-2013-2019.md).
