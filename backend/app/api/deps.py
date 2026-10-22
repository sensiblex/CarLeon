from collections.abc import Generator
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.blockchain_service import BlockchainService

# Единственный экземпляр сервиса на процесс (данные держим в JSON-файле).
_blockchain_service: BlockchainService | None = None


def get_blockchain_service() -> BlockchainService:
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService(Path(settings.CHAIN_JSON_PATH))
    return _blockchain_service


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


DBDep = Depends(get_db_session)
BlockchainDep = Depends(get_blockchain_service)