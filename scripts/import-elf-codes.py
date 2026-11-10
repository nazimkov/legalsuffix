#!/usr/bin/env python3
"""Copy ELF records to package data, omitting administrative columns and reserved codes."""

from __future__ import annotations

import argparse
import csv
import sys
from contextlib import ExitStack
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOVED_COLUMNS = {
    "Date created YYYY-MM-DD (ISO 8601)",
    "ELF Status ACTV/INAC",
    "Modification",
    "Modification date YYYY-MM-DD (ISO 8601)",
    "Reason",
}
EXCLUDED_ELF_CODES = {"8888", "9999"}
ELF_CODE_COLUMN = "ELF Code"
EXTRA_CSV = ROOT / "docs" / "extra-elf-codes.csv"
MERGE_TYPE_COLUMN = "Merge Type"
NEW_RECORD = "NEW"
EXTRA_SUFFIX = "EXTRA_SUFFIX"
MERGE_KEY_COLUMNS = (
    ELF_CODE_COLUMN,
    "Country Code (ISO 3166-1)",
    "Language Code (ISO 639-1)",
)
ABBREVIATION_COLUMNS = (
    "Abbreviations Local language",
    "Abbreviations transliterated",
)


def _merge_abbreviations(existing: str | None, additional: str) -> str:
    """Merge semicolon-separated source values with comma-separated extra variants."""
    variants = [variant.strip() for variant in (existing or "").split(";") if variant.strip()]
    for variant in additional.split(","):
        variant = variant.strip()
        if variant and variant not in variants:
            variants.append(variant)
    return ";".join(variants)


def import_elf_codes(
    csv_path: Path,
    output_path: Path,
    extra_csv_path: Path = EXTRA_CSV,
) -> None:
    """Copy source rows and apply extra suffixes or append new records."""
    with ExitStack() as stack:
        source = stack.enter_context(csv_path.open(encoding="utf-8-sig", newline=""))
        source_reader = csv.DictReader(source)
        if source_reader.fieldnames is None:
            raise ValueError(f"{csv_path}: missing CSV header")

        extra_source = stack.enter_context(extra_csv_path.open(encoding="utf-8-sig", newline=""))
        extra_reader = csv.DictReader(extra_source)
        if extra_reader.fieldnames is None:
            raise ValueError(f"{extra_csv_path}: missing CSV header")

        fieldnames = [name for name in source_reader.fieldnames if name not in REMOVED_COLUMNS]
        missing = (REMOVED_COLUMNS | {ELF_CODE_COLUMN}) - set(source_reader.fieldnames)
        if missing:
            raise ValueError(f"{csv_path}: missing CSV columns: {', '.join(sorted(missing))}")

        required_extra_columns = {
            *MERGE_KEY_COLUMNS,
            MERGE_TYPE_COLUMN,
        }
        extra_missing = required_extra_columns - set(extra_reader.fieldnames)
        extra_abbreviation_columns = tuple(
            column for column in ABBREVIATION_COLUMNS if column in extra_reader.fieldnames
        )
        if extra_missing:
            raise ValueError(f"{extra_csv_path}: missing CSV columns: {', '.join(sorted(extra_missing))}")
        if not extra_abbreviation_columns:
            raise ValueError(f"{extra_csv_path}: missing abbreviation columns")

        source_rows = list(source_reader)
        key_to_rows: dict[tuple[str, ...], list[dict[str, str]]] = {}
        for row in source_rows:
            key = tuple(row[column] for column in MERGE_KEY_COLUMNS)
            key_to_rows.setdefault(key, []).append(row)

        new_rows = []
        for extra_row in extra_reader:
            merge_type = (extra_row.get(MERGE_TYPE_COLUMN) or "").strip().upper()
            if merge_type == NEW_RECORD:
                new_rows.append(extra_row)
            elif merge_type == EXTRA_SUFFIX:
                key = tuple((extra_row.get(column) or "").strip() for column in MERGE_KEY_COLUMNS)
                matching_rows = key_to_rows.get(key)
                if not matching_rows:
                    raise ValueError(f"{extra_csv_path}: no source row matches merge key {key!r}")
                if not any((extra_row.get(column) or "").strip() for column in extra_abbreviation_columns):
                    raise ValueError(f"{extra_csv_path}: {EXTRA_SUFFIX} row must include an abbreviation")
                for row in matching_rows:
                    for column in extra_abbreviation_columns:
                        additional = (extra_row.get(column) or "").strip()
                        if additional:
                            row[column] = _merge_abbreviations(row[column], additional)
            else:
                raise ValueError(f"{extra_csv_path}: unsupported {MERGE_TYPE_COLUMN} {merge_type!r}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                lineterminator="\n",
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(row for row in (*source_rows, *new_rows) if row[ELF_CODE_COLUMN] not in EXCLUDED_ELF_CODES)

    print(f"wrote {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv",
        nargs="?",
        type=Path,
        default=ROOT / "tmp" / "2026-02-19-elf-code-list-v1.6.csv",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=ROOT / "src" / "legalsuffix" / "data" / "suffixes.csv",
    )
    parser.add_argument(
        "--extra",
        type=Path,
        default=EXTRA_CSV,
        help="additional ELF records to append",
    )
    args = parser.parse_args()
    import_elf_codes(args.csv, args.output, args.extra)


if __name__ == "__main__":
    main()
