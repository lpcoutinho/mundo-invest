from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "postgresql+asyncpg://app:app123@localhost:5432/mundo_invest"
    DEBUG: bool = False


settings = Settings()
