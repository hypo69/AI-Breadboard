# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Sensors Main Entry Point
# =============================================================================
# Description:
#   Главный входной点 для AI-Sensors telemetry aggregator.
#
# File: main.py
# Project: ai-sensors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Главный входной точка для AI-Sensors telemetry aggregator."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from typing import Optional

from logger import logger

from core.aggregator import TelemetryAggregator
from utils.config import ConfigManager


def parse_arguments() -> argparse.Namespace:
    """Парсит аргументы командной строки.

    Returns:
        argparse.Namespace: Парсенные аргументы.
    """
    parser = argparse.ArgumentParser(
        description="AI-Sensors telemetry aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Override interval from config.json (seconds)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.json",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Path to log directory",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Обработчик сигналов для корректной остановки.

    Args:
        signum: Номер сигнала.
        frame: Стек вызовов.
    """
    logger.info(f"Получен сигнал {signum}, остановка...")
    sys.exit(0)


def main() -> int:
    """Главный入口点.

    Returns:
        int: Код завершения.
    """
    args = parse_arguments()

    # Настройка логгера
    if args.verbose:
        logger.setLevel("DEBUG")

    # Инициализация конфигурации
    try:
        config_manager = ConfigManager(config_path=args.config)
        logger.info("Конфигурация загружена")
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        return 1

    # Если интервал переопределен в командной строке
    if args.interval:
        config_manager._config["interval_seconds"] = args.interval
        logger.info(f"Интервал переопределен: {args.interval} сек")

    # Инициализация агрегатора
    try:
        aggregator = TelemetryAggregator(
            config_manager=config_manager,
            log_dir=args.log_dir,
        )
        logger.info("Агрегатор телеметрии инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации агрегатора: {e}")
        return 1

    # Установка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Запуск агрегатора
    try:
        if not aggregator.start():
            logger.error("Не удалось запустить агрегатор")
            return 1

        logger.info("Агрегатор телеметрии запущен")
        logger.info(f"Лог-директория: {aggregator.log_dir}")
        logger.info(f"Лог-файл: {aggregator.logger.filename}")
        logger.info(f"Включенные сенсоры: {config_manager.get_enabled_sensors()}")

        # Цикл ожидания
        while True:
            status = aggregator.get_status()
            logger.debug(
                f"Статус: {status['measurement_count']} измерений, "
                f"запущен: {status['is_running']}"
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
