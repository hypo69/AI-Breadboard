"""Планировщик синхронизации на Google Drive.

Автоматизирует синхронизацию данных по расписанию или по требованию.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import schedule
    from schedule import Scheduler
except ImportError:
    Scheduler = None  # type: ignore
    schedule = None  # type: ignore

from logger import logger
from .google_drive_sync import GoogleDriveSync


class SyncScheduler:
    """Управляет расписанием синхронизации на Google Drive."""

    def __init__(self, sync_interval_hours: int = 6) -> None:
        """Инициализация планировщика.

        Args:
            sync_interval_hours: Интервал синхронизации в часах (по умолчанию 6).
        """
        self.sync_interval_hours = sync_interval_hours
        self.drive_sync = GoogleDriveSync()
        self.last_sync_time: Optional[datetime] = None
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        if schedule is not None:
            self.scheduler = schedule.Scheduler()
            self._setup_schedule()
        else:
            self.scheduler = None
            logger.warning("Модуль schedule не установлен, используется ручная синхронизация")

    def _setup_schedule(self) -> None:
        """Настройка расписания синхронизации."""
        if self.scheduler is None:
            return

        self.scheduler.every(self.sync_interval_hours).hours.do(self.sync_now)
        self.scheduler.every().day.at("00:00").do(self.sync_now)
        logger.info(
            f"Расписание синхронизации настроено: каждые {self.sync_interval_hours} часов"
        )

    def sync_now(self) -> bool:
        """Выполнить синхронизацию немедленно.

        Returns:
            bool: True если успешно, False в противном случае.
        """
        try:
            logger.info("Начало синхронизации...")
            start_time = datetime.now()

            results = self.drive_sync.sync_all_data()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.last_sync_time = end_time

            total_uploaded = sum(
                r.get("uploaded", 0) for r in results.values() if isinstance(r, dict)
            )
            total_failed = sum(
                r.get("failed", 0) for r in results.values() if isinstance(r, dict)
            )

            logger.info(
                f"Синхронизация завершена за {duration:.2f} сек. "
                f"Загружено: {total_uploaded}, Ошибок: {total_failed}"
            )

            self._send_sync_notification(results, duration)
            return True

        except Exception as e:
            logger.error(f"Ошибка при синхронизации: {e}")
            return False

    def _send_sync_notification(self, results: dict, duration: float) -> None:
        """Отправить уведомление о результатах синхронизации.

        Args:
            results: Результаты синхронизации.
            duration: Время выполнения синхронизации.
        """
        try:
            total_failed = sum(
                r.get("failed", 0) for r in results.values() if isinstance(r, dict)
            )
            status = "успешно ✓" if total_failed == 0 else "с ошибками ✗"

            message = f"""
Синхронизация на Google Drive {status}
Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Продолжительность: {duration:.2f} сек

Результаты:
{json.dumps(results, indent=2, ensure_ascii=False)}
            """
            logger.info(message)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")

    def start(self) -> None:
        """Запустить планировщик в фоновом потоке."""
        if not self.scheduler:
            logger.warning("Планировщик недоступен (schedule не установлен)")
            return

        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return

        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Планировщик синхронизации запущен")

    def stop(self) -> None:
        """Остановить планировщик."""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        logger.info("Планировщик синхронизации остановлен")

    def _run_scheduler(self) -> None:
        """Внутренний цикл планировщика."""
        while self.is_running:
            try:
                if self.scheduler:
                    self.scheduler.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Ошибка в цикле планировщика: {e}")
                time.sleep(60)

    def get_status(self) -> Dict[str, Any]:
        """Получить статус планировщика.

        Returns:
            Dict[str, Any]: Статус планировщика и последней синхронизации.
        """
        status: Dict[str, Any] = {
            "is_running": self.is_running,
            "sync_interval_hours": self.sync_interval_hours,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "next_sync_time": None,
        }

        if self.scheduler and self.scheduler.jobs:
            next_run = min(self.scheduler.idle_seconds for job in self.scheduler.jobs)
            if next_run is not None:
                status["next_sync_time"] = (
                    datetime.now() + timedelta(seconds=next_run)
                ).isoformat()

        return status


class ManualSyncHandler:
    """Обработчик ручной синхронизации."""

    def __init__(self) -> None:
        self.drive_sync = GoogleDriveSync()

    def sync_single_directory(
        self, local_dir: str, folder_name: Optional[str] = None
    ) -> Dict[str, int]:
        """Синхронизировать одну директорию.

        Args:
            local_dir: Локальный путь к директории.
            folder_name: Название папки на Google Drive.

        Returns:
            Dict[str, int]: Результаты синхронизации.
        """
        try:
            self.drive_sync.ensure_sync_folder()
            if not folder_name:
                folder_name = os.path.basename(local_dir)

            drive_parent_id = self.drive_sync.root_folder_id
            if not drive_parent_id:
                return {}
            results = self.drive_sync.sync_directory(local_dir, drive_parent_id)

            logger.info(f"Синхронизирована директория: {local_dir}")
            return results
        except Exception as e:
            logger.error(f"Ошибка при синхронизации {local_dir}: {e}")
            return {}

    def sync_single_file(self, local_file: str, folder_name: str = "uploads") -> bool:
        """Синхронизировать один файл.

        Args:
            local_file: Локальный путь к файлу.
            folder_name: Название папки на Google Drive.

        Returns:
            bool: True если успешно, False в противном случае.
        """
        try:
            self.drive_sync.ensure_sync_folder()
            if not self.drive_sync.root_folder_id:
                return False

            drive_parent_id = self.drive_sync._get_or_create_subfolder(
                self.drive_sync.root_folder_id, folder_name
            )
            if not drive_parent_id:
                return False

            result = self.upload_file_handler(local_file, drive_parent_id)
            logger.info(f"Синхронизирован файл: {local_file}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при синхронизации {local_file}: {e}")
            return False

    def upload_file_handler(self, local_file: str, drive_parent_id: str) -> bool:
        """Вспомогательный метод загрузки файла.

        Args:
            local_file: Путь к файлу.
            drive_parent_id: Родительская папка на Google Drive.

        Returns:
            bool: Результат загрузки.
        """
        return self.drive_sync.upload_file(local_file, drive_parent_id)


_global_scheduler: Optional[SyncScheduler] = None


def get_scheduler() -> SyncScheduler:
    """Получить глобальный экземпляр планировщика.

    Returns:
        SyncScheduler: Экземпляр планировщика.
    """
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = SyncScheduler()
    return _global_scheduler


def start_sync_scheduler(sync_interval_hours: int = 6) -> None:
    """Запустить планировщик синхронизации.

    Args:
        sync_interval_hours: Интервал синхронизации в часах.
    """
    scheduler = get_scheduler()
    scheduler.sync_interval_hours = sync_interval_hours
    scheduler.start()


def stop_sync_scheduler() -> None:
    """Остановить планировщик синхронизации."""
    global _global_scheduler
    if _global_scheduler:
        _global_scheduler.stop()
        _global_scheduler = None


def manual_sync() -> bool:
    """Выполнить ручную синхронизацию.

    Returns:
        bool: Результат выполнения синхронизации.
    """
    scheduler = get_scheduler()
    return scheduler.sync_now()
