from datetime import date
from fractions import Fraction
import unittest

import check_surveillance_sources as audit
from summarize_nrevss_annual_change import annual_pairs, calendar_year_cells, matched_effects


class AnnualPositivityChange(unittest.TestCase):
    def setUp(self):
        self.keys = [(1, 1), (2, 1)]
        self.earlier = {(1, 1): (0, 80), (2, 1): (16, 20)}
        self.later = {(1, 1): (1, 10), (2, 1): (54, 90)}

    def test_exact_symmetric_effects(self):
        # Shares move from (0.8, 0.2) to (0.1, 0.9), while positivity
        # moves from (0.0, 0.8) to (0.1, 0.6). The mix reverses the net direction.
        effects = matched_effects(self.earlier, self.later, self.keys)
        self.assertEqual(effects, {
            "matched_pooled": Fraction(39, 100),
            "cell_positivity": Fraction(-13, 200),  # 0.45 * 0.1 - 0.55 * 0.2
            "test_mix": Fraction(91, 200),  # 0.05 * -0.7 + 0.7 * 0.7
            "equal_weight": Fraction(-1, 20),
        })
        reverse = matched_effects(self.later, self.earlier, self.keys)
        self.assertEqual(reverse, {key: -value for key, value in effects.items()})

    def test_first_saturday_ordinal_uses_calendar_year(self):
        groups = {
            ("PCR", region): dict.fromkeys(audit.nrevss_week_ends(), (0, 1, 0))
            for region in audit.HHS_REGIONS
        }
        groups["PCR", 1].update({
            date(2015, 1, 3): (0, 15, 1),  # MMWR 2014-W53
            date(2015, 1, 10): (2, 16, 0),
            date(2016, 1, 2): (3, 17, 0),  # MMWR 2015-W52
            date(2016, 12, 31): (4, 18, 0),
            date(2017, 1, 7): (5, 19, 0),
        })
        yearly = calendar_year_cells(groups)
        self.assertEqual(yearly[2015][1, 1], (0, 15))
        self.assertEqual(yearly[2015][1, 2], (2, 16))
        self.assertEqual(yearly[2016][1, 1], (3, 17))
        self.assertEqual(yearly[2016][1, 53], (4, 18))
        self.assertEqual(yearly[2017][1, 1], (5, 19))
        self.assertEqual(len(yearly[2016]), 530)

    def test_all_years_matching_and_omission_renormalization(self):
        year0 = {**self.earlier, (1, 2): (10, 10)}
        year1 = {**self.later, (1, 2): (0, 10)}
        result, _ = annual_pairs({2013: year0, 2014: year1, 2015: self.later})
        self.assertEqual(result["matched_cells_per_year"], 2)
        self.assertEqual(result["full_cells_year0"], 3)
        self.assertEqual(result["full_cells_year1"], 3)
        self.assertEqual(result["full_pooled"], Fraction(29, 110))
        self.assertEqual(result["matched_pooled"], Fraction(39, 100))
        self.assertEqual(result["omit_one_matched_pooled_min"], Fraction(-1, 5))
        self.assertEqual(result["omit_one_matched_pooled_max"], Fraction(1, 10))
        self.assertEqual(result["omit_one_test_mix_min"], 0)
        self.assertEqual(result["omit_one_test_mix_max"], 0)


if __name__ == "__main__":
    unittest.main()
