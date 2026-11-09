from .countries import ensure_supported_country, validate_iso
from .loader import load_suffixes
from .parser import norm


def strip_legal_suffix(name: str, country_code: str | None = None, language_code: str | None = None) -> str:
    """Remove a trailing legal suffix, optionally limited by country and language.

    ``country_code`` uses ISO 3166-1 alpha-2 codes (for example, ``"US"``).
    ``language_code`` uses ISO 639-1 two-letter codes (for example, ``"en"``).
    """
    if country_code is not None:
        country_code = validate_iso(country_code)
    suffixes = load_suffixes(country_code=country_code, language_code=language_code)

    if country_code is not None and not suffixes.by_normalized_suffix:
        # A valid country can have no records for the requested language.
        country_suffixes = load_suffixes(country_code=country_code)
        ensure_supported_country(country_code, country_suffixes.by_normalized_suffix)
    elif country_code is not None:
        ensure_supported_country(country_code, suffixes.by_normalized_suffix)

    tokens = name.split()
    if not tokens:
        return name

    # Try longest match first (2-token suffixes like "e. V." or "S. A.")
    for n in (2, 1):
        if len(tokens) >= n:
            candidate = norm(" ".join(tokens[-n:]))
            if candidate in suffixes.by_normalized_suffix:
                return " ".join(tokens[:-n]).rstrip(",").strip()

    return name
