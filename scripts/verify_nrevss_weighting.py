#!/usr/bin/env python3
"""Independently replay the annual baseline decomposition with SQLite."""

import argparse
from contextlib import closing
import csv
from datetime import datetime
from hashlib import sha256
from io import StringIO
from math import isclose
from pathlib import Path
import sqlite3


SQL = """
WITH weighted AS (
    SELECT year, region, positives, tests,
           count(*) OVER regional AS weeks,
           sum(tests) OVER regional AS region_tests
    FROM pcr
    WINDOW regional AS (PARTITION BY year, region)
)
SELECT year, count(*), count(DISTINCT region), sum(positives), sum(tests),
       100 * sum(1.0 * positives / tests / weeks) / count(DISTINCT region),
       100 * sum(1.0 * positives / region_tests) / count(DISTINCT region),
       100.0 * sum(positives) / sum(tests)
FROM weighted
GROUP BY year
ORDER BY year
"""


def verify(source, summary):
    pin_file = Path(__file__).with_name("surveillance_sources.sha256")
    expected = {name: digest for digest, name in
                (line.split() for line in pin_file.read_text(encoding="ascii").splitlines())}["nrevss.csv"]
    data = source.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError("Source SHA-256 mismatch")

    rows = []
    for row in csv.DictReader(StringIO(data.decode("utf-8"), newline="")):
        if row["testtype"] != "PCR":
            continue
        ending = datetime.strptime(row["repweekdate"], "%d%b%Y").date()
        if 2013 <= ending.year <= 2019 and int(row["rsvtest"]) > 0:
            rows.append((ending.isoformat(), ending.year, row["hhs_region"], int(row["rsvpos"]), int(row["rsvtest"])))
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("""CREATE TABLE pcr (ending TEXT, year INTEGER, region TEXT,
                              positives INTEGER, tests INTEGER, PRIMARY KEY (ending, region))""")
        connection.executemany("INSERT INTO pcr VALUES (?, ?, ?, ?, ?)", rows)
        independent = connection.execute(SQL).fetchall()

    with summary.open(newline="", encoding="utf-8") as stream:
        baseline = [row for row in csv.DictReader(stream) if row["support"] == "baseline"]
    years = list(range(2013, 2020))
    if [int(row["calendar_year"]) for row in baseline] != years or [row[0] for row in independent] != years:
        raise ValueError("Expected one baseline result for every calendar year from 2013 through 2019")
    counts = ("retained_rows", "retained_regions", "reported_detections", "reported_tests")
    rates = ("a_equal_week_region_pct", "b_pooled_week_equal_region_pct", "c_pooled_all_pct",
             "within_region_pp", "region_mix_pp", "total_gap_pp")
    for reported, (year, cells, regions, detections, tests, a, b, c) in zip(baseline, independent):
        for field, actual in zip(counts, (cells, regions, detections, tests)):
            if int(reported[field]) != actual:
                raise ValueError(f"{year} {field} differs from the independent replay")
        for field, actual in zip(rates, (a, b, c, b - a, c - b, c - a)):
            if not isclose(float(reported[field]), actual, abs_tol=0.00000051, rel_tol=0):
                raise ValueError(f"{year} {field} differs from the independent replay")
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="original pinned nrevss.csv")
    parser.add_argument("summary", type=Path, help="annual weighting CSV")
    args = parser.parse_args()
    try:
        digest = verify(args.source, args.summary)
    except (OSError, ValueError, KeyError, csv.Error, sqlite3.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(f"Verified SHA-256 {digest} and annual baseline counts and decomposition for all seven years")


if __name__ == "__main__":
    main()
