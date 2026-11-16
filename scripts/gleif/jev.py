from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from logging import getLogger
from types import TracebackType
from typing import ClassVar
from urllib.parse import urlsplit

import httpx2
from typesafe_sdk import (
    Answer,
    BoxAnswer,
    Choice,
    ChoiceAnswer,
    Content,
    Noul,
    NoulAnswer,
    Questions,
    RetryPolicy,
    ScoreAnswer,
    SystemOneResponse,
    TypeSafeClient,
)

from .models import JevDecisionAnswer, JevNoulOutcome, JevValidation, JevVerdict, LegalFormPlace

logger = getLogger(__name__)

JEV_URL = "https://openrouter.ai/api/alpha/decisions"


@dataclass
class CompanyState:
    id: int
    original_company_name: str
    extracted_company_name: str
    extracted_suffix: str | None


QUESTIONS: Questions = {
    "legal_form_present": Noul(
        instructions=(
            "Is a legal entity form present in the original company name? "
            + "Answer yes only when a legal form is present; otherwise answer no."
        ),
    ),
    "legal_form_place": Choice(
        instructions=(
            "Where is the legal form placed in the original company name? Choose suffix, prefix, or middle. "
            + "Choose none if there is no legal form, and uncertain only if its placement cannot be determined."
        ),
        criteria={
            LegalFormPlace.SUFFIX.value: "The legal form appears at the end of the company name.",
            LegalFormPlace.PREFIX.value: "The legal form appears at the beginning of the company name.",
            LegalFormPlace.MIDDLE.value: "The legal form appears between other parts of the company name.",
            LegalFormPlace.NONE.value: "No legal form is present in the original company name.",
        },
    ),
    "company_name_is_substring": Noul(
        instructions=(
            "Is the extracted company name an exact, case-preserving substring of the original name "
            + "after removing the extracted legal form and surrounding whitespace?"
        ),
    ),
    "company_name_preserved": Noul(
        instructions=(
            "Has the extracted company name preserved all meaningful parts of the original company name, "
            + "removing only the legal form? For example, changing 'Foo Holdings LLC' to 'Foo' loses meaningful text."
        ),
    ),
    "legal_form_extracted": Noul(
        instructions=(
            "Is the legal form extraction complete, "
            + "with no legal entity suffix remaining in the extracted company name?"
        ),
    ),
}


class _JevEndpointTransport(httpx2.BaseTransport):
    """Send TypeSafe SDK requests to the configured Jev endpoint."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._transport = httpx2.HTTPTransport()

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        routed_request = httpx2.Request(
            method=request.method,
            url=self._url,
            headers=request.headers,
            content=request.read(),
            extensions=request.extensions,
        )
        return self._transport.handle_request(routed_request)

    def close(self) -> None:
        self._transport.close()


class JevClient:
    def __init__(self, api_key: str, model: str, url: str = JEV_URL) -> None:
        parsed_url = urlsplit(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Jev URL must be an absolute URL")

        self._client = TypeSafeClient(
            api_key=api_key,
            model=model,
            base_url=f"{parsed_url.scheme}://{parsed_url.netloc}",
            transport=_JevEndpointTransport(url),
            compression=False,
            retry=RetryPolicy(
                max_retries=6,
                backoff_initial=4,
                backoff_max=10,
                backoff_jitter=0,
                http_statuses={408, 409},
                timeout=None,
            ),
        )

    def call(
        self,
        state: Content,
        questions: Questions,
    ) -> SystemOneResponse:
        return self._client.system_one(state=state, questions=questions)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JevClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class JevVerifier:
    _VERDICT_WEIGHTS: ClassVar[dict[str, float]] = {
        "company_name_is_substring": 1.0,
        "company_name_preserved": 1.0,
        "legal_form_extracted": 1.0,
    }
    _CRITICAL_CHECKS: ClassVar[frozenset[str]] = frozenset(
        {
            "company_name_is_substring",
            "company_name_preserved",
            "legal_form_extracted",
        }
    )
    _CRITICAL_FAILURE_CONFIDENCE: ClassVar[float] = 0.75
    _AGGREGATE_VERDICT_CONFIDENCE: ClassVar[float] = 0.65

    def __init__(self, client: JevClient) -> None:
        self.client = client

    def validate(self, states: Sequence[CompanyState]) -> Mapping[int, JevValidation]:
        logger.info("Jev validate ids")
        validations: dict[int, JevValidation] = {}
        for s in states:
            response = self.client.call(state=asdict(s), questions=QUESTIONS)

            decisions = {q: self.from_answer(ra) for q, ra in response.answers.items()}
            validations[s.id] = JevValidation(
                decisions=decisions, overall_verdict=self.get_verdict(decisions, s.extracted_suffix)
            )

        return validations

    @staticmethod
    def from_answer(answer: Answer) -> JevDecisionAnswer:
        if isinstance(answer, ChoiceAnswer):
            return JevDecisionAnswer(
                choice=answer.choice,
                confidence=answer.confidence,
                probabilities=answer.probabilities,
            )
        if isinstance(answer, NoulAnswer):
            probability_yes = answer.noul
            return JevDecisionAnswer(
                choice=(JevNoulOutcome.YES if probability_yes >= 0.5 else JevNoulOutcome.NO),
                confidence=max(probability_yes, 1 - probability_yes),
                probabilities={
                    JevNoulOutcome.YES.value: probability_yes,
                    JevNoulOutcome.NO.value: 1 - probability_yes,
                },
                answer_type="noul",
                value=probability_yes,
            )
        if isinstance(answer, ScoreAnswer):
            if not answer.probabilities:
                return JevDecisionAnswer(
                    choice=None,
                    confidence=answer.confidence,
                    probabilities={},
                    answer_type="score",
                    value=answer.score,
                )
            selected_score = max(answer.probabilities, key=answer.probabilities.__getitem__)
            label = answer.legend.get(selected_score)
            return JevDecisionAnswer(
                choice=label if isinstance(label, str) else str(selected_score),
                confidence=answer.confidence,
                probabilities={str(score): probability for score, probability in answer.probabilities.items()},
                answer_type="score",
                value=answer.score,
            )
        if isinstance(answer, BoxAnswer):
            return JevDecisionAnswer(
                choice=None,
                confidence=answer.confidence,
                probabilities={},
                answer_type="box",
            )
        raise ValueError(f"Unsupported answer type: {type(answer).__name__}")

    @staticmethod
    def get_verdict(decisions: dict[str, JevDecisionAnswer], extracted_suffix: str | None) -> JevVerdict:
        """Return extraction correctness and confidence with form annotations.

        A confident failure on a structural check forces an incorrect verdict.
        The weighted checks require at least 0.65 confidence after accounting for
        disagreement. Legal-form presence and placement are reported as
        annotations and do not affect correctness or confidence.
        """
        presence_answer = decisions.get("legal_form_present")
        if presence_answer is None or not isinstance(presence_answer.choice, JevNoulOutcome):
            raise ValueError(f"Invalid presence_answer {presence_answer}")
        legal_form_present = presence_answer.choice == JevNoulOutcome.YES

        place_answer = decisions.get("legal_form_place")
        if place_answer is None or not isinstance(place_answer.choice, str):
            raise ValueError(f"Invalid place_answer {place_answer}")
        place = LegalFormPlace(place_answer.choice)

        opinions: list[tuple[str, JevNoulOutcome, float]] = []
        critical_failures: list[float] = []

        for question, answer in decisions.items():
            if question in {"legal_form_present", "legal_form_place"}:
                continue
            if answer.confidence is None or answer.choice is None:
                continue
            outcome = __class__._outcome(question, answer.choice)
            if outcome is None:
                continue

            opinions.append((question, outcome, answer.confidence))
            if question in __class__._CRITICAL_CHECKS and outcome == JevNoulOutcome.NO:
                if answer.confidence >= __class__._CRITICAL_FAILURE_CONFIDENCE:
                    critical_failures.append(answer.confidence)

        correct_weight = 0.0
        incorrect_weight = 0.0
        nominal_weight = 0.0
        for question, outcome, confidence in opinions:
            weight = __class__._VERDICT_WEIGHTS.get(question, 0.0)
            if weight == 0:
                continue
            nominal_weight += weight
            if outcome == JevNoulOutcome.YES:
                correct_weight += weight * confidence
            elif outcome == JevNoulOutcome.NO:
                incorrect_weight += weight * confidence

        evidence_weight = correct_weight + incorrect_weight
        if evidence_weight:
            agreement = abs(correct_weight - incorrect_weight) / evidence_weight
            mean_confidence = evidence_weight / nominal_weight
            aggregate_confidence = mean_confidence * agreement
        else:
            aggregate_confidence = 0.0

        if critical_failures:
            correct = False
            confidence = max(critical_failures)
        elif len(opinions) < 2 or aggregate_confidence < __class__._AGGREGATE_VERDICT_CONFIDENCE:
            correct = False
            confidence = aggregate_confidence
        else:
            correct = correct_weight > incorrect_weight
            confidence = aggregate_confidence

        if legal_form_present and not extracted_suffix:
            correct = False
            confidence = 1.0

        return JevVerdict(
            legal_form_present=legal_form_present,
            place=place,
            correct=correct,
            confidence=confidence,
        )

    @staticmethod
    def _outcome(question: str, choice: str) -> JevNoulOutcome | None:
        normalized = choice.strip().casefold()
        if question in {"legal_form_present", "legal_form_place"}:
            # These are descriptive annotations, not extraction correctness checks.
            return None
        if normalized == JevNoulOutcome.YES.value:
            return JevNoulOutcome.YES
        if normalized == JevNoulOutcome.NO.value:
            return JevNoulOutcome.NO
        return None
