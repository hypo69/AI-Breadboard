# -*- coding: utf-8 -*-
"""
Синхронізує файли локалей: `en.json` і `he.json` отримують значення з `ru.json`,
якщо у них порожні рядки або відсутні ключі.

Тільки ті ключі, які вже існують у `ru.json`, будуть скопійовані.
Це гарантує, що переклади не будуть втрачені і в інших файлах буде
хоча б оригінальний російський текст (потім його можна замінити).
"""

import json
import pathlib
import sys
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

LOCALES_DIR = pathlib.Path(__file__).resolve().parent / "locales"
RU_FILE = LOCALES_DIR / "ru.json"
EN_FILE = LOCALES_DIR / "en.json"
HE_FILE = LOCALES_DIR / "he.json"

def load(path: pathlib.Path) -> dict:
    if not path.is_file():
        logger.warning("Файл %s не найден, будет создан пустой.", path.name)
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save(path: pathlib.Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    logger.info("Сохранён %s (ключей: %d)", path.name, len(data))

def sync():
    ru = load(RU_FILE)
    en = load(EN_FILE)
    he = load(HE_FILE)
    updated = 0
    for key, ru_val in ru.items():
        # EN
        if key not in en or not isinstance(en[key], str) or not en[key].strip():
            en[key] = ru_val
            updated += 1
        # HE
        if key not in he or not isinstance(he[key], str) or not he[key].strip():
            he[key] = ru_val
            updated += 1
    logger.info("Обновлено %d записей в en.json и he.json", updated)
    save(EN_FILE, en)
    save(HE_FILE, he)

if __name__ == "__main__":
    sync()
