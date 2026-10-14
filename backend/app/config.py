from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    # No default on purpose: the app must not start with a guessable signing key.
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, gt=0)
    # Comma-separated list of allowed browser origins, e.g. "https://app.example.com,http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def use_psycopg3_driver(cls, url: str) -> str:
        # Hosting providers hand out postgres:// or postgresql:// URLs; pin the driver explicitly.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
