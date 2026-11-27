"""Verify the pinned IDB archive and compare annual territory-wide resident counts."""

from itertools import product
from zipfile import BadZipFile, ZipFile

from demographic_sources import YEARS, YOUNG_AGES, check_cells, file_digest, unsigned_integer

SEX_PREFIXES = {0: "", 1: "M", 2: "F"}
AGES = range(101)
# POP80_ overlaps five-year bands. Only use the disjoint bands below.
AGE_BANDS = {f"{age}_{age + 4}": range(age, age + 5) for age in range(0, 100, 5)}
AGE_BANDS["100_"] = range(100, 101)
SINGLE_FIELDS = ("AGE", "SEX", "POP")
GROUPED_FIELDS = tuple(
    f"{prefix}POP{band}" for prefix, band in product(SEX_PREFIXES.values(), ("", *AGE_BANDS))
)


def territory_rows(archive, member, geo_id, years, fields):
    selected = {str(year).encode("ascii"): year for year in years}
    geo = geo_id.encode("ascii")
    with archive.open(member) as stream:
        header = next(stream, b"").decode("ascii").rstrip("\r\n").split("|")
        expected = {"#YR", "GEO_ID", *fields}
        if (
            header[:2] != ["#YR", "GEO_ID"]
            or len(set(header)) != len(header)
            or not expected.issubset(header)
        ):
            raise ValueError(f"{member}: unexpected IDB header")
        columns = {field: header.index(field) for field in fields}
        for line in stream:
            year, row_geo, _ = line.split(b"|", 2)
            if row_geo != geo or year not in selected:
                continue
            values = line.decode("ascii").rstrip("\r\n").split("|")
            if len(values) != len(header):
                raise ValueError(f"{member} {selected[year]}: wrong number of fields")
            yield selected[year], {
                field: unsigned_integer(values[index], f"{member} {selected[year]} {field}")
                for field, index in columns.items()
            }


def read_vi_counts(path, source, years):
    if file_digest(path) != source["expected_sha256"]:
        raise ValueError("IDB archive SHA-256 disagrees with the source contract")
    grouped = {}
    single = {}
    try:
        with ZipFile(path) as archive:
            if sorted(archive.namelist()) != ["idb5yr.txt", "idbsingleyear.txt", "readme.txt"]:
                raise ValueError("unexpected IDB archive members")
            release = archive.read("readme.txt").decode("utf-8-sig").splitlines()
            if release[:2] != ["International Database (IDB)", source["vintage"]]:
                raise ValueError("IDB README release disagrees with the source contract")
            for year, row in territory_rows(archive, "idb5yr.txt", source["geo_id"], years, GROUPED_FIELDS):
                if year in grouped:
                    raise ValueError(f"idb5yr.txt: duplicate territory row for {year}")
                grouped[year] = row
            for year, row in territory_rows(archive, "idbsingleyear.txt", source["geo_id"], years, SINGLE_FIELDS):
                key = (year, row["AGE"], row["SEX"])
                if key in single or key[1] not in AGES or key[2] not in SEX_PREFIXES:
                    raise ValueError(f"idbsingleyear.txt: duplicate or invalid territory cell {key}")
                single[key] = row["POP"]
    except BadZipFile as error:
        raise ValueError(f"invalid IDB ZIP: {error}") from error
    check_cells(grouped, set(years), "idb5yr.txt")
    check_cells(single, set(product(years, AGES, SEX_PREFIXES)), "idbsingleyear.txt")

    for year, row in grouped.items():
        for age in AGES:
            if single[year, age, 0] != single[year, age, 1] + single[year, age, 2]:
                raise ValueError(f"idbsingleyear.txt {year}: sexes disagree at age {age}")
        for sex, prefix in SEX_PREFIXES.items():
            for band, ages in (("", AGES), *AGE_BANDS.items()):
                field = f"{prefix}POP{band}"
                if row[field] != sum(single[year, age, sex] for age in ages):
                    raise ValueError(f"IDB members disagree for {year} {field}")
        total, young = row["POP"], row["POP0_4"]
        if not 0 < young <= total:
            raise ValueError(f"idb5yr.txt {year}: invalid territory totals")
    return {year: (row["POP"], row["POP0_4"]) for year, row in grouped.items()}


def check_vi_idb(path, source):
    census = {int(year): count for year, count in source["census_april_1_totals"].items()}
    ber = dict(zip(YEARS, source["ber_resident_totals"], strict=True))
    estimates = read_vi_counts(path, source, (*YEARS, *census))
    print(f"Verified IDB {source['vintage']}, {source['geo_id']}, SHA-256 {source['expected_sha256']}")
    print(f"{len(YEARS)} annual territory rows matched same-release single ages for both sexes")
    print("July 1       IDB total  IDB ages 0–4  IDB share  BER annual  IDB vs BER")
    for year in YEARS:
        total, young = estimates[year]
        print(f"{year}-07-01  {total:9,d}  {young:12,d}  {young / total:9.2%}  "
              f"{ber[year]:10,d}  {total / ber[year] - 1:+10.2%}")

    first, last = YEARS[0], YEARS[-1]
    first_total, first_young = estimates[first]
    last_total, last_young = estimates[last]
    idb_change = last_total / first_total - 1
    ber_change = ber[last] / ber[first] - 1
    print(f"{first}–{last} all-age change: IDB {idb_change:+.2%}, BER {ber_change:+.2%}, "
          f"IDB minus BER {100 * (idb_change - ber_change):+.2f} percentage points")
    print(f"{first}–{last} IDB ages 0–4 change: {last_young / first_young - 1:+.2%}, "
          f"share change {100 * (last_young / last_total - first_young / first_total):+.2f} percentage points")
    print("Context only     IDB July 1  Census April 1  IDB vs Census")
    for year, census_total in sorted(census.items()):
        idb_total, _ = estimates[year]
        print(f"{year}             {idb_total:10,d}  {census_total:14,d}  {idb_total / census_total - 1:+12.2%}")
