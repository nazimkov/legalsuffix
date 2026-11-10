import unicodedata

from .loader import load_suffixes
from .models import LegalSuffixMatch, ParsedCompanyName
from .parser import suffix_key
from .validation import validate_country_code, validate_language_code


def _find_suffix(
    name: str,
    country_code: str | None = None,
    language_code: str | None = None,
) -> LegalSuffixMatch | None:
    country_code = validate_country_code(country_code)
    language_code = validate_language_code(language_code)
    suffixes = load_suffixes(country_code=country_code, language_code=language_code)

    # Ignore whitespace and a trailing comma/semicolon when locating the suffix,
    # while keeping punctuation attached to the suffix itself in its offsets.
    end_pos = len(name.rstrip())
    while end_pos and name[end_pos - 1] in ",;":
        end_pos -= 1
    end_pos = len(name[:end_pos].rstrip())
    if end_pos == 0:
        return None

    first_start = len(name[:end_pos]) - len(name[:end_pos].lstrip())
    starts = [first_start] if first_start < end_pos else []
    for index in range(first_start + 1, end_pos):
        previous = name[index - 1]
        current = name[index]
        if previous.isspace() or previous in ",;:-" or (_is_wide_character(previous) and _is_wide_character(current)):
            starts.append(index)

    # First try suffixes ending at the end of the name. Some registries include
    # descriptive text after the legal form, so also inspect bounded spans
    # elsewhere in the name when there is no trailing match.
    candidates: list[LegalSuffixMatch] = []
    for start_pos in starts:
        if not name[start_pos].isalnum() and not _is_wide_character(name[start_pos]):
            continue
        for candidate_end in range(end_pos, start_pos, -1):
            if candidate_end < end_pos and not _is_end_boundary(name, candidate_end):
                continue
            candidate = name[start_pos:candidate_end].strip()
            normalized = suffix_key(candidate)
            records = suffixes.by_normalized_suffix.get(normalized)
            if records:
                if start_pos == first_start and candidate_end != end_pos:
                    continue
                candidates.append(
                    LegalSuffixMatch(
                        suffix=candidate,
                        normalized_suffix=normalized,
                        start_pos=start_pos,
                        end_pos=candidate_end,
                        records=list(records),
                    )
                )

    if not candidates:
        return None
    return max(
        candidates,
        key=lambda match: (
            match.end_pos == end_pos,
            match.end_pos - match.start_pos,
            match.start_pos,
        ),
    )


def _is_wide_character(character: str) -> bool:
    return unicodedata.east_asian_width(character) in {"F", "W"}


def _is_end_boundary(name: str, position: int) -> bool:
    current = name[position]
    previous = name[position - 1]
    is_separator = current.isspace() or current in ",;:-"
    is_cjk_boundary = _is_wide_character(previous) and _is_wide_character(current)
    return previous not in ",;:-" and (is_separator or is_cjk_boundary)


def match_legal_suffix(
    name: str,
    country_code: str | None = None,
    language_code: str | None = None,
) -> LegalSuffixMatch | None:
    """Find a legal form in a company name.

    Args:
        name: Company name to inspect.
        country_code: Optional ISO 3166-1 alpha-2 country code, such as ``"US"``.
        language_code: Optional ISO 639-1 two-letter language code, such as ``"en"``.

    Returns:
        A :class:`LegalSuffixMatch`, or ``None`` if no suffix matches. Match
        offsets refer to the original string; ``end_pos`` is exclusive.

    Raises:
        ValueError: If either provided code is not in the expected format.

    Example:
        >>> match = match_legal_suffix("Acme GmbH", country_code="DE")
        >>> (match.suffix, match.start_pos, match.end_pos)
        ('GmbH', 5, 9)
    """
    return _find_suffix(name, country_code, language_code)


def strip_legal_suffix(name: str, country_code: str | None = None, language_code: str | None = None) -> str:
    """Remove a recognized legal form from a company name.

    Args:
        name: Company name to strip.
        country_code: Optional ISO 3166-1 alpha-2 country code, such as ``"US"``.
        language_code: Optional ISO 639-1 two-letter language code, such as ``"en"``.

    Returns:
        The company name without the matched legal form, or the original string
        when no suffix matches. Text before and after the form is preserved.

    Raises:
        ValueError: If either provided code is not in the expected format.

    Example:
        >>> strip_legal_suffix("Acme GmbH", country_code="DE")
        'Acme'
    """
    match = _find_suffix(name, country_code, language_code)
    if match is None:
        return name
    prefix = name[: match.start_pos].rstrip(" ,;:-")
    return (prefix + name[match.end_pos :]).strip()


def parse_company_name(
    name: str,
    country_code: str | None = None,
    language_code: str | None = None,
) -> ParsedCompanyName:
    """Split a company name around a recognized legal form.

    Args:
        name: Company name to parse.
        country_code: Optional ISO 3166-1 alpha-2 country code, such as ``"DE"``.
        language_code: Optional ISO 639-1 two-letter language code, such as ``"de"``.

    Returns:
        A :class:`ParsedCompanyName`. Its ``name`` contains the name with the
        matched legal form removed, and ``suffix`` is a :class:`LegalSuffixMatch`
        or ``None``.

    Raises:
        ValueError: If either provided code is not in the expected format.

    Example:
        >>> parsed = parse_company_name("Acme GmbH", country_code="DE")
        >>> (parsed.name, parsed.suffix.suffix)
        ('Acme', 'GmbH')
    """
    match = _find_suffix(name, country_code, language_code)
    if match is None:
        return ParsedCompanyName(name=name, suffix=None)
    prefix = name[: match.start_pos].rstrip(" ,;:-")
    clean_name = (prefix + name[match.end_pos :]).strip()
    return ParsedCompanyName(name=clean_name, suffix=match)


def normalize_legal_suffix(suffix: str) -> str:
    """Normalize suffix text to the key used for matching.

    Normalization trims surrounding whitespace, ignores punctuation and accents,
    and lowercases the text. It does not look up the suffix in the data.

    Args:
        suffix: Suffix text to normalize.

    Returns:
        The normalized suffix key.

    Example:
        >>> normalize_legal_suffix(" GmbH. ")
        'gmbh'
    """
    return suffix_key(suffix)
