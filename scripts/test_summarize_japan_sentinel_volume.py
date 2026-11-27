from datetime import date
from fractions import Fraction
from itertools import product
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from summarize_japan_sentinel_volume import (
    AUDIT,
    change_bounds,
    direction,
    format_interval,
    read_controls,
    report_bounds,
    site_week_bounds,
)


SCRIPT = Path(__file__).with_name("summarize_japan_sentinel_volume.py").resolve()


class JapanSentinelVolume(unittest.TestCase):
    def test_site_week_endpoints_against_exhaustive_integer_weeks(self):
        for weeks, low, high in [(1, 2, 2), (4, 2, 2), (2, 2, 4), (5, 2, 4)]:
            with self.subTest(weeks=weeks, low=low, high=high):
                totals = [
                    sum(counts) for counts in product(range(low, high + 1), repeat=weeks)
                    if min(counts) == low and max(counts) == high
                ]
                self.assertEqual(site_week_bounds(weeks, low, high), (min(totals), max(totals)))

    def test_impossible_weekly_extrema(self):
        for args in [(0, 2, 2), (1, 2, 4), (3, 4, 2), (3, 0, 2)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                site_week_bounds(*args)

    def test_change_endpoints_against_enumerated_denominator_pairs(self):
        for later_reports, expected in [(3, "fall"), (7, "ambiguous"), (10, "rise")]:
            with self.subTest(later_reports=later_reports):
                earlier_totals = range(8, 11)
                later_totals = range(12, 16)
                feasible = [
                    Fraction(1000 * later_reports, later) - Fraction(1000 * 5, earlier)
                    for earlier, later in product(earlier_totals, later_totals)
                ]
                bounds = change_bounds(report_bounds(5, (8, 10)),
                                       report_bounds(later_reports, (12, 15)))
                self.assertEqual(bounds, (min(feasible), max(feasible)))
                self.assertEqual(direction(bounds), expected)

    def test_zero_endpoints_and_outward_rounding(self):
        self.assertEqual(report_bounds(0, (8, 10)), (0, 0))
        self.assertEqual(direction((0, 0)), "no change")
        self.assertEqual(direction((0, 1)), "ambiguous")
        self.assertEqual(direction((-1, 0)), "ambiguous")
        self.assertEqual(format_interval((Fraction(-1, 300), Fraction(1, 300))), "[-0.01, 0.01]")

    def test_committed_controls_and_directions(self):
        controls = read_controls()
        self.assertEqual([row.year for row in controls], list(range(2013, 2020)))
        for row in controls:
            self.assertEqual(row.weeks, date(row.year, 12, 28).isocalendar().week)
        rates = [
            report_bounds(row.cases, site_week_bounds(row.weeks, row.weekly_min, row.weekly_max))
            for row in controls
        ]
        self.assertEqual(
            [direction(change_bounds(earlier, later)) for earlier, later in zip(rates, rates[1:])],
            ["ambiguous", "rise", "fall", "rise", "fall", "rise"],
        )
        self.assertEqual(direction(change_bounds(rates[0], rates[-1])), "rise")

    def test_cli_rejects_invalid_audit_before_output(self):
        original = AUDIT.read_text(encoding="utf-8")
        separator = "| --- | ---: | ---: | ---: | ---: | ---: |"
        mutations = [
            ("96,625", "96,62", "2013 national reports"),
            ("140,093", "14,00,093", "2019 national reports"),
            ("2,995–3,161", "29,95–3,161", "2013 weekly site minimum"),
            ("2,911–3,176", "2,911–3,17", "2019 weekly site maximum"),
            ("| 134 | 2,995", "| 13,4 | 2,995", "2013 prefecture-weeks"),
            ("74.1%", "74,1%", "2013: expected an under-two percentage"),
            (separator, separator.replace("---:", "bad", 1), "expected a Markdown delimiter"),
            (separator, "| --- | ---: |", "expected six pipe-delimited columns"),
            ("| 2013 |", "2013 |", "expected six pipe-delimited columns"),
            ("| 2015 | 53 |", "| 2015 | 52 |", "2015: expected 53 diagnosis weeks"),
            ("| 2019 | 52 |", "| 2019 | 53 |", "2019: expected 52 diagnosis weeks"),
            ("2,911–3,176", "3,176–2,911", "Weekly extrema must be positive"),
        ]
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scripts").mkdir()
            (root / "notes").mkdir()
            script = root / "scripts" / SCRIPT.name
            copyfile(SCRIPT, script)
            verifier = SCRIPT.with_name("check_surveillance_sources.py")
            copyfile(verifier, script.with_name(verifier.name))
            audit = root / "notes" / AUDIT.name
            for old, new, error in mutations:
                with self.subTest(new=new):
                    self.assertIn(old, original)
                    audit.write_text(original.replace(old, new, 1), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(script)], capture_output=True, check=False
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertIn(error.encode("utf-8"), result.stderr)

    def test_cli_reproduces_documented_tables(self):
        note = AUDIT.with_name("japan-annual-sentinel-volume-2013-2019.md")
        output = subprocess.check_output([sys.executable, "-B", str(SCRIPT)])
        self.assertIn(output + b"\n", note.read_bytes())


if __name__ == "__main__":
    unittest.main()
