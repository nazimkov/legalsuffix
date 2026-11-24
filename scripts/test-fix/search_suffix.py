"""Search the ELF code list and project additions for an ELF code or suffix."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = (
    PROJECT_ROOT / "docs" / "extra-elf-codes.csv",
    PROJECT_ROOT / "tmp" / "2026-02-19-elf-code-list-v1.6.csv",
)
NAME_COLUMNS = (
    "Entity Legal Form name Local name",
    "Entity Legal Form name Transliterated name (per ISO 01-140-10)",
    "Abbreviations Local language",
    "Abbreviations transliterated",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find records by partial ELF code and/or legal-form suffix (case-insensitive)."
    )
    parser.add_argument("--elf-code", help="ELF code or part of an ELF code to search for")
    parser.add_argument("--suffix", help="Suffix or legal-form text to search for")
    parser.add_argument(
        "--source",
        action="append",
        type=Path,
        dest="sources",
        help="CSV file to search; may be repeated (defaults to extra-elf-codes.csv and the v1.6 ELF list)",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum records to print (default: 100; 0 means all)")
    args = parser.parse_args()
    if not args.elf_code and not args.suffix:
        parser.error("provide --elf-code, --suffix, or both")
    if args.limit < 0:
        parser.error("--limit must be zero or greater")
    return args


def search_file(path: Path, elf_code: str | None, suffix: str | None):
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            code = row.get("ELF Code", "")
            code_match = bool(elf_code and elf_code.casefold() in code.casefold())
            suffix_matches = [
                (column, row.get(column, ""))
                for column in NAME_COLUMNS
                if suffix and suffix.casefold() in row.get(column, "").casefold()
            ]
            if code_match or suffix_matches:
                yield reader.line_num, row, code_match, suffix_matches


def main() -> int:
    args = parse_args()
    sources = args.sources or list(DEFAULT_SOURCES)
    result_count = 0
    for path in sources:
        if not path.is_file():
            print(f"Missing source: {path}")
            continue
        for line_number, row, code_match, suffix_matches in search_file(path, args.elf_code, args.suffix):
            if args.limit and result_count >= args.limit:
                print(f"Stopped after {args.limit} records; use --limit 0 to show all.")
                return 0
            matched = []
            if code_match:
                matched.append("ELF Code")
            matched.extend(column for column, _ in suffix_matches)
            print(f"{path}:{line_number}  [{', '.join(matched)}]")
            for field in ("ELF Code", "Country of formation", "Country Code (ISO 3166-1)", *NAME_COLUMNS):
                value = row.get(field, "")
                if value:
                    print(f"  {field}: {value}")
            result_count += 1
    if not result_count:
        print("No matching records found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
