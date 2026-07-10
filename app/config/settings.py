from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    ENVIRONMENT: str = "development"
    ENABLE_DOCS: bool = True

    HOST: str
    PORT: int
    CORS_ALLOWED_ORIGINS: str = "*"

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    DB_MIN_CONNECTIONS: int
    DB_MAX_CONNECTIONS: int

    AUTH_BASE_URL: str
    PUBLIC_KEY_FILE: str
    JWT_ALGORITHM: str
    AUTH_TIMEOUT_SECONDS: int = 10

    CHUNK_SIZE: int
    MAX_RECORDS_PER_REQUEST: int

    LOG_LEVEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_allowed_origins(self) -> List[str]:
        origins = [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

        if self.is_production and "*" in origins:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS cannot contain '*' in production."
            )

        return origins


@lru_cache
def get_settings():
    return Settings()
