import csv
from contextlib import contextmanager
from io import StringIO
import os
from pathlib import Path
import stat
import subprocess
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
import unittest
from unittest.mock import patch

import check_surveillance_sources as audit
import export_weekly_observations as export


FULLWIDTH_DIGITS = str.maketrans("0123456789", "０１２３４５６７８９")
COVERAGE_SCRIPT = Path(__file__).with_name("summarize_weekly_coverage.py")


@contextmanager
def nesid_fixture(directory, year, table, missing_field=None):
    weeks = 53 if year == 2015 else 52
    codes = [f"{week}週".translate(FULLWIDTH_DIGITS) for week in range(1, weeks + 1)]
    if table == "14-1":
        # Table 14-1 has an annual-average column before week 1.
        headers = [
            f"{code}(week {min(week, 52)})" for week, code in enumerate(codes, start=1)
        ]
        sites = [671] * 52 + [718]
        prefectures = [
            (None, label, None, *([14] * 52), 15) for label in audit.NESID_AREAS[2:]
        ]
        first_site_count = None if missing_field == "site" else 27
        rows = [()] * 4 + [(None, None, "Avg", *headers)]
        rows += [
            (None, audit.NESID_AREAS[0], None, *sites),
            (None, audit.NESID_AREAS[1], None, first_site_count, *([27] * 51), 28),
            *prefectures,
        ]
        yield [audit.PEDIATRIC], lambda name, height: rows
    elif table == "8-1":
        rows = [()] * 4 + [(None, None, audit.RSV), ()]
        rows += [
            (None, audit.NESID_AREAS[0], 92),
            (None, audit.NESID_AREAS[1], None if missing_field == "count" else 0),
            *((None, label, 2) for label in audit.NESID_AREAS[2:]),
        ]
        yield [audit.TOTAL, *codes], lambda name, height: rows
    else:
        raise AssertionError(f"Unexpected workbook {table}")


def write_nrevss_fixture(directory):
    with (directory / audit.CDC_EXPORT).open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow((
            "testtype", "repweekdate", "repweekcode", "hhs_region", "rsvpos", "rsvtest", "outlier",
        ))
        for day in audit.nrevss_week_ends():
            report_date = f"{day.day:02d}{audit.MONTHS[day.month - 1]}{day.year}"
            code = audit.mmwr_week_code(day)
            for region in audit.HHS_REGIONS:
                writer.writerow(("PCR", report_date, code, region, 1, 8, int(code == "1801")))
        writer.writerows((
            ("Antigen", "06JAN2018", "1801", 2, 0, 0, 0),
            ("Antigen", "13JAN2018", "1802", 2, 0, 12, 1),
            ("Antigen", "20JAN2018", "1803", 2, 3, 10, 0),
            ("Antigen", "06JAN2018", "1801", 7, 0, 0, 1),
            ("PCR", "06JAN2018", "1801", "National", 301, 801, 0),
            ("Antigen", "04JAN2020", "2001", 2, 0, 12, 0),
        ))


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.directory = Path(temporary.name)
        write_nrevss_fixture(cls.directory)
        stream = StringIO()
        with patch.object(audit, "workbook", nesid_fixture), patch.object(
            audit, "verify_inputs"
        ) as verify:
            export.write_observations(cls.directory, stream)
            verify.assert_called_once_with(cls.directory)
        csv_text = stream.getvalue()
        cls.csv_bytes = csv_text.encode("utf-8")
        cls.rows = list(csv.DictReader(StringIO(csv_text)))
        cls.by_key = {}
        for row in cls.rows:
            key = (
                row["source_id"], row["method"], row["region_id"],
                row["source_week_year"], row["source_week_code"],
            )
            cls.by_key[key] = row

    def test_full_grid_has_unique_keys_and_excludes_aggregate_geography(self):
        self.assertEqual(len(self.rows), 24_455)
        self.assertEqual(len(self.rows), len(self.by_key))
        for source_id, method, expected, regions in (
            ("NESID", "", 17_155, {f"{region:02d}" for region in range(1, 48)}),
            ("NREVSS:52kb-ccu2", "PCR", 3650, {str(region) for region in range(1, 11)}),
            ("NREVSS:52kb-ccu2", "Antigen", 3650, {str(region) for region in range(1, 11)}),
        ):
            with self.subTest(source=source_id, method=method):
                rows = [
                    row for row in self.rows
                    if (row["source_id"], row["method"]) == (source_id, method)
                ]
                self.assertEqual(len(rows), expected)
                self.assertEqual({row["region_id"] for row in rows}, regions)

    def test_japan_preserves_native_week_and_site_count(self):
        row = self.by_key["NESID", "", "01", "2015", "５３週"]
        self.assertEqual((row["week_start"], row["week_end"]), ("2015-12-28", "2016-01-03"))
        self.assertEqual(row["region_label"], "北海道(Hokkaido)")
        self.assertEqual(row["observation_type"], "rsv_case_notifications")
        self.assertEqual(row["denominator_kind"], "paediatric_sentinel_sites")
        self.assertEqual((row["count"], row["denominator"]), ("0", "28"))
        self.assertEqual(row["coverage"], "present")
        self.assertEqual(row["source_version"], "final_annual_2015")
        for field in ("source_vintage", "source_outlier", "positivity"):
            self.assertEqual(row[field], "")

    def test_us_retains_2014_week_53_and_inclusive_cross_source_overlap(self):
        us = self.by_key["NREVSS:52kb-ccu2", "PCR", "2", "2014", "1453"]
        self.assertEqual((us["week_start"], us["week_end"]), ("2014-12-28", "2015-01-03"))
        japan = self.by_key["NESID", "", "01", "2017", "５２週"]
        us = self.by_key["NREVSS:52kb-ccu2", "PCR", "2", "2018", "1801"]
        self.assertEqual((japan["week_start"], japan["week_end"]), ("2017-12-25", "2017-12-31"))
        self.assertEqual((us["week_start"], us["week_end"]), ("2017-12-31", "2018-01-06"))
        self.assertEqual(max(japan["week_start"], us["week_start"]), "2017-12-31")
        self.assertEqual(min(japan["week_end"], us["week_end"]), "2017-12-31")

    def test_us_absent_zero_test_and_zero_detection_have_distinct_values(self):
        fields = ("coverage", "count", "denominator", "source_outlier", "positivity")
        for method, code, expected in (
            ("PCR", "1801", ("present", "1", "8", "1", "0.125")),
            ("Antigen", "1801", ("present", "0", "0", "0", "")),
            ("Antigen", "1802", ("present", "0", "12", "1", "0.0")),
            ("Antigen", "1803", ("present", "3", "10", "0", "0.3")),
            ("Antigen", "1804", ("absent", "", "", "", "")),
        ):
            with self.subTest(method=method, code=code):
                row = self.by_key["NREVSS:52kb-ccu2", method, "2", "2018", code]
                self.assertEqual(tuple(row[field] for field in fields), expected)
                self.assertEqual(row["denominator_kind"], "reported_tests")
                self.assertEqual(row["source_vintage"], "2022-10-21")
                self.assertEqual(row["region_label"], "HHS Region 2")

    def test_coverage_summary_cli_counts_synthetic_export_without_modifying_it(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic-weekly.csv"
            path.write_bytes(self.csv_bytes)
            command = [sys.executable, "-B", str(COVERAGE_SCRIPT), str(path)]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            replay = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, replay.stdout)
            self.assertEqual(path.read_bytes(), self.csv_bytes)

        fields = ("input_rows", "present_rows", "absent_rows", "zero_reports", "tested_rows",
                  "zero_test_rows", "zero_detection_rows", "flagged_tested_rows",
                  "flagged_zero_test_rows", "positive_denominator_min",
                  "positive_denominator_median", "positive_denominator_max")
        groups = {
            (row["source_id"], row["method"], row["region_id"], row["source_week_year"]): row
            for row in csv.DictReader(StringIO(result.stdout))
        }
        self.assertEqual(len(groups), 469)
        self.assertEqual(sum(int(row["input_rows"]) for row in groups.values()), 24455)
        for key, expected in (
            (("NESID", "", "01", "2015"),
             ("53", "53", "0", "53", "", "", "", "", "", "27", "27", "28")),
            (("NREVSS:52kb-ccu2", "PCR", "2", "2018"),
             ("52", "52", "0", "", "52", "0", "0", "1", "0", "8", "8.0", "8")),
            (("NREVSS:52kb-ccu2", "Antigen", "2", "2018"),
             ("52", "3", "49", "", "2", "1", "1", "1", "0", "10", "11.0", "12")),
            (("NREVSS:52kb-ccu2", "Antigen", "7", "2018"),
             ("52", "1", "51", "", "0", "1", "0", "0", "1", "", "", "")),
            (("NREVSS:52kb-ccu2", "Antigen", "8", "2019"),
             ("52", "0", "52", "", "0", "0", "0", "0", "0", "", "", "")),
        ):
            with self.subTest(key=key):
                self.assertEqual(tuple(groups[key][field] for field in fields), expected)

    def test_coverage_summary_cli_rejects_invalid_rows(self):
        absent = self.by_key["NREVSS:52kb-ccu2", "Antigen", "2", "2018", "1804"]
        for rows, expected in (
            ([{**absent, "denominator": "0"}], "expected an absent antigen row"),
            ([{**absent, "source_week_code": ""}], "missing observation key field"),
            ([absent, absent], "duplicate observation key"),
        ):
            with self.subTest(expected=expected), TemporaryDirectory() as temporary:
                path = Path(temporary) / "synthetic-weekly.csv"
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=export.Observation._fields)
                    writer.writeheader()
                    writer.writerows(rows)
                result = subprocess.run(
                    [sys.executable, "-B", str(COVERAGE_SCRIPT), str(path)],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(expected, result.stderr)

    def test_missing_japan_count_or_site_denominator_is_rejected(self):
        for field in ("count", "site"):
            def workbook_with_missing_value(directory, year, table):
                return nesid_fixture(directory, year, table, missing_field=field)

            with self.subTest(field=field), patch.object(
                audit, "workbook", workbook_with_missing_value
            ):
                with self.assertRaisesRegex(ValueError, "2013 week 1: missing or invalid count"):
                    next(export.nesid_observations(self.directory))

    def test_missing_pcr_is_rejected(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / audit.CDC_EXPORT).write_text("testtype\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PCR region 1 incomplete coverage"):
                next(export.nrevss_observations(directory))

    def test_duplicate_us_week_is_rejected(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with (directory / audit.CDC_EXPORT).open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow((
                    "testtype", "repweekdate", "repweekcode", "hhs_region", "rsvpos", "rsvtest",
                    "outlier",
                ))
                row = ("PCR", "06JAN2018", "1801", 2, 0, 8, 0)
                writer.writerows((row, row))
            with self.assertRaisesRegex(ValueError, "duplicate week"):
                next(export.nrevss_observations(directory))

    def test_missing_inputs_fail_before_export(self):
        with TemporaryDirectory() as temporary:
            stream = StringIO()
            with self.assertRaisesRegex(ValueError, "missing source file"):
                export.write_observations(Path(temporary), stream)
            self.assertEqual(stream.getvalue(), "")

    def test_cli_missing_pinned_input_preserves_output(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sources = directory / "missing-inputs"
            sources.mkdir()
            destination = directory / "weekly.csv"
            destination.write_bytes(self.csv_bytes)
            result = subprocess.run(
                [sys.executable, "-B", export.__file__, str(sources), "--output", str(destination)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("2013-8-1.xls: missing source file", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(destination.read_bytes(), self.csv_bytes)
            self.assertEqual(set(directory.iterdir()), {sources, destination})

    def test_cli_success_replaces_output_with_deterministic_bytes(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            destination = directory / "weekly.csv"
            argv = [export.__file__, str(self.directory), "--output", str(destination)]
            with patch.object(sys, "argv", argv), patch.object(
                audit, "workbook", nesid_fixture
            ), patch.object(audit, "verify_inputs"):
                export.main()
                self.assertEqual(destination.read_bytes(), self.csv_bytes)
                if os.name == "posix":
                    self.assertEqual(stat.S_IMODE(destination.stat().st_mode) & 0o077, 0)
                    destination.chmod(0o640)
                destination.write_bytes(b"prior,export\n")
                export.main()
            self.assertEqual(destination.read_bytes(), self.csv_bytes)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o640)
            self.assertEqual(list(directory.iterdir()), [destination])

    def test_cli_refuses_to_replace_pinned_sources(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sources = directory / "sources"
            sources.mkdir()
            aliased_sources = directory / "alias"
            aliased_sources.symlink_to(sources, target_is_directory=True)
            cdc = sources / audit.CDC_EXPORT
            cdc.write_bytes(b"original CDC input")
            workbook = sources / audit.workbook_name(2013, "8-1")
            staged_workbook = directory / "official.xls"
            staged_workbook.write_bytes(b"original workbook input")
            workbook.symlink_to(staged_workbook)

            for destination in (cdc, aliased_sources / cdc.name, staged_workbook):
                with self.subTest(destination=destination):
                    result = subprocess.run(
                        [sys.executable, "-B", export.__file__, str(sources), "--output",
                         str(destination)],
                        capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("output destination must not be an audit source file", result.stderr)
                    self.assertEqual(result.stdout, "")
            self.assertEqual(cdc.read_bytes(), b"original CDC input")
            self.assertEqual(staged_workbook.read_bytes(), b"original workbook input")
            self.assertTrue(workbook.is_symlink())
            self.assertEqual(set(sources.iterdir()), {cdc, workbook})
            self.assertEqual(set(directory.iterdir()), {sources, aliased_sources, staged_workbook})

    def test_cli_close_failure_preserves_output(self):
        @contextmanager
        def failing_close(*args, **kwargs):
            with NamedTemporaryFile(*args, **kwargs) as stream:
                yield stream
            raise OSError("synthetic close failure")

        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            destination = directory / "weekly.csv"
            destination.write_bytes(b"prior,export\n")
            argv = [export.__file__, str(self.directory), "--output", str(destination)]
            with patch.object(sys, "argv", argv), patch.object(
                audit, "workbook", nesid_fixture
            ), patch.object(audit, "verify_inputs"), patch.object(
                export, "NamedTemporaryFile", failing_close
            ):
                with self.assertRaisesRegex(OSError, "synthetic close failure"):
                    export.main()
            self.assertEqual(destination.read_bytes(), b"prior,export\n")
            self.assertEqual(list(directory.iterdir()), [destination])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX special files")
    def test_cli_rejects_symlink_fifo_and_directory(self):
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "target.csv"
            target.write_bytes(b"prior,export\n")
            link = directory / "link.csv"
            link.symlink_to(target)
            fifo = directory / "fifo"
            os.mkfifo(fifo)
            folder = directory / "folder"
            folder.mkdir()
            for destination in (link, fifo, folder):
                argv = [export.__file__, str(self.directory), "--output", str(destination)]
                with self.subTest(destination=destination), patch.object(
                    sys, "argv", argv
                ), patch.object(audit, "workbook", nesid_fixture), patch.object(
                    audit, "verify_inputs"
                ):
                    with self.assertRaisesRegex(
                        ValueError, "output destination must be a regular file"
                    ):
                        export.main()
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_bytes(), b"prior,export\n")
            self.assertTrue(stat.S_ISFIFO(fifo.lstat().st_mode))
            self.assertTrue(folder.is_dir())
            self.assertEqual(set(directory.iterdir()), {target, link, fifo, folder})


if __name__ == "__main__":
    unittest.main()
