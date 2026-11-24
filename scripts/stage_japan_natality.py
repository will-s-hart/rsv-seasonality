#!/usr/bin/env python3
"""Normalize the pinned final Japan Table 2 CSVs and reconcile with Table 4-3."""

import argparse
import csv
import hashlib
import re
import tomllib
import unicodedata
from pathlib import Path

from check_natality import MANIFEST, MONTHS, PREFECTURES, parse_counts

SOURCE_PERIODS = ("annual", *MONTHS)
TABLE2_HEADER = ["", "総数", "", ""] + [
    value for month in MONTHS for value in (f"{int(month)}月", "", "")
]
SEX_HEADER = [""] + ["総数", "男", "女"] * len(SOURCE_PERIODS)
TABLE2_TITLES = {
    "中巻出生第2表出生数,性・出生月・市部-郡部(全国)・都道府県(21大都市再掲)別",
    "中巻出生第2表出生数,市部-郡部-都道府県(特別区-指定都市再掲)・出生月・性別",
}
TABLE43_TITLE = "上巻出生第4.3表都道府県別にみた年次別出生数"
JAPAN_LABELS = {"総数": "national", "全国": "national", "外国": "abroad"}
CITY_REPRINT_CODES = {f"{code:02d}" for code in range(50, 71)}
TABLE2_LOCATIONS = PREFECTURES | {"national", "abroad", "市部", "郡部"}


def compact(text):
    return "".join(unicodedata.normalize("NFKC", text).split())


def read_release(path, year, checksum):
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != checksum:
        raise ValueError(f"{path}: SHA-256 differs from the verified release")
    rows = list(csv.reader(source.decode("cp932").splitlines(), strict=True))
    era_year = f"平成{int(year) - 1988}年" if int(year) <= 2018 else "令和元年"
    if len(rows) < 2 or not rows[0] or rows[0][0] != era_year:
        raise ValueError(f"{path}: expected release year {year}")
    return rows


def prefecture_code(label):
    match = re.fullmatch(r"([0-9]{2})\D+", label)
    if match:
        return match[1]


def table2_counts(rows, path):
    if not rows[1] or compact(rows[1][0]) not in TABLE2_TITLES:
        raise ValueError(f"{path}: expected a final natality Table 2 birth-count title")
    headers = [index for index, row in enumerate(rows) if list(map(compact, row)) == TABLE2_HEADER]
    if (
        len(headers) != 1
        or headers[0] + 1 >= len(rows)
        or list(map(compact, rows[headers[0] + 1])) != SEX_HEADER
    ):
        raise ValueError(f"{path}: expected total and birth-month triplets in total, male, female order")
    counts = {}
    zero_markers = 0
    for line, row in enumerate(rows[headers[0] + 2 :], headers[0] + 3):
        if len(row) != len(SEX_HEADER):
            raise ValueError(f"{path}:{line}: wrong Table 2 row width")
        label, *values = row
        label = compact(label)
        code = prefecture_code(label)
        if code in CITY_REPRINT_CODES:
            continue
        location = JAPAN_LABELS.get(label, label if label in {"市部", "郡部"} else code)
        if location in counts or location not in TABLE2_LOCATIONS:
            raise ValueError(f"{path}:{line}: unexpected or duplicate Table 2 row {label!r}")
        values = [value.strip() for value in values]
        zero_markers += values.count("-")
        counts[location] = parse_counts(
            ["0" if value == "-" else value for value in values], f"{path}:{line}"
        )
    if missing := sorted(TABLE2_LOCATIONS - counts.keys()):
        raise ValueError(f"{path}: missing Table 2 geography {missing}")
    for index, (urban, rural) in enumerate(zip(counts.pop("市部"), counts.pop("郡部"), strict=True)):
        if urban + rural != sum(counts[code][index] for code in PREFECTURES):
            raise ValueError(f"{path}: city plus county disagrees with prefectures in column {index + 2}")
    return counts, zero_markers


def table43_counts(rows, path, year):
    if not rows[1] or compact(rows[1][0]) != TABLE43_TITLE:
        raise ValueError(f"{path}: expected the counts-only natality Table 4-3 title")
    headers = [
        index for index, row in enumerate(rows)
        if row[:1] == [""] and row[-1] == year and all(re.fullmatch(r"[0-9]{4}", c) for c in row[1:])
    ]
    if len(headers) != 1:
        raise ValueError(f"{path}: expected one annual Table 4-3 header ending in {year}")
    header = headers[0]
    counts = {}
    for line, row in enumerate(rows[header + 1 :], header + 2):
        if not any(row):
            continue
        label = compact(row[0])
        location = JAPAN_LABELS.get(label, prefecture_code(label))
        if location in counts or location not in PREFECTURES | {"national", "abroad"}:
            raise ValueError(f"{path}:{line}: unexpected or duplicate Table 4-3 row {label!r}")
        if len(row) != len(rows[header]):
            raise ValueError(f"{path}:{line}: wrong Table 4-3 row width")
        (counts[location],) = parse_counts([row[-1].strip()], f"{path}:{line}")
    return counts


def reconcile_annual(monthly, annual, year):
    if monthly.keys() != annual.keys():
        raise ValueError(f"{year}: Table 2 and Table 4-3 cover different locations")
    for location, counts in monthly.items():
        months = sum(counts[3::3])
        if months != counts[0] or months != annual[location]:
            raise ValueError(
                f"{year} {location}: Table 2 month sum {months}, annual {counts[0]}, "
                f"Table 4-3 {annual[location]}"
            )


def stage(source_dir, output_dir, sources):
    normalized = []
    residence = []
    zero_markers = 0
    for year, release in sorted(sources.items()):
        monthly_path = source_dir / f"jp-table2-{year}.csv"
        annual_path = source_dir / f"jp-table43-{year}.csv"
        monthly, markers = table2_counts(
            read_release(monthly_path, year, release["sha256"]), monthly_path
        )
        annual = table43_counts(
            read_release(annual_path, year, release["table43_sha256"]), annual_path, year
        )
        reconcile_annual(monthly, annual, year)
        zero_markers += markers
        for location, counts in sorted(monthly.items()):
            for index, period in enumerate(SOURCE_PERIODS):
                normalized.append((year, period, location, *counts[index * 3 : index * 3 + 3]))
        # The source audit established the residence categories for these pinned releases.
        residence.append(
            (year, release["stat_infid"], release["catalogue_updated"], "present", "absent")
        )

    output_dir.mkdir()
    outputs = (
        ("japan.csv", ("year", "month", "location_id", "births", "male", "female"), normalized),
        (
            "japan-residence-contract.csv",
            ("year", "stat_infid", "catalogue_updated", "abroad", "unknown"),
            residence,
        ),
    )
    for name, header, rows in outputs:
        with (output_dir / name).open("x", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)
    return len(sources) * len(PREFECTURES), zero_markers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="directory with the pinned original e-Stat CSVs")
    parser.add_argument("output_dir", type=Path, help="new directory for the normalized extract and contract")
    args = parser.parse_args()
    try:
        with MANIFEST.open("rb") as stream:
            sources = tomllib.load(stream)["japan"]["years"]
        controls, markers = stage(args.source_dir, args.output_dir, sources)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(f"Matched {controls:,} prefecture-years plus annual national and abroad rows to Table 4-3.")
    print(f"Normalized {markers} published Table 2 zero markers.")


if __name__ == "__main__":
    main()
