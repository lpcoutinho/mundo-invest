"""Application-level configuration sourced from environment variables.

Loads DATABASE_URL and DEBUG from a .env file (or environment)
so that the same codebase can be pointed at local PostgreSQL,
CI SQLite, or production Aurora without code changes.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration holder.

    Every layer (database, services, API) reads from this single
    object so that switching environments only requires a .env swap.
    """
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "postgresql+asyncpg://app:app123@localhost:5432/mundo_invest"
    DEBUG: bool = False
    PIPEFY_PIPE_ID: str = "307173097"


settings = Settings()
