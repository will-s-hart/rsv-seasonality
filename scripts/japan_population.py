"""Read and reconcile the contracted Statistics Bureau population tables."""

import csv
from demographic_sources import (
    assert_cells,
    read_xlsx_sheets,
    spreadsheet_count,
    unsigned_integer,
    verify_stage,
)

PREFECTURES = {f"{code:02}" for code in range(1, 48)}
NATIONAL = "00"
GEOGRAPHIES = PREFECTURES | {NATIONAL}
REVISED_YEARS = (2016, 2017, 2018, 2019)
REVISED_SHEETS = {year: f"第10表 {year}年" for year in REVISED_YEARS}


def read_xls(path, name):
    import xlrd

    with xlrd.open_workbook(path) as workbook:
        sheet = workbook.sheet_by_name(name)
        return [sheet.row_values(i) for i in range(sheet.nrows)]


def compact(text):
    return "".join(str(text).split())


def prefecture_rows(rows, table_code, series_code, columns, label):
    population = {}
    for row in rows:
        if (row[0], compact(row[2]), row[3]) != (table_code, series_code, "01"):
            continue
        # The whole-country row has no prefecture code.
        code = NATIONAL if row[11] == "Japan" and not row[8] else str(row[8])
        name = str(row[7] if code == NATIONAL else row[9]).strip()
        if code not in GEOGRAPHIES or not name or code in population:
            raise ValueError(f"{label}: invalid or duplicate geography {code!r}")
        population[code] = (
            name, *(spreadsheet_count(row[col - 1], f"{label}, geography {code}") for col in columns)
        )
    if population.keys() != GEOGRAPHIES:
        raise ValueError(f"{label}: expected Japan and all 47 prefecture codes")
    return population


def prefecture_age(rows, year, label, *, revised):
    scope = {(11, 26): "Total population Both sexes"} if revised else {(11, 25): "Both sexes"}
    table_scope = "Total population, Japanese population" if revised else "Total population"
    continued = " - Continued" if revised and year > 2016 else ""
    age_group = "Five-Year Groups" if revised else "5-Year Age Group"
    assert_cells(rows, {
        (5, 20): f"Table 10. Population by Age ({age_group}) and Sex",
        (5, 21): f"for Prefectures - {table_scope}, October 1, {year}{continued}",
        (8, 31): "(Thousand persons)",
        (14, 14): "0～4歳",
        (17, 13): "Total",
        **scope,
    }, label)
    # In the revised workbook the six series codes advance with each worksheet year.
    series = f"{1 + 6 * (year - 2016):02}" if revised else "01"
    return prefecture_rows(rows, "01000", series, (13, 14), label)


def original_controls(total_rows, national_rows, year):
    label = f"Japan {year} Table 4"
    assert_cells(total_rows, {
        (5, 8): (
            f"Table 4. Population by Sex and Sex ratio for Prefectures - "
            f"Total population, Japanese population, October 1, {year}"
        ),
        (8, 20): "(Thousand persons)",
        (10, 13): "総 人 口 Total population",
        (15, 13): "Both sexes",
    }, label)
    total = prefecture_rows(total_rows, "00400", "", (13,), label)
    label = f"Japan {year} national Table 2"
    assert_cells(national_rows, {
        (5, 14): "Table 2. Population by Age (5-Year Age Group) and Sex, Monthly Estimates",
        (5, 15): "‐ Total population, Japanese population, the First Day, Each Month",
        (8, 22): "(Thousand persons)",
        (11, 18): "Both sexes",
        (16, 22): f"October {year}",
        (19, 18): "Total population",
        (20, 9): "Total",
        (21, 9): "years old",
    }, label)
    if compact(national_rows[20][7]) != "0～4歳":
        raise ValueError(f"{label}: unexpected age band")
    national = tuple(spreadsheet_count(national_rows[i][21], label) for i in (19, 20))
    return total, national


def revised_controls(total_rows, national_rows, year):
    total_col = 14 + (year - 2016)
    label = f"Japan {year} revised Table 5"
    assert_cells(total_rows, {
        (5, 18): "Table 5. Population by Sex for Prefectures",
        (8, 8): "（単位 千人）",
        (11, 14): "Total population",
        (11, 16): "Both sexes",
        (13, total_col): f"{year}年",
    }, label)
    total = prefecture_rows(total_rows, "00500", "01", (total_col,), label)
    national_col = 11 + (year - 2016)
    label = f"Japan {year} revised national Table 3"
    assert_cells(national_rows, {
        (5, 15): "Table 3. Population and Percentage distribution by Age (Five-Year Groups) and Sex",
        (10, 13): "Both sexes",
        (12, national_col): f"{year}年",
        (18, 10): "人 口（単位 千人） Population（Thousand persons)",
        (19, 9): "Total",
        (20, 9): "years old",
    }, label)
    if compact(national_rows[19][7]) != "0～4歳":
        raise ValueError(f"{label}: unexpected age band")
    national = tuple(spreadsheet_count(national_rows[i][national_col - 1], label) for i in (18, 19))
    return total, national


def census_2015(path, *, single_year_ages):
    table = 1 if single_year_ages else 2
    age_columns = tuple(f"{age}歳" for age in range(5)) if single_year_ages else ("0～4歳",)
    label = f"Japan 2015 apportionment Table {table}"
    with path.open(encoding="cp932", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        headers = [next(reader, []) for _ in range(13)]
        assert_cells(headers, {
            (1, 2): "平成27年国勢調査 年齢・国籍不詳をあん分した人口(参考表）（総務省統計局）",
            (5, 7): "0101(総数（男女別），総数（国籍）)",
            (13, 3): "地域コード",
            (13, 4): "地域識別コード",
            (13, 6): "総数（年齢）",
            **{(13, 7 + i): age for i, age in enumerate(age_columns)},
        }, label)
        if not headers[2][5].startswith(f"第{table}表"):
            raise ValueError(f"{label}: unexpected table number")
        population = {}
        for row in reader:
            if len(row) != len(headers[12]):
                raise ValueError(f"{label}: wrong number of fields on line {reader.line_num}")
            if row[1] != "0101" or row[3] != "a":
                continue
            geo, name = row[2], row[4].strip()
            code = geo[:2]
            if code not in GEOGRAPHIES or geo != f"{code}000" or not name or code in population:
                raise ValueError(f"{label}: invalid or duplicate geography {geo!r}")
            total = unsigned_integer(row[5], f"{label}, {geo} total")
            young = sum(
                unsigned_integer(value, f"{label}, {geo} age")
                for value in row[6:6 + len(age_columns)]
            )
            population[code] = (name, total, young)
    if population.keys() != GEOGRAPHIES or population[NATIONAL][0] != "全国":
        raise ValueError(f"{label}: expected Japan and all 47 prefecture codes")
    return population


def reconcile(year, age, totals, national, *, rounded):
    for code, (name, total, young) in age.items():
        if total <= 0 or not 0 <= young <= total:
            raise ValueError(f"Japan {year} {code}: invalid all-age or age-0–4 count")
        if totals[code] != (name, total):
            raise ValueError(f"Japan {year} {code}: all ages disagree with the companion table")
    if age[NATIONAL][1:] != national:
        raise ValueError(f"Japan {year}: national line disagrees with the separate national control")
    gaps = tuple(sum(age[code][i + 1] for code in PREFECTURES) - national[i] for i in range(2))
    # Forty-seven independently rounded prefectures and one rounded national estimate.
    limit = len(GEOGRAPHIES) // 2 if rounded else 0
    if any(abs(gap) > limit for gap in gaps):
        raise ValueError(f"Japan {year}: prefecture-to-national gaps exceed published precision")
    return gaps


def read_japan(cache, sources):
    """Return prefecture populations with provenance and annual control gaps in source units."""
    prefectures = {}
    differences = {}

    def staged(source_id):
        return verify_stage(cache, sources[source_id])

    def record(year, age, total, national, primary, controls, rounded):
        differences[year] = reconcile(year, age, total, national, rounded=rounded)
        prefectures[year] = (age, primary, controls)

    for year in (2013, 2014):
        age_id, total_id, national_id = (f"jp-{year}-{part}" for part in ("age", "total", "national"))
        age_path, age_receipt = staged(age_id)
        total_path, total_receipt = staged(total_id)
        national_path, national_receipt = staged(national_id)
        age = prefecture_age(read_xls(age_path, "第10表"), year, age_id, revised=False)
        total, national = original_controls(
            read_xls(total_path, "第４表"), read_xls(national_path, "第２表"), year,
        )
        record(year, age, total, national, age_receipt, (total_receipt, national_receipt), True)

    census_path, census_receipt = staged("jp-2015-census")
    single_path, single_receipt = staged("jp-2015-single-age")
    age = census_2015(census_path, single_year_ages=False)
    single = census_2015(single_path, single_year_ages=True)
    if any(age[code][2] != single[code][2] for code in GEOGRAPHIES):
        raise ValueError("Japan 2015: age 0–4 differs between the apportionment tables")
    record(2015, age, {code: row[:2] for code, row in single.items()}, single[NATIONAL][1:],
           census_receipt, (single_receipt,), False)

    age_path, age_receipt = staged("jp-2016-2019-age")
    total_path, total_receipt = staged("jp-2016-2019-total")
    national_path, national_receipt = staged("jp-2016-2019-national")
    sheets = read_xlsx_sheets(age_path, REVISED_SHEETS.values())
    total_rows = read_xlsx_sheets(total_path, ("第５表",))["第５表"]
    national_rows = read_xlsx_sheets(national_path, ("第３表",))["第３表"]
    for year, sheet in REVISED_SHEETS.items():
        age = prefecture_age(sheets[sheet], year, sheet, revised=True)
        total, national = revised_controls(total_rows, national_rows, year)
        record(year, age, total, national, age_receipt, (total_receipt, national_receipt), True)

    names = {code: prefectures[2015][0][code][0] for code in PREFECTURES}
    for year, (ages, _, _) in prefectures.items():
        if {code: ages[code][0] for code in PREFECTURES} != names:
            raise ValueError(f"Japan {year}: prefecture code/name pairs disagree with the 2015 census")
    return prefectures, differences
