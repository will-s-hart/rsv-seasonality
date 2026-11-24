#!/usr/bin/env python3
"""Inventory or verify the audited raw inputs without assembling an analysis panel."""

import argparse
import json
import re
import sys
import tomllib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

# A direct invocation must leave the checkout unchanged, including on failure.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

import check_surveillance_sources as surveillance
import demographic_sources as population

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/analysis-inputs.toml"
SHA256 = re.compile(r"[0-9a-f]{64}")


def surveillance_artifacts(scope, years):
    pins = surveillance.load_pins(ROOT / scope["pins"])
    jp = scope["jp"]
    tables = {
        "8-1": "weekly_response",
        "14-1": "weekly_sentinel_denominator",
        "8-2": "weekly_rate_control",
        "12-1": "annual_age_control",
    }
    for year in years:
        for table in surveillance.NESID_TABLES:
            name = surveillance.workbook_name(year, table)
            number, part = table.split("-")
            yield {
                "path": f"{scope['raw_directory']}/{name}",
                "table": table,
                "role": tables[table],
                "source_label_year": year,
                "url": jp["url_template"].format(
                    year=year, number=number.zfill(2), part=part, extension=Path(name).suffix[1:]
                ),
                "sha256": pins.pop(name),
            }
    name = surveillance.CDC_EXPORT
    yield {
        "path": f"{scope['raw_directory']}/{name}",
        "dataset_id": scope["us"]["dataset_id"],
        "role": "weekly_pcr_and_antigen_responses_and_test_denominators",
        "url": scope["us"]["url"],
        "sha256": pins.pop(name),
    }
    if pins:
        raise ValueError("surveillance scope does not match the pinned workbooks and CDC export")


def natality_artifacts(scope, years):
    with (ROOT / scope["contract"]).open("rb") as stream:
        contract = tomllib.load(stream)
    jp, us = contract["japan"], contract["us"]
    expected_years = {str(year) for year in years}
    if (
        list(range(contract["baseline_start"], contract["baseline_end"] + 1)) != years
        or set(jp["years"]) != expected_years
        or set(us["years"]) != expected_years
    ):
        raise ValueError("natality scope does not match the pinned baseline years")

    directory = scope["raw_directory"]
    for year in years:
        release = jp["years"][str(year)]
        for table, id_key, hash_key, role in (
            ("2", "stat_infid", "sha256", "monthly_births"),
            ("43", "table43_stat_infid", "table43_sha256", "prefecture_annual_control"),
        ):
            table_id = release[id_key]
            yield {
                "path": f"{directory}/jp-table{table}-{year}.csv",
                "role": role,
                "release_year": year,
                "stat_infid": table_id,
                "catalogue_updated": release["catalogue_updated"],
                "catalog_url": jp["catalogue_url_template"].format(id=table_id),
                "url": jp["download_url_template"].format(id=table_id),
                "sha256": release[hash_key],
            }

    for group, query_key, hash_key, role in (
        ("state", "state_month_query", "state_month_export_sha256", "state_dc_monthly_births"),
        ("national", "national_month_query", "national_month_export_sha256", "national_monthly_control"),
    ):
        yield {
            "path": f"{directory}/us-wonder-{group}.tsv",
            "role": role,
            "url": us["request_url"],
            "group_by": us[query_key],
            "sha256": us[hash_key],
        }
    for year in years:
        release = us["years"][str(year)]
        for url_key, hash_key, table, role in (
            ("report_url", "report_sha256", release["residence_table"], "state_dc_annual_control"),
            ("monthly_report_url", "monthly_report_sha256", us["monthly_control_table"], "national_monthly_control"),
        ):
            url = release[url_key]
            yield {
                "path": f"{directory}/{Path(urlsplit(url).path).name}",
                "role": role,
                "release": f"NCHS final Births report for {year}",
                "table": table,
                "url": url,
                "sha256": release[hash_key],
            }

    scope["jp"].update({field: jp[field] for field in (
        "publisher", "series", "universe", "residence", "terms_url", "expected_prefecture_months",
    )})
    scope["us"].update({field: us[field] for field in (
        "publisher", "series", "universe", "residence", "expected_state_months",
        "year_filter", "show_totals", "show_zero_values", "show_suppressed", "measure",
    )})


def population_artifacts(scope, years, contract, sources):
    if years != contract["years"]:
        raise ValueError("population scope does not match the demographic baseline years")
    local_ids = scope["local_control_pins"]
    if len(set(local_ids)) != len(local_ids) or set(local_ids) != {
        source_id for source_id, source in sources.items() if "expected_sha256" not in source
    }:
        raise ValueError("population scope does not match the controls awaiting local audit pins")

    unmatched = set(sources)
    for panel_id, panel in contract["panels"].items():
        scope[panel_id].update(panel, age_band=contract["age_band"])
        for source_id in scope[panel_id]["sources"]:
            if source_id not in unmatched or sources[source_id]["panel"] != panel_id:
                raise ValueError(f"{source_id}: missing, duplicate or assigned to the wrong population panel")
            unmatched.remove(source_id)
            source = sources[source_id]
            yield {
                **source,
                "publisher": contract["publishers"][source["publisher"]]["name"],
                "terms_url": contract["publishers"][source["publisher"]]["terms_url"],
                "path": f"{scope['raw_directory']}/{source_id}/source",
                "receipt_path": f"{scope['raw_directory']}/{source_id}/manifest.json",
                "sha256": source.get("expected_sha256"),
            }
    if unmatched:
        raise ValueError(f"population sources missing from scope: {', '.join(sorted(unmatched))}")


def load_inventory():
    with MANIFEST.open("rb") as stream:
        inventory = tomllib.load(stream)
    if inventory["schema_version"] != 1 or inventory["analysis_freeze_status"] != "pending":
        raise ValueError("unsupported analysis input manifest version or freeze status")
    years = inventory["source_label_years"]
    if years != list(surveillance.YEARS) or ROOT / inventory["population"]["contract"] != population.CONTRACT_PATH:
        raise ValueError("analysis scope does not match the audited years or demographic contract")

    contract, sources = population.load_contract()
    artifacts = {
        "surveillance": list(surveillance_artifacts(inventory["surveillance"], years)),
        "natality": list(natality_artifacts(inventory["natality"], years)),
        "population": list(population_artifacts(inventory["population"], years, contract, sources)),
    }
    paths = set()
    for family, entries in artifacts.items():
        for artifact in entries:
            path = artifact["path"]
            if path in paths:
                raise ValueError(f"{path}: duplicate analysis input")
            paths.add(path)
            if family == "population" and artifact["id"] in inventory["population"]["local_control_pins"]:
                continue
            if not isinstance(artifact["sha256"], str) or not SHA256.fullmatch(artifact["sha256"]):
                raise ValueError(f"{path}: missing or invalid repository SHA-256 pin")
        inventory[family]["artifacts"] = entries
    return inventory, contract, sources


def read_control_pins(path, expected_ids):
    if path is None:
        raise ValueError("provide --population-control-pins from the original department audit receipts")
    with path.open("rb") as stream:
        pins = tomllib.load(stream)
    if set(pins) != set(expected_ids) or any(
        not isinstance(pin, str) or not SHA256.fullmatch(pin) for pin in pins.values()
    ):
        raise ValueError("population control pins must contain exactly the required source IDs with SHA-256 hashes")
    return pins


def verify_inputs(inventory, contract, sources, raw_root, control_pin_path):
    local_ids = inventory["population"]["local_control_pins"]
    control_pins = read_control_pins(control_pin_path, local_ids)
    counts = {}
    for family in ("surveillance", "natality"):
        artifacts = inventory[family]["artifacts"]
        for artifact in artifacts:
            path = raw_root / artifact["path"]
            if not path.is_file():
                raise ValueError(f"{artifact['path']}: missing source file")
            if population.file_digest(path) != artifact["sha256"]:
                raise ValueError(f"{artifact['path']}: SHA-256 mismatch")
        counts[family] = len(artifacts)

    scope = inventory["population"]
    for artifact in scope["artifacts"]:
        source_id = artifact["id"]
        source = sources[source_id]
        expected = control_pins.get(source_id, artifact["sha256"])
        try:
            _, receipt = population.verify_stage(
                raw_root / scope["raw_directory"], {**source, "expected_sha256": expected}
            )
            captured = datetime.fromisoformat(receipt["captured_at_utc"])
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{source_id}: {error}") from error
        if captured.utcoffset() != timedelta(0):
            raise ValueError(f"{source_id}: staged receipt requires a UTC capture timestamp")
        for field, value in population.receipt_scope(source, contract).items():
            if field not in receipt or receipt[field] != value:
                raise ValueError(f"{source_id}: staged receipt {field} disagrees with the source scope")
    counts["population"] = len(scope["artifacts"])
    return {
        "audited_source_bytes": "verified",
        "verified_artifacts": counts,
        "verified_population_receipts": counts["population"],
        "analysis_freeze_status": inventory["analysis_freeze_status"],
        "analysis_ready": False,
        "unresolved": inventory["unresolved"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inventory", help="print public coverage and artifact metadata as JSON")
    verify = commands.add_parser("verify", help="verify the local files and population receipts")
    verify.add_argument("--raw-root", type=Path, default=ROOT / "data/raw")
    verify.add_argument("--population-control-pins", type=Path, help="TOML pins from the original audit receipts")
    args = parser.parse_args()

    try:
        inventory, contract, sources = load_inventory()
        report = inventory if args.command == "inventory" else verify_inputs(
            inventory, contract, sources, args.raw_root, args.population_control_pins
        )
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(f"analysis input audit failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
