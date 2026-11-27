import datetime as dt
from fractions import Fraction
from io import StringIO
from math import sqrt
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from summarize_nrevss_assay_uncertainty import contrast_bounds, matched_rows, write_summary


class AssayUncertaintyTests(unittest.TestCase):
    def test_hand_calculated_bounds_and_break_even(self):
        matched = [
            (1, ((1, 1, False), (0, 4, False), (0, 16, False), (4, 64, False))),
            (1, ((0, 4, False), (2, 4, False), (1, 4, False), (0, 4, False))),
            (2, ((4, 16, False), (0, 16, False), (0, 16, False), (0, 16, False))),
        ]
        result = contrast_bounds(matched)
        self.assertEqual(result["matched_cells_per_year"], 3)
        self.assertEqual(result["matched_regions"], 2)
        self.assertEqual(result["antigen_minus_pcr_pp"], Fraction(75, 4))

        # Before applying 100/3, region SD ceilings are 31/16 and 8/16.
        for model, numerator in (
            ("independent_rows", 165), ("independent_region_dates", 313),
            ("independent_regions", 1025), ("unrestricted_dependence", 1521),
        ):
            variance = numerator / 256 * (100 / 3)**2
            with self.subTest(model=model):
                self.assertAlmostEqual(result[f"{model}_variance_cap_pp2"], variance)
                self.assertAlmostEqual(result[f"{model}_sd_cap_pp"], sqrt(variance))
        self.assertAlmostEqual(result["break_even_row_sd_multiplier"], 9 / sqrt(165))
        self.assertAlmostEqual(result["break_even_row_variance_multiplier"], 81 / 165)

    def test_support_uses_four_distinct_tested_rows_at_matching_saturday_ranks(self):
        dates = [dt.date.fromisoformat(value) for value in (
            "2016-01-02", "2016-01-09", "2016-01-16", "2016-12-24", "2016-12-31",
            "2017-01-07", "2017-01-14", "2017-01-21", "2017-12-30",
        )]
        pcr = dict.fromkeys(dates, (1, 8, False))
        antigen = dict.fromkeys(dates, (1, 4, False))
        antigen[dates[0]] = (0, 4, True)
        pcr[dates[5]] = (2, 8, False)
        antigen[dates[5]] = (3, 4, False)
        del antigen[dates[6]]
        antigen[dates[7]] = (0, 0, False)
        groups = {("PCR", 1): pcr, ("Antigen", 1): antigen}

        self.assertEqual(list(matched_rows(groups, 2016, 2017, [1])), [
            (1, ((1, 8, False), (0, 4, True), (2, 8, False), (3, 4, False))),
            (1, ((1, 8, False), (1, 4, False), (1, 8, False), (1, 4, False))),
        ])

    def test_empty_support_is_undefined(self):
        with self.assertRaisesRegex(ValueError, "No four-way positive-test support"):
            contrast_bounds([])

    def test_checksum_mismatch_produces_no_summary(self):
        output = StringIO()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nrevss.csv"
            path.write_bytes(b"wrong source")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                write_summary(path, output)
        self.assertEqual(output.getvalue(), "")
