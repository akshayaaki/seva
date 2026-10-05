"""
Janseva AI — Application Configuration
Loads environment variables with validation using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "Janseva AI"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # ── Supabase ─────────────────────────────────────────────────────────
    supabase_url: str = Field(default="https://localhost.supabase.co", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="test-anon-key", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="test-service-role-key", alias="SUPABASE_SERVICE_ROLE_KEY")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # ── Google Gemini AI ─────────────────────────────────────────────────
    gemini_api_key: str = Field(default="test-gemini-key", alias="GEMINI_API_KEY")

    # ── LibreTranslate ───────────────────────────────────────────────────
    libretranslate_url: Optional[str] = Field(
        default=None, alias="LIBRETRANSLATE_URL"
    )
    libretranslate_api_key: Optional[str] = Field(
        default=None, alias="LIBRETRANSLATE_API_KEY"
    )

    # ── Geocoding ────────────────────────────────────────────────────────
    nominatim_url: str = Field(
        default="https://nominatim.openstreetmap.org", alias="NOMINATIM_URL"
    )
    nominatim_user_agent: str = Field(
        default="janseva-ai", alias="NOMINATIM_USER_AGENT"
    )

    # ── Routing ──────────────────────────────────────────────────────────
    osrm_url: str = Field(
        default="https://router.project-osrm.org", alias="OSRM_URL"
    )

    # ── Sentry ───────────────────────────────────────────────────────────
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")

    # ── Notification Providers ───────────────────────────────────────────
    email_smtp_host: Optional[str] = Field(default=None, alias="EMAIL_SMTP_HOST")
    email_smtp_port: Optional[int] = Field(default=None, alias="EMAIL_SMTP_PORT")
    email_smtp_user: Optional[str] = Field(default=None, alias="EMAIL_SMTP_USER")
    email_smtp_password: Optional[str] = Field(default=None, alias="EMAIL_SMTP_PASSWORD")
    email_from: Optional[str] = Field(default=None, alias="EMAIL_FROM")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
