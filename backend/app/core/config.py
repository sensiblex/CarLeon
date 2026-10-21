from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CarLeon API"
    APP_ENV: str = "dev"
    API_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql+psycopg://carleon:carleon@localhost:5432/carleon"

    CHAIN_JSON_PATH: Path = Path("./data/blockchain.json")


settings = Settings()