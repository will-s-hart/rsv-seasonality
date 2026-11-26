import csv
from datetime import date, timedelta
from hashlib import sha256
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import check_surveillance_sources as audit


class AssaySummaryCLI(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        scripts = Path(__file__).parent
        for name in ("check_surveillance_sources.py", "summarize_nrevss_assays.py"):
            shutil.copyfile(scripts / name, self.directory / name)
        self.manifest = self.directory / audit.MANIFEST.name
        self.source = self.directory / audit.CDC_EXPORT
        self.make_source()

    def make_source(self, replace_region=None):
        # An entirely invented release with the catalogue's row counts and code sets.
        region_one = {
            date(2013, 1, 5): ((5, 25), (10, 100)),
            date(2013, 1, 12): ((15, 100), (0, 25)),
            date(2013, 1, 19): ((20, 100), (40, 100)),
            date(2013, 1, 26): ((0, 100), (0, 100)),
            date(2013, 2, 2): ((50, 200), (1, 20)),
            date(2013, 2, 9): ((0, 20), (20, 40)),
            date(2015, 1, 3): ((1, 100), (31, 100)),  # MMWR 2014-W53
        }
        with self.source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("testtype", "repweekdate", "repweekcode", "hhs_region", "rsvpos", "rsvtest", "outlier"))
            for week in range(521):
                day = date(2010, 7, 10) + timedelta(weeks=week)
                raw_date = f"{day.day:02d}{audit.MONTHS[day.month - 1]}{day.year}"
                code = audit.mmwr_week_code(day)
                for region in audit.HHS_REGIONS:
                    pcr, antigen = region_one.get(day, ((0, 10), (0, 10))) if region == 1 else ((0, 10), (0, 10))
                    if region == 2 and day == date(2013, 1, 12):
                        antigen = (0, 0)
                    region_code = replace_region if region == 10 and week == 0 and replace_region else region
                    writer.writerow(("PCR", raw_date, code, region_code, *pcr, 0))
                    if (region == 2 and (week < 2 or day == date(2013, 1, 5))) or (region == 8 and week >= 417):
                        continue
                    writer.writerow(("Antigen", raw_date, code, region, *antigen, 0))
        fixture_pin = sha256(self.source.read_bytes()).hexdigest()
        pins = audit.load_pins()
        pins[audit.CDC_EXPORT] = fixture_pin
        self.manifest.write_text("".join(f"{digest}  {name}\n" for name, digest in pins.items()), encoding="ascii")

    def run_cli(self):
        return subprocess.run(
            [sys.executable, "-B", str(self.directory / "summarize_nrevss_assays.py"), str(self.source)],
            capture_output=True, text=True, check=False,
        )

    def test_same_region_week_pairing_and_thresholds(self):
        before = self.source.read_bytes()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, self.run_cli().stdout)
        self.assertEqual(before, self.source.read_bytes())

        rows = {
            (row["hhs_region"], row["mmwr_year"], row["min_tests_per_assay"]): row
            for row in csv.DictReader(StringIO(result.stdout))
        }
        self.assertEqual(len(rows), 10 * 8 * 3)
        self.assertEqual({region for region, _, _ in rows}, {str(region) for region in range(1, 11)})
        region_two = rows["2", "2013", "1"]
        self.assertEqual(region_two["both_rows_present"], "51")
        self.assertEqual(region_two["antigen_absent"], "1")
        self.assertEqual(region_two["antigen_zero_tests"], "1")
        self.assertEqual(region_two["both_tested"], "50")
        self.assertEqual(region_two["antigen_zero_positivity"], "50")
        self.assertEqual(region_two["equal_positivity"], "50")
        self.assertEqual(rows["2", "2013", "25"]["antigen_minus_pcr_pp_median"], "")

        region_one = rows["1", "2013", "25"]
        fields = {
            "both_tested": "52",
            "pcr_only_below_min": "1",
            "antigen_only_below_min": "1",
            "both_below_min": "46",
            "retained_pairs": "4",
            "pcr_zero_positivity": "1",
            "antigen_zero_positivity": "2",
            "pcr_tests_median": "100.0",
            "antigen_tests_median": "100.0",
            "equal_test_counts": "2",
            "pcr_more_tests": "1",
            "median_pcr_to_antigen_test_ratio": "1.000000",
            "pcr_higher_positivity": "2",
            "antigen_higher_positivity": "1",
            "equal_positivity": "1",
            "antigen_minus_pcr_pp_q25": "-11.250000",
            "antigen_minus_pcr_pp_median": "-5.000000",
            "antigen_minus_pcr_pp_q75": "5.000000",
        }
        self.assertEqual({field: region_one[field] for field in fields}, fields)
        self.assertEqual(rows["1", "2013", "100"]["retained_pairs"], "2")
        self.assertEqual(rows["1", "2013", "100"]["antigen_minus_pcr_pp_median"], "10.000000")

        singleton = rows["1", "2014", "100"]
        self.assertEqual(singleton["expected_weeks"], "53")
        self.assertEqual(singleton["retained_pairs"], "1")
        self.assertEqual(singleton["antigen_minus_pcr_pp_q25"], "30.000000")
        self.assertEqual(singleton["antigen_minus_pcr_pp_q75"], "30.000000")
        self.assertEqual(rows["1", "2015", "100"]["retained_pairs"], "0")
        self.assertEqual(rows["8", "2019", "1"]["antigen_absent"], "52")

    def test_bad_checksum_returns_no_summary(self):
        with self.source.open("ab") as stream:
            stream.write(b"\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("SHA-256 mismatch", result.stderr)

    def test_national_row_is_rejected_even_with_matching_pin(self):
        self.make_source(replace_region="US")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unexpected CDC geography inventory", result.stderr)


if __name__ == "__main__":
    unittest.main()
