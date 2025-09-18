"""Pydantic models used across the application."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Pill(BaseModel):
    """Represents a pill entry from the MFDS dataset."""

    pill_id: str = Field(..., description="Unique identifier of the pill in the dataset.")
    name: str = Field(..., description="Product name of the medication.")
    imprint: Optional[str] = Field(
        default=None,
        description="Text or pattern imprinted on the pill, if any.",
    )
    color: Optional[str] = Field(default=None, description="Primary color of the pill.")
    shape: Optional[str] = Field(default=None, description="Shape description (e.g., round, oval).")
    manufacturer: Optional[str] = Field(default=None, description="Manufacturer name.")
    ingredients: Optional[str] = Field(default=None, description="Active ingredients contained in the pill.")
    image_url: Optional[str] = Field(default=None, description="Official reference image URL.")
    description: Optional[str] = Field(
        default=None,
        description="Additional human readable description from MFDS data.",
    )


class PillSearchRequest(BaseModel):
    """Filters that can be used when searching for pills."""

    color: Optional[str] = Field(default=None, description="Filter by pill color.")
    shape: Optional[str] = Field(default=None, description="Filter by pill shape.")
    imprint: Optional[str] = Field(default=None, description="Filter by imprint text.")
    name: Optional[str] = Field(default=None, description="Filter by product name keyword.")


class PillCandidate(BaseModel):
    """Represents a candidate pill suggested by the classical model."""

    pill: Pill
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score from the baseline model.")


class IdentificationResult(BaseModel):
    """Result returned to the user after completing the identification pipeline."""

    top_match: Optional[Pill] = Field(default=None, description="Best matching pill according to GPT reranking.")
    candidates: List[PillCandidate] = Field(
        default_factory=list, description="Top candidate pills sorted by similarity score."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Free-form explanation of how the decision was made.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the top match after GPT reranking.",
    )


class IdentificationRequest(BaseModel):
    """Payload accepted by the API to identify a pill from an image."""

    color: Optional[str] = Field(default=None, description="Detected color of the pill from the captured image.")
    shape: Optional[str] = Field(default=None, description="Detected shape of the pill.")
    imprint: Optional[str] = Field(default=None, description="OCR-detected imprint text.")
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes such as camera conditions or surrounding context.",
    )


class HealthWarning(BaseModel):
    """Information about safety considerations that can be surfaced to the user."""

    title: str
    details: str


class PillDetailsResponse(BaseModel):
    """Pill metadata returned to clients for display."""

    pill: Pill
    warnings: List[HealthWarning] = Field(default_factory=list)
