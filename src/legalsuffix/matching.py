from .countries import ensure_supported_country, validate_iso
from .loader import load_suffixes
from .parser import norm


def strip_legal_suffix(name: str, iso: str | None = None) -> str:
    """Remove a trailing legal suffix for the given country, if present."""

    suffixes = load_suffixes()
    if iso is not None:
        iso = validate_iso(iso)
        ensure_supported_country(iso, suffixes.by_country)
        suffixes_set = suffixes.by_country[iso]
    else:
        suffixes_set = suffixes.all

    tokens = name.split()
    if not tokens:
        return name

    # Try longest match first (2-token suffixes like "e. V." or "S. A.")
    for n in (2, 1):
        if len(tokens) >= n:
            candidate = norm(" ".join(tokens[-n:]))
            if candidate in suffixes_set:
                return " ".join(tokens[:-n]).rstrip(",").strip()

    return name
