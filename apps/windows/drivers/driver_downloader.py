# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU Driver Package Downloader
# =============================================================================
# Description:
#   Асинхронный загрузчик пакетов драйверов NVIDIA и AMD с отслеживанием прогресса,
#   скорости, кэшированием и контролем ошибок.
#
# File: driver_downloader.py
# Project: ai-breadboard
# Package: apps.windows.drivers
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль загрузки установочных файлов видеодрайверов."""

from __future__ import annotations

import asyncio
import os
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Dict, List, Optional

try:
    from src.logger import logger
except ImportError:
    from logger import logger

from apps.windows.drivers.models import DownloadProgress, TaskStatus, VendorType


class DriverDownloader:
    """Менеджер фоновой загрузки установочных пакетов драйверов."""

    def __init__(self, download_dir: Optional[Path] = None) -> None:
        """Инициализация каталога для загрузок."""
        if download_dir is None:
            # data/gpu_drivers/downloads/
            project_root = Path(__file__).resolve().parents[3]
            self.download_dir = project_root / "data" / "gpu_drivers" / "downloads"
        else:
            self.download_dir = download_dir

        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, DownloadProgress] = {}
        self._async_tasks: Dict[str, asyncio.Task] = {}

    def get_download_dir(self) -> Path:
        """Получить путь к папке загрузок."""
        return self.download_dir

    def get_task(self, task_id: str) -> Optional[DownloadProgress]:
        """Получить информацию о задаче загрузки."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[DownloadProgress]:
        """Список всех текущих и завершенных задач загрузки."""
        return list(self._tasks.values())

    def get_cached_file(self, filename: str) -> Optional[Path]:
        """Проверить наличие скачанного файла в кэше."""
        target = self.download_dir / filename
        if target.exists() and target.stat().st_size > 1024 * 1024:
            return target
        return None

    def start_download(
        self,
        url: str,
        filename: str,
        version: str,
        vendor: VendorType,
    ) -> str:
        """Запустить фоновую загрузку драйвера.

        Args:
            url: Прямая ссылка для скачивания.
            filename: Имя сохраняемого файла.
            version: Версия драйвера.
            vendor: Производитель GPU.

        Returns:
            task_id: Уникальный строковый идентификатор задачи.
        """
        task_id = str(uuid.uuid4())[:8]
        dest_path = self.download_dir / filename

        if dest_path.exists() and dest_path.stat().st_size > 50 * 1024 * 1024:
            file_size = dest_path.stat().st_size
            self._tasks[task_id] = DownloadProgress(
                task_id=task_id,
                version=version,
                vendor=vendor,
                url=url,
                destination_file=str(dest_path),
                status=TaskStatus.COMPLETED,
                total_bytes=file_size,
                downloaded_bytes=file_size,
                percent=100.0,
                speed_mb_s=0.0,
            )
            return task_id

        progress = DownloadProgress(
            task_id=task_id,
            version=version,
            vendor=vendor,
            url=url,
            destination_file=str(dest_path),
            status=TaskStatus.RUNNING,
            total_bytes=0,
            downloaded_bytes=0,
            percent=0.0,
            speed_mb_s=0.0,
        )
        self._tasks[task_id] = progress

        task = asyncio.create_task(self._download_worker(task_id, url, dest_path))
        self._async_tasks[task_id] = task

        return task_id

    async def _download_worker(self, task_id: str, url: str, dest_path: Path) -> None:
        """Фоновый воркер скачивания потока с расчетом скорости."""
        progress = self._tasks[task_id]

        def _sync_download():
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            temp_path = dest_path.with_suffix(dest_path.suffix + ".part")
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    total_size = int(response.headers.get("Content-Length", 0))
                    progress.total_bytes = total_size

                    downloaded = 0
                    start_time = time.time()
                    last_time = start_time
                    chunk_size = 512 * 1024

                    with open(temp_path, "wb") as out_f:
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            out_f.write(chunk)
                            downloaded += len(chunk)
                            progress.downloaded_bytes = downloaded

                            now = time.time()
                            if total_size > 0:
                                progress.percent = round((downloaded / total_size) * 100.0, 1)

                            if now - last_time >= 0.5:
                                elapsed = max(0.001, now - start_time)
                                progress.speed_mb_s = round((downloaded / (1024 * 1024)) / elapsed, 2)
                                last_time = now

                if temp_path.exists():
                    if dest_path.exists():
                        dest_path.unlink()
                    temp_path.rename(dest_path)

                progress.status = TaskStatus.COMPLETED
                progress.percent = 100.0
                progress.speed_mb_s = 0.0
                logger.info(f"Загрузка драйвера завершена: {dest_path.name} ({task_id})")

            except Exception as e:
                logger.error(f"Ошибка при скачивании драйвера ({task_id}): {e}")
                progress.status = TaskStatus.FAILED
                progress.error_message = str(e)
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_download)

    def cancel_download(self, task_id: str) -> bool:
        """Отменить выполняющуюся задачу скачивания."""
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.CANCELLED
            if task_id in self._async_tasks:
                self._async_tasks[task_id].cancel()
            return True
        return False
