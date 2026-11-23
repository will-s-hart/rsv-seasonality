#!/usr/bin/env python3
"""Check published aggregate Japan NESID workbooks and CDC NREVSS data."""

import argparse
import csv
from collections import Counter
from contextlib import contextmanager
from datetime import date, timedelta
from math import isclose
from pathlib import Path
import re
from unicodedata import normalize


YEARS = range(2013, 2020)
RSV = "ＲＳウイルス感染症"
PEDIATRIC = "小児科定点"
TOTAL = "総　数"
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


@contextmanager
def workbook(directory, year, table):
    # Both formats occur in the published archive. Read cached cell values.
    if year == 2013:
        from xlrd import open_workbook

        book = open_workbook(directory / f"{year}-{table}.xls", on_demand=True)

        def read_rows(name, height):
            sheet = book.sheet_by_name(name)
            return [sheet.row_values(i) for i in range(min(height, sheet.nrows))]

        try:
            yield book.sheet_names(), read_rows
        finally:
            book.release_resources()
    else:
        from openpyxl import load_workbook

        book = load_workbook(directory / f"{year}-{table}.xlsx", read_only=True, data_only=True)
        try:
            yield book.sheetnames, lambda name, height: list(
                book[name].iter_rows(max_row=height, values_only=True)
            )
        finally:
            book.close()


def areas(rows):
    return [row[1] for row in rows]


def integer_counts(values, label, minimum=0):
    require(
        all(isinstance(n, (float, int)) and n >= minimum and n == int(n) for n in values),
        f"{label}: missing or invalid count",
    )
    return [int(n) for n in values]


def rsv_column(rows):
    columns = [i for i, value in enumerate(rows[4]) if str(value).startswith(RSV)]
    require(len(columns) <= 1, "Several RSV columns in one sheet")
    return columns[0] if columns else None


def check_nesid(directory):
    print("NESID year weeks cases zero_case_prefecture_weeks national_site_range under_2_pct")
    for year in YEARS:
        weeks = 53 if year == 2015 else 52
        with workbook(directory, year, "14-1") as (_, read_sites):
            sites = read_sites(PEDIATRIC, 53)
        # The English subtitle for 2015 week 53 repeats "week 52".
        site_weeks = [
            int(re.match(r"(\d+)週", normalize("NFKC", label))[1])
            for label in sites[4][3:] if label
        ]
        require(site_weeks == list(range(1, weeks + 1)), f"{year} sentinel week labels")
        places = areas(sites[5:53])
        require(len(set(places)) == 48 and "total No." in places[0], f"{year} geographies")

        with workbook(directory, year, "12-1") as (_, read_ages):
            ages = read_ages(RSV, 55)
        require(areas(ages[7:55]) == places, f"{year} age geographies")
        age_columns = [
            i for i, value in enumerate(ages[4]) if value and "No. of cases" in str(ages[5][i])
        ]
        age_counts = integer_counts([ages[7][i] for i in age_columns], f"{year} age bins")
        require(sum(age_counts[1:]) == age_counts[0], f"{year} age bins do not sum to total")
        under_two = sum(age_counts[1:4]) / age_counts[0]

        annual = Counter()
        national_sites = []
        zeros = 0
        with workbook(directory, year, "8-1") as (names, read_cases), workbook(
            directory, year, "8-2"
        ) as (rate_names, read_rates):
            require(names == rate_names and names[0] == TOTAL, f"{year} sheet names")
            sheet_weeks = [int(normalize("NFKC", name).removesuffix("週")) for name in names[1:]]
            require(sheet_weeks == list(range(1, weeks + 1)), f"{year} case week labels")
            for week, name in zip(sheet_weeks, names[1:]):
                label = f"{year} week {week}"
                cases = read_cases(name, 54)
                column = rsv_column(cases)
                require(column is not None, f"{label} RSV header")
                require(areas(cases[6:54]) == places, f"{label} case geographies")
                counts = integer_counts([row[column] for row in cases[6:54]], label)
                denominators = integer_counts([row[week + 2] for row in sites[5:53]], label, 1)
                require(counts[0] == sum(counts[1:]), f"{label} national case sum")
                require(denominators[0] == sum(denominators[1:]), f"{label} national site sum")
                annual.update(dict(zip(places, counts)))
                zeros += counts[1:].count(0)
                national_sites.append(denominators[0])

                rates = read_rates(name, 54)
                column = rsv_column(rates)
                require((column is not None) == (year >= 2018), f"{label} RSV rate header")
                if column is not None:
                    require(areas(rates[6:54]) == places, f"{label} rate geographies")
                    for row, count, denominator in zip(rates[6:54], counts, denominators):
                        require(
                            isclose(row[column], count / denominator, abs_tol=1e-10),
                            f"{label} {row[1]} published rate differs from cases/sites",
                        )

            totals = read_cases(TOTAL, 54)
            column = rsv_column(totals)
            require(column is not None, f"{year} annual RSV header")
            require(areas(totals[6:54]) == places, f"{year} annual geographies")
            for place, total_row, age_row in zip(places, totals[6:54], ages[7:55]):
                require(annual[place] == total_row[column] == age_row[2], f"{year} {place} annual total")

        if year == 2013:
            require(annual[places[0]] == 96_625, "2013 national total differs from official 96,625")
        site_range = f"{min(national_sites)}–{max(national_sites)}"
        print(year, weeks, annual[places[0]], zeros, site_range, f"{under_two:.1%}")


def check_nrevss(directory):
    # Independent expected grid from the source's Saturday-ending convention.
    first = date(2013, 1, 5)
    last = date(2019, 12, 28)
    weeks = {first + timedelta(days=day) for day in range(0, (last - first).days + 1, 7)}
    methods = ("PCR", "Antigen")
    groups = {(method, region): {} for method in methods for region in range(1, 11)}
    codes = {}
    export_rows = Counter()
    annual_tests = Counter()
    with (directory / "nrevss.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            method = row["testtype"]
            export_rows[method] += 1
            raw_date = row["repweekdate"]
            week_end = date(int(raw_date[5:]), MONTHS.index(raw_date[2:5]) + 1, int(raw_date[:2]))
            if not first <= week_end <= last:
                continue
            group = (method, int(row["hhs_region"]))
            label = f"{group} {week_end}"
            require(week_end in weeks and week_end not in groups[group], f"{label} invalid or duplicate week")
            code = row["repweekcode"]
            require(codes.setdefault(week_end, code) == code, f"{label} inconsistent week code")
            positive, tested, outlier = (int(row[field]) for field in ("rsvpos", "rsvtest", "outlier"))
            require(0 <= positive <= tested and outlier in (0, 1), f"{label} invalid counts or flag")
            groups[group][week_end] = positive, tested, outlier
            annual_tests[method, week_end.year] += tested

    print("NREVSS export rows", dict(export_rows))
    print("NREVSS method region rows missing zero_tests zero_positive_with_tests flagged min_tests max_tests")
    for (method, region), observations in groups.items():
        missing = sorted(weeks - observations.keys())
        empty = sorted(week for week, (_, tests, _) in observations.items() if tests == 0)
        if method == "PCR":
            require(not missing and not empty, f"PCR region {region} incomplete coverage")
        tests = [tested for _, tested, _ in observations.values()]
        zero_positive = sum(p == 0 and n > 0 for p, n, _ in observations.values())
        flags = sum(flag for _, _, flag in observations.values())
        print(
            method, region, len(observations), len(missing), len(empty), zero_positive, flags,
            min(tests), max(tests),
        )
        if missing:
            print("  missing week endings:", ", ".join(day.isoformat() for day in missing))
        if empty:
            print("  zero-test week endings:", ", ".join(day.isoformat() for day in empty))
    for method in methods:
        print(method, "reported tests by year of week ending", {
            year: annual_tests[method, year] for year in YEARS
        })
    print("NREVSS code/date year differences:", {
        day.isoformat(): code for day, code in sorted(codes.items()) if code[:2] != str(day.year)[2:]
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="local source directory from the audit note")
    args = parser.parse_args()
    check_nesid(args.directory)
    check_nrevss(args.directory)


if __name__ == "__main__":
    main()
