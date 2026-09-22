# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Windows 64-bit Collector Launcher
# =============================================================================
# Description:
#   Запуск и управление всеми сборщиками событий Windows.
#
# File: ai_w64_collector_launcher.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Запуск и управление AI Windows 64-bit Collector."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import logger

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.windows.ai_w64_collector import AIW64Collector, get_w64_collector, start_w64_collector, stop_w64_collector
from apps.windows.ai_w64_etw_collector import AIW64ETWCollector


class AIW64CollectorManager:
    """Менеджер управления всеми сборщиками событий Windows."""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Инициализация менеджера.
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        self.config_path = config_path or str(Path(__file__).parent / "ai_w64_collector_config.json")
        self.config = self._load_config()
        
        self.w64_collector: Optional[AIW64Collector] = None
        self.etw_collector: Optional[AIW64ETWCollector] = None
        self._running = False
        
        logger.info("AIW64CollectorManager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Загрузить конфигурацию."""
        default_config = {
            "log_dir": None,
            "monitored_paths": [
                r"C:\Users\%USERNAME%\Documents",
                r"C:\Users\%USERNAME%\Downloads",
                r"C:\Users\%USERNAME%\Desktop",
                r"C:\Program Files",
                r"C:\Program Files (x86)",
                r"C:\Windows\System32",
                r"C:\Windows\SysWOW64",
            ],
            "enable_file_monitoring": True,
            "enable_process_monitoring": True,
            "enable_registry_monitoring": True,
            "enable_network_monitoring": True,
            "enable_event_log_monitoring": True,
            "enable_process_trace": True,
            "enable_disk_trace": True,
            "enable_network_trace": True,
            "enable_registry_trace": True,
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as ex:
                logger.warning(f"Ошибка загрузки конфигурации: {ex}")
        
        return default_config
    
    def start(self) -> bool:
        """Запустить все сборщики."""
        if self._running:
            logger.warning("Все сборщики уже запущены")
            return False
        
        logger.info("Запуск AI Windows 64-bit Collector...")
        
        # Запускаем основной сборщик
        self.w64_collector = AIW64Collector(
            log_dir=self.config.get("log_dir"),
            monitored_paths=self.config.get("monitored_paths", []),
            enable_file_monitoring=self.config.get("enable_file_monitoring", True),
            enable_process_monitoring=self.config.get("enable_process_monitoring", True),
            enable_registry_monitoring=self.config.get("enable_registry_monitoring", True),
            enable_network_monitoring=self.config.get("enable_network_monitoring", True),
            enable_event_log_monitoring=self.config.get("enable_event_log_monitoring", True),
        )
        self.w64_collector.start()
        
        # Запускаем ETW сборщик
        self.etw_collector = AIW64ETWCollector(
            log_dir=self.config.get("log_dir"),
            enable_process_trace=self.config.get("enable_process_trace", True),
            enable_disk_trace=self.config.get("enable_disk_trace", True),
            enable_network_trace=self.config.get("enable_network_trace", True),
            enable_registry_trace=self.config.get("enable_registry_trace", True),
        )
        self.etw_collector.start()
        
        self._running = True
        logger.info("Все сборщики запущены")
        return True
    
    def stop(self) -> bool:
        """Остановить все сборщики."""
        if not self._running:
            return False
        
        logger.info("Остановка AI Windows 64-bit Collector...")
        
        if self.etw_collector:
            self.etw_collector.stop()
        
        if self.w64_collector:
            self.w64_collector.stop()
        
        self._running = False
        logger.info("Все сборщики остановлены")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус всех сборщиков."""
        status = {
            "running": self._running,
            "w64_collector": self.w64_collector.get_status() if self.w64_collector else None,
            "etw_collector": self.etw_collector.get_status() if self.etw_collector else None,
        }
        return status
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить события из всех сборщиков."""
        events = []
        
        if self.w64_collector:
            events.extend(self.w64_collector.get_events(event_type=event_type, limit=limit))
        
        if self.etw_collector:
            # ETW события не поддерживают фильтрацию по типу
            events.extend(self.etw_collector.get_events(event_type=event_type, limit=limit))
        
        # Сортируем по времени
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return events[:limit]
    
    def save_config(self) -> None:
        """Сохранить конфигурацию."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info(f"Конфигурация сохранена: {self.config_path}")


def main() -> int:
    """Главная функция."""
    parser = argparse.ArgumentParser(description="AI Windows 64-bit Collector")
    parser.add_argument("--start", action="store_true", help="Запустить сборщики")
    parser.add_argument("--stop", action="store_true", help="Остано��ить сборщики")
    parser.add_argument("--status", action="store_true", help="Показать статус")
    parser.add_argument("--events", action="store_true", help="Показать последние события")
    parser.add_argument("--event-type", type=str, help="Фильтр по типу события")
    parser.add_argument("--limit", type=int, default=100, help="Лимит событий")
    parser.add_argument("--config", type=str, help="Путь к конфигурационному файлу")
    
    args = parser.parse_args()
    
    manager = AIW64CollectorManager(config_path=args.config)
    
    if args.start:
        manager.start()
        print("AI Windows 64-bit Collector запущен")
        print(f"Логи: {manager.w64_collector.log_dir if manager.w64_collector else 'N/A'}")
        return 0
    
    if args.stop:
        manager.stop()
        print("AI Windows 64-bit Collector остановлен")
        return 0
    
    if args.status:
        status = manager.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
        return 0
    
    if args.events:
        events = manager.get_events(event_type=args.event_type, limit=args.limit)
        print(json.dumps(events, indent=2, ensure_ascii=False, default=str))
        return 0
    
    # Если ничего не указано, показать помощь
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
