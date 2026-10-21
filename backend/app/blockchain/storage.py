"""Сохранение цепочки в JSON и загрузка при старте."""
import json
import os
import tempfile
from pathlib import Path

from .chain import Blockchain

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "blockchain.json"


class ChainLoadError(ValueError):
    """Файл цепочки нельзя загрузить: битый JSON, неверный формат или нарушена целостность."""


def save_chain(blockchain: Blockchain, path: Path = DEFAULT_PATH) -> None:
    """Атомарная запись: пишем во временный файл рядом и переименовываем.

    Если процесс упадёт посреди записи, старый файл останется целым.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(blockchain.to_dict(), f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def load_chain(path: Path = DEFAULT_PATH) -> Blockchain:
    if not path.exists():
        return Blockchain()

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ChainLoadError(f"Файл {path} не является корректным JSON: {e}") from e

    if not isinstance(data, dict) or not data.get("chain"):
        raise ChainLoadError(f"Файл {path}: в данных нет цепочки блоков")

    try:
        blockchain = Blockchain.from_dict(data)
    except (KeyError, TypeError, ValueError) as e:
        raise ChainLoadError(
            f"Файл {path}: неверный формат данных ({type(e).__name__}: {e})"
        ) from e

    errors = blockchain.validate()
    if errors:
        first = errors[0]
        raise ChainLoadError(
            f"Цепочка в {path} повреждена. Первая проблема: {first.message}. "
            f"Всего проблем: {len(errors)}"
        )
    return blockchain