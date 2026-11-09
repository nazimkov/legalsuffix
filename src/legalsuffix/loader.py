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
            country_code = csv_row["Country Code (ISO 3166-1)"]
            if not country_code:
                raise ValueError(f"{DATA_FILE_PATH}:{line_number}: missing Country Code (ISO 3166-1)")
            row = LegalSuffix(
                elf_code=csv_row["ELF Code"],
                country_of_formation=csv_row["Country of formation"],
                country_code=country_code,
                jurisdiction_of_formation=csv_row["Jurisdiction of formation"],
                country_subdivision_code=csv_row["Country sub-division code (ISO 3166-2)"],
                entity_legal_form_name_local_name=csv_row["Entity Legal Form name Local name"],
                language=csv_row["Language"],
                language_code=csv_row["Language Code (ISO 639-1)"],
                entity_legal_form_name_transliterated_name=csv_row[
                    "Entity Legal Form name Transliterated name (per ISO 01-140-10)"
                ],
                abbreviations_local_language=_split_abbreviations(csv_row["Abbreviations Local language"]),
                abbreviations_transliterated=_split_abbreviations(csv_row["Abbreviations transliterated"]),
            )
            rows.append(row)
            suffixes = {
                norm(abbreviation)
                for abbreviations in (
                    row.abbreviations_local_language,
                    row.abbreviations_transliterated,
                    row.entity_legal_form_name_local_name,
                    row.entity_legal_form_name_transliterated_name,
                )
                for abbreviation in abbreviations
            }
            suffixes.discard("")
            if not suffixes:
                continue

            by_country.setdefault(country_code, set()).update(suffixes)
            all_suffixes.update(suffixes)

    return LegalSuffixes(
        all=frozenset(all_suffixes),
        by_country={country: frozenset(suffixes) for country, suffixes in by_country.items()},
        rows=rows,
    )
