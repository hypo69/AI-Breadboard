# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Windows 64-bit Collector (ai_w64_collector)
# =============================================================================
# Description:
#   Максимально детальный сборщик событий Windows для последующего анализа.
#   Собирает ВСЕ изменения в системе: процессы, файлы, реестр, сеть, события.
#   Не содержит логики анализа - только сбор и логгирование.
#
# File: ai_w64_collector.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AI Windows 64-bit Collector - максимальный сборщик событий Windows."""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import logger


class AIW64Collector:
    """Максимально детальный сборщик событий Windows 64-bit."""
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        enable_file_monitoring: bool = True,
        enable_process_monitoring: bool = True,
        enable_registry_monitoring: bool = True,
        enable_network_monitoring: bool = True,
        enable_event_log_monitoring: bool = True,
        monitored_paths: Optional[List[str]] = None,
    ) -> None:
        """Инициализация сборщика.
        
        Args:
            log_dir: Директория для логов (по умолчанию %LOCALAPPDATA%\\AI-Breadboard\\ai_w64_logs)
            enable_file_monitoring: Мониторинг файловой системы
            enable_process_monitoring: Мониторинг процессов
            enable_registry_monitoring: Мониторинг реестра
            enable_network_monitoring: Мониторинг сети
            enable_event_log_monitoring: Мониторинг событий Windows
            monitored_paths: Список путей для мониторинга
        """
        self.log_dir = log_dir or str(
            Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))) 
            / "AI-Breadboard" / "ai_w64_logs"
        )
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Настройки мониторинга
        self.enable_file_monitoring = enable_file_monitoring
        self.enable_process_monitoring = enable_process_monitoring
        self.enable_registry_monitoring = enable_registry_monitoring
        self.enable_network_monitoring = enable_network_monitoring
        self.enable_event_log_monitoring = enable_event_log_monitoring
        
        # Пути для мониторинга
        self.monitored_paths = monitored_paths or [
            r"C:\Users\%USERNAME%\Documents",
            r"C:\Users\%USERNAME%\Downloads",
            r"C:\Users\%USERNAME%\Desktop",
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Windows\System32",
            r"C:\Windows\SysWOW64",
        ]
        
        # Состояние
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_counter = 0
        self._last_baseline: Dict[str, Any] = {}
        
        # Логгеры
        self._loggers: Dict[str, Any] = {}
        
        logger.info(f"AIW64Collector initialized. Log dir: {self.log_dir}")
    
    def _get_log_file(self, event_type: str) -> Path:
        """Получить файл лога для типа события."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return Path(self.log_dir) / f"{event_type}_{date_str}.jsonl"
    
    def _log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Записать событие в лог."""
        self._event_counter += 1
        event_data["event_id"] = f"evt_{int(time.time())}_{self._event_counter}"
        event_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        event_data["event_type"] = event_type
        
        log_file = self._get_log_file(event_type)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
        
        # Логируем в основной лог
        logger.debug(f"AIW64: {event_type} - {event_data.get('event_id', 'N/A')}")
    
    def start(self) -> bool:
        """Запустить сборщик."""
        if self._running:
            logger.warning("AIW64Collector уже запущен")
            return False
        
        self._running = True
        self._stop_event.clear()
        
        # Устанавливаем начальный baseline
        self._update_baseline()
        
        # Запускаем потоки мониторинга
        self._thread = threading.Thread(target=self._monitoring_loop, name="AIW64Collector", daemon=True)
        self._thread.start()
        
        logger.info("AIW64Collector started")
        return True
    
    def stop(self) -> bool:
        """Остановить сборщик."""
        if not self._running:
            return False
        
        self._running = False
        self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        logger.info(f"AIW64Collector stopped. Total events: {self._event_counter}")
        return True
    
    def _update_baseline(self) -> None:
        """Обновить baseline для сравнения."""
        self._last_baseline = {
            "processes": self._get_current_processes(),
            "network_connections": self._get_current_network_connections(),
            "registry_keys": self._get_registry_keys(),
            "file_hashes": self._get_file_hashes(),
        }
    
    def _monitoring_loop(self) -> None:
        """Основной цикл мониторинга."""
        last_check = time.time()
        check_interval = 1.0  # Проверка каждую секунду
        
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # Проверяем интервал
                if current_time - last_check >= check_interval:
                    # Собираем текущее состояние
                    current_state = {
                        "processes": self._get_current_processes(),
                        "network_connections": self._get_current_network_connections(),
                        "registry_keys": self._get_registry_keys(),
                        "file_hashes": self._get_file_hashes(),
                    }
                    
                    # Сравниваем с baseline
                    self._detect_changes(self._last_baseline, current_state)
                    
                    # Обновляем baseline
                    self._last_baseline = current_state
                    last_check = current_time
                
                # Спим короткое время
                self._stop_event.wait(timeout=0.1)
                
            except Exception as ex:
                logger.error(f"Ошибка в цикле мониторинга: {ex}")
    
    def _detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """Обнаружить изменения между состояниями."""
        # Процессы
        if self.enable_process_monitoring:
            self._detect_process_changes(old_state["processes"], new_state["processes"])
        
        # Сеть
        if self.enable_network_monitoring:
            self._detect_network_changes(old_state["network_connections"], new_state["network_connections"])
        
        # Реестр
        if self.enable_registry_monitoring:
            self._detect_registry_changes(old_state["registry_keys"], new_state["registry_keys"])
        
        # Файлы
        if self.enable_file_monitoring:
            self._detect_file_changes(old_state["file_hashes"], new_state["file_hashes"])
    
    def _get_current_processes(self) -> List[Dict[str, Any]]:
        """Получить текущие процессы."""
        processes = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'cpu_percent', 'memory_info', 'num_threads', 'status']):
                try:
                    info = proc.info
                    mem_info = info.get('memory_info')
                    processes.append({
                        "pid": info.get('pid'),
                        "name": info.get('name'),
                        "exe": info.get('exe'),
                        "cmdline": info.get('cmdline'),
                        "username": info.get('username'),
                        "cpu_percent": info.get('cpu_percent') or 0.0,
                        "memory_mb": round((mem_info.rss / 1024 / 1024), 2) if mem_info else 0.0,
                        "num_threads": info.get('num_threads') or 1,
                        "status": info.get('status'),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as ex:
            logger.debug(f"Ошибка получения процессов: {ex}")
        
        return processes
    
    def _detect_process_changes(self, old_procs: List[Dict], new_procs: List[Dict]) -> None:
        """Обнаружить изменения в процессах."""
        old_pids = {p["pid"] for p in old_procs if p.get("pid")}
        new_pids = {p["pid"] for p in new_procs if p.get("pid")}
        
        # Новые процессы
        new_process_pids = new_pids - old_pids
        for pid in new_process_pids:
            proc = next((p for p in new_procs if p.get("pid") == pid), None)
            if proc:
                self._log_event("process_start", {
                    "pid": proc["pid"],
                    "name": proc["name"],
                    "exe": proc["exe"],
                    "cmdline": proc["cmdline"],
                    "username": proc["username"],
                    "cpu_percent": proc["cpu_percent"],
                    "memory_mb": proc["memory_mb"],
                })
        
        # Завершенные процессы
        terminated_pids = old_pids - new_pids
        for pid in terminated_pids:
            proc = next((p for p in old_procs if p.get("pid") == pid), None)
            if proc:
                self._log_event("process_terminate", {
                    "pid": proc["pid"],
                    "name": proc["name"],
                    "exe": proc["exe"],
                    "cpu_percent": proc["cpu_percent"],
                    "memory_mb": proc["memory_mb"],
                })
        
        # Изменение метрик процессов
        for new_proc in new_procs:
            if not new_proc.get("pid"):
                continue
            old_proc = next((p for p in old_procs if p.get("pid") == new_proc["pid"]), None)
            if old_proc:
                # Проверяем изменения CPU
                cpu_diff = new_proc.get("cpu_percent", 0) - old_proc.get("cpu_percent", 0)
                if abs(cpu_diff) > 5.0:  # Изменение > 5%
                    self._log_event("process_cpu_change", {
                        "pid": new_proc["pid"],
                        "name": new_proc["name"],
                        "cpu_before": old_proc.get("cpu_percent"),
                        "cpu_after": new_proc.get("cpu_percent"),
                        "cpu_delta": cpu_diff,
                    })
                
                # Проверяем изменения памяти
                mem_diff = new_proc.get("memory_mb", 0) - old_proc.get("memory_mb", 0)
                if abs(mem_diff) > 10.0:  # Изменение > 10 MB
                    self._log_event("process_memory_change", {
                        "pid": new_proc["pid"],
                        "name": new_proc["name"],
                        "memory_before": old_proc.get("memory_mb"),
                        "memory_after": new_proc.get("memory_mb"),
                        "memory_delta_mb": mem_diff,
                    })
    
    def _get_current_network_connections(self) -> List[Dict[str, Any]]:
        """Получить текущие сетевые соединения."""
        connections = []
        try:
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                if conn.status in ('ESTABLISHED', 'LISTEN', 'TIME_WAIT'):
                    connections.append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        "status": conn.status,
                        "pid": conn.pid,
                        "type": "TCP" if conn.type == 1 else "UDP",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception as ex:
            logger.debug(f"Ошибка получения сетевых соединений: {ex}")
        
        return connections
    
    def _detect_network_changes(self, old_conns: List[Dict], new_conns: List[Dict]) -> None:
        """Обнаружить изменения в сетевых соединениях."""
        old_keys = {f"{c['local_address']}_{c['remote_address']}_{c['type']}" for c in old_conns}
        new_keys = {f"{c['local_address']}_{c['remote_address']}_{c['type']}" for c in new_conns}
        
        # Новые соединения
        new_keys_set = new_keys - old_keys
        for key in new_keys_set:
            conn = next((c for c in new_conns if f"{c['local_address']}_{c['remote_address']}_{c['type']}" == key), None)
            if conn:
                self._log_event("network_connection_new", conn)
        
        # Закрытые соединения
        closed_keys = old_keys - new_keys
        for key in closed_keys:
            conn = next((c for c in old_conns if f"{c['local_address']}_{c['remote_address']}_{c['type']}" == key), None)
            if conn:
                self._log_event("network_connection_closed", conn)
    
    def _get_registry_keys(self) -> Dict[str, Any]:
        """Получить ключи реестра (ограниченный набор для производительности)."""
        registry_data = {}
        try:
            import winreg
            
            # Основные ветки
            hives = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services"),
            ]
            
            for hive, subkey in hives:
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        values = []
                        for i in range(winreg.QueryInfoKey(key)[1]):
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                values.append({"name": name, "value": str(value)})
                            except OSError:
                                break
                        registry_data[f"{hive}_{subkey}"] = values
                except OSError:
                    continue
        except Exception as ex:
            logger.debug(f"Ошибка получения реестра: {ex}")
        
        return registry_data
    
    def _detect_registry_changes(self, old_reg: Dict, new_reg: Dict) -> None:
        """Обнаружить изменения в реестре."""
        for key, new_values in new_reg.items():
            old_values = old_reg.get(key, [])
            
            old_names = {v["name"] for v in old_values}
            new_names = {v["name"] for v in new_values}
            
            # Новые значения
            for name in new_names - old_names:
                value = next((v for v in new_values if v["name"] == name), None)
                if value:
                    self._log_event("registry_value_created", {
                        "key": key,
                        "name": value["name"],
                        "value": value["value"],
                    })
            
            # Измененные значения
            for name in new_names & old_names:
                new_val = next((v for v in new_values if v["name"] == name), None)
                old_val = next((v for v in old_values if v["name"] == name), None)
                if new_val and old_val and new_val["value"] != old_val["value"]:
                    self._log_event("registry_value_modified", {
                        "key": key,
                        "name": new_val["name"],
                        "old_value": old_val["value"],
                        "new_value": new_val["value"],
                    })
            
            # Удаленные значения
            for name in old_names - new_names:
                self._log_event("registry_value_deleted", {
                    "key": key,
                    "name": name,
                })
    
    def _get_file_hashes(self) -> Dict[str, str]:
        """Получить хэши файлов для мониторинга изменений."""
        file_hashes = {}
        try:
            import hashlib
            
            # Проверяем только файлы из monitored_paths
            for path in self.monitored_paths:
                path = path.replace("%USERNAME%", os.environ.get("USERNAME", "user"))
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files[:100]:  # Ограничиваем до 100 файлов на путь
                            try:
                                filepath = os.path.join(root, file)
                                with open(filepath, 'rb') as f:
                                    file_hash = hashlib.md5(f.read(4096)).hexdigest()
                                file_hashes[filepath] = file_hash
                            except (IOError, PermissionError):
                                continue
                        break  # Только один уровень вглубь
        except Exception as ex:
            logger.debug(f"Ошибка получения хэшей файлов: {ex}")
        
        return file_hashes
    
    def _detect_file_changes(self, old_hashes: Dict[str, str], new_hashes: Dict[str, str]) -> None:
        """Обнаружить изменения в файлах."""
        old_paths = set(old_hashes.keys())
        new_paths = set(new_hashes.keys())
        
        # Новые файлы
        for path in new_paths - old_paths:
            self._log_event("file_created", {
                "path": path,
                "hash": new_hashes[path],
            })
        
        # Удаленные файлы
        for path in old_paths - new_paths:
            self._log_event("file_deleted", {
                "path": path,
                "hash": old_hashes[path],
            })
        
        # Измененные файлы
        for path in old_paths & new_paths:
            if old_hashes[path] != new_hashes[path]:
                self._log_event("file_modified", {
                    "path": path,
                    "old_hash": old_hashes[path],
                    "new_hash": new_hashes[path],
                })
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус сборщика."""
        return {
            "running": self._running,
            "log_dir": self.log_dir,
            "total_events": self._event_counter,
            "monitored_paths": self.monitored_paths,
            "settings": {
                "file_monitoring": self.enable_file_monitoring,
                "process_monitoring": self.enable_process_monitoring,
                "registry_monitoring": self.enable_registry_monitoring,
                "network_monitoring": self.enable_network_monitoring,
                "event_log_monitoring": self.enable_event_log_monitoring,
            },
        }
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить события из логов."""
        events = []
        
        log_files = []
        if event_type:
            log_files = [self._get_log_file(event_type)]
        else:
            # Все типы событий
            for f in Path(self.log_dir).glob("*.jsonl"):
                log_files.append(f)
        
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            events.append(event)
                        except json.JSONDecodeError:
                            continue
            except Exception as ex:
                logger.debug(f"Ошибка чтения лога {log_file}: {ex}")
        
        # Сортируем по времени и берем последние
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return events[:limit]
    
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить события определенного типа."""
        return self.get_events(event_type=event_type, limit=limit)
    
    def get_events_by_time_range(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Получить события за временной диапазон."""
        all_events = self.get_events()
        return [
            e for e in all_events
            if start_time <= e.get("timestamp", "") <= end_time
        ]


# Глобальный экземпляр
_w64_collector: Optional[AIW64Collector] = None


def get_w64_collector(**kwargs) -> AIW64Collector:
    """Получить или создать глобальный экземпляр сборщика."""
    global _w64_collector
    
    if _w64_collector is None:
        _w64_collector = AIW64Collector(**kwargs)
    
    return _w64_collector


def start_w64_collector(**kwargs) -> AIW64Collector:
    """Запустить глобальный сборщик."""
    collector = get_w64_collector(**kwargs)
    collector.start()
    return collector


def stop_w64_collector() -> bool:
    """Остановить глобальный сборщик."""
    global _w64_collector
    
    if _w64_collector:
        return _w64_collector.stop()
    return False


__all__ = [
    "AIW64Collector",
    "get_w64_collector",
    "start_w64_collector",
    "stop_w64_collector",
]
