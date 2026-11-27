#!/usr/bin/env python3
"""Bound annual Japan reports per sentinel-site week using the committed audit."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor
from pathlib import Path
import re

from check_surveillance_sources import YEARS, japan_week_dates


AUDIT = Path(__file__).resolve().parent.parent / "notes" / "surveillance-audit-2013-2019.md"
HEADER = (
    "| Diagnosis year | Weeks | National reports | Prefecture-weeks with zero reports |"
    " Weekly national sites, min–max | Reports aged under 2 |"
)
COUNT = re.compile(r"[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+")
SEPARATOR = re.compile(r":?-{3,}:?")
AGE_SHARE = re.compile(r"[0-9]{1,2}\.[0-9]%|100\.0%")


@dataclass(frozen=True)
class AnnualControl:
    year: int
    weeks: int
    cases: int
    weekly_min: int
    weekly_max: int


def table_cells(line, label):
    cells = [cell.strip() for cell in line.split("|")]
    if len(cells) != 8 or cells[0] or cells[-1]:
        raise ValueError(f"{label}: expected six pipe-delimited columns")
    return cells[1:-1]


def parse_count(value, label):
    if COUNT.fullmatch(value) is None:
        raise ValueError(f"{label}: expected a nonnegative integer with valid comma grouping")
    return int(value.replace(",", ""))


def read_controls(audit=AUDIT):
    lines = audit.read_text(encoding="utf-8").splitlines()
    if lines.count(HEADER) != 1:
        raise ValueError("Expected one national diagnosis-year table in the surveillance audit")
    separator_index = lines.index(HEADER) + 1
    label = "National diagnosis-year table separator"
    if separator_index == len(lines) or not all(
        SEPARATOR.fullmatch(cell) for cell in table_cells(lines[separator_index], label)
    ):
        raise ValueError(f"{label}: expected a Markdown delimiter row")

    controls = []
    for line_number, line in enumerate(lines[separator_index + 1:], start=separator_index + 2):
        if not line.strip():
            break
        label = f"National diagnosis-year table line {line_number}"
        year, weeks, cases, zeros, sites, under_two = table_cells(line, label)
        if not re.fullmatch(r"[0-9]{4}", year) or int(year) not in YEARS:
            raise ValueError(f"{label}: expected a diagnosis year in 2013–2019")
        year = int(year)
        first_week, _ = japan_week_dates(year, 1)
        next_first_week, _ = japan_week_dates(year + 1, 1)
        expected_weeks = (next_first_week - first_week).days // 7
        if weeks != str(expected_weeks):
            raise ValueError(f"{year}: expected {expected_weeks} diagnosis weeks")
        parse_count(zeros, f"{year} prefecture-weeks with zero reports")
        if AGE_SHARE.fullmatch(under_two) is None:
            raise ValueError(f"{year}: expected an under-two percentage with one decimal place")
        low, _, high = sites.partition("–")
        controls.append(AnnualControl(
            year, expected_weeks, parse_count(cases, f"{year} national reports"),
            parse_count(low, f"{year} weekly site minimum"),
            parse_count(high, f"{year} weekly site maximum"),
        ))
    if [control.year for control in controls] != list(YEARS):
        raise ValueError("Expected one national control for each diagnosis year in order")
    return controls


def site_week_bounds(weeks, low, high):
    if weeks < 1 or not 0 < low <= high or (weeks == 1 and low != high):
        raise ValueError("Weekly extrema must be positive, ordered and attainable")
    # A maximum week raises the lower bound, and a minimum week lowers the upper bound.
    span = high - low
    return weeks * low + span, weeks * high - span


def report_bounds(cases, site_weeks):
    if cases < 0:
        raise ValueError("Reports must be nonnegative")
    low, high = site_weeks
    return Fraction(1000 * cases, high), Fraction(1000 * cases, low)


def change_bounds(earlier, later):
    return later[0] - earlier[1], later[1] - earlier[0]


def direction(bounds):
    low, high = bounds
    if low > 0:
        return "rise"
    if high < 0:
        return "fall"
    if low == high == 0:
        return "no change"
    return "ambiguous"


def format_interval(bounds):
    low, high = bounds

    def decimal(hundredths):
        sign = "-" if hundredths < 0 else ""
        whole, fractional = divmod(abs(hundredths), 100)
        return f"{sign}{whole}.{fractional:02d}"

    return f"[{decimal(floor(100 * low))}, {decimal(ceil(100 * high))}]"


def main():
    controls = read_controls()
    rates = {}
    rows = [
        "| Year | Weeks | Reports | Sentinel-site weeks | Reports per 1,000 site-weeks |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for control in controls:
        low, high = site_week_bounds(control.weeks, control.weekly_min, control.weekly_max)
        rate = report_bounds(control.cases, (low, high))
        rates[control.year] = rate
        rows.append(f"| {control.year} | {control.weeks} | {control.cases:,} | "
                    f"{low:,}–{high:,} | {format_interval(rate)} |")

    rows.extend([
        "",
        "| Years | Change in reports | Change per 1,000 site-weeks | Direction |",
        "| --- | ---: | ---: | --- |",
    ])
    pairs = list(zip(controls, controls[1:])) + [(controls[0], controls[-1])]
    for earlier, later in pairs:
        bounds = change_bounds(rates[earlier.year], rates[later.year])
        rows.append(f"| {earlier.year}–{later.year} | {later.cases - earlier.cases:+,} | "
                    f"{format_interval(bounds)} | {direction(bounds)} |")
    print("\n".join(rows))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f"{AUDIT.name}: {error}") from None
