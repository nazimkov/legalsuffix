import csv
from functools import lru_cache

from .constants import DATA_FILE_PATH
from .models import LegalSuffix, LegalSuffixes
from .parser import norm


def _split_abbreviations(value: str | None) -> list[str]:
    if not value:
        return []
    return [abbreviation for abbreviation in value.split(";") if abbreviation.strip()]


@lru_cache(maxsize=1)
def load_suffixes() -> LegalSuffixes:
    rows: list[LegalSuffix] = []
    by_country: dict[str, set[str]] = {}
    all_suffixes: set[str] = set()

    with DATA_FILE_PATH.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for line_number, csv_row in enumerate(reader, start=2):
            row = LegalSuffix(
                elf_code=csv_row.get("ELF Code") or "",
                country_of_formation=csv_row.get("Country of formation") or "",
                country_code=csv_row["Country Code (ISO 3166-1)"],
                jurisdiction_of_formation=csv_row.get("Jurisdiction of formation") or "",
                country_subdivision_code=csv_row.get("Country sub-division code (ISO 3166-2)") or "",
                entity_legal_form_name_local_name=csv_row.get("Entity Legal Form name Local name") or "",
                language=csv_row.get("Language") or "",
                language_code=csv_row.get("Language Code (ISO 639-1)") or "",
                entity_legal_form_name_transliterated_name=csv_row.get(
                    "Entity Legal Form name Transliterated name (per ISO 01-140-10)"
                )
                or "",
                abbreviations_local_language=_split_abbreviations(csv_row["Abbreviations Local language"]),
                abbreviations_transliterated=_split_abbreviations(csv_row["Abbreviations transliterated"]),
            )
            rows.append(row)
            if row.country_code is None:
                continue
            country = row.country_code.strip().upper()
            if not country:
                continue
            if len(country) != 2 or not country.isalpha():
                raise ValueError(f"{DATA_FILE_PATH}:{line_number}: bad ISO code {country!r}")

            suffixes = {
                norm(abbreviation)
                for abbreviations in (row.abbreviations_local_language, row.abbreviations_transliterated)
                for abbreviation in abbreviations
            }
            suffixes.discard("")
            if not suffixes:
                continue

            by_country.setdefault(country, set()).update(suffixes)
            all_suffixes.update(suffixes)

    return LegalSuffixes(
        all=frozenset(all_suffixes),
        by_country={country: frozenset(suffixes) for country, suffixes in by_country.items()},
        rows=rows,
    )
