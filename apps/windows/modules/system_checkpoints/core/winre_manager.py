# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Core - Winre Manager
# =============================================================================
# Description:
#   Модуль управления средой восстановления Windows RE (WinRE / reagentc).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.system_checkpoints.core.winre_manager import WinREManager
#
#     service = WinREManager()
#
# File: winre_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.system_checkpoints.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль управления средой восстановления Windows RE (WinRE / reagentc)."""

import re
import subprocess
from typing import Any, Dict, Optional
from logger import logger
from apps.windows.system_checkpoints.models import WinREStatus


class WinREManager:
    """Менеджер среды восстановления Windows (Windows Recovery Environment).

    Использует нативную системную утилиту reagentc.exe для инспекции статуса,
    включения, отключения и настройки расположения образа Winre.wim.
    """

    def __init__(self, timeout_seconds: int = 30) -> None:
        """Инициализация менеджера WinRE.

        Args:
            timeout_seconds: Таймаут выполнения вызовов reagentc.
        """
        self.timeout_seconds = timeout_seconds

    def get_status(self) -> WinREStatus:
        """Получение детального статуса среды восстановления Windows RE.

        Returns:
            WinREStatus: Структурированный статус WinRE.
        """
        try:
            res = subprocess.run(
                ["reagentc.exe", "/info"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            raw_output = res.stdout + "\n" + res.stderr
            return self.parse_reagentc_info(raw_output, exit_code=res.returncode)
        except subprocess.TimeoutExpired:
            msg = f"Таймаут выполнения reagentc /info ({self.timeout_seconds} сек)"
            logger.warning(msg)
            return WinREStatus(enabled=False, error=msg)
        except Exception as ex:
            logger.error(f"Ошибка при вызове reagentc /info: {ex}")
            return WinREStatus(enabled=False, error=str(ex))

    @staticmethod
    def parse_reagentc_info(output: str, exit_code: int = 0) -> WinREStatus:
        """Парсинг текстового вывода команды reagentc /info (поддержка RU и EN локалей).

        Args:
            output: Текстовый вывод команды reagentc.
            exit_code: Код возврата процесса.

        Returns:
            WinREStatus: Сформированный объект статуса.
        """
        status = WinREStatus()
        if not output:
            status.error = "Пустой вывод reagentc"
            return status

        # Поиск статуса: "Windows RE status: Enabled" или "Состояние Windows RE: Enabled/Включено/1"
        is_enabled = False
        status_match = re.search(
            r"(?:Windows RE status|Состояние Windows RE)\s*:\s*([^\r\n]+)",
            output,
            re.IGNORECASE,
        )
        if status_match:
            val = status_match.group(1).strip().lower()
            is_enabled = any(k in val for k in ["enabled", "1", "включено", "включена", "active"])
        status.enabled = is_enabled

        # Поиск расположения: "Windows RE location: \\?\GLOBALROOT\device\..."
        loc_match = re.search(
            r"(?:Windows RE location|Расположение Windows RE)\s*:\s*([^\r\n]+)",
            output,
            re.IGNORECASE,
        )
        if loc_match:
            status.location = loc_match.group(1).strip()

        # Поиск BCD ID: "Boot Configuration Data (BCD) identifier: {guid}"
        bcd_match = re.search(
            r"(?:Boot Configuration Data \(BCD\) identifier|Идентификатор данных конфигурации загрузки \(BCD\))\s*:\s*([^\r\n]+)",
            output,
            re.IGNORECASE,
        )
        if bcd_match:
            status.bcd_id = bcd_match.group(1).strip()

        # Поиск пользовательского образа: "Custom image location: ..."
        custom_match = re.search(
            r"(?:Custom image location|Расположение пользовательского образа)\s*:\s*([^\r\n]+)",
            output,
            re.IGNORECASE,
        )
        if custom_match:
            status.custom_image_location = custom_match.group(1).strip()

        # Определение признака подготовки (staged)
        staged_match = re.search(
            r"(?:Is staged|Подготовлено)\s*:\s*([^\r\n]+)",
            output,
            re.IGNORECASE,
        )
        if staged_match:
            s_val = staged_match.group(1).strip().lower()
            status.is_staged = any(k in s_val for k in ["1", "yes", "да", "true"])

        if exit_code != 0 and not status.location and not status.bcd_id:
            status.error = output.strip()

        return status

    def enable(self) -> Dict[str, Any]:
        """Включение среды восстановления Windows RE.

        Returns:
            Dict[str, Any]: Результат выполнения операции.
        """
        logger.info("Вызов reagentc /enable для активации среды WinRE")
        try:
            res = subprocess.run(
                ["reagentc.exe", "/enable"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            success = res.returncode == 0
            msg = res.stdout.strip() or res.stderr.strip()
            return {
                "success": success,
                "message": msg if msg else ("WinRE успешно включена" if success else "Ошибка включения WinRE"),
                "exit_code": res.returncode,
            }
        except Exception as ex:
            logger.error(f"Исключение при вызове reagentc /enable: {ex}")
            return {"success": False, "message": str(ex), "exit_code": -1}

    def disable(self) -> Dict[str, Any]:
        """Отключение среды восстановления Windows RE.

        Returns:
            Dict[str, Any]: Результат выполнения операции.
        """
        logger.info("Вызов reagentc /disable для отключения среды WinRE")
        try:
            res = subprocess.run(
                ["reagentc.exe", "/disable"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            success = res.returncode == 0
            msg = res.stdout.strip() or res.stderr.strip()
            return {
                "success": success,
                "message": msg if msg else ("WinRE успешно отключена" if success else "Ошибка отключения WinRE"),
                "exit_code": res.returncode,
            }
        except Exception as ex:
            logger.error(f"Исключение при вызове reagentc /disable: {ex}")
            return {"success": False, "message": str(ex), "exit_code": -1}

    def set_reimage_path(self, custom_path: str) -> Dict[str, Any]:
        """Установка пользовательского пути к образу восстановления WinRE.

        Args:
            custom_path: Директория, содержащая файл Winre.wim.

        Returns:
            Dict[str, Any]: Результат выполнения операции.
        """
        logger.info(f"Настройка пути WinRE: reagentc /setreimage /path {custom_path}")
        try:
            res = subprocess.run(
                ["reagentc.exe", "/setreimage", "/path", custom_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            success = res.returncode == 0
            msg = res.stdout.strip() or res.stderr.strip()
            return {
                "success": success,
                "path": custom_path,
                "message": msg if msg else ("Путь WinRE успешно установлен" if success else "Ошибка установки пути WinRE"),
                "exit_code": res.returncode,
            }
        except Exception as ex:
            logger.error(f"Исключение при установке пути WinRE: {ex}")
            return {"success": False, "path": custom_path, "message": str(ex), "exit_code": -1}
