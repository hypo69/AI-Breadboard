# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Item Manager
# =============================================================================
# Description:
#   Модуль безопасного управления состоянием элементов автозагрузки
#   (включение, отключение, удаление битых записей через StartupApproved)
#   и экспорта отчетов аудита в форматы JSON и CSV.
#
# Examples:
#   >>> from apps.windows_startup_auditor.core.manager import StartupManager
#   >>> manager = StartupManager()
#   >>> res = manager.toggle_item("reg_run_1", enable=False)
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows_startup_auditor.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления элементами автозагрузки и экспорта отчетов."""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import logger
from apps.windows_startup_auditor.core.models import (
    AuditReport,
    StartupEntry,
    StartupLocationType,
    ToggleResponse,
)

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    winreg = None
    HAS_WINREG = False


class StartupManager:
    """Менеджер управления элементами автозагрузки."""

    def toggle_item(self, entry: StartupEntry, enable: bool) -> ToggleResponse:
        """Переключает статус активности элемента автозагрузки.

        Args:
            entry: Запись автозапуска для изменения.
            enable: True для включения, False для отключения.

        Returns:
            ToggleResponse: Результат операции переключения.
        """
        if not HAS_WINREG:
            return ToggleResponse(
                success=False,
                entry_id=entry.id,
                new_state=entry.is_enabled,
                message="winreg недоступен на данной платформе",
            )

        try:
            # Для реестровых записей используем механизм Windows StartupApproved
            if entry.location_type in (StartupLocationType.REGISTRY_RUN, StartupLocationType.REGISTRY_RUNONCE):
                return self._set_startup_approved_state(entry.name, enable, entry.id)

            # Для задач планировщика
            elif entry.location_type == StartupLocationType.SCHEDULED_TASK:
                action = "Enable" if enable else "Disable"
                cmd = ["schtasks", "/Change", "/TN", entry.name.replace("Задача: ", ""), f"/{action}"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    return ToggleResponse(
                        success=True,
                        entry_id=entry.id,
                        new_state=enable,
                        message=f"Задача планировщика успешно {'включена' if enable else 'отключена'}",
                    )
                else:
                    return ToggleResponse(
                        success=False,
                        entry_id=entry.id,
                        new_state=entry.is_enabled,
                        message=f"Ошибка schtasks: {res.stderr.strip()}",
                    )

            # Для файлов в папке автозагрузки
            elif entry.location_type in (StartupLocationType.STARTUP_FOLDER_USER, StartupLocationType.STARTUP_FOLDER_COMMON):
                return self._set_startup_approved_folder_state(entry.name, enable, entry.id)

            return ToggleResponse(
                success=False,
                entry_id=entry.id,
                new_state=entry.is_enabled,
                message=f"Управление для типа {entry.location_type} требует повышенных прав",
            )

        except Exception as e:
            logger.error(f"Ошибка при изменении статуса элемента {entry.id}: {e}")
            return ToggleResponse(
                success=False,
                entry_id=entry.id,
                new_state=entry.is_enabled,
                message=str(e),
            )

    def _set_startup_approved_state(self, item_name: str, enable: bool, entry_id: str) -> ToggleResponse:
        """Устанавливает значение в ключе StartupApproved\\Run."""
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey) as key:
                # Байт 02 = Включено, Байт 03 = Отключено (Windows 10/11 standard)
                # 12-байтовый массив с меткой времени
                now_bytes = int(datetime.now().timestamp()).to_bytes(8, byteorder="little", signed=False)
                state_byte = b"\x02" if enable else b"\x03"
                binary_val = state_byte + b"\x00\x00\x00" + now_bytes

                winreg.SetValueEx(key, item_name, 0, winreg.REG_BINARY, binary_val)
                logger.info(f"Элемент автозагрузки '{item_name}' установлен в состояние: {'Включен' if enable else 'Отключен'}")

                return ToggleResponse(
                    success=True,
                    entry_id=entry_id,
                    new_state=enable,
                    message=f"Элемент успешно {'включен' if enable else 'отключен'}",
                )
        except Exception as e:
            logger.warning(f"Не удалось записать в StartupApproved: {e}")
            return ToggleResponse(
                success=False,
                entry_id=entry_id,
                new_state=not enable,
                message=str(e),
            )

    def _set_startup_approved_folder_state(self, item_name: str, enable: bool, entry_id: str) -> ToggleResponse:
        """Устанавливает значение в ключе StartupApproved\\StartupFolder."""
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey) as key:
                now_bytes = int(datetime.now().timestamp()).to_bytes(8, byteorder="little", signed=False)
                state_byte = b"\x02" if enable else b"\x03"
                binary_val = state_byte + b"\x00\x00\x00" + now_bytes

                winreg.SetValueEx(key, item_name, 0, winreg.REG_BINARY, binary_val)
                return ToggleResponse(
                    success=True,
                    entry_id=entry_id,
                    new_state=enable,
                    message=f"Ярлык автозагрузки успешно {'включен' if enable else 'отключен'}",
                )
        except Exception as e:
            return ToggleResponse(
                success=False,
                entry_id=entry_id,
                new_state=not enable,
                message=str(e),
            )

    def export_to_json(self, report: AuditReport, target_path: Optional[Path] = None) -> str:
        """Экспорт отчета аудита в формат JSON.

        Args:
            report: Отчет аудита.
            target_path: Опциональный путь для сохранения файла.

        Returns:
            str: JSON-строка отчета.
        """
        data = report.model_dump()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        if target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(json_str, encoding="utf-8")
            logger.info(f"Отчет аудита сохранен в {target_path}")

        return json_str

    def export_to_csv(self, report: AuditReport, target_path: Optional[Path] = None) -> str:
        """Экспорт отчета аудита в формат CSV.

        Args:
            report: Отчет аудита.
            target_path: Опциональный путь для сохранения файла.

        Returns:
            str: CSV-строка отчета.
        """
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Заголовки
        writer.writerow([
            "ID",
            "Имя",
            "Тип локации",
            "Категория",
            "Уровень риска",
            "Статус (Включен)",
            "Файл существует",
            "Исполняемый путь",
            "Команда",
            "Издатель",
            "Размер (КБ)",
            "Влияние на старт",
            "Причины риска",
            "Рекомендация",
        ])

        for e in report.entries:
            writer.writerow([
                e.id,
                e.name,
                e.location_type.value if hasattr(e.location_type, "value") else str(e.location_type),
                e.category.value if hasattr(e.category, "value") else str(e.category),
                e.risk_level.value if hasattr(e.risk_level, "value") else str(e.risk_level),
                "Да" if e.is_enabled else "Нет",
                "Да" if e.file_exists else "Нет",
                e.executable_path,
                e.command,
                e.publisher,
                e.file_size_kb,
                e.boot_impact,
                "; ".join(e.risk_reasons),
                e.recommendation,
            ])

        csv_str = output.getvalue()
        if target_path:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(csv_str, encoding="utf-8-sig")
            logger.info(f"CSV отчет аудита сохранен в {target_path}")

        return csv_str
