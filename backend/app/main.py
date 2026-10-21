from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .blockchain import Blockchain, StatusChange
from .blockchain.storage import load_chain, save_chain
from .blockchain.transaction import hash_file

blockchain: Blockchain


@asynccontextmanager
async def lifespan(app: FastAPI):
    global blockchain
    blockchain = load_chain()
    yield
    save_chain(blockchain)


app = FastAPI(title="CarLeon Blockchain", lifespan=lifespan)


class StatusChangeIn(BaseModel):
    deal_id: str
    status: int
    # Необязательный внешний файл (договор, ПТС и т.п.): хэш считает сервер
    file_path: str | None = None


@app.post("/api/v1/blockchain/status", status_code=201)
def add_status_change(payload: StatusChangeIn):
    file_hash = None
    if payload.file_path is not None:
        if not Path(payload.file_path).is_file():
            raise HTTPException(status_code=422, detail=f"Файл не найден: {payload.file_path}")
        file_hash = hash_file(payload.file_path)
    try:
        tx = StatusChange(
            deal_id=payload.deal_id,
            status=payload.status,
            file_path=payload.file_path,
            file_hash=file_hash,
        )
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Недопустимый статус: {payload.status}")
    block = blockchain.add_block([tx])
    save_chain(blockchain)
    return {"success": True, "data": block.to_dict()}


@app.get("/api/v1/blockchain")
def get_chain():
    return {"success": True, "data": blockchain.to_dict()}


@app.get("/api/v1/blockchain/validate")
def validate_chain():
    """Проверка цепочки. Если невалидна - в ответе первая точка разрыва и все найденные ошибки."""
    errors = blockchain.validate()
    return {
        "success": True,
        "data": {
            "valid": not errors,
            "first_break": errors[0].to_dict() if errors else None,
            "errors": [e.to_dict() for e in errors],
        },
    }


@app.get("/api/v1/blockchain/files/verify")
def verify_files():
    """Сверка реальных файлов с хэшами, сохранёнными в записях."""
    errors = blockchain.verify_files()
    return {
        "success": True,
        "data": {"valid": not errors, "errors": [e.to_dict() for e in errors]},
    }


@app.get("/api/v1/blockchain/deals/{deal_id}/history")
def get_deal_history(deal_id: str):
    history = blockchain.get_deal_history(deal_id)
    return {"success": True, "data": [tx.to_dict() for tx in history]}