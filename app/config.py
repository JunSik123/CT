"""Application configuration utilities."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Environment settings for the application."""

    mfds_api_key: Optional[str] = Field(
        default=None,
        description=(
            "API key for the Ministry of Food and Drug Safety (MFDS) pill identification API. "
            "The sample dataset bundled with the project is used when no key is provided."
        ),
    )
    mfds_base_url: str = Field(
        default="https://api.odcloud.kr/api/15049680/v1/uddi:1fb7f4d7-66ec-4ff0-9d8c-bcc796f9649a",
        description="Base URL for the MFDS pill identification API endpoint.",
    )
    gpt_model: str = Field(
        default="gpt-4o-mini",
        description="Default GPT model identifier used for reranking pill candidates.",
    )

    class Config:
        env_prefix = "PILL_ID_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
