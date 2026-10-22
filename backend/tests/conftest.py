import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("CHAIN_JSON_PATH", str(Path(tempfile.mkdtemp()) / "chain.json"))

from app.db.base import Base  # noqa: E402
from app.api.deps import get_db_session  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: F401,E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,          # одно соединение на все сессии
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    # эндпоинты зависят от get_db_session, поэтому подменяем обе зависимости
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_session] = override_get_db

    # Изолируем JSON-цепочку под каждый тест
    chain_path = tmp_path / "chain.json"
    monkeypatch.setattr("app.core.config.settings.CHAIN_JSON_PATH", chain_path)
    monkeypatch.setattr("app.api.deps._blockchain_service", None)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()