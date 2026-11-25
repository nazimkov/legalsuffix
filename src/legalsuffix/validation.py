from collections.abc import Sequence

from .models import CountryCodeFilter, LanguageCodeFilter

NormalizedCountryCodeFilter = str | tuple[str, ...] | None
NormalizedLanguageCodeFilter = str | tuple[str, ...] | None


def _validate_codes(
    value: CountryCodeFilter | LanguageCodeFilter,
    *,
    uppercase: bool,
    description: str,
) -> str | tuple[str, ...] | None:
    if value is None:
        return None

    is_multiple = not isinstance(value, str)
    if is_multiple and not isinstance(value, Sequence):
        raise ValueError(f"Invalid {description}: {value}")
    codes = value if is_multiple else (value,)
    normalized_codes: list[str] = []
    for code in codes:
        if not isinstance(code, str):
            raise ValueError(f"Invalid {description}: {code}")
        normalized = code.upper() if uppercase else code.lower()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError(f"Invalid {description}: {code}")
        normalized_codes.append(normalized)

    if is_multiple:
        return tuple(normalized_codes)
    return normalized_codes[0]


def validate_country_code(country_code: CountryCodeFilter) -> NormalizedCountryCodeFilter:
    """Validate and uppercase one or more ISO 3166-1 alpha-2 country codes."""
    return _validate_codes(country_code, uppercase=True, description="ISO 3166-1 alpha-2 country code")


def validate_language_code(language_code: LanguageCodeFilter) -> NormalizedLanguageCodeFilter:
    """Validate and lowercase one or more ISO 639-1 two-letter language codes."""
    return _validate_codes(language_code, uppercase=False, description="ISO 639-1 language code")
