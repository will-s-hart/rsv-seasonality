#!/usr/bin/env python3
"""Compare provisional source-week labels with complete observation intervals."""

import argparse
from collections import Counter
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import sys


LABEL_YEARS = {"train": (2013, 2016), "tune": (2017, 2017), "holdout": (2018, 2019)}
ROW_FIELDS = (
    "source_id", "source_calendar", "source_week_year", "source_week_code",
    "week_start", "week_end", "region_id", "method", "coverage",
)
CONTRIBUTOR_FIELDS = ("interval_kind", "contributor_start", "contributor_end")
COUNT_FIELDS = (
    "source_id", "method", "coverage", "label_period", "strict_period", "strict_status",
)


def parse_date(value):
    day = date.fromisoformat(value)
    if day.isoformat() != value:
        raise ValueError(f"expected a YYYY-MM-DD date, got {value!r}")
    return day


def compare_row(row, periods, window_start, period_ends):
    source_year = int(row["source_week_year"])
    start = parse_date(row["week_start"])
    end = parse_date(row["week_end"])
    if end < start:
        raise ValueError("week_end precedes week_start")

    contributor_metadata = {}
    if "interval_kind" in row:
        interval_kind, contributor_start, contributor_end = (
            row[field] for field in CONTRIBUTOR_FIELDS
        )
        contributor_metadata["interval_kind"] = interval_kind
        if interval_kind == "derived":
            if not contributor_start or not contributor_end:
                raise ValueError("derived observations require contributor_start and contributor_end")
            first = parse_date(contributor_start)
            last = parse_date(contributor_end)
            if last < first:
                raise ValueError("contributor_end precedes contributor_start")
            if first > start or last < end:
                raise ValueError("contributor interval must contain the labeled week")
            start, end = first, last
            contributor_metadata.update(
                contributor_start=contributor_start, contributor_end=contributor_end,
            )
        elif interval_kind == "raw":
            if contributor_start or contributor_end:
                raise ValueError("raw observations require blank contributor dates")
        else:
            raise ValueError("interval_kind must be raw or derived")

    label_period = next(
        (name for name, (first, last) in LABEL_YEARS.items() if first <= source_year <= last),
        None,
    )
    strict_period = next(
        (name for name, first, last in periods if first <= start and end <= last),
        None,
    )
    crossings = ["window_start"] if start < window_start <= end else []
    crossings.extend(name for name, cutoff in period_ends.items() if start <= cutoff < end)
    if crossings:
        status = "crosses_cutoff"
    elif strict_period is None:
        status = "outside_window"
    else:
        status = "assigned"

    return {
        **{field: row[field] for field in ROW_FIELDS},
        **contributor_metadata,
        "label_period": label_period,
        "strict_period": strict_period,
        "strict_status": status,
        "crossed_cutoffs": crossings,
        "assignments_differ": label_period != strict_period,
    }


def report(stream, window_start, train_through, tune_through, holdout_through):
    periods = (
        ("train", window_start, train_through),
        ("tune", train_through + timedelta(days=1), tune_through),
        ("holdout", tune_through + timedelta(days=1), holdout_through),
    )
    period_ends = {
        "train_through": train_through, "tune_through": tune_through,
        "holdout_through": holdout_through,
    }
    reader = csv.DictReader(stream, strict=True)
    fields = reader.fieldnames or []
    field_set = set(fields)
    missing = sorted(set(ROW_FIELDS) - field_set)
    if missing:
        raise ValueError(f"missing calendar columns: {', '.join(missing)}")
    if len(field_set) != len(fields):
        raise ValueError("duplicate CSV column names")

    expected_fields = ROW_FIELDS
    count_fields = COUNT_FIELDS
    if set(CONTRIBUTOR_FIELDS) & field_set:
        missing = sorted(set(CONTRIBUTOR_FIELDS) - field_set)
        if missing:
            raise ValueError(f"missing contributor columns: {', '.join(missing)}")
        expected_fields += CONTRIBUTOR_FIELDS
        count_fields += ("interval_kind",)

    counts = Counter()
    affected = []
    for row in reader:
        if None in row or any(row[field] is None for field in expected_fields):
            raise ValueError(f"CSV line {reader.line_num}: malformed row")
        try:
            comparison = compare_row(row, periods, window_start, period_ends)
        except ValueError as error:
            raise ValueError(f"CSV line {reader.line_num}: {error}") from error
        counts[tuple(comparison[field] for field in count_fields)] += 1
        if comparison["strict_period"] is None or comparison["assignments_differ"]:
            affected.append(comparison)

    return {
        "label_years_inclusive": LABEL_YEARS,
        "interval_cutoffs_inclusive": {
            "window_start": window_start.isoformat(),
            **{name: cutoff.isoformat() for name, cutoff in period_ends.items()},
        },
        "period_end_availability": "unknown_from_observation_dates_and_source_vintage",
        "rows_examined": sum(counts.values()),
        "comparison_counts": [
            {**dict(zip(count_fields, fields)), "rows": count} for fields, count in counts.items()
        ],
        "affected_rows": affected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="weekly observations CSV with optional contributor metadata")
    parser.add_argument("--window-start", type=parse_date, required=True, help="first training date")
    parser.add_argument("--train-through", type=parse_date, required=True, help="last training date")
    parser.add_argument("--tune-through", type=parse_date, required=True, help="last tuning date")
    parser.add_argument("--holdout-through", type=parse_date, required=True, help="last holdout date")
    args = parser.parse_args()
    if not args.window_start <= args.train_through < args.tune_through < args.holdout_through:
        parser.error("expected window start <= train cutoff < tune cutoff < holdout cutoff")

    try:
        with args.csv_path.open(encoding="utf-8", newline="") as stream:
            comparison = report(
                stream, args.window_start, args.train_through, args.tune_through, args.holdout_through,
            )
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))

    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(comparison, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
