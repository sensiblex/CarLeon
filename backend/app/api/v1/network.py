from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_network_service
from app.blockchain.chain import InvalidBlockError
from app.core.config import settings
from app.core.security import require_api_key
from app.schemas.blockchain import BlockSubmission
from app.services.network_service import NetworkService, PeerNetworkError

router = APIRouter()


def _raise_peer_error(error: PeerNetworkError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error.to_dict(),
    ) from error


@router.get("/info", response_model=dict)
def get_node_info(
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    return {"success": True, "data": network.info()}


@router.get("/peers", response_model=dict)
def get_peers(
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    return {"success": True, "data": network.peers_status()}


@router.get("/peers/{peer_id}/info", response_model=dict)
def get_peer_info(
    peer_id: str,
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    try:
        return {"success": True, "data": network.peer_info(peer_id)}
    except PeerNetworkError as error:
        _raise_peer_error(error)


@router.get("/blocks/{block_hash}", response_model=dict)
def get_local_block(
    block_hash: str,
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    try:
        return {"success": True, "data": network.local_block(block_hash).to_dict()}
    except PeerNetworkError as error:
        _raise_peer_error(error)


@router.post("/blocks", response_model=dict)
def receive_block(
    payload: BlockSubmission,
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    try:
        receipt = network.receive_block(payload.block.model_dump())
        return {"success": True, "data": receipt}
    except PeerNetworkError as error:
        _raise_peer_error(error)
    except InvalidBlockError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_block",
                "message": "Полученный блок не прошёл проверку",
                "errors": [item.to_dict() for item in error.errors],
            },
        ) from error


@router.get("/peers/{peer_id}/blocks/{block_hash}", response_model=dict)
def request_peer_block(
    peer_id: str,
    block_hash: str,
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    try:
        block = network.peer_block(peer_id, block_hash)
        return {"success": True, "data": block}
    except PeerNetworkError as error:
        _raise_peer_error(error)


@router.post("/peers/{peer_id}/blocks/{block_hash}/send", response_model=dict)
def send_block_to_peer(
    peer_id: str,
    block_hash: str,
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    try:
        receipt = network.send_block(peer_id, block_hash)
        return {"success": True, "data": receipt}
    except PeerNetworkError as error:
        _raise_peer_error(error)


@router.post("/peers/{peer_id}/invalid-block-demo", response_model=dict)
def demonstrate_invalid_block_rejection(
    peer_id: str,
    network: NetworkService = Depends(get_network_service),
    _: None = Depends(require_api_key),
):
    if settings.APP_ENV not in {"dev", "demo"}:
        raise HTTPException(
            status_code=404,
            detail="Демонстрация некорректного блока доступна только в dev/demo",
        )
    try:
        evidence = network.probe_invalid_block(peer_id)
        return {"success": True, "data": evidence}
    except PeerNetworkError as error:
        _raise_peer_error(error)
