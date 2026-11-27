# Data sources and feasibility

Assessed 18 November 2026. Small official CSV/API responses were inspected; no analysis datasets have been saved in this repository. See [literature](literature-review.md), [methodology](modelling-methodology.md), and [analysis plan](analysis-plan.md).

## Initial joint panel: Japan and the United States

**Recommend Japan + US from the outset, targeting 2013–2019.** Japanese prefectures supply the summer/winter contrast; US HHS regions supply a well documented winter comparator, substantial climate variation, and verified historical test denominators. Fit both countries jointly, with country-specific observation models and adaptation/context effects. Canada is a good alternative or third country; UK inclusion is optional. Country choice should follow data quality, climate support and seasonality, rather than a commitment to the UK.

### Japan: official IDWR paediatric surveillance

Use **JIHS/NIID's final NESID annual workbooks** for 2013–2019. Table 8-1 supplies weekly counts, table 14-1 supplies paediatric sentinel denominators, and table 12-1 supplies annual age counts. The final files were checked across all 47 prefectures and diagnosis weeks. They reconcile to 96,625 national reports in 2013. Use provisional IDWR as a separate release vintage when needed. [Final annual archive](https://id-info.jihs.go.jp/surveillance/idwr/annual/2024/archive/index.html), [2013 week 52 provisional archive](https://id-info.jihs.go.jp/niid/ja/data/4172-idwr-sokuho-data-j-1352.html), [2013–2019 surveillance audit](surveillance-audit-2013-2019.md).

For later extensions, the provisional 2024 week 52 CSV was retrieved and has 47 prefectures plus a national total, Japanese multilevel headers and CP932 encoding. [2024 provisional archive](https://id-info.jihs.go.jp/surveillance/idwr/provisional/2024/index.html), [2024 week 52 CSV](https://id-info.jihs.go.jp/surveillance/idwr/provisional/2024/52/2024-52-teiten.csv).

Cases are clinically suspected **and test-diagnosed**, reported through paediatric sentinels; they are not all infections. Antigen-test reimbursement expanded in October 2011. From 2025 week 15, sentinel selection changed and site numbers fell from about 3,000 to 2,000. Per-sentinel rates do not remove changes in site selection, and rounded rates cannot reconstruct exact denominators. Prefer 2013–2019 initially; treat pandemic and 2025 changes separately. [Official methods/epidemiology](https://id-info.jihs.go.jp/surveillance/idwr/article/rsv/010/index.html). Record original [JIHS reuse terms](https://id-info.jihs.go.jp/usage-contract.html), attribution, revisions, and missing-value conventions.

An optional convenience input is the [published author CSV](https://github.com/parksw3/perturbation/blob/main/data/japan_rsv.csv): inspected 26,978 records, 47 prefectures, 2013–2023. It can accelerate data checking independently of any published model; pin its commit and reconcile against official reports before analysis. Its repository licence does not replace original data terms.

### US: historical NREVSS — recommended winter comparator

The historical public-use file provides **weekly RSV-positive and total tests by diagnostic method and 10 HHS regions, July 2010–June 2020**. For 2013–2019, PCR has all 365 weekly rows per region with positive test denominators. Antigen has 81 absent rows and eight zero-test rows across the ten regions. The audit records which regions and weeks are affected, the coverage evidence from CDC studies, and the need to review source outlier flags individually. [CDC public-use dataset](https://data.cdc.gov/Laboratory-Surveillance/Respiratory-Syncytial-Virus-Laboratory-Data-NREVSS/52kb-ccu2/about_data), [2013–2019 surveillance audit](surveillance-audit-2013-2019.md).

```text
https://data.cdc.gov/resource/52kb-ccu2.json?$limit=20000
https://data.cdc.gov/resource/52kb-ccu2.csv?$limit=20000
```

Fields: `testtype`, `season`, `repweekcode`, `repweekdate`, `hhs_region`, `rsvpos`, `rsvtest`, `outlier`. The date is a string such as `10JUL2010`; weeks end Saturday. JSON retrieval was tested; CSV is the equivalent Socrata export route. Use PCR primarily and antigen as a separate sensitivity stream. The catalogue lists **Public Domain U.S. Government** licensing and unrestricted public access; retain CDC's requested citation and source metadata.

[CDC surveillance](https://www.cdc.gov/rsv/php/surveillance/index.html) describes usual autumn/winter circulation and regional exceptions. A simple source-validation calculation pooling 2013–2019 PCR tests by calendar month placed peak positivity in December for HHS regions 1–6 and February for 7–10; this is descriptive, not a transmission estimate. Include regional heterogeneity rather than treating the US as homogeneous.

NREVSS is voluntary; lab participation, diagnostic use and tested populations change. Multiple specimens can represent one person; patient demographics and catchment populations are unavailable. Positive tests/total tests support a sampling model, **not a population incidence denominator**. HHS regions are large, may include labs receiving out-of-region specimens, and need spatial-exposure sensitivity analyses. [Dataset limitations](https://data.cdc.gov/Laboratory-Surveillance/Respiratory-Syncytial-Virus-Laboratory-Data-NREVSS/52kb-ccu2/about_data). For later years, [current NREVSS raw national/regional data](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb) begin July 2019; audit overlap before stitching. State series use moving averages and are unsuitable as equivalent raw weekly observations.

### Alternatives compared

| Candidate | Verified access/overlap | Decision |
| --- | --- | --- |
| **Canada RVDSS/FluWatch** | Official national CSVs for 2013/14–2016/17 were downloaded: 209 weekly rows, 2013 week 35–2017 week 34, with `TotalRSVTests` and `TotalPositiveRSV`. Example [2016/17 CSV](https://health.canada.ca/apps/open-data/fluwatch/FluWatch2016-2017RespiratoryVirusDetectionsIsolations-en.csv), [official catalogue](https://open.canada.ca/data/en/dataset/4315264c-a604-432b-b2a8-e47f0608e3b1). The file footer lists 32 sentinel labs, 17 in Ontario. | Strong winter comparator; [official guidance](https://www.canada.ca/en/public-health/services/diseases/respiratory-syncytial-virus-rsv/health-professionals.html) confirms late-autumn–spring activity. Prefer US initially because regional raw coverage is verified. The tested filename pattern failed for 2017 onward: do not promise a seamless historical Canadian regional panel yet. |
| **Canada extension** | [Current FluWatch+ downloads](https://health-infobase.canada.ca/respiratory-virus-surveillance/explore.html) advertise lab data and dictionaries; [historical reports](https://www.canada.ca/en/public-health/services/surveillance/respiratory-virus-detections-canada.html) extend through 2015–2024 archives. Canada catalogue uses Open Government Licence–Canada. | Lab participation varies geographically and weekly; identify original raw regional downloads and overlapping years before adding. Current download workflow was not exercised. |
| **UK optional** | England API inspected: 488 all-age weeks, July 2017–November 2026, positivity but no numerator/denominator metrics. [UKHSA access](https://ukhsa-dashboard.data.gov.uk/access-our-data/getting-started). [Scotland CSV resources](https://www.opendata.nhs.scot/dataset/viral-respiratory-diseases-including-influenza-and-covid-19-data-in-scotland) inspected: national case counts October 2016 onward; RSV PCR numerator/denominator series October 2022 onward. OGL. | Useful future validation; shorter shared pre-COVID history and observation limitations make it less attractive than US for the initial joint fit. Keep UK nations separate. |

## Climate: same exposure pipeline across countries

| Source | Verified specification | Use |
| --- | --- | --- |
| **ERA5 single levels — primary** | [CDS dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview): 1940–present, hourly, 0.25° grid. Request 2 m temperature/dewpoint (K), surface pressure (Pa), optionally precipitation/radiation. | Aggregate actual weather to prefectures/HHS regions; retain within-area variability and compare population versus area weighting. Prefer final ERA5 to provisional ERA5T. |
| **ERA5-Land — sensitivity** | [CDS dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview): 1950–present, hourly, 0.1° (~9 km native), land only. | Spatial-resolution check; atmospheric forcing comes from ERA5, so not independent validation. |
| **Station observations** | [JMA download portal](https://www.data.jma.go.jp/risk/obsdl/), [NOAA Integrated Surface Database](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database). | Selected-station temperature/dewpoint validation; station coverage, relocations and humidity completeness require audit. Bulk retrieval not tested. |

CDS requires account/token and manual dataset-terms acceptance; current catalogue entries use CC-BY licensing. No climate retrieval has been performed. [Access instructions](https://cds.climate.copernicus.eu/how-to-api) document portal/API routes; pilot reproducible Julia-compatible retrieval and NetCDF/GRIB processing.

Derive humidity **hourly before spatial/weekly averaging**: vapour pressure `e = es(Td)`, `RH = 100e/es(T)`, absolute humidity `e/(Rv*T_kelvin)` using consistent SI units, specific humidity `q = 0.622e/(p − 0.378e)`. Document water/ice convention. Compare temperature plus one humidity measure; humidity measures are mathematically related. [ECMWF example](https://era-explorer.climate.copernicus.eu/notebooks/content/humidity/humidity_monthly_climatology.html). Align actual local week boundaries; US weeks end Saturday, unlike Japanese reporting weeks. Preserve week 53.

### ERA5 inventory gap check, 27 November 2026

Checked the supplied snapshot at `9ace6eb332cd601d57254ad3faf9757593fbf05d` for issue #22. The [analysis input manifest](../data/analysis-inputs.toml) explicitly records `unresolved.climate.status = "missing"` and contains no locked ERA5 artifacts. The catalogue specification above is the planned source; it does not establish an acquired Japan or US release. The source notes record no climate retrieval.

| Requested provenance | Japan | United States |
| --- | --- | --- |
| Dataset/release | Planned ERA5 single levels; acquired release/version unrecorded | Planned ERA5 single levels; acquired release/version unrecorded |
| Variables and units | Planned 2 m temperature and dewpoint (K), surface pressure (Pa); no artifact metadata verified | Same planned fields; no artifact metadata verified |
| Date coverage | Target 2013–2019; actual climate timestamps unverified | Target 2013–2019; actual climate timestamps unverified |
| Checksum evidence | No ERA5 artifact digests or receipt-derived metadata recorded | No ERA5 artifact digests or receipt-derived metadata recorded |
| Spatial processing | Prefecture selection, boundary/weight inputs and transformations unpinned | HHS region selection, boundary/weight inputs and transformations unpinned |

Precipitation is included in the analysis plan but optional in the source shortlist. Its inclusion, native units and accumulation convention need an explicit decision. The suggested processed precipitation unit is mm; this is not verified source metadata. Humidity derivation, water/ice convention, local-time alignment and aggregation also remain to be implemented and pinned.

The surveillance manifest gives Japan's inclusive local observation interval as **2012-12-31–2019-12-29** and the US interval as **2012-12-30–2019-12-28**. A January 2013 climate start would therefore omit part of each first observation week. These dates describe observation support, not available ERA5 coverage. Freeze the corresponding hourly UTC coverage and any earlier lag/initialisation buffer after agreeing local-time handling.

**Next action — Torkel:** identify any existing acquisitions and provide public-safe metadata for each country's artifacts: stable dataset URL, acquired release/product/grid, variable names and native units, exact timestamp coverage, retrieval date, licence/attribution and SHA-256 digests checked against preserved bytes. Retain original acquisition receipts privately. If acquisitions do not exist, retrieve a documented pilot for both countries using the existing project environment before claiming coverage; package changes remain with Torkel. Pin boundary and weight sources and Julia transformation code before panel assembly. Stage 1 remains open.

## Adaptation, behaviour and feasibility gate

Population and age structure: [Japan Statistics Bureau](https://www.stat.go.jp/english/data/jinsui/2.html) and [US Census population estimates](https://www.census.gov/programs-surveys/popest.html). Add school/childcare calendars and regional testing-policy metadata. Optional adaptation proxies include US [2015 RECS](https://www.eia.gov/consumption/residential/data/2015/) heating/cooling and appliance-use surveys, Japanese [Consumer Confidence Survey durable-goods tables](https://www.esri.cao.go.jp/jp/stat/shouhi/honbun202403.pdf) with historical air-conditioner adoption, and [time-use surveys](https://www.stat.go.jp/english/data/shakai/index.html). Canada [Households and Environment Survey](https://www.statcan.gc.ca/o1/en/plus/4034-air-conditioning-more-canadians-keep-cool-costs-heat) offers provincial AC context if added. Match reference years and geography to the analysis period. These sparse proxies are not measured weekly indoor humidity, ventilation or contact rates; use as context/effect modifiers with uncertainty. Weather-driven behaviour remains part of the climate-associated transmission relationship.

Monthly live births and their official annual and monthly controls are documented in the [2013–2019 natality source audit](natality-sources-2013-2019.md).

Before fitting, retrieve and validate both countries together; audit surveillance changes, observations, population weighting, climate support and sampling differences. Lock a manifest with original licence, URL/version, retrieval date, checksum, revisions and transformations. Treat 2020 onward separately, including pandemic disruption and prevention-programme changes. Missing or suspended surveillance is not zero transmission.
