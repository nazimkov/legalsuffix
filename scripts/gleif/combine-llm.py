#!/usr/bin/env python3
"""Combine extracted batch JSON files into review and final test-case CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from .models import BatchRecords, ExtractedRecord

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


DEFAULT_INPUT = ROOT / "tmp" / "test-data" / "sampled-test-cases.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "tmp" / "test-data" / "extracted-llm"
CASE_COLUMNS = ["country_code", "language_code", "elf_code", "entity_name", "clean_entity", "suffix", "lei"]
EXTRA_COLUMNS = ["jev_overall_decision", "jev_overall_confidence", "jev_validation"]
EXTRACTED_COLUMNS = [
    "id",
    "lei",
    "country_code",
    "language_code",
    "elf_code",
    "entity_name",
    "clean_entity",
    "suffix",
    *EXTRA_COLUMNS,
]


def _latest_run(output_root: Path) -> Path:
    runs = [path for path in output_root.iterdir() if path.is_dir()]
    if not runs:
        raise FileNotFoundError(f"No extraction run directories found in {output_root}")
    return max(runs, key=lambda path: path.name)


def _read_sampled(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = set(CASE_COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing CSV columns: {', '.join(sorted(missing))}")
        return [{column: row.get(column) or "" for column in CASE_COLUMNS} for row in reader]


def _read_batches(run_dir: Path, cases: list[dict[str, str]]) -> list[ExtractedRecord]:
    batch_files = sorted(
        run_dir.glob("extracted-llm-batch-*.json"),
        key=lambda path: int(path.stem.rsplit("-", 1)[1]),
    )
    if len(batch_files) != (len(cases) + 9) // 10:
        expected_batches = (len(cases) + 9) // 10
        raise ValueError(
            f"Expected {expected_batches} batch files for {len(cases)} sampled cases; found {len(batch_files)}"
        )

    records: list[ExtractedRecord] = []
    for expected_batch, path in enumerate(batch_files, start=1):
        if path.stem != f"extracted-llm-batch-{expected_batch}":
            raise ValueError(f"Missing extraction batch {expected_batch} before {path.name}")
        batch_records = BatchRecords.model_validate_json(path.read_text(encoding="utf-8"))
        start = (expected_batch - 1) * 10

        for record in batch_records.records:
            case = cases[start + record.id - 1]
            record_identity = (
                record.lei,
                record.country_code,
                record.language_code,
                record.elf_code,
                record.entity_name,
            )
            case_identity = tuple(
                case[column] for column in ("lei", "country_code", "language_code", "elf_code", "entity_name")
            )
            if record_identity != case_identity:
                raise ValueError(f"{path}: record {record.id} does not match its sampled case")
            records.append(record)
    return records


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def combine(sampled_path: Path, run_dir: Path) -> tuple[Path, Path]:
    cases = _read_sampled(sampled_path)
    records = _read_batches(run_dir, cases)
    extracted_path = run_dir / "extracted-llm.csv"
    final_path = run_dir / "extracted-llm-final.csv"

    with extracted_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=EXTRACTED_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for record in records:
            values = record.model_dump()
            writer.writerow({column: _csv_value(values.get(column)) for column in EXTRACTED_COLUMNS})

    with final_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=[*CASE_COLUMNS, *EXTRA_COLUMNS], lineterminator="\n")
        writer.writeheader()
        for case, record in zip(cases, records, strict=True):
            merged: dict[str, Any] = {
                **case,
                "clean_entity": record.clean_entity,
                "suffix": record.suffix,
                "jev_overall_decision": record.jev_overall_decision,
                "jev_overall_confidence": record.jev_overall_confidence,
                "jev_validation": record.jev_validation,
            }
            writer.writerow({column: _csv_value(merged.get(column)) for column in [*CASE_COLUMNS, *EXTRA_COLUMNS]})

    return extracted_path, final_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", type=Path, help="Timestamped extraction directory (defaults to newest)")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Sampled input CSV")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    run_dir = args.run_dir or _latest_run(args.output_root)
    extracted_path, final_path = combine(args.input, run_dir)
    print(f"wrote {extracted_path}")
    print(f"wrote {final_path}")


if __name__ == "__main__":
    main()
