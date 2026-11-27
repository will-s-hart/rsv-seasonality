#!/usr/bin/env python3
"""Decompose annual NREVSS PCR reported positivity on two supports."""

import argparse
import csv
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path
from statistics import mean
import sys

import check_surveillance_sources as audit
from summarize_nrevss_assays import decimal, load_pinned_groups


RATE_FIELDS = (
    "a_equal_week_region_pct", "b_pooled_week_equal_region_pct", "c_pooled_all_pct",
    "within_region_pp", "region_mix_pp", "total_gap_pp",
)
FIELDS = (
    "calendar_year", "support", "expected_weeks", "expected_region_weeks",
    "absent_rows", "zero_test_rows", "eligible_rows", "excluded_by_matching",
    "retained_rows", "retained_regions", "retained_zero_positive_rows", "retained_flagged_rows",
    "reported_detections", "reported_tests", *RATE_FIELDS,
)


def calendar_weeks(year):
    # Assign the whole Sunday–Saturday count to the year of its Saturday.
    january = date(year, 1, 1)
    first_saturday = january + timedelta(days=(5 - january.weekday()) % 7)
    days = (date(year + 1, 1, 1) - first_saturday).days
    return tuple(first_saturday + timedelta(days=offset) for offset in range(0, days, 7))


def eligible(row):
    return row is not None and row[1] > 0


def summarize_year(week_rows, support, ranks, *, exact=False):
    # Each position is the same Saturday ordinal across regions and years.
    source_rows = [row for weeks in week_rows for row in weeks]
    region_rows = [[row for rank, row in enumerate(weeks) if rank in ranks and eligible(row)]
                   for weeks in week_rows]
    region_rows = [rows for rows in region_rows if rows]
    retained = [row for rows in region_rows for row in rows]
    detections = sum(row[0] for row in retained)
    tests = sum(row[1] for row in retained)
    eligible_rows = sum(eligible(row) for row in source_rows)
    result = {
        "support": support,
        "expected_weeks": len(week_rows[0]),
        "expected_region_weeks": len(source_rows),
        "absent_rows": source_rows.count(None),
        "zero_test_rows": sum(row is not None and row[1] == 0 for row in source_rows),
        "eligible_rows": eligible_rows,
        "excluded_by_matching": eligible_rows - len(retained),
        "retained_rows": len(retained),
        "retained_regions": len(region_rows),
        "retained_zero_positive_rows": sum(row[0] == 0 for row in retained),
        "retained_flagged_rows": sum(row[2] for row in retained),
        "reported_detections": detections,
        "reported_tests": tests,
    }
    if tests:
        a = mean(mean(Fraction(p, n) for p, n, _ in rows) for rows in region_rows)
        b = mean(Fraction(sum(row[0] for row in rows), sum(row[1] for row in rows))
                 for rows in region_rows)
        c = Fraction(detections, tests)
        rates = (a, b, c, b - a, c - b, c - a)
        result.update({field: 100 * rate if exact else decimal(100 * rate)
                       for field, rate in zip(RATE_FIELDS, rates)})
    return result


def annual_summaries(pcr, years, *, exact=False):
    grids = {}
    for year in years:
        weeks = calendar_weeks(year)
        grids[year] = [[observations.get(day) for day in weeks] for observations in pcr]
    complete_ranks = [
        {rank for rank, rows in enumerate(zip(*grid)) if all(eligible(row) for row in rows)}
        for grid in grids.values()
    ]
    matched = set.intersection(*complete_ranks)
    for year, grid in grids.items():
        yield {"calendar_year": year,
               **summarize_year(grid, "baseline", range(len(grid[0])), exact=exact)}
        yield {"calendar_year": year, **summarize_year(grid, "matched", matched, exact=exact)}


def write_summary(path, output, *, exact=False):
    groups, _ = load_pinned_groups(path)
    pcr = [groups["PCR", region] for region in audit.HHS_REGIONS]
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(annual_summaries(pcr, audit.YEARS, exact=exact))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="original nrevss.csv matching the repository SHA-256 pin")
    parser.add_argument("--exact", action="store_true", help="write rates and gaps as rational numbers")
    args = parser.parse_args()
    try:
        write_summary(args.csv, sys.stdout, exact=args.exact)
    except (OSError, ValueError, KeyError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
