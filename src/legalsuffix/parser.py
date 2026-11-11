import unicodedata


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
