from datetime import date
from fractions import Fraction
from itertools import product
import unittest

from summarize_japan_sentinel_volume import (
    change_bounds,
    direction,
    format_interval,
    read_controls,
    report_bounds,
    site_week_bounds,
)


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


if __name__ == "__main__":
    unittest.main()
