"""Exercise population controls with synthetic workbooks and geographic data."""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from demographic_sources import COUNTY_YEAR_CODES
from japan_population import PREFECTURES, prefecture_age, reconcile
from test_demographic_sources import fixture_checkout

EXPECTED_DATES = {
    5: "2013-07-01", 6: "2014-07-01", 7: "2015-07-01", 8: "2016-07-01",
    9: "2017-07-01", 10: "2018-07-01", 11: "2019-07-01",
}


class PopulationCLITest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.scripts = self.root / "checkout" / "scripts"
        fixture_checkout(self.scripts.parent, "check_population.py", "japan_population.py")
        self.cache = self.root / "raw"
        self.output = self.root / "processed" / "puerto-rico.csv"

    def cli(self, script, *args, error=None):
        result = subprocess.run(
            [sys.executable, "-B", str(self.scripts / script), "--cache-dir", str(self.cache), *map(str, args)],
            text=True, capture_output=True, check=False,
        )
        if error is None:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(error, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        return result.stdout

    def stage_pr(self, fault=None):
        names = {f"{code:03}": f"Peña {code} Municipio" for code in range(1, 79)}
        codes = self.root / "codes.txt"
        with codes.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="|")
            writer.writerow(("STATE", "STATEFP", "COUNTYFP", "COUNTYNAME"))
            for code, name in names.items():
                writer.writerow(("PR", "71" if fault == "fips" and code == "001" else "72", code, name))

        csv_path = self.root / "municipios.csv"
        with csv_path.open("w", encoding="cp1252", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("SUMLEV", "MUNICIPIO", "NAME", "YEAR", "POPESTIMATE", "UNDER5_TOT", "AGE04_TOT"))
            for code, name in names.items():
                # Include the April endpoints and earlier July counts to test filtering.
                for year_code in range(1, 13):
                    row = ["050", code, name, year_code, 1000 + year_code, 10 + year_code, 10 + year_code]
                    if (code, year_code) == ("001", 5):
                        if fault == "missing":
                            continue
                        if fault == "scope":
                            row[0] = "040"
                        if fault == "band":
                            row[6] += 1
                        if fault == "disagree":
                            row[4] += 1
                        if fault == "duplicate":
                            writer.writerow(row)
                    writer.writerow(row)

        workbook_path = self.root / "commonwealth.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "PRC-EST2020INT-AGESEX"
        for cell, value in {
            "A2": (
                "Annual Intercensal Estimates of the Resident Population for Selected Age Groups "
                "by Sex for Puerto Rico Commonwealth: April 1, 2010 to April 1, 2020"
            ),
            "B3": "April 1, 2010 Estimates Base",
            "E3": "Population Estimate (as of July 1)",
            "AI3": "April 1, 2020 Census",
            "A6": "Total",
            "A7": ".Under 5 years",
            "A27": ".Under 5 years",
            "A45": "Source: U.S. Census Bureau, Population Division",
            "A46": "Release Date: September 2025",
        }.items():
            sheet[cell] = value
        for code, date in EXPECTED_DATES.items():
            year = int(date[:4])
            column = 14 + 3 * (code - 5)
            sheet.cell(4, column, 2012 if fault == "date" and code == 5 else year)
            for offset, sex in enumerate(("Total\nPopulation", "Male", "Female")):
                sheet.cell(5, column + offset, sex)
            sheet.cell(6, column, (1000 + code) * 78)
            sheet.cell(7, column, (10 + code) * 78)
            sheet.cell(27, column, (10 + code) * 78)
        workbook.save(workbook_path)

        for source, path in (
            ("pr-commonwealth", workbook_path), ("pr-municipios", csv_path), ("pr-municipio-codes", codes),
        ):
            self.cli("demographic_sources.py", "stage", source, "--from-file", path)

    def build_pr(self, error=None):
        return self.cli("check_population.py", "build-pr", "--output", self.output, error=error)

    def test_cli_writes_seven_july_rows_with_exact_year_mapping_and_controls(self):
        self.stage_pr()
        self.assertIn("7 Puerto Rico commonwealth rows match", self.build_pr())
        self.assertEqual(
            {code: f"{year}-07-01" for code, year in COUNTY_YEAR_CODES.items()}, EXPECTED_DATES,
        )
        with self.output.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["reference_date"] for row in rows], list(EXPECTED_DATES.values()))
        for code, row in zip(EXPECTED_DATES, rows, strict=True):
            self.assertEqual(row["location_id"], "PR-72")
            self.assertEqual(int(row["population_total"]), (1000 + code) * 78)
            self.assertEqual(int(row["population_age_0_4"]), (10 + code) * 78)
            controls = json.loads(row["control_sources"])
            self.assertEqual([c["source_id"] for c in controls], ["pr-municipios", "pr-municipio-codes"])

    def test_cli_rejects_wrong_workbook_july_year(self):
        self.stage_pr("date")
        self.build_pr("unexpected header")
        self.assertFalse(self.output.exists())

    def test_cli_rejects_wrong_fips(self):
        self.stage_pr("fips")
        self.build_pr("invalid or duplicate Puerto Rico geography")

    def test_cli_rejects_wrong_summary_level(self):
        self.stage_pr("scope")
        self.build_pr("SUMLEV 050 municipio in FIPS 72")

    def test_cli_rejects_missing_municipio(self):
        self.stage_pr("missing")
        self.build_pr("expected all 78 municipios in each target year")

    def test_cli_rejects_duplicate_municipio(self):
        self.stage_pr("duplicate")
        self.build_pr("duplicate municipio-year")

    def test_cli_rejects_disagreeing_under5_and_age04(self):
        self.stage_pr("band")
        self.build_pr("UNDER5_TOT and AGE04_TOT disagree")

    def test_cli_rejects_companion_disagreement_and_preserves_prior_output(self):
        self.stage_pr("disagree")
        self.output.parent.mkdir()
        self.output.write_text("prior output\n")
        self.build_pr("2013: workbook and municipio sums disagree")
        self.assertEqual(self.output.read_text(), "prior output\n")


class JapanPopulationTest(unittest.TestCase):
    def test_revised_age_selects_2019_total_population_both_sexes_with_prefecture_codes(self):
        rows = [[None] * 31 for _ in range(17)]
        for row, col, text in (
            (5, 20, "Table 10. Population by Age (Five-Year Groups) and Sex"),
            (5, 21, "for Prefectures - Total population, Japanese population, October 1, 2019 - Continued"),
            (8, 31, "(Thousand persons)"),
            (11, 26, "Total population Both sexes"),
            (14, 14, "0～4歳"),
            (17, 13, "Total"),
        ):
            rows[row - 1][col - 1] = text
        for group in ("19", "20", "22"):
            for code in ("00", *sorted(PREFECTURES)):
                row = ["01000", None, group, "01", None, None, None, None, code, code, None, None]
                if code == "00":
                    row[7:12] = ["全国", None, None, None, "Japan"]
                total = 4700 if code == "00" else 100
                rows.append([*row, total, 5 if group == "19" else 3])
        age = prefecture_age(rows, 2019, "fixture", revised=True)
        self.assertEqual(set(age), {"00", *PREFECTURES})
        self.assertEqual(age["47"], ("47", 100, 5))

    def test_exact_and_rounded_reconciliation_enforce_distinct_precision(self):
        age = {code: (code, 100, 10) for code in PREFECTURES}
        age["00"] = ("全国", 4701, 468)
        totals = {code: row[:2] for code, row in age.items()}
        self.assertEqual(reconcile(2016, age, totals, (4701, 468), rounded=True), (-1, 2))
        with self.assertRaisesRegex(ValueError, "published precision"):
            reconcile(2015, age, totals, (4701, 468), rounded=False)
        with self.assertRaisesRegex(ValueError, "national line disagrees"):
            reconcile(2016, age, totals, (4702, 468), rounded=True)
        totals["01"] = ("01", 101)
        with self.assertRaisesRegex(ValueError, "all ages disagree"):
            reconcile(2016, age, totals, (4701, 468), rounded=True)


if __name__ == "__main__":
    unittest.main()
