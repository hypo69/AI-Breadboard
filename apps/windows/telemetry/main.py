# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Telemetry Stream Aggregator Main Entry Point
# =============================================================================
# Description:
#   Главная входная точка CLI для запуска сервиса сбора телеметрии и сенсоров.
#
# File: main.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Главная точка входа для сервиса агрегации телеметрии Windows."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Резолвинг корня проекта для абсолютных импортов
_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger

from apps.windows.telemetry.aggregator import TelemetryAggregator
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager


def parse_arguments() -> argparse.Namespace:
    """Парсит аргументы командной строки.

    Returns:
        argparse.Namespace: Распарсенные аргументы.
    """
    parser = argparse.ArgumentParser(
        description="Windows Telemetry Aggregation Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Переопределить базовый интервал опроса (секунды)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Путь к файлу конфигурации config.json",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Путь к директории для логов телеметрии",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Включить подробный вывод (DEBUG)",
    )
    return parser.parse_args()


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Обработчик сигналов для корректной остановки сервиса.

    Args:
        signum: Номер сигнала.
        frame: Стек вызовов.
    """
    logger.info(f"Получен сигнал {signum}, остановка телеметрии...")
    sys.exit(0)


def main() -> int:
    """Главная точка входа сервиса телеметрии.

    Returns:
        int: Код завершения.
    """
    args = parse_arguments()

    if args.verbose:
        logger.setLevel("DEBUG")

    try:
        config_manager = TelemetryConfigManager(config_path=args.config)
        logger.info("Конфигурация телеметрии загружена")
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        return 1

    if args.interval:
        config_manager._config["interval_seconds"] = args.interval
        logger.info(f"Базовый интервал переопределен: {args.interval} сек")

    try:
        aggregator = TelemetryAggregator(
            config_manager=config_manager,
            log_dir=args.log_dir,
        )
        logger.info("Агрегатор телеметрии инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации агрегатора: {e}")
        return 1

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if not aggregator.start():
            logger.error("Не удалось запустить агрегатор телеметрии")
            return 1

        logger.info("Агрегатор телеметрии успешно запущен")
        logger.info(f"Директория логов: {aggregator.log_dir}")
        logger.info(f"Файл логов: {aggregator.logger.filename}")
        logger.info(f"Включенные сенсоры: {config_manager.get_enabled_sensors()}")

        while True:
            status = aggregator.get_status()
            logger.debug(
                f"Статус телеметрии: {status['measurement_count']} измерений, "
                f"активен: {status['is_running']}"
            )
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    finally:
        aggregator.stop()
        logger.info("Агрегатор телеметрии остановлен")

    return 0


if __name__ == "__main__":
    sys.exit(main())
