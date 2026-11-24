"""Exercise native Japan natality parsing with synthetic counts."""

import csv
import hashlib
import tempfile
import unittest
from datetime import date
from pathlib import Path

from check_natality import MONTHS, PREFECTURES, validate
from stage_japan_natality import stage

YEAR = "2019"


def monthly_rows():
    def cells(label, male, female):
        return [
            label, 12 * (male + female), 12 * male, 12 * female,
            *[male + female, male, female] * 12,
        ]

    return [
        ["令和元年", "人口動態統計"],
        ["中巻　出生　　第２表　出生数，市部－郡部－都道府県（特別区－指定都市再掲）・出生月・性別"],
        ["注：全国には住所地外国を含む。"],
        ["", "総　数", "", "", *[v for month in MONTHS for v in (f"{int(month)}月", "", "")]],
        ["", *["総　数", "男", "女"] * 13],
        cells("総　数", 48, 47),
        cells("市　部", 47, 47),
        cells("郡　部", 0, 0),
        *(cells(f"{code}　架空県", 1, 1) for code in sorted(PREFECTURES)),
        [v if v != 0 else "-" for v in cells("外　国", 1, 0)],
        cells("５０　架空市", 2, 2),
    ]


def annual_rows():
    return [
        ["令和元年", "人口動態統計"],
        ["上巻　出生　　第４．３表　都道府県別にみた年次別出生数"],
        ["", "1950", YEAR],
        ["", "", ""],
        ["全　国", "…", 1140],
        *([f"{code} 架空県", "…", 24] for code in sorted(PREFECTURES)),
        ["外　国", "…", 12],
    ]


class JapanReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "output"

    def write_inputs(self, monthly, annual):
        release = {
            "stat_infid": "synthetic",
            "catalogue_updated": date(2020, 1, 1),
            "national_births": 1140,
        }
        for table, rows, key in ((2, monthly, "sha256"), (43, annual, "table43_sha256")):
            path = self.root / f"jp-table{table}-{YEAR}.csv"
            with path.open("w", encoding="cp932", newline="") as stream:
                csv.writer(stream).writerows(rows)
            release[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        return {YEAR: release}

    def test_normalizes_and_reconciles_pinned_tables(self):
        sources = self.write_inputs(monthly_rows(), annual_rows())
        self.assertEqual(stage(self.root, self.output, sources), (47, 13))
        self.assertEqual(
            validate(
                self.output / "japan.csv", "japan", {"japan": {"years": sources}},
                self.output / "japan-residence-contract.csv", True,
            ),
            564,
        )

    def test_annual_reallocation_raises_before_creating_outputs(self):
        annual = annual_rows()
        annual[4][2] += 1
        annual[5][2] -= 1
        sources = self.write_inputs(monthly_rows(), annual)
        with self.assertRaisesRegex(ValueError, "Table 4-3"):
            stage(self.root, self.output, sources)
        self.assertFalse(self.output.exists())

    def test_unavailable_is_not_a_zero(self):
        monthly = monthly_rows()
        monthly[-2][-1] = "…"
        sources = self.write_inputs(monthly, annual_rows())
        with self.assertRaisesRegex(ValueError, "expected nonnegative integer"):
            stage(self.root, self.output, sources)

    def test_unreviewed_release_is_rejected(self):
        sources = self.write_inputs(monthly_rows(), annual_rows())
        sources[YEAR]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            stage(self.root, self.output, sources)

    def test_unknown_residence_requires_review(self):
        monthly = monthly_rows()
        monthly[-2][0] = "不　詳"
        sources = self.write_inputs(monthly, annual_rows())
        with self.assertRaisesRegex(ValueError, "unexpected or duplicate"):
            stage(self.root, self.output, sources)
