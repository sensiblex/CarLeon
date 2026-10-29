from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import configure_network_service
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.services.blockchain_service import BlockchainService

# Импортируем модели, чтобы SQLAlchemy видел их при create_all
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # На dev-режиме создаём таблицы автоматически (в проде — Alembic)
    Base.metadata.create_all(bind=engine)
    app.state.blockchain = BlockchainService(Path(settings.CHAIN_JSON_PATH))
    app.state.network = configure_network_service(app.state.blockchain)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}