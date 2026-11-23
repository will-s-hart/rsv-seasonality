# Japan and US RSV surveillance audit, 2013–2019

Sources checked on 23 November 2026. The final Japan NESID workbooks support a prefecture-week panel of reported cases and paediatric sentinel counts. The historical US NREVSS export supports a complete HHS-region-week PCR panel of detections and tests. Antigen has gaps and zero-test weeks and is a separate sensitivity stream. These are surveillance activity measures with different denominators. Population incidence, attack rates and causal effects are unidentified from these aggregates alone.

## Japan IDWR and NESID

**Observation and coverage.** RSV is a Category V sentinel-reporting disease. Designated paediatric clinics and hospitals report clinically suspected, laboratory-diagnosed RSV cases to public health authorities each week. The historical notification criteria use diagnosis week, with notification due the following Monday. They list antigen detection, isolation and identification, and specified serology. The patient tables do not subdivide cases by assay or supply negative tests, total tests, visits for compatible symptoms, or catchment populations. The separate public health institute virology series described by IASR has different selection and units. [NIID notification criteria, 2014](https://id-info.jihs.go.jp/niid/images/iasr/35/412/de4121.pdf), [MHLW notification criteria](https://www.mhlw.go.jp/bunya/kenkou/kekkaku-kansenshou11/01-05-15.html), [NIID IASR, December 2018](https://id-info.jihs.go.jp/idsc/niid/images/idsc/iasr/39/466e.pdf).

**Reporting and ascertainment.** Japan expanded insurance coverage for RSV antigen tests on 17 October 2011 from inpatient use to include infant outpatients and outpatients eligible for palivizumab. JIHS reports that the annual number of paediatric sentinels with at least one RSV case grew gradually between 2013 and 2018. IASR cited roughly 80% of paediatric sites reporting RSV in recent years when explaining the 2018 display change. That share is an annual network descriptor and cannot be used to reweight weekly denominators. The sources reviewed support a 2018 display change and changing ascertainment over the study period. A full dated review of notification amendments, reimbursement and regional testing practice remains open. JIHS records an out-of-window reduction from about 3,000 to 2,000 paediatric sentinels in 2025 week 15. [NIID IASR, June 2014](https://id-info.jihs.go.jp/niid/en/iasr/4769-tpc412.html), [NIID IASR, December 2018](https://id-info.jihs.go.jp/idsc/niid/images/idsc/iasr/39/466e.pdf), [JIHS review of 2018–2024 surveillance](https://id-info.jihs.go.jp/surveillance/idwr/article/rsv/010/index.html).

### Final annual tables checked

Opened the workbooks for each year. Table **8-1** has one sheet per diagnosis week and an annual total sheet. Each contains a national row and 47 prefectural rows, with RSV counts for both sexes combined and separately. Table **14-1**, sheet `小児科定点`, gives weekly paediatric sentinel site counts for the same areas, alongside a separate annual-average column. Its category-level counts measure reporting capacity. They do not identify which sites tested for RSV or contributed a case in a given week. Table **12-1**, sheet `ＲＳウイルス感染症`, gives annual counts by prefecture, sex and age bin, including two infant bins, single years aged 1–9 and broader older groups. The age sheet has no weekly breakdown. Table **8-2** contains weekly RSV rates in 2018 and 2019, including weeks 1–8 of 2018. RSV is absent from the weekly rate sheets for 2013–2017. [JIHS final table indexes for 2013–2019](https://id-info.jihs.go.jp/surveillance/idwr/annual/2024/archive/index.html), [2013 index](https://id-info.jihs.go.jp/niid/ja/allarticles/surveillance/5281-syulist2013.html), [2018 index](https://id-info.jihs.go.jp/niid/ja/allarticles/surveillance/9204-syulist2018.html), [2019 index](https://id-info.jihs.go.jp/niid/ja/allarticles/surveillance/10119-syulist2019.html).

| Diagnosis year | Weeks | National reports | Prefecture-weeks with zero reports | Weekly national sites, min–max | Reports aged under 2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2013 | 52 | 96,625 | 134 | 2,995–3,161 | 74.1% |
| 2014 | 52 | 100,394 | 223 | 2,896–3,172 | 72.6% |
| 2015 | 53 | 120,049 | 161 | 2,954–3,163 | 72.5% |
| 2016 | 52 | 104,703 | 198 | 3,094–3,169 | 74.7% |
| 2017 | 52 | 139,557 | 78 | 3,077–3,169 | 71.5% |
| 2018 | 52 | 120,743 | 21 | 3,073–3,165 | 73.6% |
| 2019 | 52 | 140,093 | 24 | 2,911–3,176 | 70.3% |

Project tabulation of the JIHS final tables, both sexes combined. All **17,155** prefecture-weeks had a numeric nonnegative case count and a positive paediatric sentinel count. National rows matched prefecture sums each week, and summed weekly cases matched both annual tables for each prefecture and nationally. Published weekly rates matched 8-1 cases divided by 14-1 sites in all 2018–2019 prefecture and national cells checked. The earlier years therefore have the inputs to calculate the same ratio retrospectively. Store counts and site counts separately, and pool counts over sites if a site-weighted aggregate is required. A numeric zero means zero reports in the final table. Site attendance, test uptake and site-level reporting gaps remain unobserved. [JIHS final annual archive](https://id-info.jihs.go.jp/surveillance/idwr/annual/2024/archive/index.html).

**2013 reconciliation.** Summing the 47 prefectures over 52 weeks yields **96,625**, matching the final 8-1 and 12-1 national totals and the official year-end summary as of 19 October 2014. In a manual provisional spot check outside the scripted checksum verification, the archived week 52 cumulative CSV, compiled 7 January 2014, summed to **96,503**. Six prefecture totals differed between those vintages, with a net increase of 122. Use the final annual files consistently. [Official 2013 summary](https://id-info.jihs.go.jp/niid/ja/ydata/5152-report-jb2013.html), [2013 week 52 archive](https://id-info.jihs.go.jp/niid/ja/data/4172-idwr-sokuho-data-j-1352.html), [provisional cumulative CSV](https://id-info.jihs.go.jp/niid/images/idwr/sokuho/idwr-2013/201352/2013-52-teiten-ruiseki.csv).

**2018 reporting transition.** The IDWR comparison graph switched from case counts to cases per sentinel at **2018 week 9**. Both fields appear in the archived provisional CSVs on either side of that boundary. The table compares manual provisional spot checks outside the scripted checksum verification with the final tables. The small count differences come from distinct release vintages. The graph transition alone supplies no evidence for a case-definition break and needs no mixed-unit splice. [JIHS graph notice](https://id-info.jihs.go.jp/surveillance/idwr/graph/weekly/respiratory-syncytial-virus-infection/index.html), [IDWR week 8](https://id-info.jihs.go.jp/niid/en/data/7876-idwr-sokuho-data-e-1808.html), [IDWR week 9](https://id-info.jihs.go.jp/niid/en/data/7891-idwr-sokuho-data-e-1809.html), [2018 final tables](https://id-info.jihs.go.jp/niid/ja/allarticles/surveillance/9204-syulist2018.html).

| Japan week, local dates | Provisional national cases and rate | Final national cases ÷ paediatric sites |
| --- | ---: | ---: |
| 2018 W08, 19–25 Feb | 1,141 and 0.36 | 1,147 ÷ 3,163 = 0.3626 |
| 2018 W09, 26 Feb–4 Mar | 1,191 and 0.38 | 1,192 ÷ 3,162 = 0.3770 |

## US historical NREVSS

**Observation and denominator.** CDC dataset `52kb-ccu2` contains 10,313 aggregate rows, 5,210 PCR and 5,103 antigen, from July 2010 to June 2020. A row is diagnostic method × HHS region × reporting week, with positive detections `rsvpos`, total tests `rsvtest` and statistical flag `outlier`. The laboratory network is voluntary and includes hospital, public health and commercial labs. A person may account for multiple samples. The export has no patient demographics, lab identifiers, weekly lab counts, state rows or catchment sizes. Test positivity conditions on tests reported by laboratories, whose testing practices and service areas can change. Keep PCR and antigen numerators, denominators and flags separate. CDC documented a shift toward PCR and differences in method-specific positivity and season definitions. [CDC historical public-use dataset](https://data.cdc.gov/Laboratory-Surveillance/Respiratory-Syncytial-Virus-Laboratory-Data-NREVSS/52kb-ccu2/about_data), [CDC metadata and field definitions](https://data.cdc.gov/api/views/52kb-ccu2), [Midgley et al., CDC study](https://stacks.cdc.gov/view/cdc/50468), [CDC 2014–2017 analysis](https://www.cdc.gov/mmwr/volumes/67/wr/mm6702a4.htm).

**Aggregate completeness.** Checked the independent grid of 365 Saturday endings, 5 January 2013 through 28 December 2019, for each method and region. No duplicate region-method-weeks, blank counts, or detections outside 0 through the test count occurred in the window. Counts below are project tabulations of the CDC export. CDC defines `outlier=1` using a three-standard-deviation rule within region, method and surveillance year for tests or detections. This audit counted flags without adjudicating individual events. [CDC export](https://data.cdc.gov/resource/52kb-ccu2.csv?$limit=20000&$order=:id), [CDC flag definition](https://data.cdc.gov/api/views/52kb-ccu2).

| Method and region | Rows | Missing weeks | Zero test rows | Flagged rows |
| --- | ---: | --- | ---: | ---: |
| PCR, all 10 regions | 3,650 | 0 | 0 | 11 |
| Antigen, Region 2 | 362 | 3, endings 16–30 Jun 2018 | 4 | 5 |
| Antigen, Region 7 | 365 | 0 | 4 | 7 |
| Antigen, Region 8 | 287 | 78, endings 7 Jul 2018–28 Dec 2019 | 0 | 4 |
| Antigen, other seven regions | 2,555 | 0 | 0 | 17 |
| Antigen, all 10 regions | 3,569 | 81 | 8 | 33 |

Absent rows and explicit zero-test rows both lack a defined positivity, for different reasons. Zero detections with positive test volume are observed zeros. Aggregate reporting can be thin despite complete rows. PCR weekly test minima in candidate Regions 1, 2 and 5 were 1, 27 and 286 respectively. Across the ten regions, PCR tests rose from 254,265 in calendar 2013 to 907,190 in 2019, while antigen tests fell from 218,587 to 104,836 as its coverage also declined. Missing rows have no documented cause in the export. [CDC historical public-use dataset](https://data.cdc.gov/Laboratory-Surveillance/Respiratory-Syncytial-Virus-Laboratory-Data-NREVSS/52kb-ccu2/about_data).

**Geographic laboratory coverage.** HHS regions are administrative groupings. Region 2 includes New Jersey, New York, Puerto Rico and the US Virgin Islands in the HHS definition. The public extract does not reveal which jurisdictions contributed to each aggregate, the stability of the laboratory panel or where tested patients lived. Independent CDC analyses document the scale and variation of qualifying laboratories under their respective inclusion rules:

- **Antigen.** CDC used 178 eligible laboratories across 41 states for 2012–13 and 84 across 33 states for 2013–14. In the second season, Maine, New Hampshire, Rhode Island and Vermont in Region 1, and Illinois and Wisconsin in Region 5, lacked laboratories that met the inclusion criteria. [CDC 2012–2014 analysis and table footnotes](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6348a3.htm).
- **PCR.** Midgley et al. counted 74 and 61 consistent PCR reporters nationally in 2012–13 and 2013–14. Of 135, 218 and 244 labs reporting at least one PCR week nationally in 2014–15, 2015–16 and 2016–17, respectively, 80, 108 and 118 qualified for CDC's analysis. Table 1 counts for candidate Regions 1, 2 and 5 were respectively 4/5/7, 6/8/7 and 22/29/28 over those three seasons. Maine, New Hampshire and Rhode Island lacked qualifying labs in all three. Under the later CDC analysis, Regions 1, 2 and 5 had respectively 9/10, 8/9 and 33/35 qualifying labs in 2017–18 and 2018–19. These filtered seasonal counts show variation across place and time. Weekly lab participation and weights for distributing observations within each HHS region remain unknown. [Midgley et al., Table 2](https://stacks.cdc.gov/view/cdc/50468), [CDC 2014–2017 Table 1](https://www.cdc.gov/mmwr/volumes/67/wr/mm6702a4.htm#T1_down), [CDC 2017–2023 table](https://www.cdc.gov/mmwr/volumes/72/wr/mm7214a1.htm#T1_down).

The publications apply exclusions or separate strata for some states. The 2012–2014 report defines seasons using a 10% antigen positivity threshold. The 2014–2017 report uses a retrospective slope on smoothed and normalised PCR detections, and the 2017–2023 report uses a 3% PCR positivity threshold. Treat these as analysis rules and retain the weekly source fields. The aggregate file cannot reproduce those lab cohorts or state exclusions. Geographic weighting and reporting stability remain unresolved even for regions with a complete weekly grid. [HHS regional definitions](https://www.hhs.gov/about/agencies/iea/regional-offices/index.html), [CDC 2012–2014 methods](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6348a3.htm), [CDC 2014–2017 methods](https://www.cdc.gov/mmwr/volumes/67/wr/mm6702a4.htm), [CDC 2017–2023 methods](https://www.cdc.gov/mmwr/volumes/72/wr/mm7214a1.htm).

## Date alignment and analysis decisions

Japan uses Monday–Sunday diagnosis weeks in local time. Its published calendars follow the ISO week rule in this audit window. Week 1 contains 4 January, and the audited window starts on 31 December 2012 and ends on 29 December 2019. In 2015 table 14-1, the Japanese `５３週` label is correct and the English subtitle repeats `week 52`. [JIHS calendars for 2009–2013](https://id-info.jihs.go.jp/surveillance/idwr/annual/2022/archive/09-13calendar.gif), [2014–2018](https://id-info.jihs.go.jp/surveillance/idwr/annual/2022/archive/14-18calendar.gif), [2019–2020](https://id-info.jihs.go.jp/surveillance/idwr/annual/2022/archive/19-20calendar.gif), [2015 final tables](https://id-info.jihs.go.jp/niid/ja/allarticles/surveillance/6982-syulist2015.html).

NREVSS uses Sunday–Saturday reporting periods, with a Saturday date in `repweekdate` and the two-digit MMWR year and week in `repweekcode`. MMWR week 1 is the first Sunday–Saturday week with at least four days in the new year. The complete export agrees with that calendar. In the audit window, `1453` on 3 January 2015 and `1552` on 2 January 2016 carry the preceding MMWR year as expected. The export's July–June `season` label describes a separate period. [CDC MMWR week rules](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/MMWR_Week_overview.pdf), [CDC 2014–2015 week-ending log](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/W2014-15.pdf), [CDC 2018–2019 week-ending log](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/W2018-19.pdf), [CDC field definitions](https://data.cdc.gov/api/views/52kb-ccu2).

| Source week | Start date, inclusive | End date, inclusive |
| --- | --- | --- |
| US 2014-W53 (`1453`) | 2014-12-28 | 2015-01-03 |
| Japan 2015-W01 | 2014-12-29 | 2015-01-04 |
| US 2015-W52 (`1552`) | 2015-12-27 | 2016-01-02 |
| Japan 2015-W53 | 2015-12-28 | 2016-01-03 |
| Japan 2017-W52 | 2017-12-25 | 2017-12-31 |
| US 2018-W01 (`1801`) | 2017-12-31 | 2018-01-06 |

At the provisional 2017 tuning to 2018 holdout boundary, 31 December 2017 is both the final local calendar date of Japan 2017-W52 and the first calendar date of US 2018-W01. At the preceding training to tuning boundary, Japan 2016-W52 also ends on 1 January 2017, the first date of US 2017-W01. Retain source labels and inclusive dates to aggregate daily model and weather values for each stream. The split treatment of these overlaps remains an analysis decision. [Provisional joint splits](analysis-plan.md#initial-data-and-held-out-design), [JIHS 2014–2018 calendar](https://id-info.jihs.go.jp/surveillance/idwr/annual/2022/archive/14-18calendar.gif), [CDC 2016–2017 week-ending log](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/W2016-17.pdf), [CDC 2018–2019 week-ending log](https://ndc.services.cdc.gov/wp-content/uploads/2021/02/W2018-19.pdf).

- **Use separate observation models.** Japan can describe timing and relative variation in notifications at paediatric sites under an assumption about ascertainment. A count model with a paediatric site offset is a candidate, with sensitivity to clinic mix, holidays, testing and reporting. NREVSS can describe timing and variation in positivity among tests submitted, conditional on method, volume and the sampled mix. A test-count-conditioned model with overdispersion is a candidate. Age alignment is unresolved because Japan has annual age counts and the US file has no age breakdown. Compare timing and predictive performance on each source's own scale. Absolute burden, comparable age-specific risk, infection-to-observation delays and transmission attribution require evidence beyond these tables.
- **Prespecify unresolved choices before fitting.** Agree on prefectures and HHS regions, inclusion rules for thin and flagged weeks, and sensitivity to time-varying testing and catchment composition. Decide how to handle blocks of missing antigen weeks and compare antigen with PCR over common valid weeks if used. Choose geography and time-zone conventions for HHS weather aggregation, especially for Region 2, and test weighting assumptions where the reporting catchment is unknown. Specify delays, calendar boundaries for splits and edge weeks, and initialisation separately from the surveillance audit. Archived aggregate rows alone cannot validate those choices.

## Reproduce the tabulations

The check verifies the filenames and SHA-256 digests of all 28 final NESID workbooks and the ordered CDC export before opening any workbook or reading surveillance rows. Use Python 3.9 or later with `xlrd` and `openpyxl`. The official archive provides `.xls` for 2013 and `.xlsx` for the remaining years. The commands below save the official files to the ignored raw-data directory. [SHA-256 manifest](../scripts/surveillance_sources.sha256).

```sh
audit_dir=data/raw/surveillance-audit
mkdir -p "$audit_dir"
for year in 2013 2014 2015 2016 2017 2018 2019; do
    extension=xlsx
    if [ "$year" = 2013 ]; then extension=xls; fi
    for table in 8-1 8-2 12-1 14-1; do
        number=$(printf '%02d' "${table%-*}")
        curl -fsSL "https://id-info.jihs.go.jp/niid/images/idwr/ydata/$year/Syuukei/Syu_${number}_${table#*-}.$extension" \
            -o "$audit_dir/$year-$table.$extension" || exit 1
    done
done
curl -fsSL 'https://data.cdc.gov/resource/52kb-ccu2.csv?$limit=20000&$order=:id' \
    -o "$audit_dir/nrevss.csv" || exit 1
python scripts/check_surveillance_sources.py "$audit_dir"
```

The workbook checks validate the national row and all 47 prefecture labels against e-Stat prefecture codes 01–47 and the corresponding English NESID labels. The under-two share uses the both-sex case counts for the two infant bins and age 1, divided by the both-sex total. The age columns are selected by their table 12-1 headers. The CDC check validates both parts of the MMWR code for every row in the export before tabulating the 2013–2019 window. [Japan e-Stat prefecture names and codes](https://www.e-stat.go.jp/municipalities/cities/areacode), [JIHS final annual archive](https://id-info.jihs.go.jp/surveillance/idwr/annual/2024/archive/index.html), [CDC export](https://data.cdc.gov/resource/52kb-ccu2.csv?$limit=20000&$order=:id).

Run the local regression fixtures with `python -B -m unittest discover -s scripts -p 'test_check_surveillance_sources.py'`. They use synthetic inputs and exercise checksum enforcement, invalid CDC codes, calendar boundaries and workbook labels.

The CDC catalogue lists 21 October 2022 for the last data update and Public Domain U.S. Government licensing. Cite CDC's National Center for Immunization and Respiratory Diseases, National Respiratory and Enteric Virus Surveillance System, 2022 public-use file. Attribute JIHS tables and identify project calculations in derived publications. Record retrieval dates, URLs and checksums for locked analysis inputs. [CDC catalogue](https://data.cdc.gov/Laboratory-Surveillance/Respiratory-Syncytial-Virus-Laboratory-Data-NREVSS/52kb-ccu2/about_data), [JIHS usage terms](https://id-info.jihs.go.jp/usage-contract.html), [repository data conventions](../data/README.md).
