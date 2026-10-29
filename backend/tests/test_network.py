import json

import httpx

from app.api import deps
from app.blockchain import Blockchain, StatusChange
from app.blockchain.block import Block
from app.blockchain.chain import InvalidBlockError
from app.services.blockchain_service import BlockchainService
from app.services.network_service import NetworkService, PeerNetworkError

HEADERS = {"X-API-Key": "test-key"}
BASE = "/api/v1/network"


def make_block() -> Block:
    chain = Blockchain()
    return chain.add_block([StatusChange(deal_id="network-test", status=4)])


def test_genesis_is_identical_for_independent_nodes(tmp_path):
    node_a = BlockchainService(tmp_path / "node-a.json")
    node_b = BlockchainService(tmp_path / "node-b.json")

    assert node_a.chain.last_block.hash == node_b.chain.last_block.hash
    assert node_a.path != node_b.path


def test_node_info_requires_api_key_and_reports_real_state(client):
    response = client.get(f"{BASE}/info", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["data"]["node_id"] == "node-local"
    assert response.json()["data"]["block_count"] == 1
    assert response.json()["data"]["valid"] is True
    assert client.get(f"{BASE}/info").status_code == 401


def test_peer_block_is_validated_appended_and_persisted(client, tmp_path):
    payload = {"block": make_block().to_dict()}

    response = client.post(f"{BASE}/blocks", json=payload, headers=HEADERS)

    assert response.status_code == 200
    receipt = response.json()["data"]
    assert receipt["accepted"] is True
    assert receipt["index"] == 1
    assert receipt["hash"] == payload["block"]["hash"]
    assert receipt["validation"] == {"valid": True, "errors": []}

    stored = deps.get_blockchain_service()
    assert stored.chain.last_block.hash == receipt["hash"]
    reloaded = BlockchainService(stored.path)
    assert reloaded.chain.last_block.hash == receipt["hash"]
    assert stored.path.name == "chain.json"


def test_tampered_block_is_rejected_without_mutating_chain(client):
    block = make_block().to_dict()
    block["transactions"][0]["status"] = 5

    response = client.post(f"{BASE}/blocks", json={"block": block}, headers=HEADERS)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_block"
    assert {error["type"] for error in detail["errors"]} >= {
        "block_hash_mismatch",
        "record_hash_mismatch",
    }
    chain = deps.get_blockchain_service().chain
    assert len(chain.chain) == 1
    assert chain.is_valid()


def test_block_with_wrong_previous_hash_is_rejected(client):
    block = make_block()
    block.previous_hash = "f" * 64
    block.hash = block.calculate_hash()

    response = client.post(
        f"{BASE}/blocks",
        json={"block": block.to_dict()},
        headers=HEADERS,
    )

    assert response.status_code == 422
    assert any(
        error["type"] == "previous_hash_mismatch"
        for error in response.json()["detail"]["errors"]
    )
    assert len(deps.get_blockchain_service().chain.chain) == 1


def test_block_with_wrong_index_is_rejected(client):
    block = make_block()
    block.index = 4
    block.hash = block.calculate_hash()

    response = client.post(
        f"{BASE}/blocks",
        json={"block": block.to_dict()},
        headers=HEADERS,
    )

    assert response.status_code == 422
    assert any(
        error["type"] == "index_mismatch"
        for error in response.json()["detail"]["errors"]
    )
    assert len(deps.get_blockchain_service().chain.chain) == 1


def test_duplicate_block_is_rejected(client):
    payload = {"block": make_block().to_dict()}
    first = client.post(f"{BASE}/blocks", json=payload, headers=HEADERS)
    duplicate = client.post(f"{BASE}/blocks", json=payload, headers=HEADERS)

    assert first.status_code == 200
    assert duplicate.status_code == 422
    assert any(
        error["type"] == "block_already_present"
        for error in duplicate.json()["detail"]["errors"]
    )
    assert len(deps.get_blockchain_service().chain.chain) == 2


def test_block_payload_shape_is_validated_before_service(client):
    response = client.post(
        f"{BASE}/blocks",
        json={"block": {"index": 0, "hash": "bad"}},
        headers=HEADERS,
    )

    assert response.status_code == 422
    assert len(deps.get_blockchain_service().chain.chain) == 1


def test_two_nodes_send_fetch_and_reject_invalid_block(tmp_path):
    node_a = BlockchainService(tmp_path / "node-a" / "chain.json")
    node_b = BlockchainService(tmp_path / "node-b" / "chain.json")
    receiver = NetworkService(
        node_b,
        node_id="node-b",
        network_id="classroom-v1",
        peers_json="[]",
        api_key="demo-key",
    )

    def handle_peer_request(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/info"):
            return httpx.Response(200, json={"success": True, "data": receiver.info()})
        if request.url.path.endswith("/blocks") and request.method == "POST":
            block_payload = json.loads(request.content)["block"]
            try:
                receipt = receiver.receive_block(block_payload)
                return httpx.Response(200, json={"success": True, "data": receipt})
            except InvalidBlockError as error:
                return httpx.Response(
                    422,
                    json={
                        "detail": {
                            "code": "invalid_block",
                            "message": str(error),
                            "errors": [item.to_dict() for item in error.errors],
                        }
                    },
                )
        if "/blocks/" in request.url.path and request.method == "GET":
            block_hash = request.url.path.rsplit("/", 1)[-1]
            block = next(
                (item for item in receiver.chain.chain if item.hash == block_hash),
                None,
            )
            if block is None:
                return httpx.Response(404, json={"detail": "block not found"})
            return httpx.Response(200, json={"success": True, "data": block.to_dict()})
        return httpx.Response(404, json={"detail": "unknown route"})

    sender = NetworkService(
        node_a,
        node_id="node-a",
        network_id="classroom-v1",
        peers_json='[{"id":"node-b","url":"http://node-b:8000"}]',
        api_key="demo-key",
        transport=httpx.MockTransport(handle_peer_request),
    )
    _, block_index = node_a.record("proof-123", 4)
    block = node_a.chain.chain[block_index]

    receipt = sender.send_block("node-b", block.hash)
    fetched = sender.peer_block("node-b", block.hash)

    assert receipt["accepted"] is True
    assert receipt["node_id"] == "node-b"
    assert fetched["hash"] == block.hash
    assert node_a.path != node_b.path
    assert node_b.chain.last_block.hash == node_a.chain.last_block.hash
    assert node_b.path.exists()

    before = receiver.info()
    rejection = sender.probe_invalid_block("node-b")
    after = receiver.info()
    assert rejection["accepted"] is False
    assert rejection["error"]["code"] == "invalid_block"
    assert any(
        item["type"] == "block_hash_mismatch"
        for item in rejection["error"]["errors"]
    )
    assert rejection["receiver_unchanged"] is True
    assert after["block_count"] == before["block_count"]
    assert after["head_hash"] == before["head_hash"]


def test_peer_with_different_genesis_is_not_used(tmp_path):
    local = BlockchainService(tmp_path / "local.json")
    incompatible_genesis = Blockchain()
    incompatible_genesis.chain[0].timestamp = 2.0
    incompatible_genesis.chain[0].hash = incompatible_genesis.chain[0].calculate_hash()
    remote = NetworkService(
        BlockchainService(tmp_path / "remote.json"),
        node_id="node-b",
        network_id="classroom-v1",
        peers_json="[]",
        api_key="demo-key",
    )
    remote.blockchain_service.chain = incompatible_genesis

    def handle_peer_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "data": remote.info()})

    sender = NetworkService(
        local,
        node_id="node-a",
        network_id="classroom-v1",
        peers_json='[{"id":"node-b","url":"http://node-b:8000"}]',
        api_key="demo-key",
        transport=httpx.MockTransport(handle_peer_request),
    )

    status = sender.peer_info("node-b")
    assert status["reachable"] is True
    assert status["compatible"] is False
    try:
        sender.send_block("node-b", local.chain.last_block.hash)
    except PeerNetworkError as error:
        assert error.code == "incompatible_peer"
    else:
        raise AssertionError("incompatible peer must not receive blocks")
