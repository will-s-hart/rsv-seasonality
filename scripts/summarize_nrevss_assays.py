#!/usr/bin/env python3
"""Summarize paired PCR and antigen positivity in the pinned historical CDC CSV."""

import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction
from hashlib import sha256
from io import StringIO
from pathlib import Path
from statistics import median, quantiles
import sys

import check_surveillance_sources as audit


SOURCE_ROWS = {"PCR": 5_210, "Antigen": 5_103}
MIN_TESTS = (1, 25, 100)
FIELDS = (
    "hhs_region", "mmwr_year", "min_tests_per_assay",
    "expected_weeks", "both_rows_present", "antigen_absent", "antigen_zero_tests",
    "both_tested", "pcr_only_below_min", "antigen_only_below_min", "both_below_min",
    "retained_pairs", "pcr_zero_positivity", "antigen_zero_positivity",
    "pcr_tests_min", "pcr_tests_median", "pcr_tests_max",
    "antigen_tests_min", "antigen_tests_median", "antigen_tests_max",
    "equal_test_counts", "pcr_more_tests", "median_pcr_to_antigen_test_ratio",
    "pcr_higher_positivity", "antigen_higher_positivity", "equal_positivity",
    "antigen_minus_pcr_pp_q25", "antigen_minus_pcr_pp_median", "antigen_minus_pcr_pp_q75",
)


def load_pinned_groups(path):
    # Hash and parse the same bytes, including any fields outside the audit window.
    data = path.read_bytes()
    expected = audit.load_pins()[audit.CDC_EXPORT]
    actual = sha256(data).hexdigest()
    audit.require(actual == expected, f"{path.name}: SHA-256 mismatch (expected {expected}, got {actual})")
    rows = list(csv.DictReader(StringIO(data.decode("utf-8"), newline="")))
    regions = {row["hhs_region"] for row in rows}
    audit.require(regions == {str(region) for region in audit.HHS_REGIONS}, "Unexpected CDC geography inventory")
    source_rows = Counter(row["testtype"] for row in rows)
    audit.require(source_rows == SOURCE_ROWS, f"Unexpected CDC assay inventory: {dict(source_rows)}")
    groups, codes, _ = audit.parse_nrevss(rows)
    return groups, codes


def decimal(value):
    return f"{float(value):.6f}"


def paired_summary(pairs, minimum):
    # Each pair shares an inclusive MMWR period and HHS region. The audited
    # parser requires a tested PCR row at every key, including antigen gaps.
    tested = [(pcr, antigen) for pcr, antigen in pairs if antigen is not None and antigen[1] > 0]
    below_min = Counter((pcr[1] < minimum, antigen[1] < minimum) for pcr, antigen in tested)
    retained = [(pcr, antigen) for pcr, antigen in tested if min(pcr[1], antigen[1]) >= minimum]
    result = {
        "expected_weeks": len(pairs),
        "both_rows_present": sum(antigen is not None for _, antigen in pairs),
        "antigen_absent": sum(antigen is None for _, antigen in pairs),
        "antigen_zero_tests": sum(antigen is not None and antigen[1] == 0 for _, antigen in pairs),
        "both_tested": len(tested),
        "pcr_only_below_min": below_min[True, False],
        "antigen_only_below_min": below_min[False, True],
        "both_below_min": below_min[True, True],
        "retained_pairs": len(retained),
        "pcr_zero_positivity": sum(pcr[0] == 0 for pcr, _ in retained),
        "antigen_zero_positivity": sum(antigen[0] == 0 for _, antigen in retained),
    }

    pcr_tests = [pcr[1] for pcr, _ in retained]
    antigen_tests = [antigen[1] for _, antigen in retained]
    ratios = [Fraction(pcr, antigen) for pcr, antigen in zip(pcr_tests, antigen_tests)]
    differences = [
        100 * (Fraction(antigen[0], antigen[1]) - Fraction(pcr[0], pcr[1]))
        for pcr, antigen in retained
    ]
    result.update(
        equal_test_counts=sum(ratio == 1 for ratio in ratios),
        pcr_more_tests=sum(ratio > 1 for ratio in ratios),
        pcr_higher_positivity=sum(delta < 0 for delta in differences),
        antigen_higher_positivity=sum(delta > 0 for delta in differences),
        equal_positivity=sum(delta == 0 for delta in differences),
    )
    if retained:
        quartiles = quantiles(differences, n=4, method="inclusive") if len(differences) > 1 else differences * 3
        q25, middle, q75 = quartiles
        result.update(
            pcr_tests_min=min(pcr_tests),
            pcr_tests_median=median(pcr_tests),
            pcr_tests_max=max(pcr_tests),
            antigen_tests_min=min(antigen_tests),
            antigen_tests_median=median(antigen_tests),
            antigen_tests_max=max(antigen_tests),
            median_pcr_to_antigen_test_ratio=decimal(median(ratios)),
            antigen_minus_pcr_pp_q25=decimal(q25),
            antigen_minus_pcr_pp_median=decimal(middle),
            antigen_minus_pcr_pp_q75=decimal(q75),
        )
    return result


def write_summary(path, output):
    groups, codes = load_pinned_groups(path)
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for region in audit.HHS_REGIONS:
        by_year = defaultdict(list)
        pcr = groups["PCR", region]
        antigen = groups["Antigen", region]
        for day in audit.nrevss_week_ends():
            year = 2000 + int(codes[day][:2])
            by_year[year].append((pcr[day], antigen.get(day)))
        all_weeks = [pair for pairs in by_year.values() for pair in pairs]
        for year, pairs in [("all", all_weeks), *by_year.items()]:
            for minimum in MIN_TESTS:
                writer.writerow({
                    "hhs_region": region,
                    "mmwr_year": year,
                    "min_tests_per_assay": minimum,
                    **paired_summary(pairs, minimum),
                })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="original nrevss.csv matching the repository SHA-256 pin")
    args = parser.parse_args()
    try:
        write_summary(args.csv, sys.stdout)
    except (OSError, ValueError, KeyError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
