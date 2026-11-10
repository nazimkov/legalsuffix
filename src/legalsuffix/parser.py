import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedSuffixes:
    all: frozenset[str]
    by_country: dict[str, frozenset[str]]


def parse_suffixes(text: str) -> ParsedSuffixes:
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
    return ParsedSuffixes(all=frozenset(all_suffixes), by_country=by_country)


def norm(s: str) -> str:
    """Normalize a suffix for matching: lowercase, trim, and drop final punctuation."""
    return s.strip().lower().rstrip(".,").strip()


def suffix_key(suffix: str) -> str:
    """Canonicalize punctuation and accents for matching suffix spellings."""
    decomposed = unicodedata.normalize("NFKD", suffix).casefold()
    words = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character) and (character.isalnum() or character.isspace())
    ).split()

    normalized_words: list[str] = []
    short_words: list[str] = []
    for word in words:
        if len(word) <= 2:
            short_words.append(word)
        else:
            if short_words:
                normalized_words.append("".join(short_words))
                short_words = []
            normalized_words.append(word)
    if short_words:
        normalized_words.append("".join(short_words))
    return " ".join(normalized_words)
