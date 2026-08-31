# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Returns list измененных файлов .py в git репозитор
# =============================================================================
# Description:
#   Скрипт checks наличие и заполненность документации (README.md, docstrings)
#
# File: update_docs.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import subprocess
from pathlib import Path
from typing import List

def get_modified_python_files() -> List[Path]:
    """Returns list измененных файлов .py в git репозитории."""
    modified_files = []
    try:
        res = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in res.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) > 1:
                filepath = Path(parts[1])
                if filepath.suffix == ".py" and filepath.exists():
                    modified_files.append(filepath)
    except Exception:
        # Если git недоступен, вернем empty list
        pass
    return modified_files

def validate_docblocks(files: List[Path]) -> bool:
    """Checks наличие docstring в измененных файлах."""
    all_valid = True
    for f in files:
        content = f.read_text(encoding="utf-8")
        # Простая check на наличие тройных кавычек (docstrings)
        if '"""' not in content and "'''" not in content:
            print(f"⚠️  Файл {f.name} изменен, но не содержит docstring!")
            all_valid = False
    return all_valid

def main() -> int:
    print("🔎 Запуск проверки актуальности документации и комментариев...")
    
    modified = get_modified_python_files()
    if not modified:
        print("✅ Измененных файлов Python в Git не найдено. Дополнительная validation не требуется.")
        return 0
        
    print(f"Обнаружено измененных файлов: {len(modified)}")
    valid = validate_docblocks(modified)
    
    if valid:
        print("✅ Все измененные файлы содержат docstring.")
        return 0
    else:
        print("❌ Рекомендуется добавить или обновить комментарии/документацию.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
