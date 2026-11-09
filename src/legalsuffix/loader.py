import csv
from functools import lru_cache

from .constants import DATA_FILE_PATH
from .models import LegalSuffix, LegalSuffixes
from .parser import norm
from .validation import validate_country_code, validate_language_code


def _split_abbreviations(value: str | None) -> list[str]:
    if not value:
        return []
    return [abbreviation for abbreviation in value.split(";") if abbreviation.strip()]


def load_suffixes(country_code: str | None = None, language_code: str | None = None) -> LegalSuffixes:
    """Load suffix records, optionally limiting them by country and language."""
    if country_code is not None:
        country_code = country_code.upper()
    if language_code is not None:
        language_code = language_code.lower()

    return _load_suffixes(country_code, language_code)


def get_suffixes(country_code: str | None = None, language_code: str | None = None) -> list[LegalSuffix]:
    """Return legal suffix records, optionally filtered by country and language.

    Args:
        country_code: Optional ISO 3166-1 alpha-2 country code, such as ``"DE"``.
        language_code: Optional ISO 639-1 two-letter language code, such as ``"de"``.

    Returns:
        A list of :class:`LegalSuffix` records. The returned list can be modified
        without changing the loader's cached list.

    Raises:
        ValueError: If either provided code is not in the expected format.

    Example:
        >>> records = get_suffixes(country_code="DE", language_code="de")
        >>> all(record.country_code == "DE" for record in records)
        True
    """
    country_code = validate_country_code(country_code)
    language_code = validate_language_code(language_code)
    return list(load_suffixes(country_code, language_code).records)


@lru_cache(maxsize=1)
def _load_suffixes(country_code: str | None, language_code: str | None) -> LegalSuffixes:
    by_normalized_suffix: dict[str, list[LegalSuffix]] = {}
    records: list[LegalSuffix] = []

    with DATA_FILE_PATH.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for line_number, csv_row in enumerate(reader, start=2):
            row_country_code = csv_row["Country Code (ISO 3166-1)"]
            if not row_country_code:
                raise ValueError(f"{DATA_FILE_PATH}:{line_number}: missing Country Code (ISO 3166-1)")

            row_language_code = csv_row["Language Code (ISO 639-1)"]
            if country_code is not None and row_country_code.upper() != country_code:
                continue
            if language_code is not None and row_language_code.lower() != language_code:
                continue

            row = LegalSuffix(
                elf_code=csv_row["ELF Code"],
                country_of_formation=csv_row["Country of formation"],
                country_code=row_country_code,
                jurisdiction_of_formation=csv_row["Jurisdiction of formation"],
                country_subdivision_code=csv_row["Country sub-division code (ISO 3166-2)"],
                entity_legal_form_name_local_name=csv_row["Entity Legal Form name Local name"],
                language=csv_row["Language"],
                language_code=row_language_code,
                entity_legal_form_name_transliterated_name=csv_row[
                    "Entity Legal Form name Transliterated name (per ISO 01-140-10)"
                ],
                abbreviations_local_language=_split_abbreviations(csv_row["Abbreviations Local language"]),
                abbreviations_transliterated=_split_abbreviations(csv_row["Abbreviations transliterated"]),
            )
            records.append(row)
            suffixes = {
                norm(suffix)
                for suffix in (
                    *row.abbreviations_local_language,
                    *row.abbreviations_transliterated,
                    row.entity_legal_form_name_local_name,
                    row.entity_legal_form_name_transliterated_name,
                )
            }
            suffixes.discard("")
            for suffix in suffixes:
                by_normalized_suffix.setdefault(suffix, []).append(row)

    return LegalSuffixes(by_normalized_suffix=by_normalized_suffix, records=records)
