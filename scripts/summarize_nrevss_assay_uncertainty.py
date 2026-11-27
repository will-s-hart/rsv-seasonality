#!/usr/bin/env python3
"""Bound hypothetical test-count noise for adjacent-year NREVSS assay contrasts."""

import argparse
from collections import defaultdict
import csv
from fractions import Fraction
from itertools import pairwise
from math import fsum, sqrt
from pathlib import Path
import sys

import check_surveillance_sources as audit
from summarize_nrevss_assay_changes import calendar_cells, match_support
from summarize_nrevss_assays import decimal, load_pinned_groups


# Earlier PCR, earlier antigen, later PCR, later antigen.
SIGNS = (1, -1, -1, 1)


def matched_rows(groups, year0, year1, regions):
    earlier = calendar_cells(groups, year0, regions)
    later = calendar_cells(groups, year1, regions)
    matched, _ = match_support(earlier, later, minimum=1)
    return ((region, rows) for (region, _), rows in matched.items())


def contrast_bounds(matched):
    contrast = Fraction(0)
    row_variance_sum = Fraction(0)
    region_date_variances = []
    row_sd_by_region = defaultdict(list)
    cells = 0
    for region, rows in matched:
        cells += 1
        for sign, (positives, tests, _) in zip(SIGNS, rows, strict=True):
            contrast += sign * Fraction(positives, tests)
        variances = [Fraction(1, 4 * tests) for _, tests, _ in rows]
        row_variance_sum += sum(variances)
        row_sds = [sqrt(variance) for variance in variances]
        earlier_pcr, earlier_antigen, later_pcr, later_antigen = row_sds
        region_date_variances.extend(((earlier_pcr + earlier_antigen)**2, (later_pcr + later_antigen)**2))
        row_sd_by_region[region].extend(row_sds)

    audit.require(cells > 0, "No four-way positive-test support for the year pair")
    scale = Fraction(100, cells)  # Percentage points, with one equal cell weight per row.
    region_sd_caps = [scale * fsum(sds) for sds in row_sd_by_region.values()]
    variance_caps = {
        "independent_rows": scale**2 * row_variance_sum,
        "independent_region_dates": scale**2 * fsum(region_date_variances),
        "independent_regions": fsum(sd**2 for sd in region_sd_caps),
        "unrestricted_dependence": fsum(region_sd_caps)**2,
    }
    contrast_pp = 100 * contrast / cells
    break_even_sd = abs(contrast_pp) / sqrt(variance_caps["independent_rows"])
    return {
        "matched_cells_per_year": cells,
        "matched_regions": len(region_sd_caps),
        "antigen_minus_pcr_pp": contrast_pp,
        **{f"{name}_variance_cap_pp2": variance for name, variance in variance_caps.items()},
        **{f"{name}_sd_cap_pp": sqrt(variance) for name, variance in variance_caps.items()},
        "break_even_row_sd_multiplier": break_even_sd,
        "break_even_row_variance_multiplier": break_even_sd**2,
    }


def annual_pairs(groups, years=audit.YEARS, regions=audit.HHS_REGIONS):
    for year0, year1 in pairwise(years):
        yield {
            "year0": year0,
            "year1": year1,
            **contrast_bounds(matched_rows(groups, year0, year1, regions)),
        }


def write_summary(path, output):
    groups, _ = load_pinned_groups(path)
    rows = list(annual_pairs(groups))
    writer = csv.DictWriter(output, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: value if isinstance(value, int) else decimal(value) for key, value in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="original nrevss.csv matching the repository SHA-256 pin")
    args = parser.parse_args()
    try:
        write_summary(args.csv, sys.stdout)
    except (OSError, ValueError, KeyError, csv.Error) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
