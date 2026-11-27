#!/usr/bin/env python3
"""Compare signs of national annual Japan reports and US PCR positivity."""

import argparse
import csv
from fractions import Fraction
from io import StringIO
from pathlib import Path

import check_surveillance_sources as audit
from summarize_japan_sentinel_volume import read_controls, site_week_bounds
from summarize_nrevss_weighting import write_summary


SIGN_LABEL = {-1: "fall", 0: "tie", 1: "rise"}


def japan_controls():
    return {row.year: (row.cases, *site_week_bounds(row.weeks, row.weekly_min, row.weekly_max))
            for row in read_controls()}


def japan_signs(earlier, later):
    reports0, low0, high0 = earlier
    reports1, low1, high1 = later
    # The extremal rates attain the extremal differences.
    signs = []
    if reports1 * low0 < reports0 * high1:
        signs.append(-1)
    tied = reports0 == reports1 == 0
    if reports0 and reports1:
        ratio = Fraction(reports1, reports0)
        factor1, factor0 = ratio.numerator, ratio.denominator
        # A tie requires both site-week totals to use the same integer multiplier.
        min_multiplier = max((low1 + factor1 - 1) // factor1, (low0 + factor0 - 1) // factor0)
        max_multiplier = min(high1 // factor1, high0 // factor0)
        tied = min_multiplier <= max_multiplier
    if tied:
        signs.append(0)
    if reports1 * high0 > reports0 * low1:
        signs.append(1)
    return signs


def agreement(signs, us_change):
    if not us_change:
        return "US tie"
    if len(signs) > 1:
        return "Indeterminate"
    if signs == [0]:
        return "Japan tie"
    us_sign = 1 if us_change > 0 else -1
    return "Agreement" if signs == [us_sign] else "Disagreement"


def us_matched_rates(path):
    summary = StringIO()
    write_summary(path, summary, exact=True)
    summary.seek(0)
    matched = [row for row in csv.DictReader(summary) if row["support"] == "matched"]
    audit.require(len(matched) == len(audit.YEARS) and all(row["retained_rows"] == "520" for row in matched),
                  "Expected 520 matched PCR cells in each study year")
    return {
        int(row["calendar_year"]): (Fraction(row["a_equal_week_region_pct"]), Fraction(row["c_pooled_all_pct"]))
        for row in matched
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="original nrevss.csv matching the repository SHA-256 pin")
    args = parser.parse_args()
    try:
        us = us_matched_rates(args.csv)
        japan = japan_controls()
    except (OSError, ValueError, KeyError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")

    print("| Years | Japan possible signs | US equal (pp) | US pooled (pp) | Equal agreement | Pooled agreement |")
    print("| --- | --- | ---: | ---: | --- | --- |")
    for earlier, later in zip(audit.YEARS, audit.YEARS[1:]):
        signs = japan_signs(japan[earlier], japan[later])
        equal = us[later][0] - us[earlier][0]
        pooled = us[later][1] - us[earlier][1]
        japan_label = " or ".join(SIGN_LABEL[sign] for sign in signs)
        print(f"| {earlier}–{later} | {japan_label} | {float(equal):+.3f} | {float(pooled):+.3f} | "
              f"{agreement(signs, equal)} | {agreement(signs, pooled)} |")


if __name__ == "__main__":
    main()
