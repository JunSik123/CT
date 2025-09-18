"""FastAPI application exposing the pill identification workflow."""
from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .gpt_client import GPTClient
from .mfds_client import MFDSClient
from .models import IdentificationRequest, IdentificationResult, Pill, PillDetailsResponse, PillSearchRequest
from .pipeline import PillIdentificationService

settings = get_settings()
mfds_client = MFDSClient(base_url=settings.mfds_base_url, api_key=settings.mfds_api_key)
gpt_client = GPTClient(model=settings.gpt_model)
service = PillIdentificationService(mfds_client=mfds_client, gpt_client=gpt_client)

app = FastAPI(
    title="의약품 낱알 식별 API",
    description="식약처 데이터와 GPT 후처리를 결합한 캡스톤 디자인 예시 백엔드.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Simple health check endpoint."""

    return {"status": "ok"}


@app.post("/identify", response_model=IdentificationResult, tags=["identification"])
def identify_pill(request: IdentificationRequest) -> IdentificationResult:
    """Identify a pill based on extracted image features."""

    return service.identify(request)


@app.post("/pills/search", response_model=List[Pill], tags=["pills"])
def search_pills(request: PillSearchRequest) -> List[Pill]:
    """Search the MFDS dataset using basic filters."""

    return mfds_client.search_pills(
        color=request.color,
        shape=request.shape,
        imprint=request.imprint,
        name=request.name,
    )


@app.get("/pills/{pill_id}", response_model=PillDetailsResponse, tags=["pills"])
def get_pill_details(pill_id: str) -> PillDetailsResponse:
    """Return metadata and safety notes for a single pill."""

    details = service.get_pill_details(pill_id)
    if not details:
        raise HTTPException(status_code=404, detail="해당 의약품을 찾을 수 없습니다.")
    return details
