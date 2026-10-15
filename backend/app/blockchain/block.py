"""Блок - список транзакций, временная метка и хэши."""
import hashlib
import json
import time
from dataclasses import dataclass, field

from .transaction import StatusChange


@dataclass
class Block:
    index: int
    transactions: list[StatusChange]
    previous_hash: str
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def calculate_hash(self) -> str:
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            previous_hash=data["previous_hash"],
            hash=data["hash"],
            transactions=[StatusChange.from_dict(tx) for tx in data["transactions"]],
        )
