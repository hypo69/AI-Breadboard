# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: File Recovery (R-Studio) Router
# =============================================================================
# Description:
#   FastAPI роутер для запуска и проверки статуса утилиты восстановления
#   удаленных файлов R-Studio Technician Portable:
#   - Проверка наличия исполняемого файла в \bin\R-Studio_Technician_9.5.191810_Portable\R-Studio_9.5.exe
#   - Запуск процесса R-Studio в среде Windows
#   - Мониторинг статуса выполнения программы
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from src.api.router_recovery import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router_recovery.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для управления и запуска утилиты восстановления файлов R-Studio."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from header import __root__
from logger import logger

# Относительный и абсолютный путь к R-Studio Portable
RSTUDIO_RELATIVE_PATH = Path("bin") / "R-Studio_Technician_9.5.191810_Portable" / "R-Studio_9.5.exe"
RSTUDIO_EXE = __root__ / RSTUDIO_RELATIVE_PATH


def _check_rstudio_exists() -> bool:
    """Проверяет существование исполняемого файла R-Studio.

    Returns:
        bool: True, если файл существует на диске.
    """
    return RSTUDIO_EXE.is_file()


def _get_rstudio_info() -> Dict[str, Any]:
    """Возвращает информацию о файле и статусе R-Studio.

    Returns:
        Dict[str, Any]: Метаданные исполняемого файла.
    """
    exists = _check_rstudio_exists()
    return {
        "exists": exists,
        "name": "R-Studio Technician Portable",
        "version": "9.5.191810",
        "path": str(RSTUDIO_EXE),
        "relative_path": str(RSTUDIO_RELATIVE_PATH),
        "size_bytes": RSTUDIO_EXE.stat().st_size if exists else 0,
        "modified_time": (
            datetime.fromtimestamp(RSTUDIO_EXE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            if exists else ""
        ),
    }


def init_router() -> APIRouter:
    """Инициализирует и возвращает FastAPI роутер для восстановления файлов.

    Returns:
        APIRouter: Сконфигурированный роутер.
    """
    router = APIRouter(prefix="/api/recovery", tags=["file-recovery"])

    @router.get("/status")
    async def get_recovery_status() -> Dict[str, Any]:
        """Возвращает статус утилиты восстановления файлов R-Studio."""
        return {
            "success": True,
            "tool": _get_rstudio_info(),
        }

    @router.post("/launch")
    async def launch_recovery_tool() -> Dict[str, Any]:
        """Запускает программу R-Studio для восстановления удаленных файлов.

        Returns:
            Dict[str, Any]: Результат запуска процесса (PID, статус).
        """
        if not _check_rstudio_exists():
            logger.error(f"Исполняемый файл R-Studio не найден: {RSTUDIO_EXE}")
            raise HTTPException(
                status_code=404,
                detail=f"Исполняемый файл R-Studio не найден по пути: {RSTUDIO_EXE}",
            )

        try:
            exe_str = str(RSTUDIO_EXE)
            work_dir = str(RSTUDIO_EXE.parent)
            logger.info(f"Запуск утилиты восстановления файлов R-Studio: {exe_str}")

            # Запуск в независимом фоновом процессе
            proc = subprocess.Popen(
                [exe_str],
                cwd=work_dir,
                close_fds=False,
            )

            logger.info(f"Программа R-Studio успешно запущена (PID: {proc.pid})")
            return {
                "success": True,
                "pid": proc.pid,
                "path": exe_str,
                "message": f"Программа восстановления файлов R-Studio успешно запущена (PID: {proc.pid})",
            }
        except Exception as e:
            logger.error(f"Ошибка при запуске R-Studio: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось запустить R-Studio: {e}",
            )

    return router
