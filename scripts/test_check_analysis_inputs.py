"""Test the analysis input CLI with synthetic bytes in an isolated checkout."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_analysis_inputs import ROOT, load_inventory
from demographic_sources import file_digest, load_contract, stage_source
from test_demographic_sources import write_workbook


class AnalysisInputsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.checkout = Path(temp.name)
        self.script = self.checkout / "scripts/check_analysis_inputs.py"
        self.raw = self.checkout / "data/raw"
        self.control_pins = self.raw / "population-control-pins.toml"
        self.inventory, _, _ = load_inventory()
        for name in (
            "scripts/check_analysis_inputs.py",
            "scripts/check_surveillance_sources.py",
            "scripts/demographic_sources.py",
            "scripts/surveillance_sources.sha256",
            "data/analysis-inputs.toml",
            "data/demographic-sources.toml",
            "data/natality-sources.toml",
        ):
            destination = self.checkout / name
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def prepare_sources(self):
        contract, sources = load_contract()
        for family in ("surveillance", "natality"):
            scope = self.inventory[family]
            pin_path = self.checkout / (scope.get("pins") or scope["contract"])
            pins = pin_path.read_text(encoding="utf-8")
            (self.raw / scope["raw_directory"]).mkdir(parents=True)
            for artifact in scope["artifacts"]:
                path = self.raw / artifact["path"]
                path.write_text(f"Synthetic fixture for {artifact['path']}\n", encoding="utf-8")
                pins = pins.replace(artifact["sha256"], file_digest(path))
            pin_path.write_text(pins, encoding="utf-8")

        scope = self.inventory["population"]
        pin_path = self.checkout / scope["contract"]
        pins = pin_path.read_text(encoding="utf-8")
        local_pins = []
        for source in sources.values():
            source_id = source["id"]
            fixture = self.checkout / source_id
            if source["format"] in ("spreadsheet", "xlsx"):
                write_workbook(fixture)
            else:
                separator = "|" if source["format"] == "pipe-delimited" else ","
                fixture.write_text(f"fixture{separator}{source_id}\n", encoding="utf-8")
            digest = file_digest(fixture)
            if source_id in scope["local_control_pins"]:
                local_pins.append(f'{source_id} = "{digest}"\n')
            else:
                pins = pins.replace(source["expected_sha256"], digest)
                source = {**source, "expected_sha256": digest}
            stage_source(self.raw / scope["raw_directory"], source, contract, fixture)
        pin_path.write_text(pins, encoding="utf-8")
        self.control_pins.write_text("".join(local_pins), encoding="utf-8")

    def cli(self, *args, error=None):
        result = subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.checkout, capture_output=True, text=True, check=False,
        )
        if error is not None:
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(error, result.stderr)
            self.assertEqual(result.stdout, "")
            return None
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def verify(self, *, error=None):
        return self.cli("verify", "--raw-root", str(self.raw),
                        "--population-control-pins", str(self.control_pins), error=error)

    def test_public_inventory_reports_scope_without_local_inputs(self):
        report = self.cli("inventory")
        self.assertFalse(self.raw.exists())
        self.assertFalse((self.script.parent / "__pycache__").exists())
        self.assertEqual(report["analysis_freeze_status"], "pending")
        self.assertEqual({name: len(report[name]["artifacts"]) for name in (
            "surveillance", "natality", "population",
        )}, {"surveillance": 29, "natality": 30, "population": 20})
        self.assertEqual(report["surveillance"]["us"]["antigen"]["absent_rows"], 81)
        self.assertIn("paediatric sentinel sites", report["surveillance"]["jp"]["denominator"])
        self.assertEqual(report["population"]["pr"]["expected_rows"], 7)
        self.assertIn("US Virgin Islands", report["unresolved"]["territories"]["detail"])
        self.assertNotIn("national_births", json.dumps(report))
        pending = [source["id"] for source in report["population"]["artifacts"] if source["sha256"] is None]
        self.assertEqual(pending, ["us-national-control", "us-county-control"])

    def test_verify_reports_only_audit_success_and_leaves_all_files_unchanged(self):
        self.prepare_sources()
        before = {path: path.read_bytes() for path in self.raw.rglob("*") if path.is_file()}
        report = self.verify()
        self.assertEqual(report["verified_artifacts"], {"surveillance": 29, "natality": 30, "population": 20})
        self.assertEqual(report["verified_population_receipts"], 20)
        self.assertFalse(report["analysis_ready"])
        self.assertEqual(report["analysis_freeze_status"], "pending")
        self.assertEqual(before, {path: path.read_bytes() for path in self.raw.rglob("*") if path.is_file()})

    def test_verify_rejects_missing_or_unmatched_sources(self):
        self.prepare_sources()
        path = self.raw / "surveillance-audit/nrevss.csv"
        path.unlink()
        self.verify(error="surveillance-audit/nrevss.csv: missing source file")
        path.write_text("Replacement response\n", encoding="utf-8")
        self.verify(error="surveillance-audit/nrevss.csv: SHA-256 mismatch")

    def test_verify_rejects_changed_natality_control(self):
        self.prepare_sources()
        path = self.raw / "natality/cdc_221896_DS2.pdf"
        path.write_text("Replacement control\n", encoding="utf-8")
        self.verify(error="natality/cdc_221896_DS2.pdf: SHA-256 mismatch")

    def test_verify_rejects_missing_or_wrong_vintage_receipt(self):
        self.prepare_sources()
        path = self.raw / "demography/pr-commonwealth/manifest.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        self.verify(error="pr-commonwealth: stage the source before building")
        receipt["source_vintage"] = "Different release"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        self.verify(error="pr-commonwealth: staged manifest disagrees with source contract")

    def test_verify_rejects_population_receipt_with_wrong_geography_or_reference_dates(self):
        self.prepare_sources()
        path = self.raw / "demography/pr-commonwealth/manifest.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps({**receipt, "geography": "New York"}), encoding="utf-8")
        self.verify(error="pr-commonwealth: staged receipt geography disagrees with the source scope")
        del receipt["reference_dates"]
        path.write_text(json.dumps(receipt), encoding="utf-8")
        self.verify(error="pr-commonwealth: staged receipt reference_dates disagrees with the source scope")

    def test_verify_rejects_missing_private_pin_or_replaced_source_with_new_receipt(self):
        self.prepare_sources()
        self.cli("verify", error="provide --population-control-pins")
        source_dir = self.raw / "demography/us-national-control"
        path = source_dir / "source"
        path.write_bytes(b"Fixture,replacement\n")
        receipt_path = source_dir / "manifest.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt.update(sha256=file_digest(path), bytes=path.stat().st_size)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        self.verify(error="us-national-control: SHA-256 disagrees with the source contract")

    def test_inventory_rejects_an_unpinned_audited_release(self):
        path = self.checkout / "data/natality-sources.toml"
        text = path.read_text(encoding="utf-8")
        pin = self.inventory["natality"]["artifacts"][0]["sha256"]
        path.write_text(text.replace(pin, ""), encoding="utf-8")
        self.cli("inventory", error="jp-table2-2013.csv: missing or invalid repository SHA-256 pin")


if __name__ == "__main__":
    unittest.main()
