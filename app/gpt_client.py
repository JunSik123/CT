"""Simplified GPT client used to rerank pill candidates."""
from __future__ import annotations

from typing import Iterable, List

from .models import IdentificationRequest, PillCandidate


class GPTClient:
    """A lightweight stand-in for the OpenAI GPT API.

    The real project would call the OpenAI Chat Completions or Responses API with a
    multimodal prompt containing the extracted image features and baseline candidates.
    Since network access is not available in this environment we provide a heuristic
    implementation that mimics reranking behaviour. This makes it possible to build and
    test the surrounding system while maintaining a clean seam for plugging in the real
    API later on.
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model

    def rerank_candidates(
        self,
        request: IdentificationRequest,
        candidates: Iterable[PillCandidate],
    ) -> List[PillCandidate]:
        """Return candidates sorted by an estimated relevance score.

        The heuristic boosts candidates whose imprint, color, or shape matches the
        features detected from the image. This behaviour roughly imitates how GPT might
        reason over the metadata and textual description of a pill provided in the
        prompt.
        """

        reranked: List[PillCandidate] = []
        for candidate in candidates:
            score = candidate.similarity
            pill = candidate.pill

            if request.imprint and pill.imprint:
                if request.imprint.lower() == pill.imprint.lower():
                    score += 0.4
                elif request.imprint.lower() in pill.imprint.lower():
                    score += 0.2
            if request.color and pill.color:
                if request.color.lower() == pill.color.lower():
                    score += 0.2
            if request.shape and pill.shape:
                if request.shape.lower() == pill.shape.lower():
                    score += 0.2

            reranked.append(PillCandidate(pill=pill, similarity=min(score, 1.0)))

        reranked.sort(key=lambda c: c.similarity, reverse=True)
        return reranked

    def build_reasoning(self, request: IdentificationRequest, candidates: List[PillCandidate]) -> str:
        """Generate an explanation string describing the ranking decision."""

        if not candidates:
            return "제공된 특징과 일치하는 의약품 후보를 찾지 못했습니다."

        top = candidates[0]
        explanations = []
        if request.imprint and top.pill.imprint:
            explanations.append(f"이미지에서 추출된 각인 '{request.imprint}'이(가) 데이터의 '{top.pill.imprint}'와 일치합니다.")
        if request.color and top.pill.color:
            explanations.append(f"색상 '{request.color}' 정보가 동일합니다.")
        if request.shape and top.pill.shape:
            explanations.append(f"형태 '{request.shape}' 정보가 동일합니다.")
        if not explanations:
            explanations.append("기본 모델의 유사도 점수가 가장 높았습니다.")
        return " ".join(explanations)
