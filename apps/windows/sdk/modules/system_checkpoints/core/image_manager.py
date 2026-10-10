# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Core - Image Manager
# =============================================================================
# Description:
#   Модуль управления системными WIM-образами восстановления Windows через DISM.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.system_checkpoints.core.image_manager import SystemImageManager
#
#     service = SystemImageManager()
#
# File: image_manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.system_checkpoints.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль управления системными WIM-образами восстановления Windows через DISM."""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.system_checkpoints.models import SystemImageMetadata


class SystemImageManager:
    """Менеджер создания, инвентаризации и инспекции WIM-образов Windows.

    Использует нативный инструмент обслуживания образов развертывания DISM.exe
    для захвата эталонных образов (Baseline) и периодических контрольных точек.
    """

    def __init__(
        self,
        default_dir: str = "C:\\Recovery\\AI-Breadboard",
        compress_level: str = "fast",
        timeout_seconds: int = 3600,
    ) -> None:
        """Инициализация менеджера WIM-образов.

        Args:
            default_dir: Директория по умолчанию для хранения образов.
            compress_level: Уровень сжатия ('fast', 'max', 'none').
            timeout_seconds: Максимальное время выполнения операции DISM в секундах.
        """
        self.default_dir = Path(default_dir)
        self.compress_level = compress_level
        self.timeout_seconds = timeout_seconds

    def ensure_storage_dir(self, target_dir: Optional[str] = None) -> Path:
        """Проверка и создание каталога хранения образов.

        Args:
            target_dir: Путь к каталогу (если не задан — используется default_dir).

        Returns:
            Path: Объект Path проверенной директории.
        """
        out_path = Path(target_dir) if target_dir else self.default_dir
        try:
            out_path.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            logger.warning(f"Не удалось создать каталог {out_path}: {ex}. Используем локальный fallback.")
            fallback = Path("data/system_checkpoints/images")
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        return out_path

    def build_capture_command(
        self,
        source_drive: str,
        image_path: str,
        name: str,
        description: str = "",
        append: bool = False,
    ) -> List[str]:
        """Формирование безопасной команды DISM для захвата или добавления образа.

        Args:
            source_drive: Буква исходного системного диска (например, 'C:').
            image_path: Полный путь к файлу .wim.
            name: Имя образа внутри WIM.
            description: Описание индекса.
            append: Флаг добавления в существующий WIM (/Append-Image) вместо нового (/Capture-Image).

        Returns:
            List[str]: Список аргументов командной строки DISM.
        """
        clean_drive = source_drive.rstrip("\\").rstrip("/")
        if not clean_drive.endswith(":"):
            clean_drive = f"{clean_drive}:"
        capture_dir = f"{clean_drive}\\"

        action = "/Append-Image" if append else "/Capture-Image"
        cmd = [
            "dism.exe",
            action,
            f"/ImageFile:{image_path}",
            f"/CaptureDir:{capture_dir}",
            f"/Name:{name}",
        ]
        if description:
            cmd.append(f"/Description:{description}")
        if not append:
            cmd.append(f"/Compress:{self.compress_level}")
        cmd.extend(["/CheckIntegrity", "/Verify"])
        return cmd

    def get_wim_info(self, wim_path: str) -> Optional[SystemImageMetadata]:
        """Получение метаданных о существующем WIM-файле через DISM /Get-WimInfo.

        Args:
            wim_path: Путь к файлу .wim.

        Returns:
            Optional[SystemImageMetadata]: Метаданные образа или None при ошибке.
        """
        target = Path(wim_path)
        if not target.exists():
            return None

        stat = target.stat()
        file_size = stat.st_size
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        is_baseline = "baseline" in target.stem.lower()

        index_count = 1
        description = ""
        try:
            res = subprocess.run(
                ["dism.exe", "/Get-WimInfo", f"/WimFile:{str(target)}"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if res.returncode == 0:
                indices = re.findall(r"(?:Index|Индекс)\s*:\s*(\d+)", res.stdout, re.IGNORECASE)
                if indices:
                    index_count = max(len(indices), int(indices[-1]))
                desc_match = re.search(r"(?:Description|Описание)\s*:\s*([^\r\n]+)", res.stdout, re.IGNORECASE)
                if desc_match:
                    description = desc_match.group(1).strip()
        except Exception as ex:
            logger.debug(f"Не удалось получить подробную информацию DISM для {wim_path}: {ex}")

        return SystemImageMetadata(
            image_path=str(target.resolve()),
            file_size_bytes=file_size,
            created_at=mod_time,
            is_baseline=is_baseline,
            index_count=index_count,
            description=description,
            captured_drive="C:",
        )

    def scan_recovery_images(
        self,
        custom_directories: Optional[List[str]] = None,
    ) -> List[SystemImageMetadata]:
        """Сканирование директорий на наличие существующих образов .wim / .esd.

        Args:
            custom_directories: Дополнительные папки для сканирования.

        Returns:
            List[SystemImageMetadata]: Список найденных образов, отсортированный по дате создания.
        """
        scan_dirs: List[Path] = [
            self.default_dir,
            Path("data/system_checkpoints/images"),
            Path("C:\\Recovery"),
        ]
        if custom_directories:
            for d in custom_directories:
                scan_dirs.append(Path(d))

        found_images: List[SystemImageMetadata] = []
        scanned_paths = set()

        for s_dir in scan_dirs:
            if not s_dir.exists():
                continue
            try:
                for ext in ["*.wim", "*.esd"]:
                    for img_file in s_dir.glob(ext):
                        full_p = str(img_file.resolve())
                        if full_p in scanned_paths:
                            continue
                        scanned_paths.add(full_p)
                        meta = self.get_wim_info(full_p)
                        if meta:
                            found_images.append(meta)
            except Exception as ex:
                logger.debug(f"Ошибка при сканировании каталога {s_dir}: {ex}")

        # Сортировка от новых к старым
        found_images.sort(key=lambda x: x.created_at, reverse=True)
        return found_images

    def create_baseline_image(
        self,
        source_drive: str = "C:",
        destination_dir: Optional[str] = None,
        image_name: Optional[str] = None,
        description: str = "Базовый эталонный образ чистой и настроенной системы",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Создание базового эталонного образа восстановления (Baseline Gold Image).

        Args:
            source_drive: Исходный диск (например, 'C:').
            destination_dir: Каталог сохранения.
            image_name: Имя образа (по умолчанию Recovery_Baseline.wim).
            description: Описание образа.
            dry_run: Только симуляция команды без запуска DISM.

        Returns:
            Dict[str, Any]: Результат создания или симуляции.
        """
        out_dir = self.ensure_storage_dir(destination_dir)
        date_str = datetime.now().strftime("%Y-%m-%d")
        base_name = image_name or f"Recovery_{date_str}_Baseline.wim"
        if not base_name.endswith(".wim"):
            base_name = f"{base_name}.wim"

        target_file = out_dir / base_name
        cmd = self.build_capture_command(
            source_drive=source_drive,
            image_path=str(target_file),
            name="Baseline Windows Image",
            description=description,
            append=False,
        )

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "command": " ".join(cmd),
                "target_file": str(target_file),
                "is_baseline": True,
                "message": f"Сгенерирована команда создания базового образа для {target_file}",
            }

        logger.info(f"Запуск создания базового образа Windows: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds)
            success = res.returncode == 0
            return {
                "success": success,
                "dry_run": False,
                "command": " ".join(cmd),
                "target_file": str(target_file),
                "is_baseline": True,
                "exit_code": res.returncode,
                "message": "Базовый образ восстановления успешно создан" if success else (res.stderr.strip() or res.stdout.strip()),
            }
        except subprocess.TimeoutExpired:
            msg = f"Таймаут создания базового образа ({self.timeout_seconds} сек)"
            logger.error(msg)
            return {"success": False, "target_file": str(target_file), "error": msg}
        except Exception as ex:
            logger.error(f"Исключение при захвате базового образа DISM: {ex}")
            return {"success": False, "target_file": str(target_file), "error": str(ex)}

    def create_periodic_checkpoint(
        self,
        source_drive: str = "C:",
        destination_dir: Optional[str] = None,
        image_name: Optional[str] = None,
        description: str = "Периодическая контрольная точка состояния системы",
        append_if_exists: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Создание периодической контрольной точки / версионированного образа.

        Предотвращает автоматическую перезапись единственного файла. Создает датированный
        новый снимок (Recovery_YYYY-MM-DD.wim) либо добавляет новый индекс в WIM-контейнер.

        Args:
            source_drive: Исходный диск.
            destination_dir: Каталог сохранения.
            image_name: Кастомное имя.
            description: Описание.
            append_if_exists: Добавить новый индекс в существующий файл вместо создания отдельного.
            dry_run: Режим симуляции.

        Returns:
            Dict[str, Any]: Результат операции.
        """
        out_dir = self.ensure_storage_dir(destination_dir)
        now_dt = datetime.now()
        date_str = now_dt.strftime("%Y-%m-%d")
        time_str = now_dt.strftime("%H%M%S")

        if append_if_exists:
            base_file_name = image_name or "Recovery_Continuous.wim"
            if not base_file_name.endswith(".wim"):
                base_file_name = f"{base_file_name}.wim"
            target_file = out_dir / base_file_name
            is_append = target_file.exists()
        else:
            base_file_name = image_name or f"Recovery_{date_str}_{time_str}.wim"
            if not base_file_name.endswith(".wim"):
                base_file_name = f"{base_file_name}.wim"
            target_file = out_dir / base_file_name
            is_append = False

        idx_name = f"Checkpoint {date_str} {now_dt.strftime('%H:%M')}"
        cmd = self.build_capture_command(
            source_drive=source_drive,
            image_path=str(target_file),
            name=idx_name,
            description=description,
            append=is_append,
        )

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "command": " ".join(cmd),
                "target_file": str(target_file),
                "is_append": is_append,
                "message": f"Сгенерирована команда периодической контрольной точки: {target_file}",
            }

        logger.info(f"Запуск создания периодической контрольной точки: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds)
            success = res.returncode == 0
            return {
                "success": success,
                "dry_run": False,
                "command": " ".join(cmd),
                "target_file": str(target_file),
                "is_append": is_append,
                "exit_code": res.returncode,
                "message": "Периодическая контрольная точка успешно зафиксирована" if success else (res.stderr.strip() or res.stdout.strip()),
            }
        except subprocess.TimeoutExpired:
            msg = f"Таймаут создания контрольной точки ({self.timeout_seconds} сек)"
            logger.error(msg)
            return {"success": False, "target_file": str(target_file), "error": msg}
        except Exception as ex:
            logger.error(f"Исключение при вызове DISM: {ex}")
            return {"success": False, "target_file": str(target_file), "error": str(ex)}
