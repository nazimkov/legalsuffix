#!/usr/bin/env python3
"""Sample GLEIF entity names for common country and ELF code combinations."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "tmp" / "20261109-0800-gleif-legal-forms.csv"
DEFAULT_OUTPUT = ROOT / "tests" / "data" / "test-cases.json"
NAME_COLUMN = "Entity.LegalName"
CODE_COLUMN = "Entity.LegalForm.EntityLegalFormCode"
DEFAULT_COUNTRY_COUNT = 20
DEFAULT_CODES_PER_COUNTRY = 3
DEFAULT_SEED = 20261109

# Allow running the script directly from the repository without installing the package.
sys.path.insert(0, str(ROOT / "src"))

from legalsuffix import get_suffixes  # noqa: E402


def _read_counts(input_path: Path) -> Counter[str]:
    """Count entity rows per ELF code in the GLEIF extract."""
    counts: Counter[str] = Counter()
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"{input_path}: missing CSV header")
        missing = {NAME_COLUMN, CODE_COLUMN} - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{input_path}: missing CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            code = (row[CODE_COLUMN] or "").strip()
            if code and (row[NAME_COLUMN] or "").strip():
                counts[code] += 1
    return counts


def _country_codes_and_elf_codes() -> dict[str, set[str]]:
    """Get country-to-ELF-code mappings through the package's public API."""
    countries = {record.country_code for record in get_suffixes() if record.country_code}
    return {
        country_code: {record.elf_code for record in get_suffixes(country_code=country_code)}
        for country_code in sorted(countries)
    }


def _select_codes(
    code_counts: Counter[str],
    country_codes: dict[str, set[str]],
    country_count: int,
    codes_per_country: int,
) -> list[tuple[str, str]]:
    """Choose the most common countries, then their most common distinct codes."""
    country_counts = {
        country_code: sum(code_counts[elf_code] for elf_code in elf_codes)
        for country_code, elf_codes in country_codes.items()
    }
    popular_countries = sorted(
        (country_code for country_code, count in country_counts.items() if count),
        key=lambda country_code: (-country_counts[country_code], country_code),
    )[:country_count]

    selected: list[tuple[str, str]] = []
    for country_code in popular_countries:
        matching_codes = sorted(
            (code for code in country_codes[country_code] if code_counts[code]),
            key=lambda code: (-code_counts[code], code),
        )
        selected.extend((country_code, code) for code in matching_codes[:codes_per_country])
    return selected


def _sample_entity_names(
    input_path: Path,
    selected_codes: set[str],
    seed: int,
) -> dict[str, str]:
    """Reservoir-sample one non-empty entity name for each selected ELF code."""
    rng = random.Random(seed)
    samples: dict[str, str] = {}
    seen: Counter[str] = Counter()
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            code = (row[CODE_COLUMN] or "").strip()
            entity_name = (row[NAME_COLUMN] or "").strip()
            if code not in selected_codes or not entity_name:
                continue

            seen[code] += 1
            if rng.randrange(seen[code]) == 0:
                samples[code] = entity_name
    return samples


def sample_test_cases(
    input_path: Path,
    output_path: Path,
    country_count: int = DEFAULT_COUNTRY_COUNT,
    codes_per_country: int = DEFAULT_CODES_PER_COUNTRY,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, str | None]]:
    """Write reproducible test cases and return the generated records."""
    if country_count < 1:
        raise ValueError("country_count must be at least 1")
    if codes_per_country < 1:
        raise ValueError("codes_per_country must be at least 1")

    code_counts = _read_counts(input_path)
    selected_pairs = _select_codes(
        code_counts,
        _country_codes_and_elf_codes(),
        country_count,
        codes_per_country,
    )
    entity_names = _sample_entity_names(input_path, {code for _, code in selected_pairs}, seed)

    cases: list[dict[str, str | None]] = []
    for country_code, elf_code in selected_pairs:
        entity_name = entity_names.get(elf_code)
        if entity_name is None:
            continue
        cases.append(
            {
                "country_code": country_code,
                "elf_code": elf_code,
                "entity_name": entity_name,
                "clean_entity": None,
                "suffix": None,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as output:
        json.dump(cases, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--countries", type=int, default=DEFAULT_COUNTRY_COUNT)
    parser.add_argument("--codes-per-country", type=int, default=DEFAULT_CODES_PER_COUNTRY)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    cases = sample_test_cases(args.input, args.output, args.countries, args.codes_per_country, args.seed)
    print(f"wrote {len(cases)} test cases to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
