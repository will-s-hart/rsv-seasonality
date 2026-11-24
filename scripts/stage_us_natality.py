#!/usr/bin/env python3
"""Normalize the state/DC and national aggregate CDC WONDER natality exports."""

import argparse
import calendar
import csv
from pathlib import Path

from check_natality import MONTHS, STATES_AND_DC, parse_counts
from demographic_sources import STATE_NAMES

STATE_FIELDS = ("State", "State Code")
DATE_FIELDS = ("Year", "Year Code", "Month", "Month Code")
MONTH_NAMES = dict(zip((str(int(month)) for month in MONTHS), calendar.month_name[1:]))


def records(stream, path, by_state):
    header = ("Notes", *(STATE_FIELDS if by_state else ()), *DATE_FIELDS, "Births")
    reader = csv.reader(stream, delimiter="\t", strict=True)
    if tuple(next(reader, ())) != header:
        raise ValueError(f"{path}: unexpected WONDER columns")
    for line, row in enumerate(reader, 2):
        if row and row[0] == "---":
            return
        if not any(row):
            continue
        if len(row) != len(header):
            raise ValueError(f"{path}:{line}: unexpected WONDER row width")
        yield f"{path}:{line}", row
    raise ValueError(f"{path}: expected WONDER query notes after the table")


def read_export(path, by_state):
    counts = {}
    subtotal_checks = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for line, row in records(stream, path, by_state):
            kind, *fields, births = row
            location = "national"
            if by_state:
                name, location, *fields = fields
                if location and (
                    location not in STATES_AND_DC or STATE_NAMES[int(location)] != name
                ):
                    raise ValueError(f"{line}: unexpected state/DC name or FIPS")
                if not location and name:
                    raise ValueError(f"{line}: state name without a FIPS")
            year_name, year, month_name, month_code = fields
            (count,) = parse_counts([births], line)
            if count <= 9:
                raise ValueError(f"{line}: count outside the permitted aggregate export range")
            if year != year_name or (year and not year.isascii()) or (year and not year.isdecimal()):
                raise ValueError(f"{line}: inconsistent year and year code")
            if kind == "Total" and not month_name and not month_code:
                if not year:
                    subtotal_checks.append((location, count))
                    continue
                if not location:
                    raise ValueError(f"{line}: state/year subtotal without a FIPS")
                period = "annual"
            elif kind == "" and year and location and MONTH_NAMES.get(month_code) == month_name:
                period = month_code.zfill(2)
            else:
                raise ValueError(f"{line}: unexpected WONDER month or subtotal")
            key = year, period, location
            if key in counts:
                raise ValueError(f"{line}: duplicate WONDER row for {key}")
            counts[key] = count

    expected_subtotals = (STATES_AND_DC | {""}) if by_state else {"national"}
    totals = dict(subtotal_checks)
    annual = {key: count for key, count in counts.items() if key[1] == "annual"}
    if len(subtotal_checks) != len(totals) or totals.keys() != expected_subtotals:
        raise ValueError(f"{path}: missing or duplicate across-year WONDER totals")
    for location, count in totals.items():
        if count != sum(v for (_, _, code), v in annual.items() if not location or code == location):
            raise ValueError(f"{path}: across-year WONDER total disagrees for {location or 'all states/DC'}")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path, help="WONDER State, Year, Month export")
    parser.add_argument("national", type=Path, help="WONDER Year, Month export")
    parser.add_argument("output", type=Path, help="new normalized CSV")
    args = parser.parse_args()
    try:
        counts = read_export(args.state, True)
        counts.update(read_export(args.national, False))
        with args.output.open("x", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("year", "month", "location_id", "births"))
            writer.writerows((*key, value) for key, value in sorted(counts.items()))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    print(f"Normalized {len(counts):,} WONDER monthly and annual rows. Run check_natality.py to validate.")


if __name__ == "__main__":
    main()
