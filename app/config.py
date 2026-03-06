"""
Application settings loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/college_db"

    # JWT Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # File storage
    file_upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Runtime environment — controls log verbosity and error detail
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        """True when running in production — disables debug details in responses."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — reads .env once at startup."""
    return Settings()
