HEADERS = {"X-API-Key": "test-key"}


def _create_deal(client) -> str:
    resp = client.post(
        "/api/v1/deals",
        json={
            "track_code": "TRK-001",
            "title": "Toyota Camry",
            "supplier": "supplier-1",
            "buyer": "buyer-1",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["track_code"]


def test_add_tracking_point(client):
    code = _create_deal(client)
    resp = client.post(
        f"/api/v1/deals/{code}/tracking",
        json={"status": 1, "comment": "Order created"},
        headers=HEADERS,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]
    assert body["status"] == 1
    assert body["tx_hash"]
    assert body["block_index"] == 1


def test_invalid_status_rejected(client):
    code = _create_deal(client)
    resp = client.post(
        f"/api/v1/deals/{code}/tracking",
        json={"status": 42},
        headers=HEADERS,
    )
    assert resp.status_code == 422


def test_api_key_required(client):
    code = _create_deal(client)
    resp = client.post(
        f"/api/v1/deals/{code}/tracking",
        json={"status": 1},
    )
    assert resp.status_code == 401