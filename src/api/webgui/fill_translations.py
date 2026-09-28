# -*- coding: utf-8 -*-
"""
Заполняет файлы локалей (en.json, he.json) переводами из CSV.

CSV‑файл должен содержать заголовки:
    key,en,he
где `key` – идентификатор строки, `en` и `he` – переводы.

Если CSV не содержит перевод для языка, оставляется пустая строка.

Для генерации шаблона `locales/template.json` (ключи с пустыми значениями) используйте опцию `--generate-template`.

Скрипт безопасно обновляет только указанные языки, не затрагивая существующие переводы.
"""

import argparse
import csv
import json
import logging
import pathlib
import sys
from typing import Dict

# Настройка логгера согласно проектным стандартам
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

LOCALES_DIR = pathlib.Path(__file__).resolve().parent / "locales"
RU_FILE = LOCALES_DIR / "ru.json"
EN_FILE = LOCALES_DIR / "en.json"
HE_FILE = LOCALES_DIR / "he.json"
TEMPLATE_FILE = LOCALES_DIR / "template.json"

def load_json(path: pathlib.Path) -> Dict[str, str]:
    """Загружает JSON‑файл и возвращает словарь.
    Если файл не существует – возвращает пустой словарь.
    """
    if not path.is_file():
        logger.warning("Файл %s не найден, создаётся пустой словарь.", path)
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: pathlib.Path, data: Dict[str, str]) -> None:
    """Сохраняет словарь в JSON‑файл с читаемым форматированием.
    """
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    logger.info("Обновлён файл %s (ключей: %d).", path.name, len(data))

def generate_template() -> None:
    """Генерирует шаблонный JSON‑файл с теми же ключами, что и ru.json, но пустыми значениями.
    """
    ru = load_json(RU_FILE)
    template = {key: "" for key in ru.keys()}
    save_json(TEMPLATE_FILE, template)
    logger.info("Создан шаблон %s с %d ключами.", TEMPLATE_FILE.name, len(template))

def fill_from_csv(csv_path: pathlib.Path) -> None:
    """Заполняет en.json и he.json переводами из CSV‑файла.
    CSV‑файл ожидает заголовки: key,en,he.
    """
    if not csv_path.is_file():
        logger.error("CSV‑файл %s не найден.", csv_path)
        sys.exit(1)

    en_data = load_json(EN_FILE)
    he_data = load_json(HE_FILE)

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("key")
            if not key:
                continue
            en_val = row.get("en", "")
            he_val = row.get("he", "")
            if en_val:
                en_data[key] = en_val
            if he_val:
                he_data[key] = he_val
            logger.debug("Обработан ключ %s", key)

    save_json(EN_FILE, en_data)
    save_json(HE_FILE, he_data)
    logger.info("Переводы из %s импортированы.", csv_path.name)

def main() -> None:
    parser = argparse.ArgumentParser(description="Заполнение локалей переводами из CSV.")
    parser.add_argument("--csv", type=pathlib.Path, help="Путь к CSV‑файлу с переводами.")
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Сгенерировать шаблон template.json из ru.json.",
    )
    args = parser.parse_args()

    if args.generate_template:
        generate_template()
        return

    if not args.csv:
        parser.error("Для заполнения переводов требуется параметр --csv.")

    fill_from_csv(args.csv)

if __name__ == "__main__":
    main()
