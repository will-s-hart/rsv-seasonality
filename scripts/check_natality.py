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


def read_counts(path, year_controls, locations, measures):
    header = ["year", "month", "location_id", *measures]
    counts = {}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        if next(reader, None) != header:
            raise ValueError(f"{path}: expected header {','.join(header)}")
        for row in reader:
            line = f"{path}:{reader.line_num}"
            if len(row) != len(header):
                raise ValueError(f"{line}: expected {len(header)} columns")
            year, period, location, *values = row
            if year not in year_controls or period not in PERIODS or location not in locations:
                raise ValueError(f"{line}: unexpected year, month or location {row[:3]}")
            key = (year, period, location)
            if key in counts:
                raise ValueError(f"{line}: duplicate cell {key}")
            if any(not re.fullmatch(r"0|[1-9][0-9]*", value) for value in values):
                raise ValueError(f"{line}: expected nonnegative integer counts")
            totals = tuple(map(int, values))
            if len(totals) == 3 and totals[0] != totals[1] + totals[2]:
                raise ValueError(f"{line}: total differs from male plus female")
            counts[key] = totals
    return counts


def validate(path, country, manifest, confirm_japan_control_scope):
    japan = country == "japan"
    geography = PREFECTURES if japan else STATES_AND_DC
    measures = ("births", "male", "female") if japan else ("births",)
    expected_locations = geography | {"national"}
    if japan:
        expected_locations |= {"abroad"}
    controls = manifest[country]["years"]
    allowed_locations = expected_locations | {"unknown"} if japan else expected_locations
    counts = read_counts(path, controls, allowed_locations, measures)
    unknown_years = {year for year, _, location in counts if location == "unknown"}

    for year, control in controls.items():
        locations = expected_locations | {"unknown"} if year in unknown_years else expected_locations
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

    return sum(period in MONTHS and location in geography for _, period, location in counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("country", choices=("japan", "us"))
    parser.add_argument("extract", type=Path, help="normalized UTF-8 CSV")
    parser.add_argument(
        "--confirm-japan-control-scope",
        action="store_true",
        help="apply MHLW national controls after independently matching the source scope and vintage",
    )
    args = parser.parse_args()
    if args.country != "japan" and args.confirm_japan_control_scope:
        parser.error("--confirm-japan-control-scope applies only to Japan")
    try:
        with MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        months = validate(args.extract, args.country, manifest, args.confirm_japan_control_scope)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(f"Validated normalized {args.country} extract with {months:,} subnational months.")
    if args.country == "japan" and not args.confirm_japan_control_scope:
        print("Published MHLW national controls are pending source vintage and scope confirmation.")


if __name__ == "__main__":
    main()
