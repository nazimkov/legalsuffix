import unicodedata

from .loader import load_suffixes
from .models import CountryCodeFilter, LanguageCodeFilter, LegalSuffixMatch, ParsedCompanyName
from .parser import suffix_key
from .validation import validate_country_code, validate_language_code


def _find_suffix(
    name: str,
    country_code: CountryCodeFilter = None,
    language_code: LanguageCodeFilter = None,
) -> LegalSuffixMatch | None:
    country_code = validate_country_code(country_code)
    language_code = validate_language_code(language_code)
    suffixes = load_suffixes(country_code=country_code, language_code=language_code)

    # Ignore whitespace and trailing separator punctuation when locating the
    # suffix. A terminal period can be part of the suffix (for example Inc.),
    # but a period before a trailing comma or semicolon is punctuation.
    end_pos = len(name)
    while end_pos and name[end_pos - 1].isspace():
        end_pos -= 1
    had_trailing_separator = False
    while end_pos and name[end_pos - 1] in ",;:-":
        had_trailing_separator = True
        end_pos -= 1
    if had_trailing_separator:
        while end_pos and name[end_pos - 1] == ".":
            end_pos -= 1
    while end_pos and name[end_pos - 1].isspace():
        end_pos -= 1
    if end_pos == 0:
        return None

    first_start = len(name) - len(name.lstrip())
    segment = name[first_start:end_pos]
    # For ASCII words separated by spaces, suffix_key's normalization can be
    # streamed one word at a time. Other input uses the full normalization
    # below, including punctuation and Unicode compatibility characters.
    simple_words = segment.split() if segment.isascii() and segment.replace(" ", "").isalnum() else None
    if simple_words:
        node = suffixes.suffix_trie.root
        best_start = None
        best_records = None
        cursor = end_pos
        previous_short = False
        for word_index, word in enumerate(reversed(simple_words)):
            while cursor > first_start and name[cursor - 1] == " ":
                cursor -= 1
            cursor -= len(word)
            short = len(word) <= 2
            if word_index and not (short and previous_short):
                child = node.children.get(" ")
                if child is None:
                    break
                node = child
            for character in reversed(word.lower()):
                child = node.children.get(character)
                if child is None:
                    break
                node = child
            else:
                if node.records:
                    best_start = cursor
                    best_records = node.records
                previous_short = short
                continue
            break
        if best_start is not None and best_records is not None:
            candidate = name[best_start:end_pos]
            return LegalSuffixMatch(
                suffix=candidate,
                normalized_suffix=suffix_key(candidate),
                start_pos=best_start,
                end_pos=end_pos,
                records=list(best_records),
            )

        # Prefix candidates end at a space, and the original matcher retains
        # the last boundary in a run of spaces when selecting the longest one.
        node = suffixes.prefix_trie.root
        best_end = None
        best_records = None
        cursor = first_start
        previous_short = False
        for word_index, word in enumerate(simple_words):
            short = len(word) <= 2
            if word_index and not (short and previous_short):
                child = node.children.get(" ")
                if child is None:
                    break
                node = child
            for character in word.lower():
                child = node.children.get(character)
                if child is None:
                    break
                node = child
            else:
                cursor += len(word)
                while cursor < end_pos and name[cursor] == " ":
                    cursor += 1
                if cursor < end_pos and node.records:
                    best_end = cursor - 1
                    best_records = node.records
                previous_short = short
                continue
            break
        if best_end is not None and best_records is not None:
            candidate = name[first_start:best_end].rstrip()
            return LegalSuffixMatch(
                suffix=candidate,
                normalized_suffix=suffix_key(candidate),
                start_pos=first_start,
                end_pos=best_end,
                records=list(best_records),
            )

    starts = [first_start] if first_start < end_pos else []
    for index in range(first_start + 1, end_pos):
        previous = name[index - 1]
        current = name[index]
        if (
            previous.isspace()
            or previous in ",;:-"
            or (not previous.isascii() and _is_wide_character(previous) and _is_wide_character(current))
        ):
            starts.append(index)

    # First try suffixes ending at the end of the name. Some registries include
    # descriptive text after the legal form, so also inspect bounded spans
    # elsewhere in the name when there is no trailing match.
    # Starts are in ascending order, so the first trailing match is the
    # longest one and outranks every match ending earlier in the name.
    if simple_words is None:
        for start_pos in starts:
            if not name[start_pos].isalnum() and not _is_wide_character(name[start_pos]) and name[start_pos] != "(":
                continue
            # Starts and end_pos are already trimmed to candidate boundaries.
            candidate = name[start_pos:end_pos]
            normalized = suffix_key(candidate)
            records = suffixes.by_normalized_suffix.get(normalized)
            if records:
                return LegalSuffixMatch(
                    suffix=candidate,
                    normalized_suffix=normalized,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    records=list(records),
                )

    # Reuse end boundaries for leading and interior spans. ASCII characters
    # cannot be wide, so avoid Unicode width lookups for the common case.
    end_boundaries = []
    for position in range(first_start + 1, end_pos):
        previous = name[position - 1]
        current = name[position]
        if previous not in ",;:-" and (
            current.isspace()
            or current in ",;:-"
            or (not previous.isascii() and _is_wide_character(previous) and _is_wide_character(current))
        ):
            end_boundaries.append(position)

    # A few registries put the legal form before the company name. Try the
    # longest leading span first, as for trailing candidates.
    if simple_words is None:
        for candidate_end in reversed(end_boundaries):
            candidate = name[first_start:candidate_end]
            if candidate[-1].isspace():
                candidate = candidate.rstrip()
            normalized = suffix_key(candidate)
            records = suffixes.by_normalized_suffix.get(normalized)
            if records:
                return LegalSuffixMatch(
                    suffix=candidate,
                    normalized_suffix=normalized,
                    start_pos=first_start,
                    end_pos=candidate_end,
                    records=list(records),
                )

    # Interior candidates cannot start at the first non-whitespace character.
    # Retain the longest match, breaking ties in favor of the later start, as
    # for the original candidate ordering.
    best: LegalSuffixMatch | None = None
    best_length = 0
    for start_pos in starts:
        if start_pos == first_start or (not name[start_pos].isalnum() and not _is_wide_character(name[start_pos])):
            continue
        for candidate_end in reversed(end_boundaries):
            candidate_length = candidate_end - start_pos
            if candidate_length <= 0 or candidate_length < best_length:
                break
            candidate = name[start_pos:candidate_end]
            if candidate[-1].isspace():
                candidate = candidate.rstrip()
            normalized = suffix_key(candidate)
            records = suffixes.by_normalized_suffix.get(normalized)
            if records:
                best = LegalSuffixMatch(
                    suffix=candidate,
                    normalized_suffix=normalized,
                    start_pos=start_pos,
                    end_pos=candidate_end,
                    records=list(records),
                )
                best_length = candidate_length
                break

    return best


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
    country_code: CountryCodeFilter = None,
    language_code: LanguageCodeFilter = None,
) -> LegalSuffixMatch | None:
    """Find a legal form in a company name.

    Args:
        name: Company name to inspect.
        country_code: Optional ISO 3166-1 alpha-2 code or sequence, such as ``"US"`` or ``["US", "CA"]``.
        language_code: Optional ISO 639-1 two-letter code or sequence, such as ``"en"`` or ``["en", "fr"]``.

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


def strip_legal_suffix(
    name: str,
    country_code: CountryCodeFilter = None,
    language_code: LanguageCodeFilter = None,
) -> str:
    """Remove a recognized legal form from a company name.

    Args:
        name: Company name to strip.
        country_code: Optional ISO 3166-1 alpha-2 code or sequence, such as ``"US"`` or ``["US", "CA"]``.
        language_code: Optional ISO 639-1 two-letter code or sequence, such as ``"en"`` or ``["en", "fr"]``.

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
    suffix_tail = name[match.end_pos :]
    if not suffix_tail.strip(" ,;:-."):
        suffix_tail = ""
    return (prefix + suffix_tail).strip()


def parse_company_name(
    name: str,
    country_code: CountryCodeFilter = None,
    language_code: LanguageCodeFilter = None,
) -> ParsedCompanyName:
    """Split a company name around a recognized legal form.

    Args:
        name: Company name to parse.
        country_code: Optional ISO 3166-1 alpha-2 code or sequence, such as ``"DE"`` or ``["DE", "AT"]``.
        language_code: Optional ISO 639-1 two-letter code or sequence, such as ``"de"`` or ``["de", "fr"]``.

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
    suffix_tail = name[match.end_pos :]
    if not suffix_tail.strip(" ,;:-."):
        suffix_tail = ""
    clean_name = (prefix + suffix_tail).strip()
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
