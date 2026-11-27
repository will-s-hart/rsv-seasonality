#!/usr/bin/env python3
"""Validate demographic panels, workbooks and the U.S. Virgin Islands IDB sensitivity."""

import argparse
import csv
import json
import sys
from itertools import product
from pathlib import Path

from demographic_sources import (
    COUNTY_YEAR_CODES,
    POPULATION_FIELDS,
    RACES,
    ROOT,
    STATE_AGES,
    STATE_NAMES,
    US_STATES,
    YEARS,
    YOUNG_AGES,
    assert_cells,
    load_contract,
    read_source_csv,
    read_states,
    read_xlsx_sheets,
    spreadsheet_count,
    unsigned_integer,
    verify_stage,
    write_panel,
)
from japan_population import PREFECTURES, read_japan
from vi_idb import check_vi_idb

PANEL_FIELDS = (*POPULATION_FIELDS, "control_sources")
PR_WORKBOOK = "pr-commonwealth"
PR_MUNICIPIOS = "pr-municipios"
PR_CODES = "pr-municipio-codes"
PR_FIELDS = ("SUMLEV", "MUNICIPIO", "NAME", "YEAR", "POPESTIMATE", "UNDER5_TOT", "AGE04_TOT")
PR_CODE_FIELDS = ("STATE", "STATEFP", "COUNTYFP", "COUNTYNAME")
US_WORKBOOKS = {state: f"us-age-sex-{state:02}" for state in (11, 34, 36)}


def census_workbook(path, table, geography):
    rows = read_xlsx_sheets(path, (table,))[table]
    assert_cells(rows, {
        (2, 1): (
            "Annual Intercensal Estimates of the Resident Population for Selected Age Groups "
            f"by Sex for {geography}: April 1, 2010 to April 1, 2020"
        ),
        (3, 2): "April 1, 2010 Estimates Base",
        (3, 5): "Population Estimate (as of July 1)",
        (3, 35): "April 1, 2020 Census",
        (6, 1): "Total",
        (7, 1): ".Under 5 years",
        (27, 1): ".Under 5 years",
        (45, 1): "Source: U.S. Census Bureau, Population Division",
        (46, 1): "Release Date: September 2025",
    }, table)
    counts = {}
    for year in YEARS:
        col = 5 + 3 * (year - 2010)
        assert_cells(rows, {
            (4, col): year,
            (5, col): "Total Population",
            (5, col + 1): "Male",
            (5, col + 2): "Female",
        }, table)
        label = f"{table}, July 1 {year}"
        total, young, under5 = (
            spreadsheet_count(rows[row - 1][col - 1], label) for row in (6, 7, 27)
        )
        if total <= 0 or young > total or young != under5:
            raise ValueError(f"{label}: inconsistent total or under-5 workbook counts")
        counts[year] = (total, young)
    return counts


def municipio_codes(path):
    codes = {}
    for line, row in read_source_csv(path, PR_CODE_FIELDS, exact_header=False, delimiter="|"):
        code, name = row["COUNTYFP"], row["COUNTYNAME"]
        label = f"{PR_CODES} line {line}"
        if (
            (row["STATE"], row["STATEFP"]) != ("PR", "72")
            or len(code) != 3
            or not 1 <= unsigned_integer(code, label) <= 999
            or not name.endswith(" Municipio")
            or code in codes
        ):
            raise ValueError(f"{label}: invalid or duplicate Puerto Rico geography")
        codes[code] = name
    if len(codes) != 78 or len(set(codes.values())) != 78:
        raise ValueError(f"{PR_CODES}: expected 78 unique FIPS 72 municipios")
    return codes


def municipio_totals(path, codes):
    counts = {}
    for line, row in read_source_csv(path, PR_FIELDS, encoding="cp1252", exact_header=False):
        label = f"{PR_MUNICIPIOS} line {line}"
        code = row["MUNICIPIO"]
        if row["SUMLEV"] != "050" or codes.get(code) != row["NAME"]:
            raise ValueError(f"{label}: expected a SUMLEV 050 municipio in FIPS 72")
        year_code = unsigned_integer(row["YEAR"], label)
        if not 1 <= year_code <= 12:
            raise ValueError(f"{label}: unexpected YEAR code {year_code}")
        if year_code not in COUNTY_YEAR_CODES:
            continue
        year = COUNTY_YEAR_CODES[year_code]
        if (year, code) in counts:
            raise ValueError(f"{label}: duplicate municipio-year")
        total, under5, age04 = (
            unsigned_integer(row[field], f"{label}, {field}")
            for field in ("POPESTIMATE", "UNDER5_TOT", "AGE04_TOT")
        )
        if under5 != age04:
            raise ValueError(f"{label}: UNDER5_TOT and AGE04_TOT disagree")
        if total <= 0 or age04 > total:
            raise ValueError(f"{label}: inconsistent POPESTIMATE or AGE04_TOT")
        counts[year, code] = (total, age04)
    if counts.keys() != set(product(YEARS, codes)):
        raise ValueError(f"{PR_MUNICIPIOS}: expected all 78 municipios in each target year")
    return {
        year: tuple(sum(counts[year, code][i] for code in codes) for i in (0, 1))
        for year in YEARS
    }


def require_same_census_release(source, control):
    if tuple(source["years"]) != YEARS or any(
        source[field] != control[field]
        for field in ("panel", "publisher", "release_id", "release_date", "years", "source_unit")
    ):
        raise ValueError(f"{control['id']}: expected the same Census release, years and units")


def population_row(panel, location, name, year, total, young, source, controls):
    control_sources = [
        {field: receipt[field] for field in ("source_id", "sha256", "capture_method")}
        for receipt in controls
    ]
    return (
        location, name, panel["geography"], year, f"{year}-{panel['reference_month_day']}",
        total, young, format(young / total, ".12g"), panel["universe"],
        source["source_unit"], source["source_id"], source["source_table"], source["source_vintage"],
        source["source_release_date"], source["source_release_id"], source["sha256"],
        source["capture_method"], json.dumps(control_sources, separators=(",", ":")),
    )


def build_jp(cache, output, panel, sources):
    prefectures, differences = read_japan(cache, sources)
    if (panel["reference_month_day"], panel["locations"]) != ("10-01", len(PREFECTURES)):
        raise ValueError("Japan: unexpected reference date or geography count in the source contract")
    rows = []
    for year, (age, source, controls) in prefectures.items():
        factor = {"persons": 1, "thousand persons": 1000}[source["source_unit"]]
        for code in sorted(PREFECTURES):
            name, total, young = age[code]
            rows.append(population_row(
                panel, f"JP-{code}", name, year, total * factor, young * factor, source, controls,
            ))
    if len(rows) != panel["expected_rows"]:
        raise ValueError("Japan output dimensions disagree with the demographic contract")
    write_panel(output, cache, PANEL_FIELDS, rows)
    return len(rows), differences


def build_pr(cache, output, panel, sources):
    source = sources[PR_WORKBOOK]
    require_same_census_release(source, sources[PR_MUNICIPIOS])
    workbook_path, workbook_receipt = verify_stage(cache, source)
    municipios_path, municipios_receipt = verify_stage(cache, sources[PR_MUNICIPIOS])
    codes_path, codes_receipt = verify_stage(cache, sources[PR_CODES])
    commonwealth = census_workbook(workbook_path, source["table"], "Puerto Rico Commonwealth")
    municipios = municipio_totals(municipios_path, municipio_codes(codes_path))

    if (panel["reference_month_day"], panel["locations"], panel["expected_rows"]) != (
        "07-01", 1, len(YEARS)
    ):
        raise ValueError("Puerto Rico: unexpected reference date or dimensions in the source contract")
    rows = []
    for year, (total, young) in commonwealth.items():
        if (total, young) != municipios[year]:
            raise ValueError(f"Puerto Rico {year}: workbook and municipio sums disagree")
        rows.append(population_row(
            panel, "PR-72", "Puerto Rico", year, total, young, workbook_receipt,
            (municipios_receipt, codes_receipt),
        ))
    write_panel(output, cache, PANEL_FIELDS, rows)
    return len(rows)


def check_us_workbooks(cache, sources):
    source = sources[US_STATES]
    state_path, _ = verify_stage(cache, source)
    cells = read_states(state_path)
    for state, workbook_id in US_WORKBOOKS.items():
        control = sources[workbook_id]
        require_same_census_release(source, control)
        path, _ = verify_stage(cache, control)
        workbook = census_workbook(path, control["table"], STATE_NAMES[state])
        for index, year in enumerate(YEARS):
            total, young = (
                sum(cells[state, race, age][index] for race, age in product(RACES, ages))
                for ages in (STATE_AGES, YOUNG_AGES)
            )
            if (total, young) != workbook[year]:
                raise ValueError(f"{STATE_NAMES[state]} {year}: state CSV and age-by-sex workbook disagree")
    return len(US_WORKBOOKS) * len(YEARS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data/raw/demography")
    commands = parser.add_subparsers(dest="command", required=True)
    for panel, geography in (("jp", "Japan"), ("pr", "Puerto Rico")):
        build = commands.add_parser(f"build-{panel}", help=f"validate and write the {geography} panel")
        build.add_argument(
            "--output", type=Path, default=ROOT / "data/processed/demography" / f"{panel}-population.csv",
        )
    commands.add_parser("check-us-workbooks", help="check DC, NJ and NY against same-release workbooks")
    vi_idb = commands.add_parser("check-vi-idb", help="verify and compare U.S. Virgin Islands IDB estimates")
    vi_idb.add_argument("--archive", required=True, type=Path, help="path to the original Census IDB ZIP")
    args = parser.parse_args()
    contract, sources = load_contract()
    if args.command == "build-jp":
        count, gaps = build_jp(args.cache_dir, args.output, contract["panels"]["jp"], sources)
        print(f"{count} Japan prefecture-year rows passed companion table and national checks")
        print("Prefecture sums minus national controls (all ages, ages 0–4)")
        for year, (total, young) in gaps.items():
            unit = "persons" if year == 2015 else "thousand persons"
            print(f"{year}  {total:+d}  {young:+d}  {unit}")
    elif args.command == "build-pr":
        count = build_pr(args.cache_dir, args.output, contract["panels"]["pr"], sources)
        print(f"{count} Puerto Rico commonwealth rows match the sums of all 78 municipios")
    elif args.command == "check-vi-idb":
        check_vi_idb(args.archive, contract["sensitivity"]["vi_idb"])
    else:
        count = check_us_workbooks(args.cache_dir, sources)
        print(f"{count} DC, NJ and NY rows match the official state age-by-sex workbooks")


if __name__ == "__main__":
    try:
        main()
    except ImportError as error:
        sys.exit(f"population: install scripts/requirements-demography.txt ({error})")
    except (OSError, ValueError, KeyError, csv.Error) as error:
        sys.exit(f"population: {error}")
