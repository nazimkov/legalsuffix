from dataclasses import dataclass, field


@dataclass(frozen=True)
class LegalSuffix:
    elf_code: str
    country_of_formation: str
    country_code: str | None
    jurisdiction_of_formation: str
    country_subdivision_code: str
    entity_legal_form_name_local_name: str
    language: str
    language_code: str
    entity_legal_form_name_transliterated_name: str
    abbreviations_local_language: list[str]
    abbreviations_transliterated: list[str]


@dataclass(frozen=True)
class LegalSuffixes:
    all: frozenset[str]
    by_country: dict[str, frozenset[str]]
    rows: list[LegalSuffix] = field(default_factory=list)
