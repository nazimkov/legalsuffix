#!/usr/bin/env python3
"""Copy ELF records to package data, omitting administrative columns and reserved codes."""

from __future__ import annotations

import argparse
import csv
import sys
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


def import_elf_codes(csv_path: Path, output_path: Path) -> None:
    """Copy source rows except reserved codes, omitting administrative columns."""
    with csv_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path}: missing CSV header")

        fieldnames = [name for name in reader.fieldnames if name not in REMOVED_COLUMNS]
        missing = (REMOVED_COLUMNS | {ELF_CODE_COLUMN}) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{csv_path}: missing CSV columns: {', '.join(sorted(missing))}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                lineterminator="\n",
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(row for row in reader if row[ELF_CODE_COLUMN] not in EXCLUDED_ELF_CODES)

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
    args = parser.parse_args()
    import_elf_codes(args.csv, args.output)


if __name__ == "__main__":
    main()
