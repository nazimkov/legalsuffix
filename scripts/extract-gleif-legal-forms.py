#!/usr/bin/env python3
"""Extract LEIs, entity names, legal form codes, and countries from a GLEIF CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "tmp" / "20261109-0800-gleif-goldencopy-lei2-golden-copy.csv"
DEFAULT_OUTPUT = ROOT / "tmp" / "20261109-0800-gleif-legal-forms.csv"
LEI_COLUMN = "LEI"
NAME_COLUMN = "Entity.LegalName"
CODE_COLUMN = "Entity.LegalForm.EntityLegalFormCode"
COUNTRY_COLUMN = "Entity.LegalAddress.Country"
OUTPUT_COLUMNS = [LEI_COLUMN, NAME_COLUMN, CODE_COLUMN, COUNTRY_COLUMN]
BUFFER_SIZE = 1024 * 1024


def extract_legal_forms(input_path: Path, output_path: Path) -> int:
    """Write LEI/name/code/country rows with a legal form code; return row count."""
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output paths must be different")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0

    with input_path.open("r", encoding="utf-8-sig", newline="", buffering=BUFFER_SIZE) as source:
        reader = csv.reader(source)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"{input_path}: missing CSV header") from None

        missing = [column for column in OUTPUT_COLUMNS if column not in header]
        if missing:
            raise ValueError(f"{input_path}: missing CSV columns: {', '.join(missing)}")

        lei_index = header.index(LEI_COLUMN)
        name_index = header.index(NAME_COLUMN)
        code_index = header.index(CODE_COLUMN)
        country_index = header.index(COUNTRY_COLUMN)
        last_required_index = max(lei_index, name_index, code_index, country_index)

        with output_path.open("w", encoding="utf-8", newline="", buffering=BUFFER_SIZE) as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(OUTPUT_COLUMNS)

            for row in reader:
                if len(row) <= last_required_index:
                    raise ValueError(
                        f"{input_path}: CSV row ending at line {reader.line_num} has fewer "
                        f"than {last_required_index + 1} columns"
                    )

                legal_form_code = row[code_index]
                if legal_form_code.strip():
                    writer.writerow((row[lei_index], row[name_index], legal_form_code, row[country_index]))
                    rows_written += 1

    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows_written = extract_legal_forms(args.input, args.output)
    print(f"wrote {rows_written:,} rows to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
