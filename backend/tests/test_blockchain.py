import pytest

from app.blockchain import Block, Blockchain, StatusChange
from app.blockchain.storage import load_chain, save_chain


def make_tx(deal_id="deal-1", status=1):
    return StatusChange(deal_id=deal_id, status=status)


class TestStatusChange:
    def test_valid_status(self):
        tx = make_tx(status=9)
        assert tx.deal_id == "deal-1"
        assert tx.status == 9
        assert tx.timestamp > 0

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            make_tx(status=10)

    def test_roundtrip_dict(self):
        tx = make_tx()
        assert StatusChange.from_dict(tx.to_dict()) == tx


class TestBlock:
    def test_hash_is_deterministic(self):
        block = Block(index=1, transactions=[make_tx()], previous_hash="abc", timestamp=123.0)
        assert block.calculate_hash() == block.calculate_hash()
        assert len(block.calculate_hash()) == 64

    def test_hash_depends_on_content(self):
        b1 = Block(index=1, transactions=[make_tx()], previous_hash="abc", timestamp=123.0)
        b2 = Block(index=1, transactions=[make_tx(status=2)], previous_hash="abc", timestamp=123.0)
        assert b1.calculate_hash() != b2.calculate_hash()

    def test_roundtrip_dict(self):
        block = Block(index=2, transactions=[make_tx()], previous_hash="abc")
        block.hash = block.calculate_hash()
        restored = Block.from_dict(block.to_dict())
        assert restored.to_dict() == block.to_dict()


class TestBlockchain:
    def test_genesis_created_on_init(self):
        bc = Blockchain()
        assert len(bc.chain) == 1
        assert bc.chain[0].index == 0
        assert bc.chain[0].previous_hash == "0" * 64
        assert bc.is_valid()

    def test_add_block_links_hashes(self):
        bc = Blockchain()
        block = bc.add_block([make_tx()])
        assert block.index == 1
        assert block.previous_hash == bc.chain[0].hash
        assert bc.is_valid()

    def test_tampered_block_invalidates_chain(self):
        bc = Blockchain()
        bc.add_block([make_tx()])
        bc.chain[1].transactions[0].status = 9
        assert not bc.is_valid()

    def test_broken_link_invalidates_chain(self):
        bc = Blockchain()
        bc.add_block([make_tx()])
        bc.add_block([make_tx(status=2)])
        bc.chain[2].previous_hash = "deadbeef"
        assert not bc.is_valid()

    def test_get_deal_history(self):
        bc = Blockchain()
        bc.add_block([make_tx(deal_id="d1", status=1), make_tx(deal_id="d2", status=1)])
        bc.add_block([make_tx(deal_id="d1", status=2)])
        history = bc.get_deal_history("d1")
        assert [tx.status for tx in history] == [1, 2]


class TestStorage:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "blockchain.json"
        bc = Blockchain()
        bc.add_block([make_tx()])
        save_chain(bc, path)

        loaded = load_chain(path)
        assert loaded.to_dict() == bc.to_dict()
        assert loaded.is_valid()

    def test_load_missing_file_creates_genesis(self, tmp_path):
        bc = load_chain(tmp_path / "missing.json")
        assert len(bc.chain) == 1
        assert bc.is_valid()

    def test_load_corrupted_chain_raises(self, tmp_path):
        path = tmp_path / "blockchain.json"
        bc = Blockchain()
        bc.add_block([make_tx()])
        save_chain(bc, path)

        bc.chain[1].transactions[0].status = 9
        save_chain(bc, path)
        with pytest.raises(ValueError):
            load_chain(path)
