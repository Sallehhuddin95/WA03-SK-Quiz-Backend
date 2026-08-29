from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SK Quiz API"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/sk_quiz"
    timezone: str = "Asia/Kuala_Lumpur"

    session_cookie_name: str = "sk_quiz_sesi"
    cookie_secure: bool = False
    session_idle_minutes: int = 1440
    session_max_days: int = 30
    cookie_domain: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()