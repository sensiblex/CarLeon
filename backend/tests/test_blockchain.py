from app.blockchain.chain import Blockchain
from app.blockchain.transaction import StatusChange


def test_chain_valid_after_add():
    chain = Blockchain()
    chain.add_block([StatusChange(deal_id="deal-1", status=1)])
    assert chain.is_valid()


def test_chain_invalid_after_tamper():
    chain = Blockchain()
    chain.add_block([StatusChange(deal_id="deal-1", status=1)])
    chain.chain[1].transactions[0].status = 9
    assert not chain.is_valid()