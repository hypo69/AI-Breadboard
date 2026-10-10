# -*- coding: utf-8 -*-
# Updated: 2026-10-03 23:53:12
"""scanner.py – рекурсивный сканер пользовательских профилей.

Функция `scan_user_profiles` обходит директории `C:\\Users\*` (кроме
сервисных аккаунтов) и собирает информацию о потенциальных артефактах
программ: пути к файлам/директориям, расширения, даты изменения.

Возвращаемое значение – список словарей с ключами:
- `path` – абсолютный путь к найденному объекту;
- `is_dir` – `True`, если объект директория;
- `size` – размер в байтах (если файл);
- `mtime` – время последней модификации в ISO‑формате.
"""

import os
import datetime
from typing import List, Dict

def _is_service_account(name: str) -> bool:
    """Определяет, является ли каталог системным сервисным аккаунтом.
    Примеры: `Default`, `Public`, `All Users`, `Administrator`.
    """
    service_names = {"Default", "Public", "All Users", "Administrator", "systemprofile"}
    return name.lower() in {n.lower() for n in service_names}

def scan_user_profiles() -> List[Dict]:
    """Рекурсивно сканирует пользовательские каталоги.

    Returns:
        List[Dict]: список найденных артефактов.
    """
    base = r"C:\\Users"
    artifacts: List[Dict] = []
    if not os.path.isdir(base):
        return artifacts
    for entry in os.scandir(base):
        if not entry.is_dir():
            continue
        if _is_service_account(entry.name):
            continue
        for root, dirs, files in os.walk(entry.path):
            for name in files:
                fp = os.path.join(root, name)
                try:
                    stat = os.stat(fp)
                    artifacts.append({
                        "path": fp,
                        "is_dir": False,
                        "size": stat.st_size,
                        "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except OSError:
                    continue
            for name in dirs:
                dp = os.path.join(root, name)
                try:
                    stat = os.stat(dp)
                    artifacts.append({
                        "path": dp,
                        "is_dir": True,
                        "size": None,
                        "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except OSError:
                    continue
    return artifacts
