# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Выполнение git-команды в корне репозитория.
# =============================================================================
# Description:
#   Скрипт автоматического отслеживания изменений в файлах репозитория
#
# File: auto_commits.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import time
import subprocess
from pathlib import Path

from src.logger import logger

ROOT = Path(__file__).resolve().parent.parent

def git(cmd: str) -> subprocess.CompletedProcess:
    """Выполнение git-команды в корне репозитория."""
    return subprocess.run(["git"] + cmd.split(), cwd=ROOT, capture_output=True, text=True, check=False)

def commit_if_dirty(message: str) -> bool:
    """Check наличия незакоммиченных изменений и создание коммита."""
    git("add -A")
    status = git("status --porcelain")
    if status.stdout and status.stdout.strip():
        git(f'commit -m "{message}"')
        logger.info(f"[auto_commits] Закоммичены изменения: {message}")
        return True
    return False

def main():
    """Основной цикл отслеживания изменений файлов."""
    logger.info("[auto_commits] Запуск службы отслеживания изменений файлов...")
    last_mtime = {}

    while True:
        changed = False
        for p in ROOT.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                try:
                    m = p.stat().st_mtime
                except OSError:
                    continue
                if p not in last_mtime:
                    last_mtime[p] = m
                    continue
                if m != last_mtime[p]:
                    logger.info(f"[auto_commits] Обнаружено изменение файла: {p}")
                    last_mtime[p] = m
                    changed = True
        if changed:
            commit_if_dirty("chore(mcp): auto-commit changes detected by MCP server")
        time.sleep(5)

if __name__ == "__main__":
    main()
