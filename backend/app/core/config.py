"""
Central application configuration.

All secrets (model API keys, endpoints, etc.) are read from
`backend/.env` and are ONLY ever accessible on the server. The React
frontend never sees these values — it only talks to our own FastAPI
routes.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenF1
    openf1_base_url: str = "https://api.openf1.org/v1"

    # Demo / fallback behaviour
    demo_mode: bool = True

    # External model API — the one you're building.
    # Backend sends audio + F1 context to this endpoint and expects a
    # JSON response back (see app/services/model_service.py for the
    # exact contract).
    model_api_url: str = ""
    model_api_key: str = ""
    model_api_timeout_seconds: float = 30.0

    # CORS — comma separated list of allowed origins
    allowed_origins: str = "http://localhost:5173"

    # Audio
    max_audio_mb: int = 25

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
