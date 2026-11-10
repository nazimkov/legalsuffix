"""Helpers for loading company-name test cases from JSON."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompanyNameTestCase:
    country_code: str
    elf_code: str
    entity_name: str
    clean_entity: str
    suffix: str | None


TEST_CASES_PATH = Path(__file__).parent / "data" / "test-cases.json"


def load_test_cases[TestCaseT](model: type[TestCaseT], path: Path = TEST_CASES_PATH) -> list[TestCaseT]:
    """Load JSON test-case objects and instantiate ``model`` for each row."""
    with path.open(encoding="utf-8") as cases_file:
        cases = json.load(cases_file)
    return [model(**case) for case in cases]
