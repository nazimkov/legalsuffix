from collections.abc import Mapping

from .models import LegalSuffix


def validate_iso(iso: str) -> str:
    """Validate and normalize an ISO 3166-1 alpha-2 country code."""
    iso = iso.upper()
    if len(iso) != 2 or not iso.isalpha():
        raise ValueError(f"Invalid ISO country code: {iso}")
    return iso


def ensure_supported_country(iso: str, suffixes: Mapping[str, list[LegalSuffix]]) -> None:
    """Raise an error if the given ISO code is not supported."""
    iso = validate_iso(iso)
    if not any(row.country_code == iso for rows in suffixes.values() for row in rows):
        raise ValueError(f"Unsupported country code: {iso}")
