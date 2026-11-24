# Annual population sources, 2013–2019

The target is one observation per geography and annual reference date, with all-age population, population aged 0–4 inclusive, and the ratio of the two. Use the same release, reference date, geography, and population universe for both counts. These population estimates describe residents. Weekly surveillance has its own reporting coverage and observation denominators.

| Panel | Reference date | Scope | Expected rows | Workflow status |
| --- | --- | --- | ---: | --- |
| Japan | October 1 | 47 prefectures, total population across nationalities and sexes | 329 | Validated against same-release companion tables |
| United States | July 1 | 50 states and Washington, DC, resident population across sexes, races and Hispanic origins | 357 | Reconciled with national and county controls. DC, NJ and NY also match their age-by-sex workbooks. |
| Puerto Rico | July 1 | One commonwealth, resident population across sexes | 7 | Reconciled with all 78 municipios |

## Japan

- **2013 and 2014.** Use the original annual Population Estimates Prefectures Table 10 five-year age bands, with Table 4 as the same-release all-age check. Use the both-sex total-population series. The 2010–2015 intercensal revision adjusted prefecture population by sex during 2011–2014 and left age estimates as originally released. Matching the age band and denominator to the original vintage avoids introducing the later totals into those age shares. [2013 annual release](https://www.e-stat.go.jp/en/stat-search/files?layout=datalist&lid=000001118081), [2014 annual release](https://www.e-stat.go.jp/en/stat-search/files?layout=datalist&lid=000001132435), [2010–2015 revision methods](https://www.stat.go.jp/english/data/jinsui/2-5.html)
- **2015.** Use Census apportionment reference Table 2, published November 24, 2016. Use the total population across nationality and sex for both the five-year age band and all-age count. The bureau allocated unknown age and nationality proportionally within municipalities and summed those results to prefectures. It later published a retrospective Census table under a different unknown-data method. The 2016–2019 estimate revision used the 2015 Census with unknown age prorated as its starting point. [2015 Census apportionment methods](https://www.stat.go.jp/data/kokusei/2015/kekka/anbun.html), [reference tables](https://www.e-stat.go.jp/stat-search/files?layout=datalist&tclass1=000001090735&tclass2=000001090736&tstat=000001080615), [2015–2020 revision methods](https://www.stat.go.jp/english/data/jinsui/2-6.html)
- **2016–2019.** Use the October 1 prefecture estimates in Table 10 and the same-release totals in Table 5 from the February 3, 2022 intercensal release. The age-specific revision apportions the discrepancy between the 2020 estimates and Census. The workflow uses the February 2022 workbook downloads. [2015–2020 revision catalogue](https://www.e-stat.go.jp/en/stat-search/files?layout=datalist&lid=000001287677&page=1)

### Official reconciliation

The pinned files retrieved on department on 24 November 2026 produced 329 October 1 rows with codes 01–47 and consistent prefecture names. Table 10 supplies both counts for 2013–2014 and 2016–2019. Its both-sex total-population rows cover all nationalities. Each of the 282 prefecture-year all-age cells and the six national all-age cells agree with the corresponding Table 4 or Table 5. The Table 10 national all-age and age-0–4 lines agree with the original October columns of national Table 2 for 2013–2014 and the revised national Table 3 for 2016–2019. The national controls cover all Japan, all nationalities and both sexes, on October 1. These are companion tables from the same Statistics Bureau releases. [2013 annual release](https://www.e-stat.go.jp/en/stat-search/files?layout=datalist&lid=000001118081), [2014 annual release](https://www.e-stat.go.jp/en/stat-search/files?layout=datalist&lid=000001132435), [2015–2020 revision catalogue](https://www.e-stat.go.jp/en/stat-search/files?layout=datalist&lid=000001287677&page=1).

The 2015 CSVs use Windows CP932. Table 2 uses population category `0101` for both sexes and all nationalities. Geography type `a` supplies the 47 prefectures and a separate national row. This selection excludes cities and other finer geographies. Both counts match same-vintage Table 1 in all 48 comparisons, taking ages 0 through 4 from its single-year cells. The national sum of the 47 prefectures agrees exactly with both controls in persons. The age convention is the original proportional apportionment of unknown age and nationality published November 24, 2016. The later Census imputation series and the original unimputed national age count describe different conventions. [2015 apportionment methods](https://www.stat.go.jp/data/kokusei/2015/kekka/anbun.html), [apportioned Table 1](https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&cycle=0&toukei=00200521&tstat=000001080615&tclass1=000001090735&tclass2=000001090736&tclass3val=0&stat_infid=000031496977).

Japan's annual estimates use integer thousands. The exported counts are in persons and keep that source precision. The Statistics Bureau rounds to the nearest thousand and warns that sums of displayed components can differ from displayed totals. The workflow compares the prefecture sums with the matched national estimates within that precision and leaves the published values intact. The national rows are controls outside the prefecture export. [2013 summary](https://www.stat.go.jp/english/data/jinsui/2013np/index.html), [2014 summary](https://www.stat.go.jp/english/data/jinsui/2014np/index.html), [revised summary and rounding notes](https://www.stat.go.jp/data/jinsui/pdf/2-6.pdf).

| Year | Prefecture sum minus national all-age control | Prefecture sum minus national age-0–4 control | Unit |
| --- | ---: | ---: | --- |
| 2013 | −1 | +1 | Thousand persons |
| 2014 | −1 | +2 | Thousand persons |
| 2015 | 0 | 0 | Persons |
| 2016 | +2 | +1 | Thousand persons |
| 2017 | +1 | −1 | Thousand persons |
| 2018 | −1 | +1 | Thousand persons |
| 2019 | 0 | +2 | Thousand persons |

The estimate vintages establish prefecture-level agreement between tables for all ages and national agreement between tables for both counts at their published precision. The six years of rounded prefecture age estimates lack an independent prefecture-level age control in this audit. Exact person-level reconciliation of the rounded prefecture sums remains unavailable.

## United States and Puerto Rico

The Population Estimates Program released the 2010–2020 intercensal demographic series on September 30, 2025. Use July 1, 2013–2019. The state file layout specifies geography as of 2020. The command selects documented state-level rows with total sex (`SEX=0`) and total Hispanic origin (`ORIGIN=0`). It adds the six mutually exclusive race groups across ages 0–4 for the numerator and across all ages (0 through the 85+ group) for the denominator. Require each state/DC, race and age cell exactly once. The national age-by-sex CSV supplies the same-release all-age and ages 0–4 controls for each year. Its all-age row must also agree with its own complete age distribution. The official methodology describes controlling within the geographic and demographic hierarchy. [Release](https://www.census.gov/newsroom/press-releases/2025/intercensal-estimates-demographics.html), [methodology](https://www2.census.gov/programs-surveys/popest/technical-documentation/methodology/intercensal/2010-2020-intercensal-estimates-methodology.pdf), [state layout](https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2010-2020/intercensal/state/SC-EST2020INT-ALLDATA6.pdf), [national control layout](https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2010-2020/intercensal/national/NC-EST2020INT-AGESEX-RES.pdf), [Census state FIPS codes](https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html)

National sums can agree when counts move between states. With `--check-counties`, the build checks each state/DC against the sums of `POPESTIMATE` and `AGE04_TOT` in the separately published United States county age-by-sex file. It uses Census `YEAR` codes 5–11 for July 1, 2013–2019 and checks county-year uniqueness and coverage. This comparison uses a separate Census table from the same release and geography vintage. Both tables are from the same statistical program. The state and control source entries and staged receipts are tied to an explicit Census release ID. [County table catalogue](https://www.census.gov/data/tables/time-series/demo/popest/intercensal-2010-2020-counties-detail.html), [county file layout](https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2010-2020/intercensal/county/CC-EST2020INT-AGESEX.pdf)

The three same-release state age-by-sex workbooks were retrieved independently of the state CSV. Their July 1 `Total Population` columns, `Total` and `.Under 5 years` rows, match the state CSV for both counts on all 21 DC, New Jersey and New York dates. The check reads the existing state cells and produces a validation summary. [State age-by-sex workbooks](https://www.census.gov/data/tables/time-series/demo/popest/intercensal-2010-2020-state-detail.html).

### Puerto Rico

The September 30, 2025 Census release includes the commonwealth age-by-sex workbook and a separate municipio file. The workbook's both-sex totals use the July 1 columns and the `Total` and `.Under 5 years` rows. Both workbook appearances of the under-5 band agree. The municipio file contains `MUNICIPIO` and `NAME`. The workflow verifies these pairs against the independently retrieved 2020 Census FIPS 72 reference and requires `SUMLEV=050` and all 78 unique municipios in every target year. This honors the release's 2020 geographic boundaries. [Commonwealth workbook directory](https://www2.census.gov/programs-surveys/popest/tables/2010-2020/intercensal/puerto-rico/asrh/), [county and municipio layout](https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2010-2020/intercensal/county/CC-EST2020INT-AGESEX.pdf), [2020 FIPS 72 code list](https://www2.census.gov/geo/docs/reference/codes2020/cou/st72_pr_cou2020.txt).

| Census YEAR code | Reference date |
| ---: | --- |
| 5 | 2013-07-01 |
| 6 | 2014-07-01 |
| 7 | 2015-07-01 |
| 8 | 2016-07-01 |
| 9 | 2017-07-01 |
| 10 | 2018-07-01 |
| 11 | 2019-07-01 |

The official files produced 546 unique target municipio-years. `UNDER5_TOT` and `AGE04_TOT` agreed for every record in that window. The sums of `POPESTIMATE` and ages 0–4 matched the commonwealth workbook in persons for all seven dates. The output is a separate commonwealth series. U.S. Virgin Islands population remains outside the verified geography, so full HHS Region 2 population coverage remains open.

## Reproduce locally

Use Python 3.11 or later and install the workbook readers with `python3 -m pip install -r scripts/requirements-demography.txt`. [The source contract](../data/demographic-sources.toml) identifies the official tables, dates, vintages, units, and observed SHA-256 pins. The commands below use the default local Git-ignored paths. To keep files outside a checkout, pass `--cache-dir` before the subcommand and `--output` after either build.

```sh
for year in 2013 2014 2016-2019; do
    for part in age total national; do
        python3 scripts/demographic_sources.py stage "jp-$year-$part"
    done
done
for source in jp-2015-census jp-2015-single-age; do
    python3 scripts/demographic_sources.py stage "$source"
done
python3 scripts/check_population.py build-jp

for source in pr-commonwealth pr-municipios pr-municipio-codes; do
    python3 scripts/demographic_sources.py stage "$source"
done
python3 scripts/check_population.py build-pr

for source in us-states us-national-control us-county-control us-age-sex-11 us-age-sex-34 us-age-sex-36; do
    python3 scripts/demographic_sources.py stage "$source"
done
python3 scripts/demographic_sources.py build-us --check-counties
python3 scripts/check_population.py check-us-workbooks

python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

Run `stage --help` for the remaining source IDs. The `stage` command also accepts `--from-file PATH` for unchanged local bytes and marks the receipt `local_file`. It keeps original bytes and their JSON receipt together under `data/raw/demography/<source-id>/`. The receipt includes the byte count, SHA-256, capture time and method, requested URL, resolved download URL if present, available HTTP metadata, table/vintage, geography, source units, and reference dates. An observed checksum identifies the staged bytes. The optional `expected_sha256` field in the current contract determines whether the stage command checks and reports a pin. The receipt retains the pin setting at capture time. Rerunning `stage` for a cached source verifies its checksum and reports its original capture method. Use a separate cache to fetch fresh bytes or to re-stage a receipt that predates the contract release IDs. XLSX staging checks for a workbook and a linked worksheet. Japan spreadsheet entries also accept the legacy Excel file signature. [SpreadsheetML workbook structure](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/structure-of-a-spreadsheetml-document)

The builders recheck staged digests, layouts, geography coverage, and controls before writing atomically. The Japan and Puerto Rico outputs are `jp-population.csv` and `pr-population.csv` under `data/processed/demography/`. They record the age share, primary source metadata, and control receipt IDs, digests and capture methods. The US `us-states.csv` contains year, date, geography (`US-xx`, two-digit FIPS), name, counts in persons, a fraction for ages 0–4, universe, vintage, release date and ID, and input digests and capture methods. A build without `--check-counties` leaves the county provenance fields blank and establishes only national aggregate agreement. Raw and processed data live in Git-ignored directories.

The synthetic fixtures exercise the command-line workflow and rejection checks with generated data. In the earlier states/DC validation on department, the three official Census CSVs were staged with local SHA-256 receipts. The state and national files decoded as UTF-8, while the county file contained a legacy-encoded byte in Doña Ana County and is read as Windows-1252. The staged inputs passed `build-us --check-counties`, producing 357 state/DC–year rows and matching both the national and county controls for July 1, 2013–2019.

Will can reference the pinned Japan and Puerto Rico panels and documented US checks when locking the analysis input manifest. Record the rounded Japanese estimate precision and the US Virgin Islands coverage gap in that manifest.

## Natality follow-up

Audit natality as a separate source, retaining the birth event period and mother's geography of residence where available. For 2013–2019 CDC WONDER, Region 2 natality consists of New York and New Jersey. HHS Region 2 also includes Puerto Rico and the U.S. Virgin Islands. Audit the territorial releases separately before treating any birth aggregate as full HHS Region 2. For Japan, verify the Ministry of Health, Labour and Welfare Vital Statistics table's nationality coverage, whether prefecture refers to residence or occurrence, and whether counts include births abroad or foreign-national births in Japan. Document the selected release and its match to the population universe before deriving natality measures. [CDC WONDER natality geography](https://wonder.cdc.gov/wonder/help/natality.html), [HHS Region 2](https://www.hhs.gov/about/agencies/iea/regional-offices/region-2/index.html)
