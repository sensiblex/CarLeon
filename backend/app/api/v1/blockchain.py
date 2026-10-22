from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_blockchain_service
from app.core.security import require_api_key
from app.schemas.blockchain import BlockRead, StatusChangeIn
from app.services.blockchain_service import BlockchainService

router = APIRouter()


@router.post("/status", response_model=dict, status_code=201)
def add_status_change(
    payload: StatusChangeIn,
    blockchain: BlockchainService = Depends(get_blockchain_service),
    _: None = Depends(require_api_key),
):
    try:
        tx_hash, block_index = blockchain.record(
            payload.deal_id, payload.status, payload.file_path
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=422, detail=f"File not found: {payload.file_path}"
        )
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status {payload.status}")
    return {"success": True, "data": {"tx_hash": tx_hash, "block_index": block_index}}


@router.get("", response_model=dict)
def get_chain(blockchain: BlockchainService = Depends(get_blockchain_service)):
    return {"success": True, "data": blockchain.chain_dump()}


@router.get("/validate", response_model=dict)
def validate_chain(blockchain: BlockchainService = Depends(get_blockchain_service)):
    """Проверка цепочки. Если невалидна - в ответе первая точка разрыва и все ошибки."""
    return {"success": True, "data": blockchain.validate()}


@router.get("/files/verify", response_model=dict)
def verify_files(blockchain: BlockchainService = Depends(get_blockchain_service)):
    """Сверка реальных файлов с хэшами, сохранёнными в записях."""
    return {"success": True, "data": blockchain.verify_files()}


@router.get("/deals/{deal_id}/history", response_model=dict)
def get_deal_history(
    deal_id: str,
    blockchain: BlockchainService = Depends(get_blockchain_service),
):
    return {"success": True, "data": blockchain.deal_history(deal_id)}