#!/usr/bin/env python3
"""Export the audited 2013–2019 RSV weekly observation grid as UTF-8 CSV."""

import argparse
import csv
from datetime import date
from pathlib import Path
import sys
from typing import NamedTuple, Optional

import check_surveillance_sources as audit


class Observation(NamedTuple):
    source_id: str
    source_version: str
    source_vintage: Optional[date]
    source_calendar: str
    source_week_year: int
    source_week_code: str
    week_start: date
    week_end: date
    region_id: str
    region_label: str
    observation_type: str
    method: Optional[str]
    count: Optional[int]
    denominator_kind: str
    denominator: Optional[int]
    coverage: str
    source_outlier: Optional[int]
    positivity: Optional[float]


def nesid_observations(directory):
    for year in audit.YEARS:
        weeks, sites = audit.read_nesid_sites(directory, year)
        with audit.workbook(directory, year, "8-1") as (names, read_cases):
            for week, code, counts, denominators in audit.nesid_week_counts(
                year, weeks, sites, names, read_cases
            ):
                start, end = audit.japan_week_dates(year, week)
                for region, label in enumerate(audit.NESID_AREAS[1:], start=1):
                    yield Observation(
                        source_id="NESID",
                        source_version=f"final_annual_{year}",
                        source_vintage=None,
                        source_calendar="japan_diagnosis",
                        source_week_year=year,
                        source_week_code=code,
                        week_start=start,
                        week_end=end,
                        region_id=f"{region:02d}",
                        region_label=label,
                        observation_type="rsv_case_notifications",
                        method=None,
                        count=counts[region],
                        denominator_kind="paediatric_sentinel_sites",
                        denominator=denominators[region],
                        coverage="present",
                        source_outlier=None,
                        positivity=None,
                    )


def nrevss_observations(directory):
    groups, codes, _ = audit.read_nrevss(directory)
    week_ends = audit.nrevss_week_ends()
    for (method, region), observations in groups.items():
        for week_end in week_ends:
            start, end = audit.week_dates(week_end)
            code = codes[end]
            values = observations.get(end)
            count, denominator, outlier = values if values is not None else (None, None, None)
            yield Observation(
                source_id="NREVSS:52kb-ccu2",
                source_version="historical_public_use_2022",
                source_vintage=date(2022, 10, 21),
                source_calendar="cdc_mmwr",
                source_week_year=2000 + int(code[:2]),
                source_week_code=code,
                week_start=start,
                week_end=end,
                region_id=str(region),
                region_label=f"HHS Region {region}",
                observation_type="rsv_test_detections",
                method=method,
                count=count,
                denominator_kind="reported_tests",
                denominator=denominator,
                coverage="present" if values is not None else "absent",
                source_outlier=outlier,
                positivity=count / denominator if denominator else None,
            )


def write_observations(directory, stream):
    audit.verify_inputs(directory)
    rows = [*nesid_observations(directory), *nrevss_observations(directory)]
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(Observation._fields)
    writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="local source directory from the audit note")
    args = parser.parse_args()
    # A fixed encoding and newline convention keep the file reproducible across hosts.
    sys.stdout.reconfigure(encoding="utf-8", newline="")
    write_observations(args.directory, sys.stdout)


if __name__ == "__main__":
    main()
