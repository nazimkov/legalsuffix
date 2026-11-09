from dataclasses import dataclass


@dataclass(frozen=True)
class LegalSuffix:
    """A legal entity form record from the ELF code list.

    Attributes:
        elf_code: Entity Legal Form code.
        country_of_formation: Country name from the source data.
        country_code: ISO 3166-1 alpha-2 country code, if available.
        jurisdiction_of_formation: More specific jurisdiction, if available.
        country_subdivision_code: ISO 3166-2 subdivision code, if available.
        entity_legal_form_name_local_name: Legal form name in its local language.
        language: Language name used for this record.
        language_code: ISO 639-1 language code.
        entity_legal_form_name_transliterated_name: Transliterated legal form name.
        abbreviations_local_language: Abbreviations in the local language.
        abbreviations_transliterated: Transliterated abbreviations.

    Example:
        >>> from legalsuffix import get_suffixes
        >>> records = get_suffixes(country_code="DE", language_code="de")
        >>> records[0].country_code
        'DE'
    """

    elf_code: str
    country_of_formation: str
    country_code: str | None
    jurisdiction_of_formation: str | None
    country_subdivision_code: str | None
    entity_legal_form_name_local_name: str
    language: str
    language_code: str
    entity_legal_form_name_transliterated_name: str
    abbreviations_local_language: list[str]
    abbreviations_transliterated: list[str]


@dataclass(frozen=True)
class LegalSuffixes:
    by_normalized_suffix: dict[str, list[LegalSuffix]]
    records: list[LegalSuffix]

    @property
    def all(self) -> frozenset[str]:
        return frozenset(self.by_normalized_suffix)


@dataclass(frozen=True)
class LegalSuffixMatch:
    """A legal suffix found at the end of a company name.

    Attributes:
        suffix: Matched text as it appears in the input string.
        normalized_suffix: Normalized lookup key for the matched suffix.
        start_pos: Inclusive character offset where the suffix begins.
        end_pos: Exclusive character offset where the suffix ends.
        records: Legal suffix records associated with the normalized key.

    Example:
        >>> from legalsuffix import match_legal_suffix
        >>> match = match_legal_suffix("Acme GmbH", country_code="DE")
        >>> match.suffix
        'GmbH'
        >>> (match.start_pos, match.end_pos)
        (5, 9)
    """

    suffix: str
    normalized_suffix: str
    start_pos: int
    end_pos: int
    records: list[LegalSuffix]


@dataclass(frozen=True)
class ParsedCompanyName:
    """A company name split into its base name and optional legal suffix.

    Attributes:
        name: Company name with the matched trailing suffix removed.
        suffix: Match details, or ``None`` if no suffix was found.

    Example:
        >>> from legalsuffix import parse_company_name
        >>> parsed = parse_company_name("Acme GmbH", country_code="DE")
        >>> (parsed.name, parsed.suffix.suffix)
        ('Acme', 'GmbH')
    """

    name: str
    suffix: LegalSuffixMatch | None
