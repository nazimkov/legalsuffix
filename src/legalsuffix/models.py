from dataclasses import dataclass


@dataclass(frozen=True)
class LegalSuffix:
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

    @property
    def all(self) -> frozenset[str]:
        return frozenset(self.by_normalized_suffix)
