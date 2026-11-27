import csv
from datetime import date, timedelta
from fractions import Fraction
from hashlib import sha256
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import check_surveillance_sources as audit
from summarize_nrevss_weighting import annual_summaries, calendar_weeks


class WeightingFixture(unittest.TestCase):
    def test_decomposition_and_matching(self):
        first, second, third, *_ = calendar_weeks(2013)
        next_first, next_second, *_ = calendar_weeks(2014)
        regions = [
            {first: (0, 10, 1), second: (9, 30, 0), third: (0, 0, 0),
             next_first: (0, 10, 0), next_second: (9, 30, 0)},
            {first: (5, 10, 0), second: (0, 10, 0), third: (10, 10, 0),
             next_first: (5, 10, 0), next_second: (0, 10, 0)},
        ]
        baseline, matched, next_baseline, next_matched = annual_summaries(regions, [2013, 2014])

        self.assertEqual(baseline["expected_region_weeks"], 104)
        self.assertEqual(baseline["absent_rows"], 98)
        self.assertEqual(baseline["zero_test_rows"], 1)
        self.assertEqual(baseline["retained_rows"], 5)
        self.assertEqual(baseline["retained_zero_positive_rows"], 2)
        self.assertEqual(baseline["retained_flagged_rows"], 1)
        self.assertEqual(baseline["reported_detections"], 24)
        self.assertEqual(baseline["reported_tests"], 70)
        # A averages 15% and 50%, B averages 22.5% and 50%, and C pools 24/70.
        self.assertEqual(baseline["a_equal_week_region_pct"], "32.500000")
        self.assertEqual(baseline["b_pooled_week_equal_region_pct"], "36.250000")
        self.assertEqual(baseline["c_pooled_all_pct"], "34.285714")
        self.assertEqual(baseline["within_region_pp"], "3.750000")
        self.assertEqual(baseline["region_mix_pp"], "-1.964286")
        self.assertEqual(baseline["total_gap_pp"], "1.785714")

        self.assertEqual(matched["retained_rows"], 4)
        self.assertEqual(matched["excluded_by_matching"], 1)
        self.assertEqual(matched["a_equal_week_region_pct"], "20.000000")
        self.assertEqual(matched["b_pooled_week_equal_region_pct"], "23.750000")
        self.assertEqual(matched["c_pooled_all_pct"], "23.333333")
        self.assertEqual(matched["region_mix_pp"], "-0.416667")
        self.assertEqual(matched["total_gap_pp"], "3.333333")
        self.assertEqual(next_matched["retained_rows"], 4)
        self.assertEqual(next_baseline["total_gap_pp"], next_matched["total_gap_pp"])

    def test_empty_matched_support_and_no_eligible_region(self):
        regions = [{date(2013, 1, 5): (0, 1, 0)}, {}]
        baseline, matched = annual_summaries(regions, [2013])
        self.assertEqual(baseline["retained_regions"], 1)
        self.assertEqual(baseline["c_pooled_all_pct"], "0.000000")
        self.assertEqual(matched["retained_regions"], 0)
        self.assertEqual(matched["excluded_by_matching"], 1)
        self.assertNotIn("total_gap_pp", matched)


class WeightingCLI(unittest.TestCase):
    def test_pinned_cli_and_independent_replay(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in ("check_surveillance_sources.py", "summarize_nrevss_assays.py",
                         "summarize_nrevss_weighting.py", "verify_nrevss_weighting.py"):
                shutil.copyfile(Path(__file__).with_name(name), directory / name)
            source = directory / audit.CDC_EXPORT
            self.make_source(source)
            original = source.read_bytes()
            pins = audit.load_pins()
            pins[audit.CDC_EXPORT] = sha256(original).hexdigest()
            (directory / audit.MANIFEST.name).write_text(
                "".join(f"{digest}  {name}\n" for name, digest in pins.items()), encoding="ascii",
            )

            command = [sys.executable, "-B", str(directory / "summarize_nrevss_weighting.py"), str(source)]
            actual = subprocess.check_output(command, text=True)
            self.assertEqual(subprocess.check_output(command, text=True), actual)
            self.assertEqual(source.read_bytes(), original)
            rows = {(row["calendar_year"], row["support"]): row for row in csv.DictReader(StringIO(actual))}
            exact = subprocess.check_output([*command, "--exact"], text=True)
            exact_rows = {(row["calendar_year"], row["support"]): row
                          for row in csv.DictReader(StringIO(exact))}
            self.assertEqual(Fraction(exact_rows["2015", "matched"]["a_equal_week_region_pct"]), Fraction(3, 52))
            self.assertEqual(Fraction(exact_rows["2015", "matched"]["c_pooled_all_pct"]), Fraction(5, 29))
            self.assertEqual(len(rows), 14)
            self.assertEqual(sum(int(rows[str(year), "baseline"]["retained_rows"]) for year in audit.YEARS), 3650)
            self.assertEqual({rows[str(year), "matched"]["retained_rows"] for year in audit.YEARS}, {"520"})
            # The MMWR 2014-W53 observation ends on a Saturday in calendar 2015.
            self.assertEqual(rows["2014", "baseline"]["reported_detections"], "0")
            self.assertEqual(rows["2015", "baseline"]["reported_detections"], "9")
            self.assertEqual(rows["2016", "baseline"]["expected_weeks"], "53")
            self.assertEqual(rows["2016", "baseline"]["reported_detections"], "80")
            self.assertEqual(rows["2016", "matched"]["excluded_by_matching"], "10")
            self.assertEqual(rows["2016", "matched"]["reported_detections"], "0")

            summary = directory / "summary.csv"
            summary.write_text(actual, encoding="utf-8")
            replay = [sys.executable, "-B", str(directory / "verify_nrevss_weighting.py"), str(source), str(summary)]
            self.assertIn("for all seven years", subprocess.check_output(replay, text=True))
            rows["2013", "baseline"]["total_gap_pp"] = "9.000000"
            with summary.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=next(iter(rows.values())).keys())
                writer.writeheader()
                writer.writerows(rows.values())
            altered = subprocess.run(replay, capture_output=True, text=True, check=False)
            self.assertEqual(altered.returncode, 1)
            self.assertIn("2013 total_gap_pp differs", altered.stderr)

            source.write_bytes(original + b"\n")
            failed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(failed.returncode, 1)
            self.assertEqual(failed.stdout, "")
            self.assertIn("SHA-256 mismatch", failed.stderr)

    @staticmethod
    def make_source(path):
        special = {
            (1, date(2015, 1, 3)): (9, 30, 1),
            (1, date(2016, 12, 31)): (80, 100, 0),
        }
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("testtype", "repweekdate", "repweekcode", "hhs_region", "rsvpos", "rsvtest", "outlier"))
            for week in range(521):
                day = date(2010, 7, 10) + timedelta(weeks=week)
                raw_date = f"{day.day:02d}{audit.MONTHS[day.month - 1]}{day.year}"
                code = audit.mmwr_week_code(day)
                for region in audit.HHS_REGIONS:
                    counts = special.get((region, day), (0, 10, 0))
                    writer.writerow(("PCR", raw_date, code, region, *counts))
                    if region != 1 or week >= 107:
                        writer.writerow(("Antigen", raw_date, code, region, 0, 10, 0))


if __name__ == "__main__":
    unittest.main()
