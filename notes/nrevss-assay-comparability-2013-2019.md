# Paired PCR and antigen positivity in historical NREVSS

The 2022 historical CDC public-use release `52kb-ccu2` contains 10,313 rows across HHS Regions 1–10, with 5,210 PCR rows and 5,103 antigen rows. Its sole assay pair is PCR versus antigen. The file has no national series, so a separate US-wide contrast is unavailable from this pin. A sum of regional counts would have unknown national coverage, and national and regional aggregates with overlapping reporting populations would not be independent. The catalogue publication and row update both date to 21 October 2022. The exact revision and original retrieval dates of the pinned CSV remain unverified. [CDC catalogue and field metadata](https://data.cdc.gov/api/views/52kb-ccu2), [US release provenance](surveillance-audit-2013-2019.md#us-release-provenance).

## Available evidence

The [pinned department replay](weekly-reporting-qa-2013-2019.md#25-november-2026-reproducibility-record) and [source audit](surveillance-audit-2013-2019.md#us-historical-nrevss) establish the comparison universe. All 3,650 expected 2013–2019 HHS-region reporting weeks have a PCR row with positive tests. Antigen has a source row for 3,569 of those keys. The 81 missing antigen rows represent structural absence from the extract, with no documented cause. Eight source-present antigen rows have zero tests. The available evidence therefore yields **3,561 eligible region-week pairs (97.6%)** before any additional minimum-testing threshold. Positivity is undefined for absent and zero-test rows. A row with tests and zero positives contributes true zero reported positivity.

Cloud access to the pinned CDC CSV download returned HTTP 403, and the original bytes were absent from the Cloud workspace. The counts above follow from the earlier pinned audits. The paired positivity differences, denominator imbalances within pairs and threshold-specific retention remain unmeasured here. The fixture results describe invented rows.

## Comparison and replay

Match the two source rows on HHS region and the same inclusive Sunday–Saturday MMWR reporting period, within source week years 2013–2019. For every retained pair, subtract PCR detections per PCR test from antigen detections per antigen test and express the difference in percentage points. Every pair has equal weight in the median and quartiles within its HHS region and time stratum. Quartiles use inclusive linear interpolation of the ordered differences. Keep each region separate and inspect both its full-window and MMWR-year summaries. The year strata show when incomplete coverage changes which weeks can contribute.

The minimum-testing checks require at least **1, 25 or 100 tests in each assay**. One test is the baseline for a defined rate. The two higher round numbers probe the effect of progressively dropping thin aggregates and carry no project screening recommendation. The summary shows how many tested pairs fall below each minimum for PCR only, antigen only or both. It retains source-flagged rows alongside the other observations. For retained pairs it shows the number with true zero positivity, the direction of paired differences, each assay's minimum, median and maximum test counts, the median paired PCR-to-antigen test-count ratio, and how often test counts are equal or larger for PCR. Distribution summaries are blank when no pairs qualify. Counts are zero where the corresponding set is empty.

On department, use the original CDC file from the preserved surveillance cache. Run from the repository checkout and write the result to a new file in a private scratch directory.

```sh
report_dir=$(mktemp -d)
python3 -B scripts/summarize_nrevss_assays.py "$PINNED_SURVEILLANCE_DIR/nrevss.csv" \
    > "$report_dir/nrevss-assay-comparability.csv"
```

The command accepts the existing CDC SHA-256 pin and validates the release's known geography and method inventory before writing to stdout. It needs only the CDC file and the Python standard library. For a replay, reconcile the full-window baseline rows against 3,569 source-present and 3,561 tested pairs across the ten regions. Record the input digest and code commit with the output. Retain the output under the project's [result conventions](../results/README.md).

The comparison describes positivity among the tests reported to each diagnostic stream. A matched geography and week can contain different providers, patients and specimens. Lab overlap, repeat specimens and the tested populations are unobserved. Even identical reported test totals leave overlap unknown. The summaries support descriptive comparisons of the aggregate streams and reveal unequal volumes and changes in the retained set. Assay effects, individual diagnostic performance and underlying infection trends are unidentified by these data. [CDC field definitions and surveillance limitations](https://data.cdc.gov/api/views/52kb-ccu2).
