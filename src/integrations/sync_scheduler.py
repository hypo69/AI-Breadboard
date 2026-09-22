"""
Планировщик синхронизации на Google Drive

Автоматизирует синхронизацию данных по расписанию или по требованию.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Callable
import time
import threading

try:
    from schedule import Scheduler
    import schedule
except ImportError:
    Scheduler = None
    schedule = None

from .google_drive_sync import GoogleDriveSync

from logger import logger


class SyncScheduler:
    """Управляет расписанием синхронизации на Google Drive."""

    def __init__(self, sync_interval_hours: int = 6):
        """
        Инициализация планировщика.

        Args:
            sync_interval_hours: Интервал синхронизации в часах (по умолчанию 6)
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

    def _setup_schedule(self):
        """Настройка расписания синхронизации."""
        if self.scheduler is None:
            return

        # Синхронизация каждые N часов
        self.scheduler.every(self.sync_interval_hours).hours.do(self.sync_now)

        # Дополнительная синхронизация каждый день в полночь
        self.scheduler.every().day.at("00:00").do(self.sync_now)

        logger.info(
            f"Расписание синхронизации настроено: каждые {self.sync_interval_hours} часов"
        )

    def sync_now(self) -> bool:
        """
        Выполнить синхронизацию немедленно.

        Returns:
            True если успешно, False в противном случае
        """
        try:
            logger.info("Начало синхронизации...")
            start_time = datetime.now()

            results = self.drive_sync.sync_all_data()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.last_sync_time = end_time

            # Логирование результатов
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

            # Отправка уведомления
            self._send_sync_notification(results, duration)

            return True

        except Exception as e:
            logger.error(f"Ошибка при синхронизации: {e}")
            return False

    def _send_sync_notification(self, results: dict, duration: float):
        """
        Отправить уведомление о результатах синхронизации.

        Args:
            results: Результаты синхронизации
            duration: Время выполнения синхронизации
        """
        try:
            # Определение статуса
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

            # Здесь можно добавить отправку на Telegram, email и т.д.
            # if telegram_enabled:
            #     send_telegram_notification(message)

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")

    def start(self):
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

    def stop(self):
        """Остановить планировщик."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Планировщик синхронизации остановлен")

    def _run_scheduler(self):
        """Внутренний цикл планировщика."""
        while self.is_running:
            try:
                if self.scheduler:
                    self.scheduler.run_pending()
                time.sleep(60)  # Проверка каждую минуту
            except Exception as e:
                logger.error(f"Ошибка в цикле планировщика: {e}")
                time.sleep(60)

    def get_status(self) -> dict:
        """
        Получить статус планировщика.

        Returns:
            Статус планировщика и последней синхронизации
        """
        status = {
            "is_running": self.is_running,
            "sync_interval_hours": self.sync_interval_hours,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "next_sync_time": None,
        }

        if self.scheduler and self.scheduler.jobs:
            # Получение времени следующей синхронизации
            next_run = min(self.scheduler.idle_seconds for job in self.scheduler.jobs)
            status["next_sync_time"] = (
                datetime.now() + timedelta(seconds=next_run)
            ).isoformat()

        return status


class ManualSyncHandler:
    """Обработчик ручной синхронизации."""

    def __init__(self):
        self.drive_sync = GoogleDriveSync()

    def sync_single_directory(self, local_dir: str, folder_name: str = None) -> dict:
        """
        Синхронизировать одну директорию.

        Args:
            local_dir: Локальный путь к директории
            folder_name: Название папки на Google Drive

        Returns:
            Результаты синхронизации
        """
        try:
            self.drive_sync.ensure_sync_folder()

            if not folder_name:
                folder_name = os.path.basename(local_dir)

            drive_parent_id = self.drive_sync.root_folder_id
            results = self.drive_sync.sync_directory(local_dir, drive_parent_id)

            logger.info(f"Синхронизирована директория: {local_dir}")
            return results

        except Exception as e:
            logger.error(f"Ошибка при синхронизации {local_dir}: {e}")
            return {}

    def sync_single_file(self, local_file: str, folder_name: str = "uploads") -> bool:
        """
        Синхронизировать один файл.

        Args:
            local_file: Локальный путь к файлу
            folder_name: Название папки на Google Drive

        Returns:
            True если успешно, False в противном случае
        """
        try:
            self.drive_sync.ensure_sync_folder()

            drive_parent_id = self.drive_sync._get_or_create_subfolder(
                self.drive_sync.root_folder_id, folder_name
            )

            result = self.drive_sync.upload_file(local_file, drive_parent_id)
            logger.info(f"Синхронизирован файл: {local_file}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при синхронизации {local_file}: {e}")
            return False


# Глобальный экземпляр планировщика
_global_scheduler: Optional[SyncScheduler] = None


def get_scheduler() -> SyncScheduler:
    """Получить глобальный экземпляр планировщика."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = SyncScheduler()
    return _global_scheduler


def start_sync_scheduler(sync_interval_hours: int = 6):
    """
    Запустить планировщик синхронизации.

    Args:
        sync_interval_hours: Интервал синхронизации в часах
    """
    scheduler = get_scheduler()
    scheduler.sync_interval_hours = sync_interval_hours
    scheduler.start()


def stop_sync_scheduler():
    """Остановить планировщик синхронизации."""
    global _global_scheduler
    if _global_scheduler:
        _global_scheduler.stop()
        _global_scheduler = None


def manual_sync():
    """Выполнить ручную синхронизацию."""
    scheduler = get_scheduler()
    return scheduler.sync_now()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Запуск планировщика
    scheduler = get_scheduler()
    scheduler.start()

    # Выполнение синхронизации при запуске
    scheduler.sync_now()

    # Планировщик работает в фоновом потоке
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("Планировщик остановлен")
