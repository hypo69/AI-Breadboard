#!/usr/bin/env python3
"""
Скрипт для настройки и инициализации синхронизации на Google Drive.

Использование:
    python setup_google_drive_sync.py --init              # Инициализация
    python setup_google_drive_sync.py --sync-now          # Синхронизировать
    python setup_google_drive_sync.py --start-scheduler   # Запустить планировщик
    python setup_google_drive_sync.py --status            # Получить статус
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

# Добавление пути к пакетам
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "integrations"))

from google_drive_sync import GoogleDriveSync
from sync_scheduler import SyncScheduler, ManualSyncHandler

# Конфигурация логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sync_setup.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class SyncSetup:
    """Класс для настройки синхронизации."""

    def __init__(self):
        self.config_file = "sync_config.json"
        self.load_config()

    def load_config(self):
        """Загрузить конфигурацию."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "service_account_file": "src/secrets/google_sa_account_service_account.json",
                "sync_interval_hours": 6,
                "sync_on_startup": False,
                "include_data": True,
                "include_logs": True,
                "include_secrets": True,
                "include_configs": True,
                "exclude_patterns": ["*.pyc", "__pycache__", ".git"],
            }
            self.save_config()

    def save_config(self):
        """Сохранить конфигурацию."""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Конфигурация сохранена: {self.config_file}")

    def initialize(self):
        """Инициализировать синхронизацию."""
        print("\n" + "=" * 60)
        print("ИНИЦИАЛИЗАЦИЯ СИНХРОНИЗАЦИИ НА GOOGLE DRIVE")
        print("=" * 60 + "\n")

        # Проверка файла сервис-аккаунта
        service_account_file = self.config["service_account_file"]
        if not os.path.exists(service_account_file):
            logger.warning(f"⚠️  Файл сервис-аккаунта не найден: {service_account_file}")
            print(f"\nОшибка: Файл сервис-аккаунта не найден: {service_account_file}")
            print("\nШаги для исправления:")
            print(
                "1. Загрузите файл сервис-аккаунта от Google Cloud (JSON ключ)"
            )
            print(f"2. Скопируйте его в: {service_account_file}")
            print(
                "3. Убедитесь, что у сервис-аккаунта есть доступ к Google Drive"
            )
            return False

        # Инициализация Google Drive сервиса
        print("Инициализация Google Drive сервиса...")
        sync = GoogleDriveSync(service_account_file)

        if sync.drive_service is None:
            logger.error("❌ Ошибка: Не удалось инициализировать Google Drive сервис")
            print("\n❌ Ошибка инициализации Google Drive сервиса")
            return False

        # Создание папки синхронизации
        print("Создание папки синхронизации на Google Drive...")
        folder_id = sync.ensure_sync_folder()

        if not folder_id:
            logger.error("❌ Ошибка: Не удалось создать папку синхронизации")
            print("\n❌ Ошибка при создании папки синхронизации")
            return False

        print(f"✓ Папка синхронизации создана: {folder_id}")
        print(f"✓ Google Drive URL: https://drive.google.com/drive/folders/{folder_id}")

        # Успешная инициализация
        print("\n✓ Синхронизация успешно инициализирована!")
        print("\nСледующие шаги:")
        print("- Запустите синхронизацию: python setup_google_drive_sync.py --sync-now")
        print(
            "- Или запустите планировщик: python setup_google_drive_sync.py --start-scheduler"
        )

        return True

    def sync_now(self):
        """Выполнить синхронизацию."""
        print("\n" + "=" * 60)
        print("СИНХРОНИЗАЦИЯ ДАННЫХ НА GOOGLE DRIVE")
        print("=" * 60 + "\n")

        try:
            sync = GoogleDriveSync(self.config["service_account_file"])
            sync.ensure_sync_folder()

            print("Синхронизация начата...\n")

            results = sync.sync_all_data()

            # Вывод результатов
            print("\n" + "=" * 60)
            print("РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ")
            print("=" * 60)
            print(json.dumps(results, indent=2, ensure_ascii=False))

            # Суммарная статистика
            total_uploaded = sum(
                r.get("uploaded", 0) for r in results.values() if isinstance(r, dict)
            )
            total_failed = sum(
                r.get("failed", 0) for r in results.values() if isinstance(r, dict)
            )

            print(f"\n✓ Синхронизация завершена!")
            print(f"✓ Всего загружено: {total_uploaded} файлов")
            print(f"⚠️  Ошибок: {total_failed}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при синхронизации: {e}")
            print(f"\n❌ Ошибка при синхронизации: {e}")
            return False

    def start_scheduler(self):
        """Запустить планировщик синхронизации."""
        print("\n" + "=" * 60)
        print("ЗАПУСК ПЛАНИРОВЩИКА СИНХРОНИЗАЦИИ")
        print("=" * 60 + "\n")

        try:
            scheduler = SyncScheduler(self.config["sync_interval_hours"])
            scheduler.start()

            print(f"✓ Планировщик запущен!")
            print(
                f"✓ Интервал синхронизации: {self.config['sync_interval_hours']} часов"
            )
            print("✓ Синхронизация будет происходить автоматически\n")

            # Информация о статусе
            print("Чтобы проверить статус:")
            print("  python setup_google_drive_sync.py --status\n")

            print("Нажмите Ctrl+C для остановки планировщика")

            # Ожидание сигнала остановки
            try:
                import time

                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nПланировщик остановлен.")
                scheduler.stop()

        except Exception as e:
            logger.error(f"Ошибка при запуске планировщика: {e}")
            print(f"\n❌ Ошибка при запуске планировщика: {e}")
            return False

    def show_status(self):
        """Показать статус синхронизации."""
        print("\n" + "=" * 60)
        print("СТАТУС СИНХРОНИЗАЦИИ")
        print("=" * 60 + "\n")

        try:
            sync = GoogleDriveSync(self.config["service_account_file"])
            status = sync.get_sync_status()

            if status:
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                print("Информация о синхронизации не найдена")

            print("\nКонфигурация:")
            print(json.dumps(self.config, indent=2, ensure_ascii=False))

        except Exception as e:
            logger.error(f"Ошибка при получении статуса: {e}")
            print(f"\n❌ Ошибка при получении статуса: {e}")

    def show_help(self):
        """Показать справку."""
        help_text = """
СИНХРОНИЗАЦИЯ ДАННЫХ НА GOOGLE DRIVE

Использование:
  python setup_google_drive_sync.py [ОПЦИЯ]

Опции:
  --init                 Инициализировать синхронизацию
  --sync-now             Выполнить синхронизацию немедленно
  --start-scheduler      Запустить автоматический планировщик
  --status              Показать статус синхронизации
  --help                Показать эту справку

Примеры:
  # Первый запуск
  python setup_google_drive_sync.py --init

  # Синхронизировать данные
  python setup_google_drive_sync.py --sync-now

  # Запустить автоматическую синхронизацию
  python setup_google_drive_sync.py --start-scheduler

  # Проверить статус
  python setup_google_drive_sync.py --status
        """
        print(help_text)


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="Синхронизация данных на Google Drive", add_help=False
    )

    parser.add_argument("--init", action="store_true", help="Инициализировать синхронизацию")
    parser.add_argument(
        "--sync-now", action="store_true", help="Выполнить синхронизацию немедленно"
    )
    parser.add_argument(
        "--start-scheduler",
        action="store_true",
        help="Запустить автоматический планировщик",
    )
    parser.add_argument("--status", action="store_true", help="Показать статус синхронизации")
    parser.add_argument("--help", action="store_true", help="Показать справку")

    args = parser.parse_args()

    setup = SyncSetup()

    if args.help or not any(vars(args).values()):
        setup.show_help()
    elif args.init:
        setup.initialize()
    elif args.sync_now:
        setup.sync_now()
    elif args.start_scheduler:
        setup.start_scheduler()
    elif args.status:
        setup.show_status()


if __name__ == "__main__":
    main()
