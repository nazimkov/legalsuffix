"""Helpers for loading company-name test cases from CSV."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompanyNameTestCase:
    country_code: str
    elf_code: str
    entity_name: str
    clean_entity: str
    suffix: str | None
    lei: str


TEST_CASES_PATH = Path(__file__).parent / "data" / "test-cases.csv"


def load_test_cases[TestCaseT](model: type[TestCaseT], path: Path = TEST_CASES_PATH) -> list[TestCaseT]:
    """Load CSV test-case rows and instantiate ``model`` for each row."""
    with path.open(encoding="utf-8-sig", newline="") as cases_file:
        cases = list(csv.DictReader(cases_file))
    for case in cases:
        case["suffix"] = case["suffix"] or None
    return [model(**case) for case in cases]
