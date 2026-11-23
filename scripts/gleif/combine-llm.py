#!/usr/bin/env python3
"""Combine extracted batch JSON files into review and final test-case CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

from .models import BatchRecords, ExtractedRecord

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


DEFAULT_INPUT = ROOT / "tmp" / "test-data" / "sampled-test-cases.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "tmp" / "test-data" / "extracted-llm"
DEFAULT_TEST_CASES_ROOT = ROOT / "tests" / "data"
DEFAULT_UNCERTAIN_CASES = ROOT / "tmp" / "test-data" / "uncertain-cases.csv"
CASE_COLUMNS = ["country_code", "language_code", "elf_code", "entity_name", "clean_entity", "suffix", "lei"]
EXTRA_COLUMNS = ["jev_overall_decision", "jev_overall_confidence", "jev_validation"]
MIN_CONFIDENCE = 0.9
TEST_CASE_FILENAME = re.compile(r"(?:suffix|prefix|middle|none)-[A-Z]{2}\.csv\Z")
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


def _read_rows(path: Path, columns: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = set(columns) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing CSV columns: {', '.join(sorted(missing))}")
        return [{column: row.get(column) or "" for column in columns} for row in reader]


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert_by_lei(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    """Append or replace CSV rows by LEI while preserving existing row order."""
    existing = _read_rows(path, columns)
    positions = {row["lei"]: index for index, row in enumerate(existing) if row["lei"]}
    for row in rows:
        lei = row["lei"]
        if lei and lei in positions:
            existing[positions[lei]] = row
        else:
            if lei:
                positions[lei] = len(existing)
            existing.append(row)
    _write_rows(path, columns, existing)


def _persist_cases(
    records: list[ExtractedRecord],
    test_cases_root: Path,
    uncertain_cases_path: Path,
) -> None:
    uncertain_rows: list[dict[str, str]] = []
    accepted_by_lei: dict[str, tuple[Path, dict[str, str]]] = {}
    processed_leis: set[str] = set()

    for record in records:
        processed_leis.add(record.lei)
        confidence = record.jev_overall_confidence
        decision = (record.jev_overall_decision or "").strip().casefold()
        is_uncertain = decision == "incorrect" or (
            decision == "correct" and (confidence is None or confidence < MIN_CONFIDENCE)
        )
        if decision not in {"correct", "incorrect"}:
            raise ValueError(f"Record {record.lei} has unsupported Jev decision: {decision!r}")

        case = {
            "country_code": record.country_code,
            "language_code": record.language_code,
            "elf_code": record.elf_code,
            "entity_name": record.entity_name,
            "clean_entity": record.clean_entity,
            "suffix": record.suffix or "",
            "lei": record.lei,
        }
        if is_uncertain:
            uncertain_rows.append(
                {
                    **case,
                    "jev_overall_decision": decision,
                    "jev_overall_confidence": _csv_value(confidence),
                    "jev_validation": _csv_value(record.jev_validation.model_dump()),
                }
            )
            continue

        place = record.jev_validation.overall_verdict.place.value
        country_code = record.country_code.upper()
        filename = f"{place}-{country_code}.csv"
        if not TEST_CASE_FILENAME.fullmatch(filename):
            raise ValueError(f"Record {record.lei} has invalid test-case category: {filename!r}")
        accepted_by_lei[record.lei] = (test_cases_root / filename, case)

    # A LEI can occur more than once when the source has multiple legal-name
    # aliases. Keep one row per LEI and treat any uncertain alias as uncertain.
    uncertain_by_lei = {row["lei"]: row for row in uncertain_rows}
    uncertain_rows = list(uncertain_by_lei.values())
    uncertain_leis = set(uncertain_by_lei)
    accepted_by_path: dict[Path, list[dict[str, str]]] = {}
    for lei, (path, case) in accepted_by_lei.items():
        if lei not in uncertain_leis:
            accepted_by_path.setdefault(path, []).append(case)

    if uncertain_rows:
        _upsert_by_lei(uncertain_cases_path, [*CASE_COLUMNS, *EXTRA_COLUMNS], uncertain_rows)
    if uncertain_cases_path.exists():
        retained_uncertain = [
            row
            for row in _read_rows(uncertain_cases_path, [*CASE_COLUMNS, *EXTRA_COLUMNS])
            if row["lei"] not in processed_leis or row["lei"] in uncertain_leis
        ]
        _write_rows(uncertain_cases_path, [*CASE_COLUMNS, *EXTRA_COLUMNS], retained_uncertain)

    # LEIs may be reclassified to a different category or country, so remove
    # replacements from every existing generated file before writing them.
    generated_files = {path for path in test_cases_root.glob("*.csv") if TEST_CASE_FILENAME.fullmatch(path.name)}
    for path in generated_files | set(accepted_by_path):
        retained = [row for row in _read_rows(path, CASE_COLUMNS) if row["lei"] not in processed_leis]
        retained.extend(accepted_by_path.get(path, []))
        if retained or path in accepted_by_path:
            _write_rows(path, CASE_COLUMNS, retained)


def combine(
    sampled_path: Path,
    run_dir: Path,
    *,
    test_cases_root: Path = DEFAULT_TEST_CASES_ROOT,
    uncertain_cases_path: Path = DEFAULT_UNCERTAIN_CASES,
) -> tuple[Path, Path]:
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

    _persist_cases(records, test_cases_root, uncertain_cases_path)

    return extracted_path, final_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", type=Path, help="Timestamped extraction directory (defaults to newest)")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Sampled input CSV")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--test-cases-root", type=Path, default=DEFAULT_TEST_CASES_ROOT)
    parser.add_argument("--uncertain-cases", type=Path, default=DEFAULT_UNCERTAIN_CASES)
    args = parser.parse_args()
    run_dir = args.run_dir or _latest_run(args.output_root)
    extracted_path, final_path = combine(
        args.input,
        run_dir,
        test_cases_root=args.test_cases_root,
        uncertain_cases_path=args.uncertain_cases,
    )
    print(f"wrote {extracted_path}")
    print(f"wrote {final_path}")


if __name__ == "__main__":
    main()
