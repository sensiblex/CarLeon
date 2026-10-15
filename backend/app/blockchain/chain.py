"""Цепочка блоков с валидацией и добавлением блоков."""
from .block import Block
from .transaction import StatusChange

GENESIS_PREVIOUS_HASH = "0" * 64


class Blockchain:
    def __init__(self, chain: list[Block] | None = None):
        self.chain: list[Block] = chain if chain else [self.create_genesis_block()]

    @staticmethod
    def create_genesis_block() -> Block:
        block = Block(
            index=0,
            transactions=[StatusChange(deal_id="genesis", status=0)],
            previous_hash=GENESIS_PREVIOUS_HASH,
        )
        block.hash = block.calculate_hash()
        return block

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, transactions: list[StatusChange]) -> Block:
        block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=self.last_block.hash,
        )
        block.hash = block.calculate_hash()
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        for i, block in enumerate(self.chain):
            if block.hash != block.calculate_hash():
                return False
            if i > 0 and block.previous_hash != self.chain[i - 1].hash:
                return False
        return True

    def get_deal_history(self, deal_id: str) -> list[StatusChange]:
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.deal_id == deal_id:
                    history.append(tx)
        return history

    def to_dict(self) -> dict:
        return {"chain": [block.to_dict() for block in self.chain]}

    @classmethod
    def from_dict(cls, data: dict) -> "Blockchain":
        return cls(chain=[Block.from_dict(b) for b in data["chain"]])
