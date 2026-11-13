#!/usr/bin/env python3
"""Sample GLEIF entity names for common country and ELF code combinations."""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "tmp" / "20261109-0800-gleif-legal-forms.csv"
DEFAULT_OUTPUT = ROOT / "tests" / "data" / "test-cases-sample.csv"
LEI_COLUMN = "LEI"
NAME_COLUMN = "Entity.LegalName"
CODE_COLUMN = "Entity.LegalForm.EntityLegalFormCode"
COUNTRY_COLUMN = "Entity.LegalAddress.Country"
ADDRESS_COUNTRY_CODES = {"8888", "9999"}
OUTPUT_COLUMNS = [
    "country_code",
    "language_code",
    "elf_code",
    "entity_name",
    "clean_entity",
    "suffix",
    "lei",
]
DEFAULT_COUNTRY_COUNT = 20
DEFAULT_CODES_PER_COUNTRY = 3
DEFAULT_SEED = 20261109

# Allow running the script directly from the repository without installing the package.
sys.path.insert(0, str(ROOT / "src"))

from legalsuffix import list_legal_suffixes, match_legal_suffix  # noqa: E402


def _read_counts(input_path: Path) -> Counter[str]:
    """Count entity rows per ELF code in the GLEIF extract."""
    counts: Counter[str] = Counter()
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"{input_path}: missing CSV header")
        missing = {LEI_COLUMN, NAME_COLUMN, CODE_COLUMN} - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{input_path}: missing CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            code = (row[CODE_COLUMN] or "").strip()
            if code and (row[NAME_COLUMN] or "").strip():
                counts[code] += 1
    return counts


def _read_address_country_counts(input_path: Path) -> Counter[tuple[str, str]]:
    """Count special ELF codes by their GLEIF legal address country."""
    counts: Counter[tuple[str, str]] = Counter()
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"{input_path}: missing CSV header")
        missing = {NAME_COLUMN, CODE_COLUMN, COUNTRY_COLUMN} - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{input_path}: missing CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            code = (row[CODE_COLUMN] or "").strip()
            country = (row[COUNTRY_COLUMN] or "").strip().upper()
            if code in ADDRESS_COUNTRY_CODES and country and (row[NAME_COLUMN] or "").strip():
                counts[(country, code)] += 1
    return counts


def _country_codes_and_elf_codes(
    address_country_counts: Counter[tuple[str, str]],
) -> dict[str, set[str]]:
    """Get country-to-ELF-code mappings through the package's public API."""
    countries = {record.country_code for record in list_legal_suffixes() if record.country_code}
    country_codes = {
        country_code: {record.elf_code for record in list_legal_suffixes(country_code=country_code)}
        for country_code in sorted(countries)
    }
    for country_code, elf_code in address_country_counts:
        country_codes.setdefault(country_code, set()).add(elf_code)
    return country_codes


def _select_codes(
    code_counts: Counter[str],
    address_country_counts: Counter[tuple[str, str]],
    country_codes: dict[str, set[str]],
    country_count: int,
    codes_per_country: int,
) -> list[tuple[str, str]]:
    """Choose the most common countries, then their most common distinct codes."""
    country_counts = {
        country_code: sum(
            address_country_counts[(country_code, elf_code)]
            if elf_code in ADDRESS_COUNTRY_CODES
            else code_counts[elf_code]
            for elf_code in elf_codes
        )
        for country_code, elf_codes in country_codes.items()
    }
    popular_countries = sorted(
        (country_code for country_code, count in country_counts.items() if count),
        key=lambda country_code: (-country_counts[country_code], country_code),
    )[:country_count]

    selected: list[tuple[str, str]] = []
    for country_code in popular_countries:
        matching_codes = sorted(
            (
                code
                for code in country_codes[country_code]
                if (
                    address_country_counts[(country_code, code)] if code in ADDRESS_COUNTRY_CODES else code_counts[code]
                )
            ),
            key=lambda code: (
                -(address_country_counts[(country_code, code)] if code in ADDRESS_COUNTRY_CODES else code_counts[code]),
                code,
            ),
        )
        selected.extend((country_code, code) for code in matching_codes[:codes_per_country])
    return selected


def _sample_entity_names(
    input_path: Path,
    selected_pairs: list[tuple[str, str]],
    seed: int,
) -> dict[tuple[str, str], tuple[str, str, str]]:
    """Reservoir-sample an entity name and address country for each selected pair."""
    rng = random.Random(seed)
    samples: dict[tuple[str, str], tuple[str, str, str]] = {}
    seen: Counter[tuple[str, str]] = Counter()
    selected_by_code: dict[str, list[tuple[str, str]]] = {}
    for pair in selected_pairs:
        selected_by_code.setdefault(pair[1], []).append(pair)

    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            code = (row[CODE_COLUMN] or "").strip()
            entity_name = (row[NAME_COLUMN] or "").strip()
            lei = (row[LEI_COLUMN] or "").strip()
            address_country = (row[COUNTRY_COLUMN] or "").strip().upper()
            if not entity_name or code not in selected_by_code:
                continue

            for country_code, _ in selected_by_code[code]:
                if code in ADDRESS_COUNTRY_CODES and address_country != country_code:
                    continue

                pair = (country_code, code)
                seen[pair] += 1
                if rng.randrange(seen[pair]) == 0:
                    samples[pair] = (entity_name, address_country, lei)
    return samples


def _language_code(country_code: str, elf_code: str, entity_name: str) -> str | None:
    """Return a deterministic language code for a country and ELF code, if available."""
    language_codes = sorted(
        {
            record.language_code
            for record in list_legal_suffixes(country_code=country_code)
            if record.elf_code == elf_code and record.language_code
        }
    )
    match = match_legal_suffix(entity_name, country_code=country_code)
    matched_languages = []
    if match is not None:
        matched_languages = sorted({record.language_code for record in match.records if record.language_code})

    if elf_code in ADDRESS_COUNTRY_CODES:
        return matched_languages[0] if matched_languages else None
    if matched_languages:
        matching_code_languages = sorted(set(language_codes) & set(matched_languages))
        if matching_code_languages:
            return matching_code_languages[0]
    return language_codes[0] if language_codes else None


def sample_test_cases(
    input_path: Path,
    output_path: Path,
    country_count: int = DEFAULT_COUNTRY_COUNT,
    codes_per_country: int = DEFAULT_CODES_PER_COUNTRY,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, str | None]]:
    """Write reproducible CSV test cases and return the generated records."""
    if country_count < 1:
        raise ValueError("country_count must be at least 1")
    if codes_per_country < 1:
        raise ValueError("codes_per_country must be at least 1")

    code_counts = _read_counts(input_path)
    address_country_counts = _read_address_country_counts(input_path)
    selected_pairs = _select_codes(
        code_counts,
        address_country_counts,
        _country_codes_and_elf_codes(address_country_counts),
        country_count,
        codes_per_country,
    )
    entity_samples = _sample_entity_names(input_path, selected_pairs, seed)

    cases: list[dict[str, str | None]] = []
    for country_code, elf_code in selected_pairs:
        sample = entity_samples.get((country_code, elf_code))
        if sample is None:
            continue
        entity_name, address_country, lei = sample
        if elf_code in ADDRESS_COUNTRY_CODES:
            country_code = address_country
        cases.append(
            {
                "country_code": country_code,
                "language_code": _language_code(country_code, elf_code, entity_name),
                "elf_code": elf_code,
                "entity_name": entity_name,
                "clean_entity": None,
                "suffix": None,
                "lei": lei,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=OUTPUT_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(cases)
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
