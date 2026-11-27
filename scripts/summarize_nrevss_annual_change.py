#!/usr/bin/env python3
"""Decompose adjacent calendar-year changes in pooled NREVSS PCR positivity."""

import argparse
import csv
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
import sys

import check_surveillance_sources as audit
from summarize_nrevss_assays import decimal, load_pinned_groups
from summarize_nrevss_weighting import calendar_weeks


def calendar_year_cells(groups):
    by_year = {}
    for year in audit.YEARS:
        weeks = calendar_weeks(year)
        by_year[year] = {
            (region, ordinal): groups["PCR", region][saturday][:2]
            for region in audit.HHS_REGIONS
            for ordinal, saturday in enumerate(weeks, start=1)
        }
    return by_year


def pooled(cells):
    positives, tests = zip(*cells)
    return Fraction(sum(positives), sum(tests))


def matched_effects(earlier, later, keys):
    before = [earlier[key] for key in keys]
    after = [later[key] for key in keys]
    tests_before = sum(tests for _, tests in before)
    tests_after = sum(tests for _, tests in after)
    cell_change = mix_change = equal_change = Fraction(0)
    for (positive0, tests0), (positive1, tests1) in zip(before, after):
        p0, p1 = Fraction(positive0, tests0), Fraction(positive1, tests1)
        share0, share1 = Fraction(tests0, tests_before), Fraction(tests1, tests_after)
        cell_change += (share0 + share1) * (p1 - p0) / 2
        mix_change += (p0 + p1) * (share1 - share0) / 2
        equal_change += p1 - p0

    pooled_change = pooled(after) - pooled(before)
    audit.require(cell_change + mix_change == pooled_change, "Decomposition does not sum to pooled change")
    return {
        "matched_pooled": pooled_change,
        "cell_positivity": cell_change,
        "test_mix": mix_change,
        "equal_weight": equal_change / len(keys),
    }


def annual_pairs(by_year):
    support = sorted(set.intersection(*(set(cells) for cells in by_year.values())))
    regions = sorted({region for region, _ in support})
    audit.require(len(regions) >= 2, "Balanced support needs at least two regions")
    omitted = [[key for key in support if key[0] != region] for region in regions]
    for year0, year1 in pairwise(sorted(by_year)):
        earlier, later = by_year[year0], by_year[year1]
        matched = matched_effects(earlier, later, support)
        leave_one_out = [matched_effects(earlier, later, keys) for keys in omitted]
        ranges = {}
        for field in ("matched_pooled", "cell_positivity", "test_mix"):
            values = [effects[field] for effects in leave_one_out]
            ranges[f"omit_one_{field}_min"] = min(values)
            ranges[f"omit_one_{field}_max"] = max(values)
        yield {
            "year0": year0,
            "year1": year1,
            "matched_cells_per_year": len(support),
            "full_cells_year0": len(earlier),
            "full_cells_year1": len(later),
            "full_pooled": pooled(later.values()) - pooled(earlier.values()),
            **matched,
            **ranges,
        }


def write_summary(path, output):
    groups, _ = load_pinned_groups(path)
    rows = [
        {
            f"{field}_pp" if isinstance(value, Fraction) else field:
            decimal(100 * value) if isinstance(value, Fraction) else value
            for field, value in pair.items()
        }
        for pair in annual_pairs(calendar_year_cells(groups))
    ]
    writer = csv.DictWriter(output, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)


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
