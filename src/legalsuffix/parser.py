from .models import LegalSuffixes


def parse_suffixes(text: str) -> LegalSuffixes:
    """Parse TSV of `ISO<TAB>suffix1|suffix2|...` into a lookup dict.

    Suffixes are normalized: lowercased, trailing dots stripped.
    """
    all_suffixes: set[str] = set()
    by_country: dict[str, frozenset[str]] = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            iso, raw = line.split("\t", 1)
        except ValueError as ex:
            raise ValueError(f"line {lineno}: expected '<ISO>\\t<suffixes>', got {line!r}") from ex
        iso = iso.strip().upper()
        if len(iso) != 2:
            raise ValueError(f"line {lineno}: bad ISO code {iso!r}")
        suffixes = {norm(s) for s in raw.split("|")}
        if not suffixes:
            raise ValueError(f"line {lineno}: no suffixes for {iso}")
        all_suffixes.update(suffixes)
        by_country[iso] = frozenset(suffixes)
    return LegalSuffixes(all=frozenset(all_suffixes), by_country=by_country)


def norm(s: str) -> str:
    """Normalize a suffix for matching: lowercase, strip"""
    return s.strip().lower()
