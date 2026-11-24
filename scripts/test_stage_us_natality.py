"""Check native WONDER TSV parsing with synthetic grouped exports."""

import csv
import tempfile
import unittest
from pathlib import Path

from demographic_sources import STATE_NAMES
from stage_us_natality import DATE_FIELDS, STATE_FIELDS, read_export


class WonderExportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "export"

    def write_export(self, rows):
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream, delimiter="\t").writerows(rows)

    def test_state_and_grand_totals(self):
        states = [(name, f"{code:02d}") for code, name in STATE_NAMES.items()]
        rows = [
            ("Notes", *STATE_FIELDS, *DATE_FIELDS, "Births"),
            *(("", *state, "2013", "2013", "January", "1", "10") for state in states),
            *(("Total", *state, "2013", "2013", "", "", "10") for state in states),
            *(("Total", *state, "", "", "", "", "10") for state in states),
            ("Total", "", "", "", "", "", "", "510"),
            ("---",),
        ]
        self.write_export(rows)
        counts = read_export(self.path, True)
        self.assertEqual(len(counts), 102)
        self.assertEqual(counts["2013", "01", "11"], 10)
        self.assertEqual(counts["2013", "annual", "11"], 10)

    def test_rejects_wrong_month_and_unavailable_or_restricted_counts(self):
        rows = [
            ("Notes", *DATE_FIELDS, "Births"),
            ("", "2013", "2013", "January", "2", "20"),
            ("Total", "2013", "2013", "", "", "20"),
            ("Total", "", "", "", "", "20"),
            ("---",),
        ]
        for change, reason in (
            (rows[1], "unexpected WONDER month or subtotal"),
            (("", "2013", "2013", "January", "1", "Suppressed"), "nonnegative integer"),
            (("", "2013", "2013", "January", "1", "9"), "permitted aggregate export range"),
        ):
            with self.subTest(reason=reason):
                rows[1] = change
                self.write_export(rows)
                with self.assertRaisesRegex(ValueError, reason):
                    read_export(self.path, False)

    def test_rejects_wrong_wonder_subtotals(self):
        rows = [
            ("Notes", *DATE_FIELDS, "Births"),
            ("", "2013", "2013", "January", "1", "20"),
            ("Total", "2013", "2013", "", "", "20"),
            ("Total", "", "", "", "", "21"),
            ("---",),
        ]
        self.write_export(rows)
        with self.assertRaisesRegex(ValueError, "across-year WONDER total disagrees"):
            read_export(self.path, False)
