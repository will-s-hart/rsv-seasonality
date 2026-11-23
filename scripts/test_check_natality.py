"""Exercise the natality validator with synthetic aggregate extracts."""

import csv
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from check_natality import MANIFEST, MONTHS, PREFECTURES, STATES_AND_DC

SCRIPT = Path(__file__).with_name("check_natality.py")


def fixture_rows(country, *, match_controls=True):
    """Spread invented counts across all months and residence buckets."""
    with MANIFEST.open("rb") as stream:
        controls = tomllib.load(stream)[country]["years"]
    japan = country == "japan"
    locations = sorted(PREFECTURES | {"abroad", "unknown"} if japan else STATES_AND_DC)
    rows = []
    for year, control in controls.items():
        annual = control["national_births"] if match_controls else 1200
        monthly = {location: [] for location in [*locations, "national"]}
        cells = len(locations) * len(MONTHS)
        base, remainder = divmod(annual, cells)
        for month in MONTHS:
            for index, location in enumerate(locations):
                cell = (int(month) - 1) * len(locations) + index
                count = base + (cell < remainder)
                monthly[location].append((count, count // 2, count - count // 2))
            components = [monthly[location][-1] for location in locations]
            monthly["national"].append(tuple(map(sum, zip(*components))))
        for location, counts in monthly.items():
            annual_counts = tuple(map(sum, zip(*counts)))
            for period, values in zip((*MONTHS, "annual"), (*counts, annual_counts)):
                rows.append([year, period, location, *(values if japan else values[:1])])
    return rows


class NatalityCommandTests(unittest.TestCase):
    def run_check(self, country, rows, *args):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "natality.csv"
            header = ["year", "month", "location_id", "births"]
            if country == "japan":
                header += ["male", "female"]
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerows(rows)
            return subprocess.run(
                [sys.executable, str(SCRIPT), country, str(path), *args],
                capture_output=True,
                text=True,
                check=False,
            )

    def assert_invalid(self, result, reason):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(reason, result.stderr)

    def test_japan_full_grid_including_abroad_and_unknown(self):
        result = self.run_check(
            "japan", fixture_rows("japan"), "--confirm-japan-control-scope"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3,948", result.stdout)

    def test_japan_candidate_control_requires_scope_confirmation(self):
        rows = fixture_rows("japan", match_controls=False)
        result = self.run_check("japan", rows)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("controls are pending", result.stdout)
        self.assert_invalid(
            self.run_check("japan", rows, "--confirm-japan-control-scope"),
            "published 1029817",
        )

    def test_missing_japan_abroad_bucket(self):
        rows = [row for row in fixture_rows("japan") if row[2] != "abroad"]
        self.assert_invalid(self.run_check("japan", rows), "('2013', '01', 'abroad')")

    def test_unexplained_japan_national_difference(self):
        rows = [row for row in fixture_rows("japan") if row[2] != "unknown"]
        self.assert_invalid(self.run_check("japan", rows), "residence components sum")

    def test_japan_sex_reconciliation(self):
        rows = fixture_rows("japan")
        rows[0][4] += 1
        self.assert_invalid(self.run_check("japan", rows), "male plus female")

    def test_us_full_states_dc_grid(self):
        result = self.run_check("us", fixture_rows("us"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("4,284", result.stdout)

    def test_us_reference_totals_are_required(self):
        rows = fixture_rows("us", match_controls=False)
        self.assert_invalid(self.run_check("us", rows), "published 3932181")

    def test_us_annual_residence_control(self):
        rows = fixture_rows("us")
        annual = next(row for row in rows if row[:3] == ["2013", "annual", "01"])
        annual[3] += 1
        self.assert_invalid(self.run_check("us", rows), "01 births: months sum")

    def test_duplicate_or_missing_month(self):
        rows = fixture_rows("us")
        self.assert_invalid(self.run_check("us", rows + [rows[0]]), "duplicate cell")
        self.assert_invalid(self.run_check("us", rows[1:]), "missing 1 cells")

    def test_territory_code_in_us_panel(self):
        rows = fixture_rows("us")
        self.assert_invalid(
            self.run_check("us", rows + [["2013", "01", "72", 100]]),
            "unexpected year, month or location",
        )

    def test_suppressed_count(self):
        rows = fixture_rows("us")
        rows[0][3] = "Suppressed"
        self.assert_invalid(self.run_check("us", rows), "nonnegative integer counts")


if __name__ == "__main__":
    unittest.main()
