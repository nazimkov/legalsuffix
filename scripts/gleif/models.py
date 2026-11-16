"""Shared types for the GLEIF LLM extraction pipeline scripts."""

from enum import StrEnum

from openai.types.responses import ResponseUsage
from pydantic import BaseModel


class LegalFormPlace(StrEnum):
    SUFFIX = "suffix"
    PREFIX = "prefix"
    MIDDLE = "middle"
    NONE = "none"


class JevNoulOutcome(StrEnum):
    YES = "yes"
    NO = "no"


class JevDecisionAnswer(BaseModel):
    choice: str | JevNoulOutcome | None
    confidence: float | None
    probabilities: dict[str, float]
    answer_type: str = "choice"
    value: float | None = None


class JevVerdict(BaseModel):
    legal_form_present: bool
    place: LegalFormPlace
    correct: bool
    confidence: float


class JevValidation(BaseModel):
    decisions: dict[str, JevDecisionAnswer]
    overall_verdict: JevVerdict


class ExtractedRecord(BaseModel):
    id: int
    lei: str
    country_code: str
    language_code: str
    elf_code: str
    entity_name: str
    clean_entity: str
    suffix: str | None
    jev_overall_decision: str | None
    jev_overall_confidence: float | None
    jev_validation: JevValidation


class BatchRecords(BaseModel):
    batch_number: int
    records: list[ExtractedRecord]
    llm_usage: ResponseUsage | None
