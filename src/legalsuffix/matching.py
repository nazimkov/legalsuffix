from .loader import load_suffixes
from .parser import norm
from .validation import validate_country_code, validate_language_code


def strip_legal_suffix(name: str, country_code: str | None = None, language_code: str | None = None) -> str:
    """Remove a trailing legal suffix, optionally limited by country and language.

    ``country_code`` uses ISO 3166-1 alpha-2 codes (for example, ``"US"``).
    ``language_code`` uses ISO 639-1 two-letter codes (for example, ``"en"``).
    """
    if country_code is not None:
        country_code = validate_country_code(country_code)
    if language_code is not None:
        language_code = validate_language_code(language_code)
    suffixes = load_suffixes(country_code=country_code, language_code=language_code)

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
