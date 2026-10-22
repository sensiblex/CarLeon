"""Тесты эндпоинтов блокчейна: добавление записей, проверка цепочки и файлов."""
from app.api import deps

HEADERS = {"X-API-Key": "test-key"}
BASE = "/api/v1/blockchain"


def add_status(client, deal_id="deal-1", status=1, **extra):
    return client.post(
        f"{BASE}/status",
        json={"deal_id": deal_id, "status": status, **extra},
        headers=HEADERS,
    )


def test_validate_fresh_chain(client):
    data = client.get(f"{BASE}/validate").json()["data"]
    assert data == {"valid": True, "first_break": None, "errors": []}


def test_validate_after_adding_records(client):
    assert add_status(client, status=1).status_code == 201
    assert add_status(client, status=2).status_code == 201
    assert client.get(f"{BASE}/validate").json()["data"]["valid"] is True


def test_validate_reports_tampered_block(client):
    add_status(client, status=1)
    add_status(client, status=2)
    # подмена содержимого записи в блоке 2 "в обход" API
    deps.get_blockchain_service().chain.chain[2].transactions[0].status = 9
    data = client.get(f"{BASE}/validate").json()["data"]
    assert data["valid"] is False
    assert data["first_break"]["block_index"] == 2
    assert data["first_break"]["type"] == "block_hash_mismatch"
    assert {e["type"] for e in data["errors"]} >= {"record_hash_mismatch"}


def test_validate_reports_broken_link(client):
    add_status(client, status=1)
    add_status(client, status=2)
    deps.get_blockchain_service().chain.chain[1].hash = "f" * 64
    data = client.get(f"{BASE}/validate").json()["data"]
    assert data["valid"] is False
    assert any(
        e["type"] == "previous_hash_mismatch" and e["block_index"] == 2
        for e in data["errors"]
    )


def test_add_record_with_file_and_verify(client, tmp_path):
    f = tmp_path / "contract.txt"
    f.write_text("договор v1")
    assert add_status(client, status=3, file_path=str(f)).status_code == 201
    assert client.get(f"{BASE}/files/verify").json()["data"]["valid"] is True

    f.write_text("договор v2 (подмена)")
    data = client.get(f"{BASE}/files/verify").json()["data"]
    assert data["valid"] is False
    assert data["errors"][0]["type"] == "file_mismatch"
    assert data["errors"][0]["block_index"] == 1


def test_missing_file_rejected(client, tmp_path):
    resp = add_status(client, status=3, file_path=str(tmp_path / "nope.txt"))
    assert resp.status_code == 422


def test_invalid_status_rejected(client):
    assert add_status(client, status=42).status_code == 422


def test_api_key_required(client):
    resp = client.post(f"{BASE}/status", json={"deal_id": "d", "status": 1})
    assert resp.status_code == 401


def test_deal_history(client):
    add_status(client, deal_id="d1", status=1)
    add_status(client, deal_id="d1", status=2)
    data = client.get(f"{BASE}/deals/d1/history").json()["data"]
    assert [tx["status"] for tx in data] == [1, 2]