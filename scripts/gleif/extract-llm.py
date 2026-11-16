#!/usr/bin/env python3
"""Extract legal suffixes with Azure OpenAI and validate them with Jev."""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from .jev import (
    CompanyState,
    JevClient,
    JevValidation,
    JevVerifier,
)
from .llm import AzureOpenAIExtractor, CompanyExtraction, ExtractionResult
from .models import BatchRecords, ExtractedRecord

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DEFAULT_INPUT = ROOT / "tmp" / "test-data" / "sampled-test-cases.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "tmp" / "test-data" / "extracted-llm"
ENV_FILE = Path(__file__).resolve().parent / ".env"
BATCH_SIZE = 10
TEST_RUN_LIMIT = 20

INPUT_COLUMNS = ["country_code", "language_code", "elf_code", "entity_name", "clean_entity", "suffix", "lei"]


def _read_cases(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = set(INPUT_COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing CSV columns: {', '.join(sorted(missing))}")
        return [{column: (row.get(column) or "") for column in INPUT_COLUMNS} for row in reader]


def _validate_batch(
    verifier: JevVerifier,
    cases: list[dict[str, str]],
    extractions: list[CompanyExtraction],
) -> dict[int, JevValidation]:
    states: list[CompanyState] = []
    for case, extraction in zip(cases, extractions, strict=True):
        states.append(
            CompanyState(
                id=extraction.id,
                original_company_name=case["entity_name"],
                extracted_company_name=extraction.company_name,
                extracted_suffix=extraction.suffix,
            )
        )
    return dict(verifier.validate(states))


def _validation_json(validation: JevValidation) -> dict:
    verdict = validation.overall_verdict
    decisions: dict[str, dict] = {}
    for question, answer in validation.decisions.items():
        choice = answer.choice
        decisions[question] = {
            "choice": choice,
            "confidence": answer.confidence,
            "probabilities": answer.probabilities,
            "type": answer.answer_type,
            "value": answer.value,
        }
    return {
        "decisions": decisions,
        "overall_verdict": {
            "legal_form_present": verdict.legal_form_present,
            "place": verdict.place.value,
            "correct": verdict.correct,
            "confidence": verdict.confidence,
        },
    }


def _save_batch(
    output_path: Path,
    batch_number: int,
    cases: list[dict[str, str]],
    extraction: ExtractionResult,
    decisions: dict[int, JevValidation],
) -> None:
    records = []
    for case, ext in zip(cases, extraction.companies, strict=True):
        validation = decisions[ext.id]
        verdict = validation.overall_verdict
        record = ExtractedRecord(
            id=ext.id,
            lei=case["lei"],
            country_code=case["country_code"],
            language_code=case["language_code"],
            elf_code=case["elf_code"],
            entity_name=case["entity_name"],
            clean_entity=ext.company_name,
            suffix=ext.suffix,
            jev_overall_decision="correct" if verdict.correct else "incorrect",
            jev_overall_confidence=verdict.confidence,
            jev_validation=validation,
        )
        records.append(record.model_dump())
    batch = BatchRecords(batch_number=batch_number, records=records, llm_usage=extraction.usage)
    batch_json = batch.model_dump_json(indent=2)
    output_path.write_text(batch_json, encoding="utf-8")
    logger.info("Wrote batch %d (%d companies): %s", batch_number, len(records), output_path)


def extract(input_path: Path, output_root: Path, *, test_run: bool = False) -> Path:
    load_dotenv(ENV_FILE)
    required = ["OPENROUTER_API_KEY", "JEV_MODEL"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing required settings in {ENV_FILE}: {', '.join(missing)}")

    cases = _read_cases(input_path)
    logger.info("Read %d cases from %s", len(cases), input_path)
    if test_run:
        total_cases = len(cases)
        cases = cases[:TEST_RUN_LIMIT]
        logger.info("Test run: evaluating %d of %d cases", len(cases), total_cases)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    output_dir = output_root / timestamp
    total_batches = (len(cases) + BATCH_SIZE - 1) // BATCH_SIZE
    with (
        AzureOpenAIExtractor.from_environment() as extractor,
        JevClient(api_key=os.environ["OPENROUTER_API_KEY"], model=os.environ["JEV_MODEL"]) as jev_client,
    ):
        output_dir.mkdir(parents=True, exist_ok=False)
        logger.info("Writing results to %s", output_dir)
        verifier = JevVerifier(jev_client)
        for offset in range(0, len(cases), BATCH_SIZE):
            batch_number = offset // BATCH_SIZE + 1
            batch = cases[offset : offset + BATCH_SIZE]
            logger.info("Processing batch %d from %d (%d companies)", batch_number, total_batches, len(batch))
            logger.info("Batch %d: extracting company names", batch_number)
            try:
                extraction = extractor.extract_batch([case["entity_name"] for case in batch])
            except Exception as error:
                logger.exception("Batch %d extraction failed", batch_number)
                if isinstance(error, ValueError):
                    raise ValueError(f"Batch {batch_number} extraction: {error}") from error
                raise
            logger.info("Batch %d: extracted %d company names", batch_number, len(extraction.companies))
            logger.info("Batch %d: verifying extracted names with Jev", batch_number)
            try:
                decisions = _validate_batch(verifier, batch, extraction.companies)
            except Exception:
                logger.exception("Batch %d verification failed", batch_number)
                raise
            logger.info("Batch %d: verified %d company names", batch_number, len(decisions))
            logger.info("Batch %d: writing output", batch_number)
            _save_batch(
                output_dir / f"extracted-llm-batch-{batch_number}.json", batch_number, batch, extraction, decisions
            )
    return output_dir


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--test-run",
        action="store_true",
        help=f"evaluate only the first {TEST_RUN_LIMIT} input cases",
    )
    args = parser.parse_args()
    output_dir = extract(args.input, args.output_root, test_run=args.test_run)
    logger.info("Extraction complete: %s", output_dir)


if __name__ == "__main__":
    main()
