from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Matriz de Competencias API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./matriz_competencias.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str = "dev-only-change-this-secret-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    admin_initial_password: str = "Cambiar123!"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
