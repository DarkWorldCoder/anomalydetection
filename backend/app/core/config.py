from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "API Anomaly Detection Backend"
    environment: str = "development"
    debug: bool = True
    secret_key: str = Field(default="change-this-secret-key-before-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "postgresql+asyncpg://api_anomaly:api_anomaly_password@localhost:5432/api_anomaly"
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "production"}:
            return False
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
