# Annual reporting directions in Japan and the US, 2013–2019

The two national reporting measures rose together in 2018–2019 and moved in opposite directions in 2017–2018 under both US weighting methods. The relationship in 2013–2014 is indeterminate within Japan's audited site-week bounds. The other three pairs agree under US count pooling and disagree under equal weights.

| Years | Japan possible signs | US equal (pp) | US pooled (pp) | Equal agreement | Pooled agreement |
| --- | --- | ---: | ---: | --- | --- |
| 2013–2014 | fall or rise | -0.797 | -3.066 | Indeterminate | Indeterminate |
| 2014–2015 | rise | -0.022 | +0.731 | Disagreement | Agreement |
| 2015–2016 | fall | +0.065 | -0.425 | Disagreement | Agreement |
| 2016–2017 | rise | -0.315 | +0.569 | Disagreement | Agreement |
| 2017–2018 | fall | +0.039 | +0.229 | Disagreement | Disagreement |
| 2018–2019 | rise | +0.510 | +0.044 | Agreement | Agreement |

Each comparison subtracts the earlier annual value from the later one on its source's scale. US changes are shown in percentage points and classified before rounding. Agreement requires two identical nonzero directions. Exact ties are a separate outcome. Neither US weighting gives a tie, and no pair of compatible integer Japan site-week totals gives a tie.

## Source support and bounds

Japan's measure divides annual reported cases by the sum of paediatric sentinel-site counts across the full diagnosis-week year, including all 53 weeks in 2015. These are Monday–Sunday diagnosis weeks. The committed national controls provide annual cases, week counts, and attained weekly site-count extrema. The earlier department audit verified the original NESID workbooks. The Cloud comparison replayed the committed national controls at `53010b95d91a6128aaf1736d75353023def9763d`. [Japan surveillance audit](surveillance-audit-2013-2019.md#final-annual-tables-checked), [annual denominator bounds](japan-annual-sentinel-volume-2013-2019.md).

For each year, fixing one week at each observed extreme leaves the other weeks free within those bounds. Every integer total between the resulting extremes is compatible with the committed controls. The rate interval uses the maximum site-week total for its lower endpoint and the minimum total for its upper endpoint. Differences use opposite endpoints for earlier and later rates. Per 1,000 site-weeks, the outward-rounded 2013–2014 difference spans −10.09 to +77.01 reports. That interval crosses zero. An exact tie requires the two integer totals to be in the ratio of the two annual case counts, which is infeasible within the bounds.

The US assigns each whole Sunday–Saturday reporting week to the calendar year of its Saturday. Both US estimates use the same 520 tested region–Saturday cells per year, the first 52 Saturday ordinals in all ten HHS regions on the all-years common support. The additional Saturday in 2016 falls outside this support. Equal weighting averages the cell positivity ratios. Count pooling divides the total reported detections by the total reported tests. Both retain tested cells with zero detections and CDC flags. Matching applies only within the US series, and the country-year labels retain their distinct date conventions. [NREVSS weighting and support](nrevss-annual-weighting-2013-2019.md#support-and-contrasts).

Across the six pairs, the jointly attainable agreement counts are **2 equal-weight and 5 pooled** if Japan falls in 2013–2014, or **1 equal-weight and 4 pooled** if it rises. Both outcomes can use the lower site-week bound in every Japan year except 2014. Setting 2014 to 164,668 site-weeks gives the fall and setting it to 150,868 gives the rise. Each outcome uses one annual denominator per year for both of its neighboring comparisons and for both US methods. These counts summarize overlapping contrasts descriptively.

## Interpretation and provenance

Japan's site-weeks measure reporting capacity. Attendance, testing eligibility and uptake, and the number of sites actually contributing RSV reports are unresolved. US positivity is conditional on reported PCR tests. Lab participation, catchments, and who was tested can change even when aggregate cells are complete. The streams have different denominators and unknown age and ascertainment composition. A shared sign means the measured reports moved in the same direction on their respective scales. The equivalence of those signs as indicators of underlying population burden is unidentifiable from these aggregates. [Surveillance audit](surveillance-audit-2013-2019.md).

The next shared provenance dependency in the analysis plan is Torkel's independent climate-input inventory for both countries, including the ERA5 version, coverage, retrieval records and checksums. [Analysis input manifest status](analysis-plan.md#audited-analysis-input-manifest).

## Reproduce the comparison

Run from the repository root with Python 3.9 or later. Point `NREVSS_CSV` to the preserved original export if it is stored outside the default raw-data path. The comparison uses the exact annual output from the weighting CLI and verifies the source bytes before parsing. In Cloud the preserved export matched SHA-256 `157893051636c43a29b7a881e6d031dc2381ce157c553b33c3586f992e7348cc`. An independent replay reconstructed the matched calendar, checked both exact annual US rates, and checked the Japan integer tie conditions and shared-year agreement counts.

```sh
source_csv=${NREVSS_CSV:-data/raw/surveillance-audit/nrevss.csv}
python -B scripts/compare_annual_reporting_directions.py "$source_csv"
```
