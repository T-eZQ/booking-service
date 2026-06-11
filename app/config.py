from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/booking"

    secret_key: str = "dev-secret-key-please-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    app_title: str = "Booking Service"
    app_version: str = "0.1.0"


settings = Settings()
