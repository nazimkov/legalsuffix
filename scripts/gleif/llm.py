"""Azure OpenAI client for extracting legal forms from company names."""

import os
from collections.abc import Sequence
from logging import getLogger
from time import perf_counter
from types import TracebackType
from typing import Literal, get_args, get_origin

from openai import AzureOpenAI
from openai.types.responses import ResponseUsage
from openai.types.shared_params import Reasoning, ReasoningEffort
from pydantic import BaseModel, Field

logger = getLogger(__name__)

AZURE_API_VERSION = "2025-04-01-preview"


class CompanyExtraction(BaseModel):
    id: int
    company_name: str
    legal_form: str | None = Field(description="Exact legal form from company name.")


class ExtractionResponse(BaseModel):
    companies: list[CompanyExtraction]


class ExtractionResult(BaseModel):
    companies: list[CompanyExtraction]
    usage: ResponseUsage | None


class AzureOpenAIExtractor:
    """Extract clean company names and legal suffixes using Azure OpenAI."""

    def __init__(
        self,
        *,
        api_key: str,
        azure_endpoint: str,
        deployment: str = "gpt-6-luna",
        api_version: str = AZURE_API_VERSION,
        reasoning_effort: str = "low",
    ) -> None:
        self._client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
        )
        self._deployment = deployment
        reasoning_types: tuple[ReasoningEffort, ...] = tuple(
            value for arg in get_args(ReasoningEffort) if get_origin(arg) is Literal for value in get_args(arg)
        )
        assert reasoning_effort in reasoning_types
        self._reasoning: Reasoning = {"effort": reasoning_effort}

    @classmethod
    def from_environment(cls) -> "AzureOpenAIExtractor":
        """Create an extractor from the Azure OpenAI environment settings."""
        required = ["OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Missing required Azure OpenAI settings: {', '.join(missing)}")

        return cls(
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", AZURE_API_VERSION),
            deployment=os.getenv("MODEL_DEPLOYMENT", "gpt-6-luna"),
            reasoning_effort=os.getenv("MODEL_REASONING_EFFORT", "low"),
        )

    def extract_batch(self, company_names: Sequence[str]) -> ExtractionResult:
        """Extract a batch and return its usage metadata as a plain mapping."""
        numbered_names = "\n".join(
            f"{index}: {company_name}" for index, company_name in enumerate(company_names, start=1)
        )
        started = perf_counter()
        response = self._client.responses.parse(
            model=self._deployment,
            reasoning=self._reasoning,
            instructions=(
                "For each company name, extract the exact legal form as written and return the remaining name "
                "as the clean company name. Do not translate, expand, or normalize the legal form. "
                'For example, for "Company Name 1, Inc.", return legal_form "Inc." and company_name '
                '"Company Name 1". Strip leading and trailing whitespace from both values. If no legal form '
                "is present, return null for legal_form. Return one result for each numbered input, preserving its id."
            ),
            input=f"<companies>\n{numbered_names}\n</companies>",
            text_format=ExtractionResponse,
        )
        usage = response.usage
        if usage:
            usage_str = f"Usage: {usage.input_tokens}/{usage.output_tokens}"
            usage_data = usage
        else:
            usage_str = "N/A"
            usage_data = None
        elapsed = perf_counter() - started
        logger.info(f"Called LLM API. {usage_str}. Elapsed: {elapsed:.2f}s")

        if not response.output_parsed:
            raise ValueError(f"Azure OpenAI response did not contain parsed output. Reason: {response.output_text}")
        result = response.output_parsed
        expected_ids = list(range(1, len(company_names) + 1))
        returned_ids = [company.id for company in result.companies]
        if returned_ids != expected_ids:
            raise ValueError(f"Expected extraction ids {expected_ids}, received {returned_ids}")

        return ExtractionResult(companies=result.companies, usage=usage_data)

    def __enter__(self) -> "AzureOpenAIExtractor":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._client.close()
