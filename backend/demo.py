"""Демонстрация блокчейна CarLeon: 7 сценариев релиза.

Запуск из папки backend:
    python demo.py            - с паузами (Enter между сценариями)
    python demo.py --auto     - без пауз
    python demo.py --full     - показывать хэши целиком (по умолчанию - сокращённо)

Данные демо лежат в backend/data/demo/ (папка в .gitignore, на рабочие данные не влияет).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from app.blockchain import Blockchain, StatusChange
from app.blockchain.storage import ChainLoadError, load_chain, save_chain
from app.blockchain.transaction import DealStatus, hash_file

DEMO_DIR = Path(__file__).resolve().parent / "data" / "demo"
CHAIN_PATH = DEMO_DIR / "blockchain.json"
FILE_PATH = DEMO_DIR / "contract.txt"

USE_COLOR = sys.stdout.isatty()
FULL_HASHES = False


# ---------- оформление вывода ----------

def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return c(t, "32")
def red(t): return c(t, "31;1")
def yellow(t): return c(t, "33")
def dim(t): return c(t, "2")
def bold(t): return c(t, "1")


def short(h: str | None) -> str:
    if h is None:
        return "-"
    return h if FULL_HASHES or len(h) <= 16 else h[:16] + "…"


def title(n: int, text: str) -> None:
    print()
    print(bold(f"━━━ Сценарий {n}. {text} ━━━"))


def print_block(block) -> None:
    print(f"  Блок #{block.index}")
    print(f"    hash:          {yellow(short(block.hash))}")
    print(f"    previous_hash: {short(block.previous_hash)}")
    for tx in block.transactions:
        status = DealStatus(tx.status)
        line = f"    запись: сделка={tx.deal_id}, статус={int(status)} ({status.name})"
        print(line)
        print(f"            content_hash={short(tx.content_hash)}")
        if tx.file_path:
            print(f"            файл={Path(tx.file_path).name}, file_hash={short(tx.file_hash)}")


def print_links(bc: Blockchain) -> None:
    """Показать связи между блоками: previous_hash каждого блока = hash предыдущего."""
    for i in range(1, len(bc.chain)):
        prev, cur = bc.chain[i - 1], bc.chain[i]
        same = cur.previous_hash == prev.hash
        mark = green("совпадает ✓") if same else red("НЕ совпадает ✗")
        print(f"  Блок #{i}.previous_hash  ↔  Блок #{i - 1}.hash: {mark}")


def print_errors(errors) -> None:
    if not errors:
        print(green("  Ошибок нет: цепочка целая."))
        return
    first = errors[0]
    print(red(f"  ✗ Цепочка НЕВАЛИДНА. Всего проблем: {len(errors)}"))
    print(red(f"  Точка разрыва: блок #{first.block_index}, причина: {first.type}"))
    for e in errors:
        print(f"   - {e.message}")
        if e.expected is not None or e.actual is not None:
            print(dim(f"       ожидалось: {short(e.expected)}"))
            print(dim(f"       получено:  {short(e.actual)}"))


def pause(auto: bool) -> None:
    if not auto:
        input(dim("\n[Enter - следующий сценарий] "))


def tamper(mutator) -> str:
    """Изменить сохранённый JSON-файл (как это сделал бы злоумышленник). Возвращает исходный текст."""
    original = CHAIN_PATH.read_text(encoding="utf-8")
    data = json.loads(original)
    mutator(data)
    CHAIN_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return original


def diagnose_file() -> list:
    """Прочитать файл как есть (без отказа от загрузки) и получить отчёт о проблемах."""
    data = json.loads(CHAIN_PATH.read_text(encoding="utf-8"))
    return Blockchain.from_dict(data).validate()


def try_load() -> None:
    try:
        load_chain(CHAIN_PATH)
        print(red("  Программа загрузила повреждённую цепочку - так быть не должно!"))
    except ChainLoadError as e:
        print(green("  Программа отказалась загружать повреждённый файл:"))
        print(f"    {e}")


# ---------- сценарии ----------

def scenario_1() -> Blockchain:
    title(1, "Создание нового блокчейна с генезис-блоком")
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True)
    bc = Blockchain()
    print("  Создан новый блокчейн. В нём один блок - генезис:")
    print_block(bc.chain[0])
    print(f"  У генезиса previous_hash состоит из нулей: {bc.chain[0].previous_hash == '0' * 64}")
    return bc


def scenario_2(bc: Blockchain) -> None:
    title(2, "Добавление записей и блоков, хэши и связи между блоками")
    bc.add_block([StatusChange("deal-1", DealStatus.ORDER_CREATED)])
    bc.add_block([
        StatusChange("deal-1", DealStatus.DEPOSIT_PAID),
        StatusChange("deal-2", DealStatus.ORDER_CREATED),
    ])
    bc.add_block([StatusChange("deal-1", DealStatus.PURCHASED)])
    print("  Добавлено 3 блока (во втором - две записи):")
    for block in bc.chain[1:]:
        print_block(block)
    print()
    print("  Связи между блоками:")
    print_links(bc)
    print(f"\n  История сделки deal-1: "
          f"{[DealStatus(t.status).name for t in bc.get_deal_history('deal-1')]}")


def scenario_3(bc: Blockchain, python: str) -> None:
    title(3, "Сохранение, перезапуск программы и восстановление цепочки")
    save_chain(bc, CHAIN_PATH)
    print(f"  Цепочка сохранена в {CHAIN_PATH.relative_to(Path(__file__).parent)}"
          f" ({CHAIN_PATH.stat().st_size} байт). Программа 'закрывается'...")
    print("  Запускаем программу заново (отдельный процесс):")
    out = subprocess.run(
        [python, __file__, "--show", str(CHAIN_PATH)] + (["--full"] if FULL_HASHES else []),
        capture_output=True, text=True, cwd=Path(__file__).parent,
    )
    print("".join("    " + line + "\n" for line in out.stdout.splitlines()), end="")
    if out.returncode != 0:
        print(red(out.stderr))


def scenario_4() -> None:
    title(4, "Проверка валидности корректного блокчейна")
    bc = load_chain(CHAIN_PATH)
    print("  Проверяем: хэш каждого блока, связь с предыдущим блоком, хэш каждой записи.")
    print_errors(bc.validate())


def scenario_5() -> None:
    title(5, "Изменение содержимого записи: обнаружение нарушения")

    def mutator(data):
        tx = data["chain"][2]["transactions"][0]
        print(f"  Злоумышленник правит файл: блок #2, запись 0: "
              f"статус {tx['status']} -> 9 (COMPLETED)")
        tx["status"] = 9

    original = tamper(mutator)
    try:
        print()
        try_load()
        print()
        print("  Диагностика (что именно не сходится):")
        print_errors(diagnose_file())
    finally:
        CHAIN_PATH.write_text(original, encoding="utf-8")
        print(dim("\n  (файл восстановлен для следующих сценариев)"))


def scenario_6() -> None:
    title(6, "Изменение хэша предыдущего блока: обнаружение разрыва цепочки")

    def mutator(data):
        old = data["chain"][1]["hash"]
        data["chain"][1]["hash"] = "0" * 63 + "1"
        print(f"  Злоумышленник правит файл: хэш блока #1 {short(old)} -> {short(data['chain'][1]['hash'])}")

    original = tamper(mutator)
    try:
        print()
        try_load()
        print()
        print("  Диагностика (что именно не сходится):")
        print_errors(diagnose_file())
    finally:
        CHAIN_PATH.write_text(original, encoding="utf-8")
        print(dim("\n  (файл восстановлен)"))


def scenario_7() -> None:
    title(7, "Проверка внешнего файла: изменение содержимого после записи")
    FILE_PATH.write_text("Договор №1. Сумма: 1 000 000 руб.\n", encoding="utf-8")
    bc = load_chain(CHAIN_PATH)
    bc.add_block([StatusChange(
        "deal-1", DealStatus.CUSTOMS,
        file_path=str(FILE_PATH), file_hash=hash_file(FILE_PATH),
    )])
    save_chain(bc, CHAIN_PATH)
    print(f"  Создан файл {FILE_PATH.name} и добавлена запись, в которой сохранён его хэш:")
    print_block(bc.chain[-1])

    print("\n  Сверяем реальный файл с хэшем в записи:")
    errors = bc.verify_files()
    print(green("  Файл не менялся, хэш совпадает ✓") if not errors else red("  Проблема!"))

    FILE_PATH.write_text("Договор №1. Сумма: 10 000 000 руб.\n", encoding="utf-8")
    print(yellow("\n  Файл изменили: сумма 1 000 000 -> 10 000 000. Сверяем снова:"))
    errors = bc.verify_files()
    if errors:
        e = errors[0]
        print(red(f"  ✗ Файл подменён: блок #{e.block_index}, запись {e.tx_index}, причина: {e.type}"))
        print(f"   - {e.message}")
    else:
        print(red("  Подмена не обнаружена - так быть не должно!"))

    print("\n  Сама цепочка при этом остаётся целой (файл лежит вне цепочки):")
    print_errors(bc.validate())


def show_loaded(path: Path) -> None:
    """Служебный режим: загрузить цепочку из файла и вывести краткую сводку (имитация перезапуска)."""
    bc = load_chain(path)
    print(f"Файл прочитан, цепочка восстановлена: блоков - {len(bc.chain)}")
    for b in bc.chain:
        txs = ", ".join(f"{t.deal_id}:{int(t.status)}" for t in b.transactions)
        print(f"  блок #{b.index}  hash={short(b.hash)}  записи: {txs}")
    print(f"Целостность при загрузке проверена: {'OK' if bc.is_valid() else 'ОШИБКА'}")


def main() -> None:
    global FULL_HASHES
    parser = argparse.ArgumentParser(description="Демо блокчейна CarLeon")
    parser.add_argument("--auto", action="store_true", help="без пауз между сценариями")
    parser.add_argument("--full", action="store_true", help="показывать хэши целиком")
    parser.add_argument("--show", metavar="PATH", help="(служебный) загрузить цепочку и показать")
    args = parser.parse_args()
    FULL_HASHES = args.full

    if args.show:
        show_loaded(Path(args.show))
        return

    print(bold("CarLeon: демонстрация блокчейна"))
    bc = scenario_1()
    pause(args.auto)
    scenario_2(bc)
    pause(args.auto)
    scenario_3(bc, sys.executable)
    pause(args.auto)
    scenario_4()
    pause(args.auto)
    scenario_5()
    pause(args.auto)
    scenario_6()
    pause(args.auto)
    scenario_7()
    print()
    print(green(bold("Демо завершено: все 7 сценариев пройдены.")))


if __name__ == "__main__":
    main()