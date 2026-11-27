# Japan annual reports and paediatric sentinel volume, 2013–2019

Adjusting for the total number of paediatric sentinel-site weeks can reverse the 2013–2014 increase in national reported cases. The other five adjacent-year changes retain their direction across the full range allowed by the audit. The 2013–2019 change is a guaranteed rise of 229.86 to 335.44 reports per 1,000 sentinel-site weeks using outward-rounded bounds.

## Source and bounds

The input is the seven committed national rows in the [surveillance audit](surveillance-audit-2013-2019.md#final-annual-tables-checked) at main commit `53010b95d91a6128aaf1736d75353023def9763d`. The source audit derived the rows from SHA-verified final NESID workbooks and reconciled the national and prefecture totals. This Cloud run replays the committed aggregate controls. The original Japan workbooks were unavailable in the Cloud cache, so exact site-week totals and fresh verification against the [SHA-256 manifest](../scripts/surveillance_sources.sha256) remain pending.

Let `C` be annual reports, `W` diagnosis weeks, `L` and `U` the observed minimum and maximum national paediatric site counts, and `D` the sum of the weekly site counts. The broad envelope is `W × L ≤ D ≤ W × U`. Both observed extrema were attained, so

```text
D_low  = (W − 1) × L + U
D_high = (W − 1) × U + L
```

These endpoints are attainable from the annual controls by putting all but one week at the same extreme. If `L = U`, the denominator is exactly `W × L`. With `W = 1`, the extrema must coincide. The calculation uses the audited number of diagnosis weeks, including all 53 in 2015.

The annual pooled ratio lies in `[1000 × C / D_high, 1000 × C / D_low]`. For each later-minus-earlier comparison, subtract the earlier upper bound from the later lower bound and the earlier lower bound from the later upper bound. This covers every compatible pair of denominators without an independence assumption. The bounds describe the information in the annual controls. The calculation classifies signs using exact fractions and rounds displayed lower endpoints down and upper endpoints up.

## Annual results

| Year | Weeks | Reports | Sentinel-site weeks | Reports per 1,000 site-weeks |
| --- | ---: | ---: | ---: | ---: |
| 2013 | 52 | 96,625 | 155,906–164,206 | [588.43, 619.77] |
| 2014 | 52 | 100,394 | 150,868–164,668 | [609.67, 665.45] |
| 2015 | 53 | 120,049 | 156,771–167,430 | [717.01, 765.77] |
| 2016 | 52 | 104,703 | 160,963–164,713 | [635.66, 650.48] |
| 2017 | 52 | 139,557 | 160,096–164,696 | [847.36, 871.71] |
| 2018 | 52 | 120,743 | 159,888–164,488 | [734.05, 755.18] |
| 2019 | 52 | 140,093 | 151,637–164,887 | [849.63, 923.88] |

| Years | Change in reports | Change per 1,000 site-weeks | Direction |
| --- | ---: | ---: | --- |
| 2013–2014 | +3,769 | [-10.09, 77.01] | ambiguous |
| 2014–2015 | +19,655 | [51.56, 156.09] | rise |
| 2015–2016 | -15,346 | [-130.10, -66.53] | fall |
| 2016–2017 | +34,854 | [196.88, 236.04] | rise |
| 2017–2018 | -18,814 | [-137.66, -92.18] | fall |
| 2018–2019 | +19,350 | [94.45, 189.82] | rise |
| 2013–2019 | +43,468 | [229.86, 335.44] | rise |

For 2013–2014, the ratio falls if site-weeks grew faster than the 3.9006% growth in reports. The audit extrema allow, for example, 155,906 site-weeks in 2013 and 164,668 in 2014, a 5.62% increase. The distinct extremes were observed each year, but the actual annual totals within the bounds are unknown in this replay. Using the broader `W × L` to `W × U` envelope gives the same directional conclusions.

This is a reporting-volume sensitivity for national notifications. Total site-weeks measure paediatric reporting capacity. They leave the stability of contributing sites, attendance, case-definition changes and ascertainment unresolved. Incidence, testing prevalence and population burden require other denominators or evidence.

## Reproduce

```sh
python3 -B scripts/summarize_japan_sentinel_volume.py
python3 -B -m unittest discover -s scripts -p test_summarize_japan_sentinel_volume.py
```

Fixtures exhaustively enumerate small integer site-count sequences and denominator pairs, including constant networks, a single week and a sign-ambiguous contrast. An independent replay transcribed the seven committed rows, enumerated attainable integer totals with a bit set, and used decimal arithmetic for the ratios and all four endpoint combinations of each difference. It reproduced all 14 displayed rows and confirmed the same directions under the broad envelope.

The remaining measurement check is to sum the national weekly counts in the seven pinned table 14-1 workbooks when Will has access to the authorized archive and confirm the exact 2013–2014 sign. The calculation uses existing observation fields and has no dependency on Torkel's input.
