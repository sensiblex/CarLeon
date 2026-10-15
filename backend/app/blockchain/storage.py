"""Сохранение цепочки в JSON и загрузка при старте."""
import json
from pathlib import Path

from .chain import Blockchain

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "blockchain.json"


def save_chain(blockchain: Blockchain, path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(blockchain.to_dict(), f, ensure_ascii=False, indent=2)


def load_chain(path: Path = DEFAULT_PATH) -> Blockchain:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            blockchain = Blockchain.from_dict(json.load(f))
        if not blockchain.is_valid():
            raise ValueError(f"Цепочка в {path} повреждена: хэши не совпадают")
        return blockchain
    return Blockchain()
