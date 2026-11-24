#!/usr/bin/env python3
"""Stage official demographic source files and build the US states/DC panel."""

import argparse
import csv
import hashlib
import json
import os
import posixpath
import shutil
import sys
import tempfile
import tomllib
import zipfile
from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data/demographic-sources.toml"
US_STATES = "us-states"
US_CONTROL = "us-national-control"
US_COUNTY_CONTROL = "us-county-control"
YEARS = tuple(range(2013, 2020))
ESTIMATE_FIELDS = tuple(f"POPESTIMATE{year}" for year in range(2010, 2020))
COUNT_FIELDS = ("ESTIMATESBASE2010", *ESTIMATE_FIELDS, "CENSUS2020POP")
STATE_FIELDS = (
    "SUMLEV", "REGION", "DIVISION", "STATE", "NAME", "SEX", "ORIGIN",
    "RACE", "AGE", *COUNT_FIELDS,
)
NATIONAL_FIELDS = ("SEX", "AGE", *COUNT_FIELDS)
COUNTY_CONTROL_FIELDS = ("SUMLEV", "STATE", "COUNTY", "STNAME", "YEAR", "POPESTIMATE", "AGE04_TOT")
COUNTY_YEAR_CODES = dict(zip(range(5, 12), YEARS, strict=True))
POPULATION_FIELDS = (
    "location_id", "location_name", "geography", "year", "reference_date",
    "population_total", "population_age_0_4", "share_age_0_4",
    "universe", "source_unit", "source_id", "source_table", "source_vintage",
    "source_release_date", "source_release_id", "source_sha256", "source_capture_method",
)
OUTPUT_FIELDS = (
    *POPULATION_FIELDS,
    "control_source_sha256", "control_capture_method", "county_control_sha256",
    "county_control_capture_method",
)

# Census ANSI state FIPS codes. Puerto Rico (72) has its own source.
STATE_NAMES = {
    1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas", 6: "California",
    8: "Colorado", 9: "Connecticut", 10: "Delaware", 11: "District of Columbia",
    12: "Florida", 13: "Georgia", 15: "Hawaii", 16: "Idaho", 17: "Illinois",
    18: "Indiana", 19: "Iowa", 20: "Kansas", 21: "Kentucky", 22: "Louisiana",
    23: "Maine", 24: "Maryland", 25: "Massachusetts", 26: "Michigan",
    27: "Minnesota", 28: "Mississippi", 29: "Missouri", 30: "Montana",
    31: "Nebraska", 32: "Nevada", 33: "New Hampshire", 34: "New Jersey",
    35: "New Mexico", 36: "New York", 37: "North Carolina", 38: "North Dakota",
    39: "Ohio", 40: "Oklahoma", 41: "Oregon", 42: "Pennsylvania",
    44: "Rhode Island", 45: "South Carolina", 46: "South Dakota",
    47: "Tennessee", 48: "Texas", 49: "Utah", 50: "Vermont", 51: "Virginia",
    53: "Washington", 54: "West Virginia", 55: "Wisconsin", 56: "Wyoming",
}
RACES = range(1, 7)
STATE_AGES = range(86)
NATIONAL_AGES = range(101)
YOUNG_AGES = range(5)
CENSUS_TOTAL_AGE = 999
EXCEL_OLE = bytes.fromhex("d0 cf 11 e0 a1 b1 1a e1")
PACKAGE_RELATIONSHIP = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
DOCUMENT_RELATIONSHIPS = (
    ("http://schemas.openxmlformats.org/officeDocument/2006/relationships",
     "http://schemas.openxmlformats.org/spreadsheetml/2006/main"),
    ("http://purl.oclc.org/ooxml/officeDocument/relationships",
     "http://purl.oclc.org/ooxml/spreadsheetml/main"),
)


def load_contract():
    with CONTRACT_PATH.open("rb") as stream:
        contract = tomllib.load(stream)
    if contract["schema_version"] != 1 or tuple(contract["years"]) != YEARS:
        raise ValueError("unsupported demographic contract version or period")
    sources = {entry["id"]: entry for entry in contract["sources"]}
    if len(sources) != len(contract["sources"]):
        raise ValueError("duplicate source ID in demographic contract")
    for source in sources.values():
        if source["publisher"] == "us" and not source.get("release_id", "").strip():
            raise ValueError(f"{source['id']}: missing explicit Census release ID")
    return contract, sources


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_pin(source, digest):
    expected = source.get("expected_sha256")
    if expected is not None and digest != expected:
        raise ValueError(f"{source['id']}: SHA-256 disagrees with the source contract")


def relationship_target(base, relationship):
    target = relationship.attrib["Target"]
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(base, target))


def validate_xlsx(path):
    with zipfile.ZipFile(path) as archive:
        content_types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
        types_ns = "{http://schemas.openxmlformats.org/package/2006/content-types}"
        overrides = {
            entry.get("PartName"): entry.get("ContentType")
            for entry in content_types.findall(f"{types_ns}Override")
        }
        roots = ElementTree.fromstring(archive.read("_rels/.rels"))
        for relationship_ns, sheet_ns in DOCUMENT_RELATIONSHIPS:
            main = roots.find(
                f"{PACKAGE_RELATIONSHIP}[@Type='{relationship_ns}/officeDocument']"
            )
            if main is None or main.get("TargetMode") == "External":
                continue
            workbook = relationship_target("", main)
            if overrides.get(f"/{workbook}") != (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
            ):
                continue

            workbook_root = ElementTree.fromstring(archive.read(workbook))
            if workbook_root.tag != f"{{{sheet_ns}}}workbook":
                continue
            base, filename = posixpath.split(workbook)
            rels = ElementTree.fromstring(archive.read(posixpath.join(base, "_rels", filename + ".rels")))
            links = {link.get("Id"): link for link in rels.findall(PACKAGE_RELATIONSHIP)}
            for sheet in workbook_root.findall(f"{{{sheet_ns}}}sheets/{{{sheet_ns}}}sheet"):
                link = links.get(sheet.attrib[f"{{{relationship_ns}}}id"])
                if (
                    link is not None
                    and link.get("TargetMode") != "External"
                    and link.get("Type") == f"{relationship_ns}/worksheet"
                ):
                    with archive.open(relationship_target(base, link)) as worksheet:
                        start = next(ElementTree.iterparse(worksheet, events=("start",)), None)
                    if start is not None and start[1].tag == f"{{{sheet_ns}}}worksheet":
                        return
    raise ValueError("missing a linked SpreadsheetML worksheet")


def validate_download_format(path, source):
    with path.open("rb") as stream:
        prefix = stream.read(4096)
    if source["format"] in ("spreadsheet", "xlsx"):
        if source["format"] == "spreadsheet" and prefix.startswith(EXCEL_OLE):
            return
        try:
            validate_xlsx(path)
        except (zipfile.BadZipFile, ElementTree.ParseError, KeyError, RuntimeError, ValueError) as error:
            raise ValueError(f"{source['id']}: expected an XLSX workbook: {error}") from error
    elif source["format"] in ("csv", "pipe-delimited"):
        separator = b"," if source["format"] == "csv" else b"|"
        text_prefix = prefix.removeprefix(b"\xef\xbb\xbf").lstrip()
        if not text_prefix or text_prefix.startswith((b"<", b"{", b"[")) or separator not in prefix:
            label = "CSV" if source["format"] == "csv" else "pipe-delimited text"
            raise ValueError(f"{source['id']}: response does not resemble {label}")
    else:
        raise ValueError(f"{source['id']}: unsupported source format")


def verify_stage(cache_dir, source):
    source_dir = cache_dir / source["id"]
    path = source_dir / "source"
    receipt_path = source_dir / "manifest.json"
    if not path.is_file() or not receipt_path.is_file():
        raise ValueError(f"{source['id']}: stage the source before building")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt["schema_version"] != 1
        or receipt["source_id"] != source["id"]
        or receipt["source_url"] != source["url"]
        or receipt["source_table"] != source["table"]
        or receipt["source_vintage"] != source["vintage"]
        or receipt["source_release_date"] != source["release_date"]
        or receipt.get("source_release_id") != source.get("release_id")
        or receipt["source_unit"] != source["source_unit"]
        or receipt["capture_method"] not in ("download", "local_file")
    ):
        raise ValueError(f"{source['id']}: staged manifest disagrees with source contract")
    digest = file_digest(path)
    if digest != receipt["sha256"] or path.stat().st_size != receipt["bytes"]:
        raise ValueError(f"{source['id']}: staged file disagrees with manifest checksum or size")
    verify_pin(source, digest)
    validate_download_format(path, source)
    return path, receipt


def receipt_scope(source, contract):
    panel = contract["panels"][source["panel"]]
    publisher = contract["publishers"][source["publisher"]]
    return {
        "catalog_url": source["catalog_url"],
        "publisher": publisher["name"],
        "terms_url": publisher["terms_url"],
        "source_format": source["format"],
        "role": source["role"],
        "geography": source.get("geography", panel["geography"]),
        "universe": panel["universe"],
        "reference_dates": [f"{year}-{panel['reference_month_day']}" for year in source["years"]],
        "age_band": {
            "total_control": "all ages", "geography_control": None,
        }.get(source["role"], contract["age_band"]),
    }


def stage_source(cache_dir, source, contract, from_file):
    destination = cache_dir / source["id"]
    if destination.exists():
        _, receipt = verify_stage(cache_dir, source)
        if from_file is not None and file_digest(from_file) != receipt["sha256"]:
            raise ValueError(f"{source['id']}: different bytes already staged; use a new cache")
        return receipt

    cache_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{source['id']}-", dir=cache_dir) as temporary:
        source_dir = Path(temporary)
        path = source_dir / "source"
        resolved_url = None
        etag = last_modified = None
        if from_file is None:
            with urlopen(source["url"], timeout=60) as response, path.open("xb") as output:
                resolved_url = response.geturl()
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
                content_length = response.headers.get("Content-Length")
                shutil.copyfileobj(response, output)
            if content_length is not None and path.stat().st_size != int(content_length):
                raise ValueError(f"{source['id']}: response length disagrees with Content-Length")
            capture_method = "download"
        else:
            shutil.copyfile(from_file, path)
            capture_method = "local_file"

        validate_download_format(path, source)
        digest = file_digest(path)
        verify_pin(source, digest)
        receipt = {
            "schema_version": 1,
            "source_id": source["id"],
            "source_url": source["url"],
            "resolved_url": resolved_url,
            "capture_method": capture_method,
            "captured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "http_etag": etag,
            "http_last_modified": last_modified,
            "source_table": source["table"],
            "source_vintage": source["vintage"],
            "source_release_date": source["release_date"],
            "source_release_id": source.get("release_id"),
            "source_unit": source["source_unit"],
            **receipt_scope(source, contract),
            "bytes": path.stat().st_size,
            "sha256": digest,
            "expected_sha256": source.get("expected_sha256"),
        }
        (source_dir / "manifest.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        # Publish the two files together. Rename cannot replace an existing nonempty directory.
        source_dir.rename(destination)

    return receipt


def read_xlsx_sheets(path, names):
    # The staging cache deliberately stores the original bytes without a filename extension.
    from openpyxl import load_workbook

    with path.open("rb") as stream:
        workbook = load_workbook(stream, read_only=True, data_only=True)
        try:
            return {name: list(workbook[name].values) for name in names}
        finally:
            workbook.close()


def assert_cells(rows, expected, label):
    for (row, column), value in expected.items():
        try:
            actual = rows[row - 1][column - 1]
        except IndexError as error:
            raise ValueError(f"{label}: missing R{row}C{column}") from error
        if isinstance(actual, str):
            actual = " ".join(actual.split())
        if actual != value:
            raise ValueError(f"{label}: unexpected header at R{row}C{column}")


def spreadsheet_count(value, label):
    if type(value) not in (int, float) or not value >= 0 or value % 1 != 0:
        raise ValueError(f"{label}: expected a nonnegative integer count")
    return int(value)


def read_source_csv(path, fields, *, encoding="utf-8-sig", exact_header=True, delimiter=","):
    with path.open(encoding=encoding, newline="") as stream:
        reader = csv.reader(stream, strict=True, delimiter=delimiter)
        header = tuple(next(reader, ()))
        if exact_header:
            valid_header = header == fields
        else:
            valid_header = len(set(header)) == len(header) and set(fields).issubset(header)
        if not valid_header:
            raise ValueError("CSV header does not match the documented file layout")
        for row in reader:
            if len(row) != len(header):
                raise ValueError(f"line {reader.line_num}: wrong number of CSV fields")
            yield reader.line_num, dict(zip(header, row, strict=True))


def unsigned_integer(value, label):
    if not value.isascii() or not value.isdecimal():
        raise ValueError(f"{label}: expected a nonnegative integer, found {value!r}")
    return int(value)


def age_code(value, top_age, label):
    if value == f"{top_age}+":
        return top_age
    return unsigned_integer(value, label)


def population_values(row, label):
    return tuple(
        unsigned_integer(row[f"POPESTIMATE{year}"], f"{label}, POPESTIMATE{year}")
        for year in YEARS
    )


def check_cells(cells, expected, source_id):
    missing = expected - cells.keys()
    if missing:
        raise ValueError(f"{source_id}: missing required cells ({len(missing)}), including {min(missing)}")


def read_states(path):
    cells = {}
    for line, row in read_source_csv(path, STATE_FIELDS):
        label = f"{US_STATES} line {line}"
        state = unsigned_integer(row["STATE"], label)
        if unsigned_integer(row["SUMLEV"], label) != 40 or state not in STATE_NAMES:
            raise ValueError(f"{label}: unexpected state geography {row['SUMLEV']}/{row['STATE']}")
        if row["NAME"] != STATE_NAMES[state]:
            raise ValueError(f"{label}: state FIPS and name disagree")

        sex = unsigned_integer(row["SEX"], label)
        origin = unsigned_integer(row["ORIGIN"], label)
        if sex not in (0, 1, 2) or origin not in (0, 1, 2):
            raise ValueError(f"{label}: unexpected sex or Hispanic origin code")
        # Published totals for sex and origin already include all the component categories.
        if (sex, origin) != (0, 0):
            continue

        race = unsigned_integer(row["RACE"], label)
        age = age_code(row["AGE"], STATE_AGES[-1], label)
        if race not in RACES or age not in STATE_AGES:
            raise ValueError(f"{label}: undocumented aggregate race or age code")
        key = state, race, age
        if key in cells:
            raise ValueError(f"{label}: duplicate state/race/age cell {key}")
        cells[key] = population_values(row, label)
    check_cells(cells, set(product(STATE_NAMES, RACES, STATE_AGES)), US_STATES)
    return cells


def read_national_control(path):
    cells = {}
    for line, row in read_source_csv(path, NATIONAL_FIELDS):
        label = f"{US_CONTROL} line {line}"
        sex = unsigned_integer(row["SEX"], label)
        if sex not in (0, 1, 2):
            raise ValueError(f"{label}: unexpected sex code")
        if sex != 0:
            continue
        age = age_code(row["AGE"], NATIONAL_AGES[-1], label)
        if age not in NATIONAL_AGES and age != CENSUS_TOTAL_AGE:
            raise ValueError(f"{label}: undocumented age code")
        if age in cells:
            raise ValueError(f"{label}: duplicate national age cell {age}")
        cells[age] = population_values(row, label)
    check_cells(cells, {*NATIONAL_AGES, CENSUS_TOTAL_AGE}, US_CONTROL)
    return cells


def read_county_control(path):
    county_years = {}
    state_totals = {}
    for line, row in read_source_csv(
        path, COUNTY_CONTROL_FIELDS, encoding="cp1252", exact_header=False,
    ):
        label = f"{US_COUNTY_CONTROL} line {line}"
        state = unsigned_integer(row["STATE"], label)
        county = unsigned_integer(row["COUNTY"], label)
        if unsigned_integer(row["SUMLEV"], label) != 50 or state not in STATE_NAMES or not 1 <= county <= 999:
            raise ValueError(f"{label}: unexpected county geography {row['SUMLEV']}/{state}/{county}")
        if row["STNAME"] != STATE_NAMES[state]:
            raise ValueError(f"{label}: state FIPS and name disagree")
        year_code = unsigned_integer(row["YEAR"], label)
        if not 1 <= year_code <= 12:
            raise ValueError(f"{label}: unexpected Census year code {year_code}")
        if year_code not in COUNTY_YEAR_CODES:
            continue
        year = COUNTY_YEAR_CODES[year_code]
        years = county_years.setdefault((state, county), set())
        if year in years:
            raise ValueError(f"{label}: duplicate county-year {state}/{county}/{year}")
        years.add(year)
        total = unsigned_integer(row["POPESTIMATE"], f"{label}, POPESTIMATE")
        young = unsigned_integer(row["AGE04_TOT"], f"{label}, AGE04_TOT")
        if young > total:
            raise ValueError(f"{label}: population ages 0–4 exceeds the all-age total")
        previous_total, previous_young = state_totals.get((state, year), (0, 0))
        state_totals[state, year] = (previous_total + total, previous_young + young)

    for (state, county), years in county_years.items():
        if len(years) != len(YEARS):
            raise ValueError(f"{US_COUNTY_CONTROL}: county {state}/{county} does not cover every target year")
    check_cells(state_totals, set(product(STATE_NAMES, YEARS)), US_COUNTY_CONTROL)
    return state_totals


def build_states(cache_dir, output_path, contract, sources, *, check_counties=False):
    source = sources[US_STATES]
    panel = contract["panels"][source["panel"]]
    controls = [US_CONTROL, US_COUNTY_CONTROL] if check_counties else [US_CONTROL]
    for control_id in controls:
        control = sources[control_id]
        if any(control[field] != source[field] for field in (
            "panel", "publisher", "release_id", "release_date", "years", "source_unit",
        )) or tuple(source["years"]) != YEARS:
            raise ValueError(
                f"{control_id}: state and control sources must cover the same explicit "
                "Census release, period and units"
            )
    state_path, state_receipt = verify_stage(cache_dir, source)
    control_path, control_receipt = verify_stage(cache_dir, sources[US_CONTROL])
    cells = read_states(state_path)
    national = read_national_control(control_path)
    if check_counties:
        county_path, county_receipt = verify_stage(cache_dir, sources[US_COUNTY_CONTROL])
        county_totals = read_county_control(county_path)
    else:
        county_receipt = {}
        county_totals = None

    rows = []
    for index, year in enumerate(YEARS):
        state_total = state_young = 0
        for state, name in STATE_NAMES.items():
            total = sum(cells[state, race, age][index] for race, age in product(RACES, STATE_AGES))
            young = sum(cells[state, race, age][index] for race, age in product(RACES, YOUNG_AGES))
            if total <= 0 or not 0 <= young <= total:
                raise ValueError(f"{year} {name}: invalid total or population ages 0–4")
            if county_totals is not None and (total, young) != county_totals[state, year]:
                raise ValueError(
                    f"{year} US-{state:02} {name}: state (all ages {total}, ages 0–4 {young}) "
                    f"disagrees with county control {county_totals[state, year]}"
                )
            state_total += total
            state_young += young
            rows.append((
                f"US-{state:02}", name, panel["geography"], year,
                f"{year}-{panel['reference_month_day']}", total, young, format(young / total, ".12g"),
                panel["universe"], source["source_unit"], source["id"], source["table"],
                source["vintage"], source["release_date"], source["release_id"], state_receipt["sha256"],
                state_receipt["capture_method"], control_receipt["sha256"],
                control_receipt["capture_method"], county_receipt.get("sha256"),
                county_receipt.get("capture_method"),
            ))

        national_total = national[CENSUS_TOTAL_AGE][index]
        national_young = sum(national[age][index] for age in YOUNG_AGES)
        if national_total != sum(national[age][index] for age in NATIONAL_AGES):
            raise ValueError(f"{year}: national all-age row disagrees with sum of national age rows")
        if state_total != national_total or state_young != national_young:
            raise ValueError(
                f"{year}: sum of states/DC (all ages {state_total}, ages 0–4 {state_young}) "
                f"disagrees with national control ({national_total}, {national_young})"
            )

    if len(rows) != panel["expected_rows"] or len(STATE_NAMES) != panel["locations"]:
        raise ValueError("state output dimensions disagree with the demographic contract")
    write_panel(output_path, cache_dir, OUTPUT_FIELDS, rows)
    return len(rows)


def write_panel(output_path, cache_dir, fields, rows):
    if output_path.resolve().is_relative_to(cache_dir.resolve()) or output_path.resolve().is_relative_to(
        ROOT / "data/raw"
    ):
        raise ValueError("write the processed panel outside raw source directories")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".demography-", dir=output_path.parent) as temporary:
        pending = Path(temporary) / "output.csv"
        with pending.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(fields)
            writer.writerows(rows)
        os.replace(pending, output_path)


def main():
    contract, sources = load_contract()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir", type=Path, default=ROOT / "data/raw/demography",
        help="directory for untouched source bytes and manifests",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    stage = commands.add_parser("stage", help="download or stage one source with a SHA-256 receipt")
    stage.add_argument("source", choices=sources)
    stage.add_argument("--from-file", type=Path, help="stage local bytes without claiming retrieval")
    build = commands.add_parser("build-us", help="validate and build the US states/DC CSV")
    build.add_argument("--output", type=Path, default=ROOT / "data/processed/demography/us-states.csv")
    build.add_argument(
        "--check-counties", action="store_true",
        help="also compare each state/DC row to the staged US county file",
    )
    args = parser.parse_args()

    if args.command == "stage":
        source = sources[args.source]
        receipt = stage_source(args.cache_dir, source, contract, args.from_file)
        pin_status = "upstream digest pinned" if source.get("expected_sha256") else "upstream digest unpinned"
        print(f"{args.source}: {receipt['sha256']} ({receipt['capture_method']}, {pin_status})")
    else:
        count = build_states(args.cache_dir, args.output, contract, sources, check_counties=args.check_counties)
        checks = "state sums match the staged national control"
        if args.check_counties:
            checks += " and each state/DC row matches its staged county sum"
        print(f"{count} rows written to {args.output}; {checks}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, csv.Error) as error:
        sys.exit(f"demography: {error}")
