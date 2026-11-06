import csv
from functools import lru_cache

from .constants import DATA_FILE_PATH
from .models import LegalSuffixes
from .parser import norm


@lru_cache(maxsize=1)
def load_suffixes() -> LegalSuffixes:
    by_country: dict[str, set[str]] = {}
    all_suffixes: set[str] = set()

    with DATA_FILE_PATH.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {
            "Country Code (ISO 3166-1)",
            "Abbreviations Local language",
            "Abbreviations transliterated",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{DATA_FILE_PATH}: missing CSV columns: {', '.join(sorted(missing))}")

        for line_number, row in enumerate(reader, start=2):
            country = (row["Country Code (ISO 3166-1)"] or "").strip().upper()
            if not country:
                continue
            if len(country) != 2 or not country.isalpha():
                raise ValueError(f"{DATA_FILE_PATH}:{line_number}: bad ISO code {country!r}")

            suffixes = {
                norm(value)
                for column in ("Abbreviations Local language", "Abbreviations transliterated")
                for value in (row[column] or "").split(";")
            }
            suffixes.discard("")
            if not suffixes:
                continue

            by_country.setdefault(country, set()).update(suffixes)
            all_suffixes.update(suffixes)

    return LegalSuffixes(
        all=frozenset(all_suffixes),
        by_country={country: frozenset(suffixes) for country, suffixes in by_country.items()},
    )
