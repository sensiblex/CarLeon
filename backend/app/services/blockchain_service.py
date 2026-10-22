from pathlib import Path

from app.blockchain.chain import Blockchain
from app.blockchain.storage import load_chain, save_chain
from app.blockchain.transaction import DealStatus, StatusChange


class BlockchainService:
    def __init__(self, path: Path):
        self.path = path
        self.chain: Blockchain = load_chain(path)

    def record(self, deal_id: str, status: int) -> tuple[str, int]:
        tx = StatusChange(deal_id=deal_id, status=status)
        block = self.chain.add_block([tx])
        save_chain(self.chain, self.path)
        return block.hash, block.index

    def is_valid(self) -> bool:
        return self.chain.is_valid()

    def chain_dump(self) -> dict:
        return self.chain.to_dict()

    def deal_history(self, deal_id: str) -> list[dict]:
        return [tx.to_dict() for tx in self.chain.get_deal_history(deal_id)]

    def validate_status(self, status: int) -> DealStatus:
        return DealStatus(status)