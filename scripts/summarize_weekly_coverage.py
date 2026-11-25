#!/usr/bin/env python3
"""Summarize coverage and flags in the exported weekly observation CSV."""

import argparse
from collections import Counter, defaultdict
import csv
from pathlib import Path
from statistics import median
import sys


GROUP_FIELDS = ("source_id", "method", "region_id", "source_week_year", "denominator_kind")
KEY_FIELDS = GROUP_FIELDS[:4] + ("source_week_code",)
INPUT_FIELDS = (*KEY_FIELDS, "denominator_kind", "coverage", "count", "denominator",
                "source_outlier", "positivity")
OUTPUT_FIELDS = (*GROUP_FIELDS, "input_rows", "present_rows", "absent_rows", "zero_reports",
                 "tested_rows", "zero_test_rows", "zero_detection_rows", "flagged_tested_rows",
                 "flagged_zero_test_rows", "positive_denominator_min",
                 "positive_denominator_median", "positive_denominator_max")


def coverage_state(row):
    source, method, kind = (row[field] for field in ("source_id", "method", "denominator_kind"))
    japan = (source, method, kind) == ("NESID", "", "paediatric_sentinel_sites")
    us = source == "NREVSS:52kb-ccu2" and method in ("PCR", "Antigen") and kind == "reported_tests"
    if not (japan or us):
        raise ValueError("unexpected source, method or denominator kind")

    coverage, count, denominator, flag, positivity = (
        row[field] for field in ("coverage", "count", "denominator", "source_outlier", "positivity")
    )
    if coverage == "absent":
        if method != "Antigen" or any((count, denominator, flag, positivity)):
            raise ValueError("expected an absent antigen row with empty observation fields")
        return "absent", None, None
    if coverage != "present":
        raise ValueError(f"unexpected coverage {coverage!r}")

    count, denominator = int(count), int(denominator)
    if japan:
        if count < 0 or denominator <= 0 or flag or positivity:
            raise ValueError("invalid NESID cases, site count, flag or positivity")
        return "reported", count, denominator

    if not 0 <= count <= denominator or flag not in ("0", "1"):
        raise ValueError("invalid NREVSS detections, test count or outlier flag")
    if denominator == 0:
        if positivity:
            raise ValueError("expected empty positivity for a zero-test week")
        return "zero_test", count, denominator
    if float(positivity) != count / denominator:
        raise ValueError("positivity disagrees with detections divided by tests")
    return "tested", count, denominator


def summarize(stream):
    reader = csv.DictReader(stream, strict=True)
    fields = reader.fieldnames or []
    missing = sorted(set(INPUT_FIELDS) - set(fields))
    if missing:
        raise ValueError(f"missing weekly observation columns: {', '.join(missing)}")
    if len(set(fields)) != len(fields):
        raise ValueError("duplicate CSV column names")

    seen = set()
    groups = defaultdict(Counter)
    denominators = defaultdict(list)
    for row in reader:
        if None in row or None in row.values():
            raise ValueError(f"CSV line {reader.line_num}: malformed row")
        key = tuple(row[field] for field in KEY_FIELDS)
        if any(not row[field] for field in ("region_id", "source_week_year", "source_week_code")):
            raise ValueError(f"CSV line {reader.line_num}: missing observation key field")
        if key in seen:
            raise ValueError(f"CSV line {reader.line_num}: duplicate observation key {key}")
        seen.add(key)
        try:
            state, count, denominator = coverage_state(row)
        except ValueError as error:
            raise ValueError(f"CSV line {reader.line_num}: {error}") from error
        group = tuple(row[field] for field in GROUP_FIELDS)
        counts = groups[group]
        counts[state] += 1
        if row["source_outlier"] == "1":
            counts[f"{state}_flagged"] += 1
        if denominator is not None and denominator > 0:
            denominators[group].append(denominator)
            if count == 0:
                counts[f"{state}_zeros"] += 1

    if not groups:
        raise ValueError("no weekly observation rows")

    for group, counts in sorted(groups.items()):
        japan = group[0] == "NESID"
        present = counts["reported"] + counts["tested"] + counts["zero_test"]
        positive = denominators[group]
        yield (*group, present + counts["absent"], present, counts["absent"],
               counts["reported_zeros"] if japan else None,
               None if japan else counts["tested"], None if japan else counts["zero_test"],
               None if japan else counts["tested_zeros"], None if japan else counts["tested_flagged"],
               None if japan else counts["zero_test_flagged"], min(positive, default=None),
               median(positive) if positive else None, max(positive, default=None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="weekly observations CSV from the exporter")
    args = parser.parse_args()

    try:
        with args.csv_path.open(encoding="utf-8", newline="") as stream:
            rows = list(summarize(stream))
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(OUTPUT_FIELDS)
    writer.writerows(rows)


if __name__ == "__main__":
    main()
