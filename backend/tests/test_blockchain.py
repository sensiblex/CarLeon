import json

import pytest

from app.blockchain import Block, Blockchain, StatusChange
from app.blockchain import chain as chain_module
from app.blockchain.storage import ChainLoadError, load_chain, save_chain
from app.blockchain.transaction import hash_file


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


def make_chain(n=3):
    """Цепочка: генезис + n блоков с разными статусами."""
    bc = Blockchain()
    for i in range(1, n + 1):
        bc.add_block([make_tx(status=i)])
    return bc


class TestRecordHash:
    def test_content_hash_is_set_on_creation(self):
        tx = make_tx()
        assert len(tx.content_hash) == 64
        assert tx.is_content_valid()

    def test_changing_status_breaks_content_hash(self):
        tx = make_tx()
        tx.status = 2
        assert not tx.is_content_valid()

    def test_changing_deal_id_breaks_content_hash(self):
        tx = make_tx()
        tx.deal_id = "other"
        assert not tx.is_content_valid()

    def test_missing_content_hash_in_dict_is_detected(self):
        data = make_tx().to_dict()
        del data["content_hash"]
        assert not StatusChange.from_dict(data).is_content_valid()

    def test_roundtrip_keeps_file_fields(self):
        tx = StatusChange(deal_id="d", status=3, file_path="a.pdf", file_hash="ff")
        assert StatusChange.from_dict(tx.to_dict()) == tx


class TestValidate:
    def test_valid_chain_has_no_errors(self):
        bc = make_chain()
        assert bc.validate() == []
        assert bc.find_break() is None

    def test_tampered_record_is_located(self):
        bc = make_chain()
        bc.chain[2].transactions[0].status = 9
        err = bc.find_break()
        assert err.block_index == 2
        assert err.type == chain_module.BLOCK_HASH_MISMATCH
        types = {(e.type, e.block_index, e.tx_index) for e in bc.validate()}
        assert (chain_module.RECORD_HASH_MISMATCH, 2, 0) in types

    def test_record_hash_mismatch_when_block_hash_recomputed(self):
        # злоумышленник подменил запись и пересчитал хэш блока, но не хэш записи
        bc = make_chain()
        bc.chain[1].transactions[0].status = 9
        bc.chain[1].hash = bc.chain[1].calculate_hash()
        errors = bc.validate()
        assert (errors[0].type, errors[0].block_index) == (chain_module.RECORD_HASH_MISMATCH, 1)
        # блок 2 ссылается на старый хэш блока 1 -> разрыв виден и там
        assert any(e.type == chain_module.PREVIOUS_HASH_MISMATCH and e.block_index == 2 for e in errors)

    def test_tampered_block_hash_is_located(self):
        bc = make_chain()
        bc.chain[1].hash = "f" * 64
        errors = bc.validate()
        assert errors[0].type == chain_module.BLOCK_HASH_MISMATCH
        assert errors[0].block_index == 1
        # следующий блок ссылается на старый хэш -> разрыв связи виден в блоке 2
        assert any(e.type == chain_module.PREVIOUS_HASH_MISMATCH and e.block_index == 2 for e in errors)

    def test_broken_link_is_located(self):
        bc = make_chain()
        bc.chain[2].previous_hash = "deadbeef"
        bc.chain[2].hash = bc.chain[2].calculate_hash()
        err = bc.find_break()
        assert err.type == chain_module.PREVIOUS_HASH_MISMATCH
        assert err.block_index == 2
        assert err.expected == bc.chain[1].hash
        assert err.actual == "deadbeef"

    def test_genesis_previous_hash_must_be_zeros(self):
        bc = make_chain()
        bc.chain[0].previous_hash = "1" * 64
        bc.chain[0].hash = bc.chain[0].calculate_hash()
        types = [e.type for e in bc.validate()]
        assert chain_module.GENESIS_PREVIOUS_HASH_MISMATCH in types

    def test_wrong_index_is_detected(self):
        bc = make_chain()
        bc.chain[1].index = 5
        bc.chain[1].hash = bc.chain[1].calculate_hash()
        assert any(e.type == chain_module.INDEX_MISMATCH and e.block_index == 1 for e in bc.validate())

    def test_empty_chain_is_invalid(self):
        bc = make_chain()
        bc.chain = []
        assert [e.type for e in bc.validate()] == [chain_module.EMPTY_CHAIN]
        assert not bc.is_valid()

    def test_errors_are_json_serializable(self):
        bc = make_chain()
        bc.chain[1].hash = "f" * 64
        json.dumps([e.to_dict() for e in bc.validate()])


class TestExternalFile:
    def test_transaction_without_file_is_ok(self):
        ok, _ = make_tx().verify_file()
        assert ok

    def test_unchanged_file_passes(self, tmp_path):
        f = tmp_path / "contract.txt"
        f.write_text("договор")
        tx = StatusChange(deal_id="d", status=3, file_path=str(f), file_hash=hash_file(f))
        assert tx.verify_file()[0]

    def test_modified_file_fails(self, tmp_path):
        f = tmp_path / "contract.txt"
        f.write_text("договор")
        tx = StatusChange(deal_id="d", status=3, file_path=str(f), file_hash=hash_file(f))
        f.write_text("договор (изменён)")
        ok, reason = tx.verify_file()
        assert not ok and "хэш файла" in reason

    def test_missing_file_fails(self, tmp_path):
        f = tmp_path / "contract.txt"
        f.write_text("x")
        tx = StatusChange(deal_id="d", status=3, file_path=str(f), file_hash=hash_file(f))
        f.unlink()
        ok, reason = tx.verify_file()
        assert not ok and "не найден" in reason

    def test_only_one_of_path_and_hash_fails(self):
        tx = StatusChange(deal_id="d", status=3, file_path="a.txt")
        assert not tx.verify_file()[0]

    def test_chain_verify_files_points_to_block(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("v1")
        bc = Blockchain()
        bc.add_block([make_tx()])
        bc.add_block([StatusChange(deal_id="d", status=3, file_path=str(f), file_hash=hash_file(f))])
        assert bc.verify_files() == []
        f.write_text("v2")
        errors = bc.verify_files()
        assert len(errors) == 1
        assert (errors[0].type, errors[0].block_index, errors[0].tx_index) == (
            chain_module.FILE_MISMATCH, 2, 0)


class TestStorageErrors:
    def test_broken_json_raises_readable_error(self, tmp_path):
        path = tmp_path / "b.json"
        path.write_text("{oops")
        with pytest.raises(ChainLoadError, match="JSON"):
            load_chain(path)

    def test_empty_chain_in_file_raises(self, tmp_path):
        path = tmp_path / "b.json"
        path.write_text(json.dumps({"chain": []}))
        with pytest.raises(ChainLoadError):
            load_chain(path)

    def test_missing_field_raises(self, tmp_path):
        path = tmp_path / "b.json"
        path.write_text(json.dumps({"chain": [{"index": 0}]}))
        with pytest.raises(ChainLoadError, match="формат"):
            load_chain(path)

    def test_invalid_status_in_file_raises_load_error(self, tmp_path):
        path = tmp_path / "b.json"
        bc = make_chain(1)
        save_chain(bc, path)
        data = json.loads(path.read_text())
        data["chain"][1]["transactions"][0]["status"] = 77
        path.write_text(json.dumps(data))
        with pytest.raises(ChainLoadError):
            load_chain(path)

    def test_tampered_file_message_names_block(self, tmp_path):
        path = tmp_path / "b.json"
        save_chain(make_chain(2), path)
        data = json.loads(path.read_text())
        data["chain"][2]["transactions"][0]["status"] = 9
        path.write_text(json.dumps(data))
        with pytest.raises(ChainLoadError, match="блок 2"):
            load_chain(path)

    def test_load_error_is_value_error(self):
        assert issubclass(ChainLoadError, ValueError)

    def test_save_leaves_no_temp_files(self, tmp_path):
        path = tmp_path / "b.json"
        save_chain(make_chain(1), path)
        save_chain(make_chain(2), path)
        assert [p.name for p in tmp_path.iterdir()] == ["b.json"]