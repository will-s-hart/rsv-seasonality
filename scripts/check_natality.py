#!/usr/bin/env python3
"""Check normalized monthly natality aggregates and their annual controls."""

import argparse
import csv
import re
import tomllib
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / "data" / "natality-sources.toml"
PREFECTURES = set(f"{code:02d}" for code in range(1, 48))
STATES_AND_DC = set(
    "01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 "
    "25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 "
    "47 48 49 50 51 53 54 55 56".split()
)
MONTHS = tuple(f"{month:02d}" for month in range(1, 13))
PERIODS = (*MONTHS, "annual")
JAPAN_BUCKETS = ("abroad", "unknown")


def read_rows(path, header):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        if next(reader, None) != header:
            raise ValueError(f"{path}: expected header {','.join(header)}")
        for row in reader:
            line = f"{path}:{reader.line_num}"
            if len(row) != len(header):
                raise ValueError(f"{line}: expected {len(header)} columns")
            yield line, row


def parse_counts(values, line):
    if any(not re.fullmatch(r"0|[1-9][0-9]*", value) for value in values):
        raise ValueError(f"{line}: expected nonnegative integer counts")
    return tuple(map(int, values))


def read_counts(path, locations_by_year, measures):
    header = ["year", "month", "location_id", *measures]
    counts = {}
    for line, row in read_rows(path, header):
        year, period, location, *values = row
        if (
            year not in locations_by_year
            or period not in PERIODS
            or location not in locations_by_year[year]
        ):
            raise ValueError(f"{line}: unexpected year, month or location {row[:3]}")
        key = (year, period, location)
        if key in counts:
            raise ValueError(f"{line}: duplicate cell {key}")
        totals = parse_counts(values, line)
        if len(totals) == 3 and totals[0] != totals[1] + totals[2]:
            raise ValueError(f"{line}: total differs from male plus female")
        counts[key] = totals
    return counts


def read_japan_residence_contract(path, sources):
    header = ["year", "stat_infid", "catalogue_updated", *JAPAN_BUCKETS]
    buckets = {}
    for line, (year, table_id, updated, *statuses) in read_rows(path, header):
        if year not in sources or year in buckets:
            raise ValueError(f"{line}: unexpected or duplicate contract year {year}")
        source = sources[year]
        if table_id != source["stat_infid"] or updated != source["catalogue_updated"].isoformat():
            raise ValueError(f"{line}: Japan Table 2 file ID or catalogue update differs from the manifest")
        if any(status not in {"present", "absent"} for status in statuses):
            raise ValueError(f"{line}: declare each residence bucket as present or absent")
        buckets[year] = {name for name, status in zip(JAPAN_BUCKETS, statuses) if status == "present"}
    if missing := sorted(sources.keys() - buckets.keys()):
        raise ValueError(f"{path}: missing Japan residence contract years {', '.join(missing)}")
    return buckets


def read_us_annual_controls(path, sources):
    header = ["year", "location_id", "births", "report_url", "residence_table"]
    controls = {}
    for line, (year, location, value, report_url, table) in read_rows(path, header):
        if year not in sources or location not in STATES_AND_DC:
            raise ValueError(f"{line}: unexpected US annual control key {(year, location)}")
        key = (year, location)
        if key in controls:
            raise ValueError(f"{line}: duplicate US annual control {key}")
        source = sources[year]
        if report_url != source["report_url"] or table != str(source["residence_table"]):
            raise ValueError(f"{line}: US annual control report URL or table differs from the manifest")
        (births,) = parse_counts((value,), line)
        controls[key] = births
    missing = sorted(
        (year, location)
        for year in sources
        for location in STATES_AND_DC
        if (year, location) not in controls
    )
    if missing:
        raise ValueError(f"{path}: missing {len(missing)} US annual controls, first is {missing[0]}")
    return controls


def validate(path, country, manifest, reference_path, confirm_japan_control_scope):
    japan = country == "japan"
    geography = PREFECTURES if japan else STATES_AND_DC
    measures = ("births", "male", "female") if japan else ("births",)
    expected_locations = geography | {"national"}
    controls = manifest[country]["years"]
    if japan:
        buckets = read_japan_residence_contract(reference_path, controls)
        locations_by_year = {year: expected_locations | buckets[year] for year in controls}
    else:
        state_controls = read_us_annual_controls(reference_path, controls)
        locations_by_year = dict.fromkeys(controls, expected_locations)
    counts = read_counts(path, locations_by_year, measures)

    for year, control in controls.items():
        locations = locations_by_year[year]
        missing = sorted(
            (year, period, location)
            for period in PERIODS
            for location in locations
            if (year, period, location) not in counts
        )
        if missing:
            raise ValueError(f"missing {len(missing)} cells in {year}, first is {missing[0]}")

        components = sorted(locations - {"national"})
        for index, measure in enumerate(measures):
            for location in sorted(locations):
                annual = counts[year, "annual", location][index]
                summed = sum(counts[year, month, location][index] for month in MONTHS)
                if annual != summed:
                    raise ValueError(
                        f"{year} {location} {measure}: months sum to {summed}, annual is {annual}"
                    )
            for period in PERIODS:
                national = counts[year, period, "national"][index]
                summed = sum(counts[year, period, location][index] for location in components)
                if national != summed:
                    raise ValueError(
                        f"{year} {period} {measure}: residence components sum to {summed}, "
                        f"national is {national}"
                    )

        if not japan or confirm_japan_control_scope:
            annual_births = counts[year, "annual", "national"][0]
            published = control["national_births"]
            if annual_births != published:
                raise ValueError(f"{year}: annual national births {annual_births}, published {published}")

        if not japan:
            for location in components:
                annual_births = counts[year, "annual", location][0]
                published = state_controls[year, location]
                if annual_births != published:
                    raise ValueError(
                        f"{year} {location}: annual births {annual_births}, "
                        f"independent state/DC control {published}"
                    )

    return sum(period in MONTHS and location in geography for _, period, location in counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("country", choices=("japan", "us"))
    parser.add_argument("extract", type=Path, help="normalized UTF-8 CSV")
    parser.add_argument("--japan-residence-contract", type=Path, help="Japan vintage and bucket CSV")
    parser.add_argument("--us-annual-controls", type=Path, help="independent US annual state/DC CSV")
    parser.add_argument(
        "--confirm-japan-control-scope",
        action="store_true",
        help="apply MHLW national controls after independently matching the source scope and vintage",
    )
    args = parser.parse_args()
    if args.country == "japan":
        if args.japan_residence_contract is None or args.us_annual_controls is not None:
            parser.error("japan requires --japan-residence-contract and accepts only Japan options")
        reference_path = args.japan_residence_contract
    else:
        if (
            args.us_annual_controls is None
            or args.japan_residence_contract is not None
            or args.confirm_japan_control_scope
        ):
            parser.error("us requires --us-annual-controls and accepts only US options")
        reference_path = args.us_annual_controls
    try:
        with MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        months = validate(
            args.extract, args.country, manifest, reference_path, args.confirm_japan_control_scope
        )
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(f"Validated normalized {args.country} extract with {months:,} subnational months.")
    if args.country == "japan" and not args.confirm_japan_control_scope:
        print("Published MHLW national controls are pending source vintage and scope confirmation.")


if __name__ == "__main__":
    main()
