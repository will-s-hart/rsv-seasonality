from fractions import Fraction
import unittest

from compare_annual_reporting_directions import agreement, japan_signs


class AnnualReportingDirections(unittest.TestCase):
    def test_integer_site_weeks_against_enumeration(self):
        earlier_totals = range(7, 9)
        later_totals = range(11, 14)
        for earlier_reports in range(10):
            for later_reports in range(10):
                with self.subTest(earlier=earlier_reports, later=later_reports):
                    changes = [Fraction(later_reports, later) - Fraction(earlier_reports, earlier)
                               for earlier in earlier_totals for later in later_totals]
                    signs = sorted({(value > 0) - (value < 0) for value in changes})
                    self.assertEqual(japan_signs((earlier_reports, 7, 8), (later_reports, 11, 13)), signs)

    def test_agreement_requires_nonzero_directions(self):
        self.assertEqual(agreement([1], Fraction(1, 10**8)), "Agreement")
        self.assertEqual(agreement([1], Fraction(-1, 10**8)), "Disagreement")
        self.assertEqual(agreement([-1, 1], Fraction(-1)), "Indeterminate")
        self.assertEqual(agreement([0, 1], Fraction(1)), "Indeterminate")
        self.assertEqual(agreement([0], Fraction(1)), "Japan tie")
        self.assertEqual(agreement([1], Fraction(0)), "US tie")


if __name__ == "__main__":
    unittest.main()
