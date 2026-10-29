"""Цепочка блоков с валидацией и добавлением блоков."""
from dataclasses import dataclass, asdict

from .block import Block
from .transaction import StatusChange

GENESIS_PREVIOUS_HASH = "0" * 64

# Типы ошибок проверки цепочки
EMPTY_CHAIN = "empty_chain"
INDEX_MISMATCH = "index_mismatch"
GENESIS_PREVIOUS_HASH_MISMATCH = "genesis_previous_hash_mismatch"
BLOCK_HASH_MISMATCH = "block_hash_mismatch"
PREVIOUS_HASH_MISMATCH = "previous_hash_mismatch"
RECORD_HASH_MISMATCH = "record_hash_mismatch"
FILE_MISMATCH = "file_mismatch"
BLOCK_ALREADY_PRESENT = "block_already_present"


@dataclass
class ChainError:
    """Одна найденная проблема: где (блок, запись), что не так, что ожидали и что получили."""
    type: str
    message: str
    block_index: int | None = None
    tx_index: int | None = None
    expected: str | None = None
    actual: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class InvalidBlockError(ValueError):
    def __init__(self, errors: list[ChainError]):
        self.errors = errors
        super().__init__("; ".join(error.message for error in errors))


class Blockchain:
    def __init__(self, chain: list[Block] | None = None):
        self.chain: list[Block] = chain if chain else [self.create_genesis_block()]

    @staticmethod
    def create_genesis_block() -> Block:
        block = Block(
            index=0,
            transactions=[StatusChange(deal_id="genesis", status=0, timestamp=0.0)],
            previous_hash=GENESIS_PREVIOUS_HASH,
            timestamp=0.0,
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

    def validate_next_block(self, block: Block) -> list[ChainError]:
        """Check a peer block without changing local state."""
        errors = self.validate()
        if errors:
            return errors

        if any(existing.hash == block.hash for existing in self.chain):
            return [ChainError(
                BLOCK_ALREADY_PRESENT,
                f"блок с хэшем {block.hash} уже есть в цепочке",
                block_index=block.index,
                actual=block.hash,
            )]

        expected_index = len(self.chain)
        if block.index != expected_index:
            errors.append(ChainError(
                INDEX_MISMATCH,
                f"ожидался блок с index={expected_index}, получен {block.index}",
                block_index=block.index,
                expected=str(expected_index),
                actual=str(block.index),
            ))

        expected_previous_hash = self.last_block.hash
        if block.previous_hash != expected_previous_hash:
            errors.append(ChainError(
                PREVIOUS_HASH_MISMATCH,
                "previous_hash блока не совпадает с хэшем последнего локального блока",
                block_index=block.index,
                expected=expected_previous_hash,
                actual=block.previous_hash,
            ))

        recalculated_hash = block.calculate_hash()
        if block.hash != recalculated_hash:
            errors.append(ChainError(
                BLOCK_HASH_MISMATCH,
                "хэш полученного блока не совпадает с пересчитанным",
                block_index=block.index,
                expected=recalculated_hash,
                actual=block.hash,
            ))

        for tx_index, tx in enumerate(block.transactions):
            expected_content_hash = tx.calculate_content_hash()
            if tx.content_hash != expected_content_hash:
                errors.append(ChainError(
                    RECORD_HASH_MISMATCH,
                    f"содержимое записи {tx_index} не совпадает с её хэшем",
                    block_index=block.index,
                    tx_index=tx_index,
                    expected=expected_content_hash,
                    actual=tx.content_hash,
                ))
        return errors

    def append_peer_block(self, block: Block) -> None:
        errors = self.validate_next_block(block)
        if errors:
            raise InvalidBlockError(errors)
        self.chain.append(block)

    # ---------- проверка целостности ----------

    def validate(self) -> list[ChainError]:
        """Полная проверка цепочки. Пустой список = цепочка валидна.

        Проверяется для каждого блока (по порядку от генезиса):
          1. index равен позиции блока;
          2. у генезиса previous_hash состоит из нулей;
          3. хэш блока совпадает с пересчитанным;
          4. previous_hash совпадает с хэшем предыдущего блока (цепочка не разорвана);
          5. content_hash каждой записи совпадает с пересчитанным.
        Внешние файлы проверяет отдельно verify_files().
        """
        if not self.chain:
            return [ChainError(EMPTY_CHAIN, "цепочка пуста: нет даже генезис-блока")]

        errors: list[ChainError] = []
        for i, block in enumerate(self.chain):
            if block.index != i:
                errors.append(ChainError(
                    INDEX_MISMATCH, f"блок {i}: index={block.index}, ожидался {i}",
                    block_index=i, expected=str(i), actual=str(block.index)))

            if i == 0 and block.previous_hash != GENESIS_PREVIOUS_HASH:
                errors.append(ChainError(
                    GENESIS_PREVIOUS_HASH_MISMATCH,
                    "блок 0 (генезис): previous_hash не состоит из нулей",
                    block_index=0, expected=GENESIS_PREVIOUS_HASH, actual=block.previous_hash))

            recalculated = block.calculate_hash()
            if block.hash != recalculated:
                errors.append(ChainError(
                    BLOCK_HASH_MISMATCH,
                    f"блок {i}: сохранённый хэш не совпадает с пересчитанным",
                    block_index=i, expected=recalculated, actual=block.hash))

            if i > 0 and block.previous_hash != self.chain[i - 1].hash:
                errors.append(ChainError(
                    PREVIOUS_HASH_MISMATCH,
                    f"блок {i}: previous_hash не совпадает с хэшем блока {i - 1} (цепочка разорвана)",
                    block_index=i, expected=self.chain[i - 1].hash, actual=block.previous_hash))

            for j, tx in enumerate(block.transactions):
                expected = tx.calculate_content_hash()
                if tx.content_hash != expected:
                    errors.append(ChainError(
                        RECORD_HASH_MISMATCH,
                        f"блок {i}, запись {j}: содержимое не совпадает с её хэшем",
                        block_index=i, tx_index=j, expected=expected, actual=tx.content_hash))
        return errors

    def find_break(self) -> ChainError | None:
        """Первая точка разрыва (самый ранний блок с проблемой) или None, если цепочка валидна."""
        errors = self.validate()
        return errors[0] if errors else None

    def is_valid(self) -> bool:
        return not self.validate()

    def verify_files(self) -> list[ChainError]:
        """Сверить реальные файлы с хэшами в записях. Пустой список = все файлы на месте и не изменены."""
        errors: list[ChainError] = []
        for i, block in enumerate(self.chain):
            for j, tx in enumerate(block.transactions):
                ok, reason = tx.verify_file()
                if not ok:
                    errors.append(ChainError(
                        FILE_MISMATCH, f"блок {i}, запись {j}: {reason}",
                        block_index=i, tx_index=j, expected=tx.file_hash))
        return errors

    # ---------- прочее ----------

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