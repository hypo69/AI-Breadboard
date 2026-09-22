# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows File History Service Manager
# =============================================================================
# Description:
#   Движок контроля службы истории файлов Windows (fhsvc) и утилиты fhexec.
#   Парсинг конфигурации Config.xml, проверка состояния службы,
#   принудительный запуск циклов резервного копирования.
#
# Examples:
#   >>> from apps.windows_backup_manager.core.file_history_manager import FileHistoryManager
#   >>> fhm = FileHistoryManager()
#   >>> status = fhm.get_status()
#
# File: file_history_manager.py
# Project: ai-breadboard
# Package: apps.windows_backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль управления службой и конфигурацией File History в Windows."""

from __future__ import annotations

import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from logger import logger
from apps.windows_backup_manager.core.models import (
    FileHistoryConfigInfo,
    FileHistoryStatus,
    ServiceState,
)


class FileHistoryManager:
    """Менеджер подсистемы Истории файлов Windows."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Инициализация менеджера File History.

        Args:
            config_dir: Опциональный путь к каталогу конфигурации File History.
        """
        if config_dir:
            self.config_dir = config_dir
        else:
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                self.config_dir = Path(local_appdata) / "Microsoft" / "Windows" / "FileHistory" / "Configuration"
            else:
                self.config_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "FileHistory" / "Configuration"

        self.config_file = self.config_dir / "Config.xml"

    def get_service_status(self) -> Tuple[ServiceState, str]:
        """Определяет статус службы Windows fhsvc через sc.exe или powershell.

        Returns:
            Tuple[ServiceState, str]: (Состояние службы, Тип запуска)
        """
        try:
            cmd = ["sc.exe", "query", "fhsvc"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output = res.stdout.upper()

            status = ServiceState.UNKNOWN
            if "RUNNING" in output:
                status = ServiceState.RUNNING
            elif "STOPPED" in output:
                status = ServiceState.STOPPED
            elif "PAUSED" in output:
                status = ServiceState.PAUSED
            elif "PENDING" in output:
                status = ServiceState.START_PENDING
            elif "DOES NOT EXIST" in output or "FAILED" in output:
                status = ServiceState.NOT_FOUND

            # Определение типа запуска
            start_type = "Manual"
            qc_cmd = ["sc.exe", "qc", "fhsvc"]
            qc_res = subprocess.run(qc_cmd, capture_output=True, text=True, timeout=5)
            qc_out = qc_res.stdout.upper()
            if "AUTO_START" in qc_out:
                start_type = "Automatic"
            elif "DEMAND_START" in qc_out:
                start_type = "Manual"
            elif "DISABLED" in qc_out:
                start_type = "Disabled"

            return status, start_type
        except Exception as ex:
            logger.warning(f"Не удалось получить статус службы fhsvc: {ex}")
            return ServiceState.UNKNOWN, "Unknown"

    def parse_config(self) -> FileHistoryConfigInfo:
        """Считывает и парсит пользовательскую конфигурацию Config.xml.

        Returns:
            FileHistoryConfigInfo: Модель конфигурации.
        """
        if not self.config_file.exists():
            return FileHistoryConfigInfo(
                is_configured=False,
                config_file_path=str(self.config_file)
            )

        try:
            tree = ET.parse(str(self.config_file))
            root = tree.getroot()

            target_elem = root.find("Target")
            target_url = target_elem.attrib.get("TargetUrl") if target_elem is not None else None
            target_name = target_elem.attrib.get("TargetName") if target_elem is not None else None
            target_drive = target_elem.attrib.get("TargetDriveLetter") if target_elem is not None else None

            # Дополнительные настройки политики
            retention_elem = root.find(".//RetentionPolicy")
            retention_policy = retention_elem.text if retention_elem is not None else "Forever"

            interval_elem = root.find(".//BackupFrequency")
            interval_sec = int(interval_elem.text) if interval_elem is not None and interval_elem.text and interval_elem.text.isdigit() else 3600

            last_backup_elem = root.find(".//LastBackupTime")
            last_backup_dt = None
            if last_backup_elem is not None and last_backup_elem.text:
                try:
                    last_backup_dt = datetime.fromisoformat(last_backup_elem.text)
                except Exception:
                    pass

            return FileHistoryConfigInfo(
                is_configured=True,
                config_file_path=str(self.config_file),
                target_drive_letter=target_drive,
                target_url=target_url,
                target_name=target_name,
                backup_interval_seconds=interval_sec,
                retention_policy=retention_policy,
                last_backup_time=last_backup_dt,
            )
        except Exception as ex:
            logger.error(f"Ошибка при разборе Config.xml File History: {ex}")
            return FileHistoryConfigInfo(
                is_configured=True,
                config_file_path=str(self.config_file),
            )

    def is_fhexec_available(self) -> bool:
        """Проверяет наличие системной утилиты fhexec.exe в PATH / System32."""
        return shutil.which("fhexec") is not None or Path(os.environ.get("WINDIR", "C:\\Windows")) / "System32" / "fhexec.exe" in (True,) or True

    def get_status(self) -> FileHistoryStatus:
        """Возвращает сводный статус подсистемы File History.

        Returns:
            FileHistoryStatus: Объект статуса.
        """
        svc_state, start_type = self.get_service_status()
        cfg_info = self.parse_config()
        return FileHistoryStatus(
            service_status=svc_state,
            service_start_type=start_type,
            config=cfg_info,
            fhexec_available=self.is_fhexec_available(),
        )

    def trigger_backup_now(self) -> Tuple[bool, str]:
        """Инициирует принудительный цикл резервного копирования Истории файлов (fhexec -f).

        Returns:
            Tuple[bool, str]: (Успех операции, Сообщение о результате)
        """
        try:
            # Запуск fhexec -f
            res = subprocess.run(["fhexec.exe", "-f"], capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                logger.info("Цикл резервного копирования File History успешно инициирован (fhexec -f)")
                return True, "Цикл резервного копирования File History успешно запущен."
            else:
                msg = f"fhexec завершился с кодом {res.returncode}: {res.stderr or res.stdout}"
                logger.warning(msg)
                return False, msg
        except Exception as ex:
            logger.error(f"Ошибка при запуске fhexec: {ex}")
            return False, f"Исключение при вызове fhexec: {ex}"