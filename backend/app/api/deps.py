from collections.abc import Generator
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.blockchain_service import BlockchainService
from app.services.network_service import NetworkService

# Единственный экземпляр сервиса на процесс (данные держим в JSON-файле).
_blockchain_service: BlockchainService | None = None
_network_service: NetworkService | None = None


def get_blockchain_service() -> BlockchainService:
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService(Path(settings.CHAIN_JSON_PATH))
    return _blockchain_service


def get_network_service() -> NetworkService:
    global _network_service
    if _network_service is None:
        _network_service = NetworkService(
            get_blockchain_service(),
            node_id=settings.NODE_ID,
            network_id=settings.NETWORK_ID,
            peers_json=settings.PEERS_JSON,
            api_key=settings.API_KEY,
            timeout_seconds=settings.PEER_REQUEST_TIMEOUT_SECONDS,
        )
    return _network_service


def configure_network_service(blockchain_service: BlockchainService) -> NetworkService:
    global _blockchain_service, _network_service
    _blockchain_service = blockchain_service
    _network_service = NetworkService(
        blockchain_service,
        node_id=settings.NODE_ID,
        network_id=settings.NETWORK_ID,
        peers_json=settings.PEERS_JSON,
        api_key=settings.API_KEY,
        timeout_seconds=settings.PEER_REQUEST_TIMEOUT_SECONDS,
    )
    return _network_service


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


DBDep = Depends(get_db_session)
BlockchainDep = Depends(get_blockchain_service)