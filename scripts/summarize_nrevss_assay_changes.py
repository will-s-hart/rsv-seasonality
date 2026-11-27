#!/usr/bin/env python3
"""Compare adjacent calendar-year NREVSS PCR and antigen positivity changes."""

import argparse
from collections import Counter
import csv
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from statistics import mean
import sys

import check_surveillance_sources as audit
from summarize_nrevss_assays import MIN_TESTS, decimal, load_pinned_groups
from summarize_nrevss_weighting import calendar_weeks


FIELDS = (
    "year0", "year1", "min_tests_per_assay_year", "calendar_cells_year0",
    "calendar_cells_year1", "common_calendar_cells", "missing_cells", "zero_test_cells",
    "below_min_cells", "matched_cells_per_year", "matched_regions",
    *(f"{weighting}_{field}" for weighting in ("pooled", "equal") for field in (
        "pcr_change_pp", "antigen_change_pp", "antigen_minus_pcr_pp", "direction",
        "omit_same_direction", "omit_gap_min_pp", "omit_gap_max_pp",
    )),
)


def calendar_cells(groups, year, regions):
    return {
        (region, ordinal): tuple(groups[method, region].get(day) for method in audit.NREVSS_METHODS)
        for ordinal, day in enumerate(calendar_weeks(year), start=1)
        for region in regions
    }


def match_support(earlier, later, minimum):
    matched = {}
    losses = Counter()
    for key in sorted(earlier.keys() & later.keys()):
        rows = (*earlier[key], *later[key])
        if None in rows:
            losses["missing"] += 1
        elif any(row[1] == 0 for row in rows):
            losses["zero_tests"] += 1
        elif any(row[1] < minimum for row in rows):
            losses["below_min"] += 1
        else:
            matched[key] = rows
    return matched, losses


def changes(cells):
    pooled, equal = [], []
    # Column order is earlier PCR, earlier antigen, later PCR, later antigen.
    for column in zip(*cells):
        positives = sum(row[0] for row in column)
        tests = sum(row[1] for row in column)
        pooled.append(Fraction(positives, tests))
        equal.append(mean(Fraction(row[0], row[1]) for row in column))
    return {
        "pooled": (pooled[2] - pooled[0], pooled[3] - pooled[1]),
        "equal": (equal[2] - equal[0], equal[3] - equal[1]),
    }


def direction(pcr, antigen):
    if pcr == 0 or antigen == 0:
        return "zero"
    return "same" if (pcr > 0) == (antigen > 0) else "opposite"


def compare_pair(matched):
    regions = {region for region, _ in matched}
    if not regions:
        return {}
    full = changes(matched.values())
    omissions = [
        changes([cell for (region, _), cell in matched.items() if region != omitted])
        for omitted in regions
    ] if len(regions) > 1 else []
    result = {}
    for method, (pcr, antigen) in full.items():
        result.update({
            f"{method}_pcr_change_pp": decimal(100 * pcr),
            f"{method}_antigen_change_pp": decimal(100 * antigen),
            f"{method}_antigen_minus_pcr_pp": decimal(100 * (antigen - pcr)),
            f"{method}_direction": direction(pcr, antigen),
        })
        if omissions:
            outcomes = [omission[method] for omission in omissions]
            gaps = [antigen - pcr for pcr, antigen in outcomes]
            agreements = Counter(direction(pcr, antigen) for pcr, antigen in outcomes)
            result.update({
                f"{method}_omit_same_direction": agreements["same"],
                f"{method}_omit_gap_min_pp": decimal(100 * min(gaps)),
                f"{method}_omit_gap_max_pp": decimal(100 * max(gaps)),
            })
    return result


def annual_pairs(groups, years=audit.YEARS, regions=audit.HHS_REGIONS):
    for year0, year1 in pairwise(years):
        earlier = calendar_cells(groups, year0, regions)
        later = calendar_cells(groups, year1, regions)
        common = len(earlier.keys() & later.keys())
        for minimum in MIN_TESTS:
            matched, losses = match_support(earlier, later, minimum)
            yield {
                "year0": year0,
                "year1": year1,
                "min_tests_per_assay_year": minimum,
                "calendar_cells_year0": len(earlier),
                "calendar_cells_year1": len(later),
                "common_calendar_cells": common,
                "missing_cells": losses["missing"],
                "zero_test_cells": losses["zero_tests"],
                "below_min_cells": losses["below_min"],
                "matched_cells_per_year": len(matched),
                "matched_regions": len({region for region, _ in matched}),
                **compare_pair(matched),
            }


def write_summary(path, output):
    groups, _ = load_pinned_groups(path)
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(annual_pairs(groups))


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
