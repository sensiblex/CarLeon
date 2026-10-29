import json
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

import httpx

from app.blockchain.block import Block
from app.blockchain.chain import Blockchain
from app.blockchain.transaction import StatusChange
from app.services.blockchain_service import BlockchainService


class PeerNetworkError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        code: str = "peer_error",
        details: object | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


@dataclass(frozen=True)
class Peer:
    peer_id: str
    url: str

    @classmethod
    def parse_many(cls, raw: str) -> list["Peer"]:
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("PEERS_JSON must contain a JSON array") from error
        if not isinstance(entries, list):
            raise ValueError("PEERS_JSON must contain a JSON array")

        peers: list[Peer] = []
        seen_ids: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("Each peer must be an object with id and url")
            peer_id = entry.get("id")
            url = entry.get("url")
            parsed_url = urlsplit(url) if isinstance(url, str) else None
            if (
                not isinstance(peer_id, str)
                or not peer_id
                or peer_id in seen_ids
                or parsed_url is None
                or parsed_url.scheme not in {"http", "https"}
                or not parsed_url.hostname
                or parsed_url.path not in {"", "/"}
                or parsed_url.username
                or parsed_url.password
                or parsed_url.query
                or parsed_url.fragment
            ):
                raise ValueError("Peer entries require a unique id and an http(s) base URL")
            peers.append(Peer(peer_id=peer_id, url=url.rstrip("/")))
            seen_ids.add(peer_id)
        return peers


class NetworkService:
    def __init__(
        self,
        blockchain_service: BlockchainService,
        *,
        node_id: str,
        network_id: str,
        peers_json: str,
        api_key: str,
        timeout_seconds: float = 3.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.blockchain_service = blockchain_service
        self.node_id = node_id
        self.network_id = network_id
        self.peers = Peer.parse_many(peers_json)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @property
    def chain(self) -> Blockchain:
        return self.blockchain_service.chain

    def info(self) -> dict:
        blocks = self.chain.chain
        head = blocks[-1] if blocks else None
        genesis = blocks[0] if blocks else None
        return {
            "node_id": self.node_id,
            "network_id": self.network_id,
            "genesis_hash": genesis.hash if genesis else None,
            "block_count": len(blocks),
            "height": head.index if head else -1,
            "head_hash": head.hash if head else None,
            "valid": self.chain.is_valid(),
        }

    def _peer(self, peer_id: str) -> Peer:
        for peer in self.peers:
            if peer.peer_id == peer_id:
                return peer
        raise PeerNetworkError(
            f"Узел '{peer_id}' не настроен в PEERS_JSON",
            status_code=404,
            code="unknown_peer",
        )

    def _request(
        self,
        peer: Peer,
        method: str,
        path: str,
        payload: dict | None = None,
    ) -> dict:
        url = f"{peer.url}/api/v1/network{path}"
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                trust_env=False,
                transport=self.transport,
            ) as client:
                response = client.request(
                    method,
                    url,
                    json=payload,
                    headers={"X-API-Key": self.api_key},
                )
        except httpx.TimeoutException as error:
            raise PeerNetworkError(
                f"Таймаут при обращении к узлу '{peer.peer_id}'",
                status_code=504,
                code="peer_timeout",
            ) from error
        except httpx.HTTPError as error:
            raise PeerNetworkError(
                f"Не удалось связаться с узлом '{peer.peer_id}': {error}",
                status_code=503,
                code="peer_unreachable",
            ) from error

        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text[:500]}
        if not response.is_success:
            detail = body.get("detail", body) if isinstance(body, dict) else body
            if isinstance(detail, dict):
                message = str(detail.get("message", detail))
                code = str(detail.get("code", "peer_rejected_request"))
            else:
                message = str(detail)
                code = "peer_rejected_request"
            raise PeerNetworkError(
                f"Узел '{peer.peer_id}' отклонил запрос: {message}",
                status_code=response.status_code,
                code=code,
                details=detail,
            )
        if not isinstance(body, dict):
            raise PeerNetworkError(
                f"Узел '{peer.peer_id}' вернул ответ не в формате JSON-объекта",
                code="invalid_peer_response",
            )
        return body

    def _compatible_peer_info(self, peer_id: str) -> tuple[Peer, dict]:
        peer = self._peer(peer_id)
        response = self._request(peer, "GET", "/info")
        remote_info = response.get("data")
        if not isinstance(remote_info, dict):
            raise PeerNetworkError(
                f"Узел '{peer_id}' вернул некорректное описание",
                code="invalid_peer_response",
            )
        local_info = self.info()
        if (
            remote_info.get("node_id") != peer_id
            or remote_info.get("network_id") != self.network_id
            or remote_info.get("genesis_hash") != local_info["genesis_hash"]
        ):
            raise PeerNetworkError(
                f"Ответ узла '{peer_id}' не совпадает с ожидаемой идентичностью/сетью/genesis",
                status_code=409,
                code="incompatible_peer",
                details={
                    "expected_peer_id": peer_id,
                    "actual_peer_id": remote_info.get("node_id"),
                    "local_network_id": self.network_id,
                    "peer_network_id": remote_info.get("network_id"),
                    "local_genesis_hash": local_info["genesis_hash"],
                    "peer_genesis_hash": remote_info.get("genesis_hash"),
                },
            )
        return peer, remote_info

    def peer_info(self, peer_id: str) -> dict:
        peer = self._peer(peer_id)
        try:
            response = self._request(peer, "GET", "/info")
            remote_info = response.get("data")
            if not isinstance(remote_info, dict):
                raise PeerNetworkError(
                    f"Узел '{peer_id}' вернул некорректное описание",
                    code="invalid_peer_response",
                )
            local_info = self.info()
            compatible = (
                remote_info.get("node_id") == peer_id
                and remote_info.get("network_id") == self.network_id
                and remote_info.get("genesis_hash") == local_info["genesis_hash"]
            )
            return {
                "peer_id": peer.peer_id,
                "reachable": True,
                "compatible": compatible,
                "node": remote_info,
                "error": None if compatible else "Идентификатор узла, сеть или genesis не совпадают",
            }
        except PeerNetworkError as error:
            return {
                "peer_id": peer.peer_id,
                "reachable": False,
                "compatible": False,
                "node": None,
                "error": error.to_dict(),
            }

    def peers_status(self) -> list[dict]:
        return [self.peer_info(peer.peer_id) for peer in self.peers]

    def local_block(self, block_hash: str) -> Block:
        for block in self.chain.chain:
            if block.hash == block_hash:
                return block
        raise PeerNetworkError(
            f"Блок '{block_hash}' не найден в локальной цепочке",
            status_code=404,
            code="block_not_found",
        )

    def peer_block(self, peer_id: str, block_hash: str) -> dict:
        peer, _ = self._compatible_peer_info(peer_id)
        response = self._request(
            peer, "GET", f"/blocks/{quote(block_hash, safe='')}"
        )
        block = response.get("data")
        if not isinstance(block, dict):
            raise PeerNetworkError(
                f"Узел '{peer_id}' вернул некорректный блок",
                code="invalid_peer_response",
            )
        return block

    def send_block(self, peer_id: str, block_hash: str) -> dict:
        peer, _ = self._compatible_peer_info(peer_id)
        block = self.local_block(block_hash)
        response = self._request(
            peer,
            "POST",
            "/blocks",
            {"block": block.to_dict()},
        )
        receipt = response.get("data")
        if not isinstance(receipt, dict):
            raise PeerNetworkError(
                f"Узел '{peer_id}' вернул некорректное подтверждение",
                code="invalid_peer_response",
            )
        return {"peer_id": peer_id, **receipt}

    def receive_block(self, block_data: dict) -> dict:
        try:
            block = Block.from_dict(block_data)
        except (KeyError, TypeError, ValueError) as error:
            raise PeerNetworkError(
                f"Структура блока некорректна: {error}",
                status_code=422,
                code="invalid_block_format",
            ) from error

        self.blockchain_service.accept_peer_block(block)
        return {
            "accepted": True,
            "node_id": self.node_id,
            "index": block.index,
            "hash": block.hash,
            "block_count": len(self.chain.chain),
            "head_hash": self.chain.last_block.hash,
            "validation": {"valid": True, "errors": []},
        }

    def probe_invalid_block(self, peer_id: str) -> dict:
        peer, remote_before = self._compatible_peer_info(peer_id)
        if not self.chain.chain:
            raise PeerNetworkError(
                "Нельзя подготовить пробный блок для пустой цепочки",
                status_code=409,
                code="empty_chain",
            )
        transaction = StatusChange(
            deal_id=f"invalid-probe-{self.node_id}",
            status=0,
        )
        candidate = Block(
            index=len(self.chain.chain),
            transactions=[transaction],
            previous_hash=self.chain.last_block.hash,
        )
        candidate.hash = "0" * 64
        if candidate.hash == candidate.calculate_hash():
            candidate.hash = "f" * 64
        try:
            self._request(
                peer,
                "POST",
                "/blocks",
                {"block": candidate.to_dict()},
            )
        except PeerNetworkError as error:
            if error.status_code == 422 and error.code == "invalid_block":
                after_response = self._request(peer, "GET", "/info")
                remote_after = after_response.get("data", {})
                unchanged = (
                    remote_after.get("block_count") == remote_before.get("block_count")
                    and remote_after.get("head_hash") == remote_before.get("head_hash")
                )
                return {
                    "accepted": False,
                    "peer_id": peer_id,
                    "rejected_hash": candidate.hash,
                    "error": error.details,
                    "receiver_before": remote_before,
                    "receiver_after": remote_after,
                    "receiver_unchanged": unchanged,
                }
            raise
        raise PeerNetworkError(
            f"Узел '{peer_id}' принял заведомо некорректный блок",
            status_code=502,
            code="invalid_block_was_accepted",
        )
