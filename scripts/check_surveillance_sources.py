#!/usr/bin/env python3
"""Check published aggregate Japan NESID workbooks and CDC NREVSS data."""

import argparse
import csv
from collections import Counter
from contextlib import contextmanager
from datetime import date, timedelta
from hashlib import sha256
from math import isclose
from pathlib import Path
import re
from unicodedata import normalize


YEARS = range(2013, 2020)
NESID_TABLES = ("8-1", "8-2", "12-1", "14-1")
CDC_EXPORT = "nrevss.csv"
MANIFEST = Path(__file__).with_name("surveillance_sources.sha256")
RSV = "ＲＳウイルス感染症"
PEDIATRIC = "小児科定点"
TOTAL = "総　数"
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()

# Japanese names and order follow e-Stat prefecture codes 01–47.
# The parenthesized names are the English labels in the NESID tables.
NESID_AREAS = ["総    数(total No.)"] + """
北海道(Hokkaido)
青森県(Aomori)
岩手県(Iwate)
宮城県(Miyagi)
秋田県(Akita)
山形県(Yamagata)
福島県(Fukushima)
茨城県(Ibaraki)
栃木県(Tochigi)
群馬県(Gunma)
埼玉県(Saitama)
千葉県(Chiba)
東京都(Tokyo)
神奈川県(Kanagawa)
新潟県(Niigata)
富山県(Toyama)
石川県(Ishikawa)
福井県(Fukui)
山梨県(Yamanashi)
長野県(Nagano)
岐阜県(Gifu)
静岡県(Shizuoka)
愛知県(Aichi)
三重県(Mie)
滋賀県(Shiga)
京都府(Kyoto)
大阪府(Osaka)
兵庫県(Hyogo)
奈良県(Nara)
和歌山県(Wakayama)
鳥取県(Tottori)
島根県(Shimane)
岡山県(Okayama)
広島県(Hiroshima)
山口県(Yamaguchi)
徳島県(Tokushima)
香川県(Kagawa)
愛媛県(Ehime)
高知県(Kochi)
福岡県(Fukuoka)
佐賀県(Saga)
長崎県(Nagasaki)
熊本県(Kumamoto)
大分県(Oita)
宮崎県(Miyazaki)
鹿児島県(Kagoshima)
沖縄県(Okinawa)
""".split()

AGE_TOTAL = "総 数(total No.)"
UNDER_TWO = ("~5ヶ月(~ 5 m.o.)", "~11ヶ月(~ 11 m.o.)", "1歳(1 y.o.)")
AGE_LABELS = {
    AGE_TOTAL, *UNDER_TWO, *(f"{age}歳({age} y.o.)" for age in range(2, 10)),
    "10~14歳(10~ 14 y.o.)", "15~19歳(15~ 19 y.o.)", "20歳~(20~ y.o.)",
}
CASE_COUNT = "報告数(No. of cases)"
BOTH_SEXES = "総数(total No.)"


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def workbook_name(year, table):
    extension = "xls" if year == 2013 else "xlsx"
    return f"{year}-{table}.{extension}"


def verify_inputs(directory, manifest=MANIFEST):
    expected_names = {workbook_name(year, table) for year in YEARS for table in NESID_TABLES}
    expected_names.add(CDC_EXPORT)
    digests = {}
    for number, line in enumerate(manifest.read_text(encoding="ascii").splitlines(), 1):
        entry = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        require(entry is not None, f"{manifest.name}:{number}: invalid SHA-256 entry")
        digest, name = entry.groups()
        require(name not in digests, f"{manifest.name}:{number}: duplicate file {name}")
        digests[name] = digest
    require(
        digests.keys() == expected_names,
        f"{manifest.name}: missing {sorted(expected_names - digests.keys())}, "
        f"unexpected {sorted(digests.keys() - expected_names)}",
    )
    for name, expected in digests.items():
        path = directory / name
        require(path.is_file(), f"{name}: missing source file")
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(128 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        require(
            actual == expected, f"{name}: SHA-256 mismatch (expected {expected}, got {actual})",
        )
    return len(digests)


def week_dates(week_end):
    return week_end - timedelta(days=6), week_end


def japan_week_dates(year, week):
    # JIHS diagnosis weeks follow the Monday–Sunday ISO week calendar.
    return week_dates(date.fromisocalendar(year, week, 7))


def mmwr_year_start(year):
    # CDC week 1 starts on the Sunday of the week containing January 4.
    jan4 = date(year, 1, 4)
    return jan4 - timedelta(days=(jan4.weekday() + 1) % 7)


def mmwr_week_code(week_end):
    require(week_end.weekday() == 5, f"{week_end}: report week must end on Saturday")
    # Wednesday is day four of a Sunday–Saturday week and determines its year.
    year = (week_end - timedelta(days=3)).year
    week = 1 + (week_end - mmwr_year_start(year)).days // 7
    return f"{year % 100:02d}{week:02d}"


@contextmanager
def workbook(directory, year, table):
    # Both formats occur in the published archive. Read cached cell values.
    path = directory / workbook_name(year, table)
    if year == 2013:
        from xlrd import open_workbook

        book = open_workbook(path, on_demand=True)

        def read_rows(name, height):
            sheet = book.sheet_by_name(name)
            return [sheet.row_values(i) for i in range(min(height, sheet.nrows))]

        try:
            yield book.sheet_names(), read_rows
        finally:
            book.release_resources()
    else:
        from openpyxl import load_workbook

        book = load_workbook(path, read_only=True, data_only=True)
        try:
            yield book.sheetnames, lambda name, height: list(
                book[name].iter_rows(max_row=height, values_only=True)
            )
        finally:
            book.close()


def check_areas(rows, label):
    require(len(rows) == len(NESID_AREAS), f"{label} geography: expected 48 area rows")
    for actual, expected in zip((row[1] for row in rows), NESID_AREAS):
        require(actual == expected, f"{label} geography: expected {expected!r}, got {actual!r}")


def check_ages(rows, label):
    columns = {}
    for index, (age, measure, sex) in enumerate(zip(*rows[4:7])):
        if not age and measure != CASE_COUNT:
            continue
        age_label = normalize("NFKC", str(age))
        require(age_label in AGE_LABELS, f"{label}: unexpected age label {age!r}")
        require(
            measure == CASE_COUNT and sex == BOTH_SEXES,
            f"{label}: invalid count header for {age!r}",
        )
        require(age_label not in columns, f"{label}: duplicate age label {age!r}")
        columns[age_label] = index
    require(
        columns.keys() == AGE_LABELS,
        f"{label}: missing age labels {sorted(AGE_LABELS - columns.keys())}",
    )
    counts = dict(zip(
        columns, integer_counts([rows[7][i] for i in columns.values()], label),
    ))
    total = counts.pop(AGE_TOTAL)
    require(total > 0 and sum(counts.values()) == total, f"{label}: bins do not sum to total")
    return columns[AGE_TOTAL], sum(counts[age] for age in UNDER_TWO) / total


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
        first_start, _ = japan_week_dates(year, 1)
        next_start, _ = japan_week_dates(year + 1, 1)
        weeks = (next_start - first_start).days // 7
        with workbook(directory, year, "14-1") as (_, read_sites):
            sites = read_sites(PEDIATRIC, 53)
        # The English subtitle for 2015 week 53 repeats "week 52".
        site_weeks = [
            int(re.match(r"(\d+)週", normalize("NFKC", label))[1])
            for label in sites[4][3:] if label
        ]
        require(site_weeks == list(range(1, weeks + 1)), f"{year} sentinel week labels")
        check_areas(sites[5:53], f"{year} sentinel")

        with workbook(directory, year, "12-1") as (_, read_ages):
            ages = read_ages(RSV, 55)
        check_areas(ages[7:55], f"{year} age")
        age_total_column, under_two = check_ages(ages, f"{year} age bins")

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
                check_areas(cases[6:54], f"{label} cases")
                counts = integer_counts([row[column] for row in cases[6:54]], label)
                denominators = integer_counts([row[week + 2] for row in sites[5:53]], label, 1)
                require(counts[0] == sum(counts[1:]), f"{label} national case sum")
                require(denominators[0] == sum(denominators[1:]), f"{label} national site sum")
                annual.update(dict(zip(NESID_AREAS, counts)))
                zeros += counts[1:].count(0)
                national_sites.append(denominators[0])

                rates = read_rates(name, 54)
                check_areas(rates[6:54], f"{label} rates")
                column = rsv_column(rates)
                require((column is not None) == (year >= 2018), f"{label} RSV rate header")
                if column is not None:
                    for row, count, denominator in zip(rates[6:54], counts, denominators):
                        require(
                            isclose(row[column], count / denominator, abs_tol=1e-10),
                            f"{label} {row[1]} published rate differs from cases/sites",
                        )

            totals = read_cases(TOTAL, 54)
            column = rsv_column(totals)
            require(column is not None, f"{year} annual RSV header")
            check_areas(totals[6:54], f"{year} annual cases")
            for place, total_row, age_row in zip(NESID_AREAS, totals[6:54], ages[7:55]):
                require(
                    annual[place] == total_row[column] == age_row[age_total_column],
                    f"{year} {place} annual total",
                )

        national_total = annual[NESID_AREAS[0]]
        if year == 2013:
            require(national_total == 96_625, "2013 national total differs from official 96,625")
        site_range = f"{min(national_sites)}–{max(national_sites)}"
        print(year, weeks, national_total, zeros, site_range, f"{under_two:.1%}")


def check_nrevss(directory):
    # Independent expected grid from CDC's MMWR week calendar.
    first = mmwr_year_start(YEARS.start) + timedelta(days=6)
    last = mmwr_year_start(YEARS.stop) - timedelta(days=1)
    weeks = {first + timedelta(days=day) for day in range(0, (last - first).days + 1, 7)}
    methods = ("PCR", "Antigen")
    groups = {(method, region): {} for method in methods for region in range(1, 11)}
    codes = {}
    export_rows = Counter()
    annual_tests = Counter()
    with (directory / CDC_EXPORT).open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            method = row["testtype"]
            export_rows[method] += 1
            raw_date = row["repweekdate"]
            require(
                re.fullmatch(r"[0-9]{2}[A-Z]{3}[0-9]{4}", raw_date),
                f"Invalid report date {raw_date!r}",
            )
            week_end = date(int(raw_date[5:]), MONTHS.index(raw_date[2:5]) + 1, int(raw_date[:2]))
            code = row["repweekcode"]
            expected = mmwr_week_code(week_end)
            require(code == expected, f"{raw_date}: expected MMWR week code {expected}, got {code!r}")
            if not first <= week_end <= last:
                continue
            group = (method, int(row["hhs_region"]))
            label = f"{group} {week_end}"
            require(week_end in weeks and week_end not in groups[group], f"{label} invalid or duplicate week")
            codes[week_end] = code
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
    print("NREVSS MMWR year differs from calendar year of week ending:", {
        day.isoformat(): code for day, code in sorted(codes.items()) if code[:2] != str(day.year)[2:]
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="local source directory from the audit note")
    args = parser.parse_args()
    verified = verify_inputs(args.directory)
    print(f"Verified SHA-256 digests for {verified} official inputs")
    check_nesid(args.directory)
    check_nrevss(args.directory)


if __name__ == "__main__":
    main()
