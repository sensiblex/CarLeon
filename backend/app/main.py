from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .blockchain import Blockchain, StatusChange
from .blockchain.storage import load_chain, save_chain

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


@app.post("/api/v1/blockchain/status", status_code=201)
def add_status_change(payload: StatusChangeIn):
    try:
        tx = StatusChange(deal_id=payload.deal_id, status=payload.status)
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
    return {"success": True, "data": {"valid": blockchain.is_valid()}}


@app.get("/api/v1/blockchain/deals/{deal_id}/history")
def get_deal_history(deal_id: str):
    history = blockchain.get_deal_history(deal_id)
    return {"success": True, "data": [tx.to_dict() for tx in history]}
