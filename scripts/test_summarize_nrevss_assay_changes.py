import unittest

from summarize_nrevss_assay_changes import annual_pairs, compare_pair, direction, match_support
from summarize_nrevss_weighting import calendar_weeks


class AnnualAssayChangeTests(unittest.TestCase):
    def test_both_weightings_use_matched_cells_and_recompute_after_omission(self):
        # Pooled positivity rises from 15% to 20% in both assays. The two equal
        # means move from 15% to 12.5% (PCR) and 50% (antigen).
        matched = {
            (1, 1): ((10, 100), (20, 100), (0, 25), (0, 100)),
            (2, 1): ((20, 100), (10, 100), (25, 100), (25, 25)),
        }
        result = compare_pair(matched)
        self.assertEqual(float(result["pooled_pcr_change_pp"]), 5)
        self.assertEqual(float(result["pooled_antigen_change_pp"]), 5)
        self.assertEqual(float(result["pooled_antigen_minus_pcr_pp"]), 0)
        self.assertEqual(result["pooled_direction"], "same")
        self.assertEqual(float(result["equal_pcr_change_pp"]), -2.5)
        self.assertEqual(float(result["equal_antigen_change_pp"]), 35)
        self.assertEqual(float(result["equal_antigen_minus_pcr_pp"]), 37.5)
        self.assertEqual(result["equal_direction"], "opposite")
        for method in ("pooled", "equal"):
            self.assertEqual(result[f"{method}_omit_same_direction"], 2)
            self.assertEqual(float(result[f"{method}_omit_gap_min_pp"]), -10)
            self.assertEqual(float(result[f"{method}_omit_gap_max_pp"]), 85)

    def test_screens_apply_to_all_four_rows_with_disjoint_losses(self):
        tested, zero, small = (0, 100), (0, 0), (0, 25)
        earlier = {(1, ordinal): (tested, tested) for ordinal in range(1, 6)}
        later = {
            (1, 1): (None, zero),
            (1, 2): (tested, zero),
            (1, 3): (small, tested),
            (1, 4): (tested, tested),
        }
        earlier[1, 4] = tested, small
        expected = {1: [(1, 3), (1, 4)], 25: [(1, 3), (1, 4)], 100: []}
        for minimum, keys in expected.items():
            matched, losses = match_support(earlier, later, minimum)
            self.assertEqual(list(matched), keys)
            self.assertEqual(losses["missing"], 1)
            self.assertEqual(losses["zero_tests"], 1)
            self.assertEqual(losses["below_min"], 2 if minimum == 100 else 0)

    def test_calendar_ordinal_matches_january_and_excludes_unpaired_saturday(self):
        first, second, third = (calendar_weeks(year) for year in (2016, 2017, 2018))
        base, high = (10, 100, 0), (20, 100, 1)
        groups = {
            ("PCR", 1): {first[0]: base, first[-1]: base, second[0]: high, third[0]: base},
            ("Antigen", 1): {first[0]: base, first[-1]: base, second[0]: high},
        }
        pair, _, _, next_pair, *_ = annual_pairs(groups, years=(2016, 2017, 2018), regions=(1,))
        self.assertEqual((pair["calendar_cells_year0"], pair["calendar_cells_year1"]), (53, 52))
        self.assertEqual(pair["common_calendar_cells"], 52)
        self.assertEqual(pair["missing_cells"], 51)
        self.assertEqual(pair["matched_cells_per_year"], 1)
        self.assertEqual(float(pair["equal_antigen_change_pp"]), 10)
        self.assertNotIn("equal_omit_same_direction", pair)
        self.assertEqual(next_pair["matched_cells_per_year"], 0)
        self.assertNotIn("equal_direction", next_pair)
        self.assertEqual(direction(0, -1), "zero")


if __name__ == "__main__":
    unittest.main()
