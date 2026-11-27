import csv
from datetime import date, timedelta
import json
from pathlib import Path
from statistics import mean
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


CLI = Path(__file__).with_name("check_weekly_cutoffs.py")
MIDDLE_END = date(2017, 12, 30)
MIDDLE_WEEK = {
    "source_id": "synthetic",
    "source_calendar": "fixture",
    "source_week_year": "2017",
    "source_week_code": "52",
    "week_start": "2017-12-24",
    "week_end": MIDDLE_END.isoformat(),
    "region_id": "fixture",
    "method": "fixture",
    "coverage": "reported",
}
RAW = dict(MIDDLE_WEEK, interval_kind="raw", contributor_start="", contributor_end="")
DERIVED = dict(
    MIDDLE_WEEK, interval_kind="derived",
    contributor_start="2017-12-17", contributor_end="2018-01-06",
)


class ContributorIntervalTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "weekly.csv"

    def run_cli(self, rows, fields=tuple(DERIVED), tune_through="2017-12-31"):
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        before = self.path.read_bytes()
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), str(self.path),
             "--window-start", "2013-01-01", "--train-through", "2016-12-31",
             "--tune-through", tune_through, "--holdout-through", "2019-12-31"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(self.path.read_bytes(), before)
        return result

    def test_centered_middle_week_declares_later_contribution(self):
        ends = (date(2017, 12, 23), MIDDLE_END, date(2018, 1, 6))
        weekly_positives = dict(zip(ends, (1, 2, 3)))
        for later_positives, expected_centered in ((3, 2), (30, 11)):
            with self.subTest(later_positives=later_positives):
                weekly_positives[ends[-1]] = later_positives
                tests_per_week = 100
                weekly_pct = {
                    day: positives / tests_per_week * 100
                    for day, positives in weekly_positives.items()
                }
                raw_pct = weekly_pct[MIDDLE_END]
                centered_pct = mean(weekly_pct.values())
                self.assertAlmostEqual(raw_pct, 2)
                self.assertAlmostEqual(centered_pct, expected_centered)

                # Only the two observations labeled with the middle week are compared.
                raw = dict(RAW, positivity=raw_pct)
                derived = dict(
                    DERIVED, positivity=centered_pct,
                    contributor_start=(ends[0] - timedelta(days=6)).isoformat(),
                    contributor_end=ends[-1].isoformat(),
                )
                result = self.run_cli((raw, derived), fields=tuple(raw))
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["rows_examined"], 2)
                raw_count, derived_count = report["comparison_counts"]
                self.assertEqual(raw_count["interval_kind"], "raw")
                self.assertEqual(raw_count["strict_period"], "tune")
                self.assertEqual(derived_count["interval_kind"], "derived")
                self.assertIsNone(derived_count["strict_period"])
                affected, = report["affected_rows"]
                self.assertEqual(affected["interval_kind"], "derived")
                self.assertEqual(affected["week_end"], "2017-12-30")
                self.assertEqual(affected["contributor_start"], "2017-12-17")
                self.assertEqual(affected["contributor_end"], "2018-01-06")
                self.assertEqual(affected["strict_status"], "crosses_cutoff")
                self.assertEqual(affected["crossed_cutoffs"], ["tune_through"])
                self.assertNotIn("positivity", affected)
                self.assertEqual(
                    report["period_end_availability"],
                    "unknown_from_observation_dates_and_source_vintage",
                )

    def test_contributor_end_can_land_on_period_end(self):
        result = self.run_cli((DERIVED,), tune_through="2018-01-06")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        count, = report["comparison_counts"]
        self.assertEqual(count["strict_period"], "tune")
        self.assertEqual(count["strict_status"], "assigned")
        self.assertEqual(report["affected_rows"], [])

    def test_contributor_start_can_cross_into_labeled_period(self):
        result = self.run_cli((DERIVED,), tune_through="2017-12-23")
        self.assertEqual(result.returncode, 0, result.stderr)
        affected, = json.loads(result.stdout)["affected_rows"]
        self.assertEqual(affected["strict_status"], "crosses_cutoff")
        self.assertEqual(affected["crossed_cutoffs"], ["tune_through"])

    def test_legacy_header_keeps_raw_report_shape(self):
        raw = dict(MIDDLE_WEEK, observation_type="rsv_test_detections")
        result = self.run_cli((raw,), fields=tuple(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        count, = report["comparison_counts"]
        self.assertNotIn("interval_kind", count)
        self.assertEqual(count["strict_period"], "tune")
        self.assertEqual(report["affected_rows"], [])

    def test_partial_contributor_header_fails(self):
        raw = dict(MIDDLE_WEEK, contributor_start="")
        result = self.run_cli((raw,), fields=tuple(raw))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("missing contributor columns: contributor_end, interval_kind", result.stderr)

    def test_invalid_contributor_rows_fail_without_partial_report(self):
        cases = (
            (dict(RAW, interval_kind=""), "interval_kind must be raw or derived"),
            (dict(RAW, interval_kind="derived"), "derived observations require"),
            (dict(DERIVED, contributor_start=""), "derived observations require"),
            (dict(DERIVED, contributor_end=""), "derived observations require"),
            (dict(DERIVED, interval_kind="raw"), "raw observations require blank"),
            (dict(DERIVED, contributor_start="20171217"), "expected a YYYY-MM-DD date"),
            (dict(DERIVED, contributor_start="2018-01-07"), "contributor_end precedes"),
            (dict(DERIVED, contributor_start="2017-12-25"), "contributor interval must contain the labeled week"),
            (dict(DERIVED, contributor_end="2017-12-29"), "contributor interval must contain the labeled week"),
        )
        for row, error in cases:
            with self.subTest(row=row):
                result = self.run_cli((RAW, row))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(f"CSV line 3: {error}", result.stderr)


if __name__ == "__main__":
    unittest.main()
