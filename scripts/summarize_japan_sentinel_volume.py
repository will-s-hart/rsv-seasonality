#!/usr/bin/env python3
"""Bound annual Japan reports per sentinel-site week using the committed audit."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor
from pathlib import Path

from check_surveillance_sources import YEARS


AUDIT = Path(__file__).resolve().parent.parent / "notes" / "surveillance-audit-2013-2019.md"
HEADER = (
    "| Diagnosis year | Weeks | National reports | Prefecture-weeks with zero reports |"
    " Weekly national sites, min–max | Reports aged under 2 |"
)


@dataclass(frozen=True)
class AnnualControl:
    year: int
    weeks: int
    cases: int
    weekly_min: int
    weekly_max: int


def read_controls(audit=AUDIT):
    lines = audit.read_text(encoding="utf-8").splitlines()
    if lines.count(HEADER) != 1:
        raise ValueError("Expected one national diagnosis-year table in the surveillance audit")
    controls = []
    for line in lines[lines.index(HEADER) + 2:]:
        if not line.startswith("|"):
            break
        year, weeks, cases, _, sites, _ = (cell.strip() for cell in line.strip("|").split("|"))
        low, high = sites.replace(",", "").split("–")
        controls.append(AnnualControl(
            int(year), int(weeks), int(cases.replace(",", "")), int(low), int(high)
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
    print("| Year | Weeks | Reports | Sentinel-site weeks | Reports per 1,000 site-weeks |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for control in controls:
        low, high = site_week_bounds(control.weeks, control.weekly_min, control.weekly_max)
        rate = report_bounds(control.cases, (low, high))
        rates[control.year] = rate
        print(f"| {control.year} | {control.weeks} | {control.cases:,} | "
              f"{low:,}–{high:,} | {format_interval(rate)} |")

    print()
    print("| Years | Change in reports | Change per 1,000 site-weeks | Direction |")
    print("| --- | ---: | ---: | --- |")
    pairs = list(zip(controls, controls[1:])) + [(controls[0], controls[-1])]
    for earlier, later in pairs:
        bounds = change_bounds(rates[earlier.year], rates[later.year])
        print(f"| {earlier.year}–{later.year} | {later.cases - earlier.cases:+,} | "
              f"{format_interval(bounds)} | {direction(bounds)} |")


if __name__ == "__main__":
    main()
