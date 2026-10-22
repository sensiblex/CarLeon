from pathlib import Path

from app.blockchain.chain import Blockchain
from app.blockchain.storage import load_chain, save_chain
from app.blockchain.transaction import DealStatus, StatusChange, hash_file


class BlockchainService:
    def __init__(self, path: Path):
        self.path = path
        self.chain: Blockchain = load_chain(path)

    def record(
        self, deal_id: str, status: int, file_path: str | None = None
    ) -> tuple[str, int]:
        """Добавить запись о смене статуса (опционально - с привязкой внешнего файла).

        Raises:
            ValueError: недопустимый статус.
            FileNotFoundError: указанный файл не существует.
        """
        file_hash = None
        if file_path is not None:
            if not Path(file_path).is_file():
                raise FileNotFoundError(file_path)
            file_hash = hash_file(file_path)
        tx = StatusChange(
            deal_id=deal_id, status=status, file_path=file_path, file_hash=file_hash
        )
        block = self.chain.add_block([tx])
        save_chain(self.chain, self.path)
        return block.hash, block.index

    def is_valid(self) -> bool:
        return self.chain.is_valid()

    def validate(self) -> dict:
        """Подробный отчёт о проверке: valid, первая точка разрыва и все ошибки."""
        errors = self.chain.validate()
        return {
            "valid": not errors,
            "first_break": errors[0].to_dict() if errors else None,
            "errors": [e.to_dict() for e in errors],
        }

    def verify_files(self) -> dict:
        """Сверка реальных файлов с хэшами, сохранёнными в записях."""
        errors = self.chain.verify_files()
        return {"valid": not errors, "errors": [e.to_dict() for e in errors]}

    def chain_dump(self) -> dict:
        return self.chain.to_dict()

    def deal_history(self, deal_id: str) -> list[dict]:
        return [tx.to_dict() for tx in self.chain.get_deal_history(deal_id)]

    def validate_status(self, status: int) -> DealStatus:
        return DealStatus(status)