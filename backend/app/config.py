from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/encurtaurl"
    )
    redis_url: str = "redis://redis:6379/0"
    base_url: str = "http://localhost:8000"
    app_env: str = "development"

    # Shortcode
    short_code_length: int = 6
    short_code_max_retries: int = 5

    # Cache TTL em segundos
    cache_ttl: int = 3600

    # Limite de tamanho da URL
    max_url_length: int = 2048

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
