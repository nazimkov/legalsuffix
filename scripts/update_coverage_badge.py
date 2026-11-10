"""Run the unit tests with coverage and refresh the README coverage badge."""

from __future__ import annotations

import re
import sys
import unittest
from io import StringIO
from pathlib import Path

from coverage import Coverage

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "src"
PACKAGE_DIR = SOURCE_DIR / "legalsuffix"
TESTS_DIR = ROOT / "tests"
README_PATH = ROOT / "README.md"
BADGE_PATTERN = re.compile(r"!\[Coverage\]\(https://img\.shields\.io/badge/coverage-\d+%25-[a-z]+\)")
BADGE_TEMPLATE = "![Coverage](https://img.shields.io/badge/coverage-{percentage}%25-{color})"


def coverage_color(percentage: int) -> str:
    if percentage >= 80:
        return "brightgreen"
    if percentage >= 60:
        return "yellow"
    return "red"


def run_tests_with_coverage() -> int | None:
    coverage = Coverage(source=[str(PACKAGE_DIR)], data_file=str(ROOT / ".coverage"))
    coverage.erase()
    sys.path.insert(0, str(SOURCE_DIR))

    coverage.start()
    try:
        suite = unittest.defaultTestLoader.discover(
            start_dir=str(TESTS_DIR),
            top_level_dir=str(ROOT),
        )
        result = unittest.TextTestRunner(verbosity=1).run(suite)
    finally:
        coverage.stop()
        coverage.save()

    if not result.wasSuccessful():
        return None

    return round(coverage.report(file=StringIO()))


def update_badge(percentage: int) -> bool:
    readme = README_PATH.read_text(encoding="utf-8")
    badge = BADGE_TEMPLATE.format(
        percentage=percentage,
        color=coverage_color(percentage),
    )
    updated_readme, replacements = BADGE_PATTERN.subn(badge, readme, count=1)
    if replacements != 1:
        raise RuntimeError("Expected exactly one coverage badge in README.md")
    if updated_readme == readme:
        return False

    README_PATH.write_text(updated_readme, encoding="utf-8", newline="")
    return True


def main() -> int:
    percentage = run_tests_with_coverage()
    if percentage is None:
        print("Coverage badge was not updated because the unit tests failed.", file=sys.stderr)
        return 1

    changed = update_badge(percentage)
    status = "Updated" if changed else "Already current"
    print(f"{status} README coverage badge: {percentage}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
