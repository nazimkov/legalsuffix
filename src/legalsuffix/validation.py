def validate_country_code(country_code: str | None) -> str | None:
    """Validate and uppercase an ISO 3166-1 alpha-2 country code."""
    if country_code is None:
        return None
    normalized = country_code.upper()
    if len(normalized) != 2 or not normalized.isalpha():
        raise ValueError(f"Invalid ISO 3166-1 alpha-2 country code: {country_code}")
    return normalized


def validate_language_code(language_code: str | None) -> str | None:
    """Validate and lowercase an ISO 639-1 two-letter language code."""
    if language_code is None:
        return None
    normalized = language_code.lower()
    if len(normalized) != 2 or not normalized.isalpha():
        raise ValueError(f"Invalid ISO 639-1 language code: {language_code}")
    return normalized
