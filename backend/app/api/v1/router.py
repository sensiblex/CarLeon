from fastapi import APIRouter

from app.api.v1 import blockchain, deals, tracking

api_router = APIRouter()
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(tracking.router, prefix="/deals", tags=["tracking"])
api_router.include_router(blockchain.router, prefix="/blockchain", tags=["blockchain"])