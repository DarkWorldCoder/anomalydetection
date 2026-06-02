from functools import lru_cache

from pydantic import Field  
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = Field("Anomaly Detection API", env="APP_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    database_url: str = Field(..., env="DATABASE_URL")
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm:str = "HS256"
    access_token_expire_minutes: int = 30
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["*"], env="BACKEND_CORS_ORIGINS")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()