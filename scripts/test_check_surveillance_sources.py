import csv
from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import check_surveillance_sources as audit


class ManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.manifest = self.directory / "fixture.sha256"
        self.entries = {}
        for line in audit.MANIFEST.read_text(encoding="ascii").splitlines():
            _, name = line.split("  ")
            contents = name.encode("ascii")
            (self.directory / name).write_bytes(contents)
            self.entries[name] = f"{sha256(contents).hexdigest()}  {name}"
        self.write_manifest(self.entries.values())

    def write_manifest(self, entries):
        self.manifest.write_text("\n".join(entries) + "\n", encoding="ascii")

    def test_complete_manifest(self):
        self.assertEqual(audit.verify_inputs(self.directory, self.manifest), 29)

    def test_invalid_manifest_entries(self):
        entries = list(self.entries.values())
        for malformed, error in (
            (entries[1:], "missing"),
            (entries + entries[:1], "duplicate file"),
            (entries + [entries[0] + ".wrong"], "unexpected"),
            (entries[1:] + ["invalid  nrevss.csv"], "invalid SHA-256 entry"),
        ):
            with self.subTest(error=error):
                self.write_manifest(malformed)
                with self.assertRaisesRegex(ValueError, error):
                    audit.verify_inputs(self.directory, self.manifest)

    def test_missing_file(self):
        (self.directory / "nrevss.csv").unlink()
        with self.assertRaisesRegex(ValueError, "nrevss.csv: missing source file"):
            audit.verify_inputs(self.directory, self.manifest)

    def test_workbook_substitution_changes_digest(self):
        replacement = (self.directory / "2013-8-2.xls").read_bytes()
        (self.directory / "2013-8-1.xls").write_bytes(replacement)
        with self.assertRaisesRegex(ValueError, "2013-8-1.xls: SHA-256 mismatch"):
            audit.verify_inputs(self.directory, self.manifest)


class CalendarTests(unittest.TestCase):
    def test_us_inclusive_periods(self):
        for code, start, end in (
            ("1453", "2014-12-28", "2015-01-03"),
            ("1501", "2015-01-04", "2015-01-10"),
            ("1552", "2015-12-27", "2016-01-02"),
            ("1801", "2017-12-31", "2018-01-06"),
        ):
            with self.subTest(code=code):
                week_end = date.fromisoformat(end)
                self.assertEqual(audit.mmwr_week_code(week_end), code)
                self.assertEqual(audit.week_dates(week_end), (date.fromisoformat(start), week_end))

    def test_japan_inclusive_periods(self):
        for year, week, start, end in (
            (2015, 1, "2014-12-29", "2015-01-04"),
            (2015, 53, "2015-12-28", "2016-01-03"),
            (2017, 52, "2017-12-25", "2017-12-31"),
        ):
            with self.subTest(year=year, week=week):
                self.assertEqual(
                    audit.japan_week_dates(year, week), (date.fromisoformat(start), date.fromisoformat(end)),
                )

    def test_holdout_boundary_overlaps_one_local_date(self):
        japan_start, japan_end = audit.japan_week_dates(2017, 52)
        us_start, us_end = audit.week_dates(date(2018, 1, 6))
        self.assertEqual(max(japan_start, us_start), date(2017, 12, 31))
        self.assertEqual(min(japan_end, us_end), date(2017, 12, 31))

    def test_reject_non_saturday(self):
        with self.assertRaisesRegex(ValueError, "report week must end on Saturday"):
            audit.mmwr_week_code(date(2013, 1, 6))

    def test_reject_consistent_but_wrong_code(self):
        fields = ("testtype", "hhs_region", "repweekdate", "repweekcode")
        for report_date, submitted, expected in (
            ("05JAN2013", "1352", "1301"),
            ("03JAN2015", "1553", "1453"),
            ("02JAN2016", "1652", "1552"),
            ("01JAN2011", "1152", "1052"),
        ):
            with self.subTest(date=report_date), TemporaryDirectory() as temporary:
                directory = Path(temporary)
                with (directory / "nrevss.csv").open("w", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(fields)
                    for method in ("PCR", "Antigen"):
                        for region in range(1, 11):
                            writer.writerow((method, region, report_date, submitted))
                with self.assertRaisesRegex(ValueError, f"{report_date}: expected MMWR week code {expected}"):
                    audit.check_nrevss(directory)


class WorkbookHeaderTests(unittest.TestCase):
    def test_reject_renamed_missing_or_duplicate_prefectures(self):
        labels = audit.NESID_AREAS
        for altered in (
            labels[:1] + ["架空県(Fictional)"] + labels[2:],
            labels[:1] + ["北海道(Aomori)"] + labels[2:],
            labels[1:],
            labels[:1] + labels[2:],
            labels[:1] + labels[2:3] + labels[2:],
        ):
            with self.subTest(first_labels=altered[:3]):
                with self.assertRaisesRegex(ValueError, "geography"):
                    audit.check_areas([(None, name) for name in altered], "fixture")
        audit.check_areas([(None, name) for name in labels], "fixture")

    @staticmethod
    def age_rows(with_rates):
        # Table 12-1 has count groups of three columns, plus rate groups from 2018.
        labels = [
            "総　数(total No.)", "～５ヶ月(～ 5 m.o.)", "～１１ヶ月(～ 11 m.o.)",
            *(f"{age}歳({age}　y.o.)" for age in range(1, 10)),
            "１０～１４歳(10～ 14　y.o.)", "１５～１９歳(15～ 19　y.o.)", "２０歳～(20～ y.o.)",
        ]
        groups = []
        for label, count in zip(labels, [100, 2, 3, 5, 90] + [0] * 10):
            group = [(label, "報告数(No. of cases)", "総数(total No.)", count)]
            group += [(None, None, "男(male)", count), (None, None, "女(female)", 0)]
            if with_rates:
                group += [
                    (None, "定点当たり(/sentinel)", "総数(total No.)", count / 7),
                    (None, None, "男(male)", count / 7), (None, None, "女(female)", 0),
                ]
            groups.append(group)
        return groups

    @staticmethod
    def to_rows(groups):
        columns = [(None, None, None, None)] * 2 + [column for group in groups for column in group]
        return [()] * 4 + list(zip(*columns))

    def test_reordered_age_groups_preserve_share_and_total_column(self):
        for with_rates in (False, True):
            with self.subTest(with_rates=with_rates):
                groups = self.age_rows(with_rates)
                self.assertEqual(audit.check_ages(self.to_rows(groups), "fixture"), (2, 0.1))
                reordered = groups[4:] + groups[1:4] + groups[:1]
                rows = self.to_rows(reordered)
                expected_column = 2 + (len(groups) - 1) * len(groups[0])
                self.assertEqual(audit.check_ages(rows, "fixture"), (expected_column, 0.1))

    def test_reject_renamed_missing_duplicate_or_wrong_measure_or_sex(self):
        first = self.age_rows(with_rates=True)[1][0]
        age, measure, sex, count = first
        cases = (
            (("unknown", measure, sex, count), "unexpected age label"),
            (None, "missing age labels"),
            (("～１１ヶ月(～ 11 m.o.)", measure, sex, count), "duplicate age label"),
            ((age, "定点当たり(/sentinel)", sex, count), "invalid count header"),
            ((age, measure, "男(male)", count), "invalid count header"),
        )
        for replacement, error in cases:
            with self.subTest(replacement=replacement):
                groups = self.age_rows(with_rates=True)
                if replacement is None:
                    del groups[1]
                else:
                    groups[1][0] = replacement
                with self.assertRaisesRegex(ValueError, error):
                    audit.check_ages(self.to_rows(groups), "fixture")


if __name__ == "__main__":
    unittest.main()
