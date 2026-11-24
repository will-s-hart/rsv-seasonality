import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import check_surveillance_sources as audit
import export_weekly_observations as export
from test_export_weekly_observations import nesid_fixture, write_nrevss_fixture


CLI = Path(__file__).with_name("check_weekly_cutoffs.py")
DATES = {
    "window-start": "2013-01-01",
    "train-through": "2016-12-31",
    "tune-through": "2017-12-31",
    "holdout-through": "2019-12-31",
}


class CutoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.directory = Path(temporary.name)
        write_nrevss_fixture(cls.directory)
        cls.export_path = cls.directory / "weekly.csv"
        with cls.export_path.open("w", encoding="utf-8", newline="") as stream, patch.object(
            audit, "workbook", nesid_fixture
        ), patch.object(audit, "verify_inputs"):
            export.write_observations(cls.directory, stream)
        cls.export_bytes = cls.export_path.read_bytes()
        with cls.export_path.open(encoding="utf-8", newline="") as stream:
            cls.by_key = {
                (row["source_id"], row["region_id"], row["method"],
                 row["source_week_year"], row["source_week_code"]): row
                for row in csv.DictReader(stream)
            }

    def run_cli(self, path, **cutoffs):
        args = [sys.executable, "-B", str(CLI), str(path)]
        for option, value in (DATES | cutoffs).items():
            args.extend((f"--{option}", value))
        return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")

    def read_report(self, path, **cutoffs):
        result = self.run_cli(path, **cutoffs)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def write_rows(self, name, *rows):
        path = self.directory / f"{name}.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=export.Observation._fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_shared_december_31_and_one_day_on_each_side(self):
        japan = self.by_key["NESID", "01", "", "2017", "５２週"]
        us = self.by_key["NREVSS:52kb-ccu2", "2", "PCR", "2018", "1801"]
        path = self.write_rows("shared-date", japan, us)
        report = self.read_report(path)
        japan_count, us_count = report["comparison_counts"]
        self.assertEqual((japan_count["label_period"], japan_count["strict_period"]), ("tune", "tune"))
        self.assertEqual(japan_count["strict_status"], "assigned")
        self.assertEqual(us_count["label_period"], "holdout")
        affected, = report["affected_rows"]
        self.assertEqual((affected["week_start"], affected["week_end"]), ("2017-12-31", "2018-01-06"))
        self.assertEqual(affected["crossed_cutoffs"], ["tune_through"])
        self.assertEqual(affected["strict_status"], "crosses_cutoff")
        self.assertIsNone(affected["strict_period"])
        self.assertTrue(affected["assignments_differ"])

        earlier = self.read_report(path, **{"tune-through": "2017-12-30"})
        japan_count, us_count = earlier["comparison_counts"]
        self.assertEqual(japan_count["strict_status"], "crosses_cutoff")
        self.assertEqual(us_count["strict_period"], "holdout")
        affected, = earlier["affected_rows"]
        self.assertEqual((affected["week_start"], affected["week_end"]), ("2017-12-25", "2017-12-31"))
        self.assertEqual(affected["source_week_code"], "５２週")

        later = self.read_report(path, **{"tune-through": "2018-01-06"})
        affected, = later["affected_rows"]
        self.assertEqual((affected["label_period"], affected["strict_period"]), ("holdout", "tune"))
        self.assertEqual(affected["strict_status"], "assigned")
        self.assertTrue(affected["assignments_differ"])
        self.assertEqual(affected["crossed_cutoffs"], [])

    def test_week_53_and_outer_window(self):
        week_53 = self.by_key["NESID", "01", "", "2015", "５３週"]
        before_start = self.by_key["NREVSS:52kb-ccu2", "2", "PCR", "2013", "1301"]
        last_week = self.by_key["NESID", "01", "", "2019", "５２週"]
        path = self.write_rows("outer-window", week_53, before_start, last_week)
        report = self.read_report(path, **{"train-through": "2015-12-31", "holdout-through": "2019-12-22"})
        japan, start, outside = report["affected_rows"]
        self.assertEqual(japan["source_week_code"], "５３週")
        self.assertEqual((japan["week_start"], japan["week_end"]), ("2015-12-28", "2016-01-03"))
        self.assertEqual(japan["label_period"], "train")
        self.assertEqual(japan["crossed_cutoffs"], ["train_through"])
        self.assertIsNone(japan["strict_period"])
        self.assertEqual(start["crossed_cutoffs"], ["window_start"])
        self.assertEqual(start["strict_status"], "crosses_cutoff")
        self.assertEqual(outside["label_period"], "holdout")
        self.assertIsNone(outside["strict_period"])
        self.assertEqual(outside["strict_status"], "outside_window")
        self.assertEqual(outside["crossed_cutoffs"], [])

        report = self.read_report(path, **{"holdout-through": "2019-12-28"})
        _, last = report["affected_rows"]
        self.assertEqual(last["crossed_cutoffs"], ["holdout_through"])
        self.assertEqual(last["strict_status"], "crosses_cutoff")

    def test_final_vintage_does_not_establish_period_end_availability(self):
        japan = self.by_key["NESID", "01", "", "2017", "５２週"]
        us = self.by_key["NREVSS:52kb-ccu2", "2", "PCR", "2018", "1801"]
        final_rows = self.write_rows("final-vintage", japan, us)
        blank_rows = self.write_rows("blank-vintage", *(
            dict(row, source_version="", source_vintage="") for row in (japan, us)
        ))
        report = self.read_report(final_rows)
        self.assertEqual(report, self.read_report(blank_rows))
        self.assertEqual(
            report["period_end_availability"], "unknown_from_observation_dates_and_source_vintage",
        )
        self.assertNotIn("2022-10-21", json.dumps(report))
        self.assertNotIn("release_date", json.dumps(report))

    def test_reads_export_without_rewriting_or_exposing_outcomes(self):
        report = self.read_report(self.export_path)
        self.assertEqual(report["rows_examined"], 24_455)
        self.assertEqual(sum(group["rows"] for group in report["comparison_counts"]), 24_455)
        self.assertEqual(self.export_path.read_bytes(), self.export_bytes)
        self.assertTrue(any(row["coverage"] == "absent" for row in report["affected_rows"]))
        for row in report["affected_rows"]:
            self.assertFalse({"count", "denominator", "positivity", "source_outlier"} & row.keys())

    def test_invalid_dates_and_missing_columns_fail_without_partial_report(self):
        japan = self.by_key["NESID", "01", "", "2017", "５２週"]
        path = self.write_rows("reversed-interval", japan, dict(japan, week_end="2017-12-24"))
        result = self.run_cli(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("CSV line 3: week_end precedes week_start", result.stderr)

        result = self.run_cli(path, **{"train-through": "2018-01-01"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("expected window start <= train cutoff < tune cutoff < holdout cutoff", result.stderr)

        path.write_text("source_id,week_start\n", encoding="utf-8")
        result = self.run_cli(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("missing calendar columns:", result.stderr)


if __name__ == "__main__":
    unittest.main()
