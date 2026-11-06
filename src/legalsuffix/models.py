from dataclasses import dataclass


@dataclass(frozen=True)
class LegalSuffixes:
    all: frozenset[str]
    by_country: dict[str, frozenset[str]]
