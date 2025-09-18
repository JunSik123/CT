"""High level service that orchestrates pill identification."""
from __future__ import annotations

from typing import List, Optional

from .gpt_client import GPTClient
from .mfds_client import MFDSClient
from .models import (
    HealthWarning,
    IdentificationRequest,
    IdentificationResult,
    Pill,
    PillCandidate,
    PillDetailsResponse,
)


class PillIdentificationService:
    """Encapsulates the steps required to identify a pill from image features."""

    def __init__(self, mfds_client: MFDSClient, gpt_client: GPTClient) -> None:
        self.mfds_client = mfds_client
        self.gpt_client = gpt_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def identify(self, request: IdentificationRequest) -> IdentificationResult:
        candidates = self._build_candidates(request)
        reranked = self.gpt_client.rerank_candidates(request, candidates)
        reasoning = self.gpt_client.build_reasoning(request, reranked)
        top_match = reranked[0].pill if reranked else None
        confidence = reranked[0].similarity if reranked else None

        return IdentificationResult(
            top_match=top_match,
            candidates=reranked,
            reasoning=reasoning,
            confidence=confidence,
        )

    def get_pill_details(self, pill_id: str) -> Optional[PillDetailsResponse]:
        pill = self.mfds_client.get_pill(pill_id)
        if not pill:
            return None
        warnings = self._build_warnings(pill.ingredients or "")
        return PillDetailsResponse(pill=pill, warnings=warnings)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_candidates(self, request: IdentificationRequest) -> List[PillCandidate]:
        pills = self.mfds_client.search_pills(
            color=request.color,
            shape=request.shape,
            imprint=request.imprint,
            name=None,
            limit=10,
        )

        candidates = []
        for pill in pills:
            similarity = self._baseline_similarity(request, pill)
            candidates.append(PillCandidate(pill=pill, similarity=similarity))
        return candidates

    def _baseline_similarity(self, request: IdentificationRequest, pill: Pill) -> float:
        score = 0.1  # base prior

        if request.imprint and pill.imprint:
            if request.imprint.lower() == pill.imprint.lower():
                score += 0.6
            elif request.imprint.lower() in pill.imprint.lower():
                score += 0.3
        if request.color and pill.color:
            if request.color.lower() == pill.color.lower():
                score += 0.2
        if request.shape and pill.shape:
            if request.shape.lower() == pill.shape.lower():
                score += 0.2

        return min(score, 1.0)

    def _build_warnings(self, ingredients: str) -> List[HealthWarning]:
        warnings: List[HealthWarning] = []
        text = ingredients.lower()
        if "ibuprofen" in text:
            warnings.append(
                HealthWarning(
                    title="위장관 이상 반응 주의",
                    details="이부프로펜은 위장 장애를 유발할 수 있으므로 식후에 복용하세요.",
                )
            )
        if "acetaminophen" in text:
            warnings.append(
                HealthWarning(
                    title="간 독성 주의",
                    details="하루 최대 용량(성인 4,000mg)을 초과하지 않도록 주의하세요.",
                )
            )
        return warnings
