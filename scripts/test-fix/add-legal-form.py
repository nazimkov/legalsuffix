"""Add a missing legal-form record to docs/extra-elf-codes.csv."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT = PROJECT_ROOT / "docs" / "extra-elf-codes.csv"
ELF_LIST = PROJECT_ROOT / "tmp" / "2026-02-19-elf-code-list-v1.6.csv"
FIELDS = (
    "ELF Code",
    "Country of formation",
    "Country Code (ISO 3166-1)",
    "Jurisdiction of formation",
    "Country sub-division code (ISO 3166-2)",
    "Entity Legal Form name Local name",
    "Language",
    "Language Code (ISO 639-1)",
    "Entity Legal Form name Transliterated name (per ISO 01-140-10)",
    "Abbreviations Local language",
    "Abbreviations transliterated",
    "Merge Type",
)
TEXT_FIELDS = (
    "Jurisdiction of formation",
    "Country sub-division code (ISO 3166-2)",
    "Entity Legal Form name Local name",
    "Language",
    "Language Code (ISO 639-1)",
    "Entity Legal Form name Transliterated name (per ISO 01-140-10)",
    "Abbreviations Local language",
    "Abbreviations transliterated",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Idempotently add or update one legal-form record in docs/extra-elf-codes.csv."
    )
    parser.add_argument("--elf-code", required=True, help="ELF code from the failing test case")
    parser.add_argument("--country", required=True, help="Country of formation")
    parser.add_argument("--country-code", required=True, help="ISO 3166-1 alpha-2 country code")
    parser.add_argument("--language", default="", help="Language name")
    parser.add_argument("--language-code", default="", help="ISO 639-1 language code")
    parser.add_argument("--local-name", default="", help="Entity legal form name in the local language")
    parser.add_argument("--transliterated-name", default="", help="Transliterated entity legal form name")
    parser.add_argument("--abbreviations-local", default="", help="Semicolon-separated local abbreviations")
    parser.add_argument(
        "--abbreviations-transliterated", default="", help="Semicolon-separated transliterated abbreviations"
    )
    parser.add_argument("--jurisdiction", default="", help="Jurisdiction of formation, if applicable")
    parser.add_argument("--subdivision-code", default="", help="ISO 3166-2 country subdivision code, if applicable")
    parser.add_argument(
        "--merge-type",
        choices=("NEW", "EXTRA_SUFFIX"),
        help="Override automatic type: existing ordinary ELF code uses EXTRA_SUFFIX; absent/8888/9999 uses NEW",
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT, help="Output CSV path (defaults to docs/extra-elf-codes.csv)"
    )
    args = parser.parse_args()
    if not any(
        (args.local_name, args.transliterated_name, args.abbreviations_local, args.abbreviations_transliterated)
    ):
        parser.error("provide at least one name or abbreviation")
    return args


def known_elf_code(code: str) -> bool:
    with ELF_LIST.open(encoding="utf-8-sig", newline="") as source:
        return any(row.get("ELF Code", "").casefold() == code.casefold() for row in csv.DictReader(source))


def merge_values(existing: str, incoming: str) -> str:
    values = [part.strip() for part in existing.split(";") if part.strip()]
    for part in incoming.split(";"):
        value = part.strip()
        if value and value.casefold() not in {item.casefold() for item in values}:
            values.append(value)
    return ";".join(values)


def main() -> int:
    args = parse_args()
    code_exists = known_elf_code(args.elf_code)
    merge_type = args.merge_type or ("EXTRA_SUFFIX" if code_exists and args.elf_code not in {"8888", "9999"} else "NEW")
    incoming = {
        "ELF Code": args.elf_code,
        "Country of formation": args.country,
        "Country Code (ISO 3166-1)": args.country_code.upper(),
        "Jurisdiction of formation": args.jurisdiction,
        "Country sub-division code (ISO 3166-2)": args.subdivision_code,
        "Entity Legal Form name Local name": args.local_name,
        "Language": args.language,
        "Language Code (ISO 639-1)": args.language_code,
        "Entity Legal Form name Transliterated name (per ISO 01-140-10)": args.transliterated_name,
        "Abbreviations Local language": args.abbreviations_local,
        "Abbreviations transliterated": args.abbreviations_transliterated,
        "Merge Type": merge_type,
    }
    if args.output.exists():
        with args.output.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            rows = list(reader)
            fieldnames = reader.fieldnames or list(FIELDS)
    else:
        rows = []
        fieldnames = list(FIELDS)

    key_fields = (
        "ELF Code",
        "Country Code (ISO 3166-1)",
        "Language Code (ISO 639-1)",
        "Entity Legal Form name Local name",
    )
    target = next(
        (row for row in rows if all(row.get(key, "").casefold() == incoming[key].casefold() for key in key_fields)),
        None,
    )
    action = "Added"
    if target is None:
        rows.append(incoming)
    else:
        action = "Updated"
        for field in TEXT_FIELDS:
            if incoming[field]:
                target[field] = merge_values(target.get(field, ""), incoming[field])
        target["Country of formation"] = incoming["Country of formation"] or target.get("Country of formation", "")
        target["Merge Type"] = merge_type

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{action} {args.elf_code} ({args.country_code.upper()}, {merge_type}) in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
