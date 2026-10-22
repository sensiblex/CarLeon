"""Запись в блокчейне - событие смены статуса сделки."""
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from pathlib import Path


class DealStatus(IntEnum):
    PUBLISHED = 0
    ORDER_CREATED = 1
    DEPOSIT_PAID = 2
    PURCHASED = 3
    IN_TRANSIT_ORIGIN = 4
    CUSTOMS = 5
    IN_TRANSIT_RF = 6
    DELIVERED_CITY = 7
    READY_FOR_PICKUP = 8
    COMPLETED = 9


def hash_file(path: str | Path) -> str:
    """SHA-256 содержимого файла (читаем кусками, файл может быть большим)."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


@dataclass
class StatusChange:
    deal_id: str
    status: DealStatus
    timestamp: float = field(default_factory=time.time)
    # Необязательный внешний файл (договор, ПТС, акт и т.п.):
    file_path: str | None = None
    file_hash: str | None = None
    # None - посчитать при создании; "" или чужое значение - останется как есть
    # и будет найдено проверкой (так подмену содержимого видно).
    content_hash: str | None = None

    def __post_init__(self):
        self.status = DealStatus(self.status)
        if self.content_hash is None:
            self.content_hash = self.calculate_content_hash()

    def calculate_content_hash(self) -> str:
        """Хэш содержимого записи (без самого поля content_hash)."""
        payload = {
            "deal_id": self.deal_id,
            "status": self.status,
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def is_content_valid(self) -> bool:
        return self.content_hash == self.calculate_content_hash()

    def verify_file(self) -> tuple[bool, str]:
        """Сверить реальный файл с file_hash из записи.

        Возвращает (ok, причина). Если файл к записи не привязан - ok.
        """
        if self.file_path is None and self.file_hash is None:
            return True, "файл не привязан"
        if self.file_path is None or self.file_hash is None:
            return False, "в записи указан только один из file_path / file_hash"
        path = Path(self.file_path)
        if not path.is_file():
            return False, f"файл не найден: {self.file_path}"
        actual = hash_file(path)
        if actual != self.file_hash:
            return False, f"хэш файла не совпадает: ожидался {self.file_hash}, получен {actual}"
        return True, "ok"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StatusChange":
        return cls(
            deal_id=data["deal_id"],
            status=data["status"],
            timestamp=data["timestamp"],
            file_path=data.get("file_path"),
            file_hash=data.get("file_hash"),
            # отсутствие поля = "" -> проверка целостности покажет несоответствие
            content_hash=data.get("content_hash", ""),
        )