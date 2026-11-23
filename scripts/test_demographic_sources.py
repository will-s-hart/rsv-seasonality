"""Exercise the demographic CLI with generated data, without network access."""

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from demographic_sources import STATE_NAMES

SCRIPT = Path(__file__).with_name("demographic_sources.py")
FILE_YEARS = range(2010, 2020)
ESTIMATES = ("ESTIMATESBASE2010", *(f"POPESTIMATE{year}" for year in FILE_YEARS), "CENSUS2020POP")
STATE_HEADER = ("SUMLEV", "REGION", "DIVISION", "STATE", "NAME", "SEX", "ORIGIN", "RACE", "AGE")
NATIONAL_HEADER = ("SEX", "AGE")
NATIONAL_OFFSET = 600 * sum(code + 1 for code in STATE_NAMES) + 210 * 51


def write_fixture(path, header, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow((*header, *ESTIMATES))
        writer.writerows(rows)


def state_rows():
    for code, name in STATE_NAMES.items():
        for race in range(1, 7):
            for age in range(86):
                values = [100 * (code + 1) + 10 * race + age * (year - 2009) for year in FILE_YEARS]
                age_label = "85+" if age == 85 else age
                yield ["040", 1, 1, str(code), name, 0, 0, race, age_label, 999999, *values, 999999]
    # These plausible rows must not get counted together with the published totals.
    yield ["040", 1, 1, "01", "Alabama", 1, 0, 1, 0, *([999999] * 12)]
    yield ["040", 1, 1, "01", "Alabama", 0, 2, 1, 0, *([999999] * 12)]


def national_count(age, year):
    if age == 999:
        return 86 * NATIONAL_OFFSET + 306 * 3655 * (year - 2009)
    if age == 100:
        return 10
    if age > 85:
        return 0
    return NATIONAL_OFFSET + 306 * age * (year - 2009) - (10 if age == 85 else 0)


def national_rows():
    for age in (*range(101), 999):
        values = [national_count(age, year) for year in FILE_YEARS]
        yield [0, "100+" if age == 100 else age, 999999, *values, 999999]
    yield [2, 999, *([999999] * 12)]


class DemographicCLITest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.cache = self.directory / "raw"
        self.states = self.directory / "synthetic-states.csv"
        self.control = self.directory / "synthetic-national.csv"
        self.output = self.directory / "processed.csv"

    def cli(self, *args, error=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--cache-dir", str(self.cache), *map(str, args)],
            text=True, capture_output=True, check=False,
        )
        if error is None:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(error, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        return result

    def stage(self, file, source):
        self.cli("stage", source, "--from-file", file)

    def stage_census(self, states=None, national=None):
        write_fixture(self.states, STATE_HEADER, state_rows() if states is None else states)
        write_fixture(self.control, NATIONAL_HEADER, national_rows() if national is None else national)
        self.stage(self.states, "us-states")
        self.stage(self.control, "us-national-control")

    def build(self, **kwargs):
        return self.cli("build-us", "--output", self.output, **kwargs)

    def test_builds_complete_deterministic_state_panel_with_provenance(self):
        self.stage_census()
        self.assertIn("357 rows written", self.build().stdout)
        first_output = self.output.read_bytes()
        with self.output.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        keys = {(row["location_id"], row["reference_date"]) for row in rows}
        self.assertEqual(len(rows), 357)
        self.assertEqual(len(keys), 357)
        self.assertIn(("US-11", "2019-07-01"), keys)
        self.assertNotIn(("US-72", "2019-07-01"), keys)

        alabama_2013 = rows[0]
        self.assertEqual(alabama_2013["location_id"], "US-01")
        self.assertEqual(alabama_2013["reference_date"], "2013-07-01")
        self.assertEqual(alabama_2013["population_total"], "208980")
        self.assertEqual(alabama_2013["population_age_0_4"], "7290")
        self.assertAlmostEqual(float(alabama_2013["share_age_0_4"]), 7290 / 208980)
        self.assertEqual(alabama_2013["source_sha256"], hashlib.sha256(self.states.read_bytes()).hexdigest())
        self.assertEqual(alabama_2013["control_source_sha256"], hashlib.sha256(self.control.read_bytes()).hexdigest())
        self.assertEqual(alabama_2013["source_capture_method"], "local_file")
        self.assertEqual(alabama_2013["control_capture_method"], "local_file")
        self.assertEqual(alabama_2013["source_release_date"], "2025-09-30")

        new_york_2019 = next(
            row for row in rows if row["location_id"] == "US-36" and row["year"] == "2019"
        )
        self.assertEqual(new_york_2019["population_age_0_4"], "112650")
        self.assertEqual(new_york_2019["population_total"], "2146560")
        self.build()
        self.assertEqual(self.output.read_bytes(), first_output)

    def test_stage_preserves_bytes_and_is_idempotent(self):
        write_fixture(self.states, STATE_HEADER, state_rows())
        self.stage(self.states, "us-states")
        source = self.cache / "us-states"
        original_manifest = (source / "manifest.json").read_bytes()
        receipt = json.loads(original_manifest)
        self.assertEqual(receipt["reference_dates"][0], "2013-07-01")
        self.assertEqual(receipt["capture_method"], "local_file")
        self.assertEqual(receipt["sha256"], hashlib.sha256(self.states.read_bytes()).hexdigest())
        self.assertIsNone(receipt["expected_sha256"])
        self.assertIsNone(receipt["resolved_url"])
        self.assertEqual((source / "source").read_bytes(), self.states.read_bytes())
        self.stage(self.states, "us-states")
        self.assertEqual((source / "manifest.json").read_bytes(), original_manifest)

        self.states.write_bytes(b"A,B\n1,2\n")
        self.cli("stage", "us-states", "--from-file", self.states, error="different bytes already staged")
        self.assertEqual((source / "manifest.json").read_bytes(), original_manifest)

    def test_puerto_rico_workbook_stages_separately(self):
        workbook = self.directory / "synthetic-pr.xlsx"
        with zipfile.ZipFile(workbook, "w") as archive:
            archive.writestr("xl/workbook.xml", "<workbook/>")
        self.stage(workbook, "pr-commonwealth")
        receipt = json.loads((self.cache / "pr-commonwealth" / "manifest.json").read_text())
        self.assertEqual(receipt["geography"], "commonwealth")
        self.assertEqual(receipt["source_table"], "PRC-EST2020INT-AGESEX")
        self.assertEqual(len(receipt["reference_dates"]), 7)
        self.assertFalse((self.cache / "us-states").exists())

    def test_japan_sources_keep_original_reference_date_and_vintage(self):
        csv_path = self.directory / "synthetic-japan.csv"
        csv_path.write_bytes(b"synthetic,csv\n1,2\n")
        self.stage(csv_path, "jp-2015-census")
        receipt = json.loads((self.cache / "jp-2015-census" / "manifest.json").read_text())
        self.assertEqual(receipt["reference_dates"], ["2015-10-01"])
        self.assertEqual(receipt["source_release_date"], "2016-11-24")
        self.assertEqual(receipt["source_unit"], "persons")

    def test_html_response_does_not_leave_a_stage(self):
        blocked = self.directory / "blocked.html"
        blocked.write_text("<html> forbidden, try later </html>", encoding="utf-8")
        self.cli("stage", "us-states", "--from-file", blocked, error="does not resemble CSV")
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_rejects_missing_cell_outside_child_band(self):
        missing = ["040", 1, 1, "1", "Alabama", 0, 0, 1, 24]
        filtered = (row for row in state_rows() if row[:9] != missing)
        self.stage_census(states=filtered)
        self.build(error="missing required cells (1), including (1, 1, 24)")
        self.assertFalse(self.output.exists())

    def test_rejects_duplicate_state_cell_after_numeric_normalization(self):
        rows = list(state_rows())
        duplicate = rows[0].copy()
        duplicate[3] = "01"
        rows.append(duplicate)
        self.stage_census(states=rows)
        self.build(error="duplicate state/race/age cell")

    def test_rejects_territory_in_state_input(self):
        rows = list(state_rows())
        rows[0][3:5] = ["72", "Puerto Rico"]
        self.stage_census(states=rows)
        self.build(error="unexpected state geography 040/72")

    def test_rejects_negative_population_in_requested_year(self):
        rows = list(state_rows())
        rows[0][13] = "-1"
        self.stage_census(states=rows)
        self.build(error="POPESTIMATE2013: expected a nonnegative integer")

    def test_rejects_swapped_year_columns(self):
        header = list(STATE_HEADER + ESTIMATES)
        header[13], header[14] = header[14], header[13]
        with self.states.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(header)
        write_fixture(self.control, NATIONAL_HEADER, national_rows())
        self.stage(self.states, "us-states")
        self.stage(self.control, "us-national-control")
        self.build(error="CSV header does not match the documented file layout")

    def test_rejects_unbalanced_age_band_even_when_all_age_total_matches(self):
        rows = list(national_rows())
        rows[4][6] += 1
        rows[5][6] -= 1
        self.stage_census(national=rows)
        self.output.write_bytes(b"prior output\n")
        self.build(error="2013: sum of states/DC")
        self.assertEqual(self.output.read_bytes(), b"prior output\n")

    def test_rejects_changed_bytes_after_staging(self):
        self.stage_census()
        with (self.cache / "us-states" / "source").open("ab") as stream:
            stream.write(b"\n")
        self.build(error="staged file disagrees with manifest checksum or size")
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
