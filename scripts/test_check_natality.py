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


def source_years(country):
    with MANIFEST.open("rb") as stream:
        return tomllib.load(stream)[country]["years"]


def fixture_rows(country, *, match_controls=True, japan_without_unknown=()):
    """Spread invented counts across all months and residence buckets."""
    japan = country == "japan"
    rows = []
    for year, control in source_years(country).items():
        if japan:
            locations = sorted(PREFECTURES | {"abroad", "unknown"})
            if year in japan_without_unknown:
                locations.remove("unknown")
        else:
            locations = sorted(STATES_AND_DC)
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


def japan_contract_rows(*, without_unknown=()):
    # The fixture declares bucket presence independently of the extract under test.
    return [
        [year, source["stat_infid"], source["catalogue_updated"].isoformat(),
         "present", "absent" if year in without_unknown else "present"]
        for year, source in source_years("japan").items()
    ]


def us_annual_control_rows():
    # Use the unmodified synthetic baseline, even when the tested extract is altered.
    sources = source_years("us")
    return [
        [year, location, count, sources[year]["report_url"], sources[year]["residence_table"]]
        for year, period, location, count in fixture_rows("us")
        if period == "annual" and location != "national"
    ]


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


class NatalityCommandTests(unittest.TestCase):
    def run_check(self, country, rows, *args, reference_rows=None, include_reference=True):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "natality.csv"
            reference_path = Path(directory) / "reference.csv"
            header = ["year", "month", "location_id", "births"]
            if country == "japan":
                header += ["male", "female"]
                reference_flag = "--japan-residence-contract"
                reference_header = ["year", "stat_infid", "catalogue_updated", "abroad", "unknown"]
                if reference_rows is None:
                    reference_rows = japan_contract_rows()
            else:
                reference_flag = "--us-annual-controls"
                reference_header = ["year", "location_id", "births", "report_url", "residence_table"]
                if reference_rows is None:
                    reference_rows = us_annual_control_rows()
            write_csv(path, header, rows)
            command = [sys.executable, str(SCRIPT), country, str(path), *args]
            if include_reference:
                write_csv(reference_path, reference_header, reference_rows)
                command += [reference_flag, str(reference_path)]
            return subprocess.run(command, capture_output=True, text=True, check=False)

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

    def test_japan_required_unknown_cannot_be_folded_into_prefecture(self):
        rows = fixture_rows("japan")
        unknown = {row[1]: row[3:] for row in rows if row[0] == "2013" and row[2] == "unknown"}
        for row in rows:
            if row[0] == "2013" and row[2] == "01":
                row[3:] = [value + extra for value, extra in zip(row[3:], unknown[row[1]])]
        rows = [row for row in rows if row[0] != "2013" or row[2] != "unknown"]
        self.assert_invalid(self.run_check("japan", rows), "('2013', '01', 'unknown')")

    def test_japan_contract_can_declare_unknown_absent_for_one_year(self):
        years_without_unknown = ("2013",)
        contract = japan_contract_rows(without_unknown=years_without_unknown)
        rows = fixture_rows("japan", japan_without_unknown=years_without_unknown)
        result = self.run_check("japan", rows, reference_rows=contract)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_invalid(
            self.run_check("japan", fixture_rows("japan"), reference_rows=contract),
            "unexpected year, month or location",
        )

    def test_japan_requires_complete_contract_for_named_vintages(self):
        rows = japan_contract_rows()
        extract = fixture_rows("japan")
        self.assert_invalid(
            self.run_check("japan", extract, reference_rows=rows[1:]),
            "missing Japan residence contract years 2013",
        )
        rows[0][2] = "2021-04-19"
        self.assert_invalid(
            self.run_check("japan", extract, reference_rows=rows),
            "file ID or catalogue update differs from the manifest",
        )

    def test_unexplained_japan_national_difference(self):
        rows = fixture_rows("japan")
        january = next(row for row in rows if row[:3] == ["2013", "01", "abroad"])
        annual = next(row for row in rows if row[:3] == ["2013", "annual", "abroad"])
        for row in (january, annual):
            row[3] += 1
            row[4] += 1
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

    def test_us_counts_cannot_be_moved_between_states_with_totals_preserved(self):
        rows = fixture_rows("us")
        for row in rows:
            if row[0] == "2013" and row[1] in {"01", "annual"}:
                if row[2] == "01":
                    row[3] += 1
                elif row[2] == "02":
                    row[3] -= 1
        self.assert_invalid(self.run_check("us", rows), "2013 01: annual births")

    def test_us_requires_complete_controls_from_named_reports(self):
        controls = us_annual_control_rows()
        rows = fixture_rows("us")
        self.assert_invalid(
            self.run_check("us", rows, reference_rows=controls[1:]),
            "missing 1 US annual controls",
        )
        self.assert_invalid(
            self.run_check("us", rows, reference_rows=controls + [controls[0]]),
            "duplicate US annual control",
        )
        controls[0][4] = 6
        self.assert_invalid(
            self.run_check("us", rows, reference_rows=controls),
            "report URL or table differs from the manifest",
        )

    def test_cli_requires_country_reference_input(self):
        for country, flag in (("us", "--us-annual-controls"), ("japan", "--japan-residence-contract")):
            with self.subTest(country=country):
                result = self.run_check(country, fixture_rows(country), include_reference=False)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(f"requires {flag}", result.stderr)

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
