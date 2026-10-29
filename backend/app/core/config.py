from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CarLeon API"
    APP_ENV: str = "dev"
    API_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql+psycopg://carleon:carleon@localhost:5432/carleon"

    CHAIN_JSON_PATH: Path = Path("./data/blockchain.json")
    NODE_ID: str = Field(default="node-local", min_length=1)
    NETWORK_ID: str = Field(default="carleon-demo-v1", min_length=1)
    PEERS_JSON: str = "[]"
    PEER_REQUEST_TIMEOUT_SECONDS: float = Field(default=3.0, gt=0, le=60)


settings = Settings()