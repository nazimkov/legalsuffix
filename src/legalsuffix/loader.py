import csv
from collections.abc import Sequence
from functools import lru_cache

from .constants import DATA_FILE_PATH
from .models import CountryCodeFilter, LanguageCodeFilter, LegalSuffix, LegalSuffixes, SuffixTrie
from .parser import suffix_key
from .validation import (
    NormalizedCountryCodeFilter,
    NormalizedLanguageCodeFilter,
    validate_country_code,
    validate_language_code,
)


def _split_abbreviations(value: str | None) -> list[str]:
    if not value:
        return []
    return [abbreviation for abbreviation in value.split(";") if abbreviation.strip()]


def load_suffixes(
    country_code: CountryCodeFilter = None,
    language_code: LanguageCodeFilter = None,
) -> LegalSuffixes:
    """Load suffix records, optionally limiting them by country and language."""
    country_code = validate_country_code(country_code)
    language_code = validate_language_code(language_code)

    return _load_suffixes(country_code, language_code)


def list_legal_suffixes(
    country_code: CountryCodeFilter = None,
    language_code: LanguageCodeFilter = None,
) -> Sequence[LegalSuffix]:
    """Return legal suffix records, optionally filtered by country and language.

    Args:
        country_code: Optional ISO 3166-1 alpha-2 code or sequence, such as ``"DE"`` or ``["DE", "FR"]``.
        language_code: Optional ISO 639-1 two-letter code or sequence, such as ``"de"`` or ``["de", "fr"]``.

    Returns:
        An immutable sequence of :class:`LegalSuffix` records.

    Raises:
        ValueError: If either provided code is not in the expected format.

    Example:
        >>> records = list_legal_suffixes(country_code="DE", language_code="de")
        >>> all(record.country_code == "DE" for record in records)
        True
    """
    country_code = validate_country_code(country_code)
    language_code = validate_language_code(language_code)
    return tuple(load_suffixes(country_code, language_code).records)


@lru_cache(maxsize=1)
def _load_suffixes(
    country_code: NormalizedCountryCodeFilter,
    language_code: NormalizedLanguageCodeFilter,
) -> LegalSuffixes:
    by_normalized_suffix: dict[str, list[LegalSuffix]] = {}
    records: list[LegalSuffix] = []
    country_codes = None if country_code is None else set(_filter_codes(country_code))
    language_codes = None if language_code is None else set(_filter_codes(language_code))

    with DATA_FILE_PATH.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for line_number, csv_row in enumerate(reader, start=2):
            row_country_code = csv_row["Country Code (ISO 3166-1)"]
            if not row_country_code:
                raise ValueError(f"{DATA_FILE_PATH}:{line_number}: missing Country Code (ISO 3166-1)")

            row_language_code = csv_row["Language Code (ISO 639-1)"]
            if country_codes is not None and row_country_code.upper() not in country_codes:
                continue
            if language_codes is not None and row_language_code.lower() not in language_codes:
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
                suffix_key(suffix)
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

    prefix_trie = SuffixTrie()
    suffix_trie = SuffixTrie(reversed_keys=True)
    for normalized_suffix, matching_records in by_normalized_suffix.items():
        prefix_trie.add(normalized_suffix, matching_records)
        suffix_trie.add(normalized_suffix, matching_records)

    return LegalSuffixes(
        by_normalized_suffix=by_normalized_suffix,
        records=records,
        prefix_trie=prefix_trie,
        suffix_trie=suffix_trie,
    )


def _filter_codes(value: str | tuple[str, ...]) -> tuple[str, ...]:
    return value if isinstance(value, tuple) else (value,)
