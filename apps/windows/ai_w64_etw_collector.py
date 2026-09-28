"""ETW Collector для максимального сбора событий Windows."""
from __future__ import annotations
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger

class AIW64ETWCollector:
    """Сборщик событий через ETW (Event Tracing for Windows)."""

    def __init__(self, log_dir: Optional[str]=None, enable_process_trace: bool=True, enable_disk_trace: bool=True, enable_network_trace: bool=True, enable_registry_trace: bool=True) -> None:
        """Инициализация ETW сборщика.
        
        Args:
            log_dir: Директория для логов
            enable_process_trace: Трассировка процессов
            enable_disk_trace: Трассировка диска
            enable_network_trace: Трассировка сети
            enable_registry_trace: Трассировка реестра
        """
        self.log_dir = log_dir or str(Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / 'AI-Breadboard' / 'ai_w64_etw_logs')
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        self.enable_process_trace = enable_process_trace
        self.enable_disk_trace = enable_disk_trace
        self.enable_network_trace = enable_network_trace
        self.enable_registry_trace = enable_registry_trace
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_counter = 0
        logger.info(f'AIW64ETWCollector initialized. Log dir: {self.log_dir}')

    def start(self) -> bool:
        """Запустить ETW трассировку."""
        if self._running:
            logger.warning('ETW Collector уже запущен')
            return False
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._etw_loop, name='AIW64ETWCollector', daemon=True)
        self._thread.start()
        logger.info('AIW64ETWCollector started')
        return True

    def stop(self) -> bool:
        """Остановить ETW трассировку."""
        if not self._running:
            return False
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info(f'AIW64ETWCollector stopped. Total events: {self._event_counter}')
        return True

    def _etw_loop(self) -> None:
        """Основной цикл ETW трассировки."""
        while not self._stop_event.is_set():
            try:
                self._collect_etw_events()
                self._stop_event.wait(timeout=5.0)
            except Exception as ex:
                logger.error(f'Ошибка в ETW цикле: {ex}')

    def _collect_etw_events(self) -> None:
        """Собрать ETW события."""
        if self.enable_process_trace:
            self._collect_process_events()
        if self.enable_disk_trace:
            self._collect_file_events()
        if self.enable_network_trace:
            self._collect_network_events()
        if self.enable_registry_trace:
            self._collect_registry_events()

    def _collect_process_events(self) -> None:
        """Собрать события создания процессов."""
        try:
            ps_script = "\n            $startTime = (Get-Date).AddMinutes(-1)\n            $events = Get-WinEvent -FilterHashtable @{\n                LogName = 'Security'\n                Id = 4688\n                StartTime = $startTime\n            } -MaxEvents 100 -ErrorAction SilentlyContinue\n            \n            foreach ($e in $events) {\n                $xml = [xml]$e.ToXml()\n                $data = @{}\n                foreach ($d in $xml.Event.EventData.Data) {\n                    $data[$d.Name] = $d.'#text'\n                }\n                $data | ConvertTo-Json -Compress\n            }\n            "
            res = subprocess.run(f'powershell.exe -NoProfile -NonInteractive -Command "& {{ {ps_script} }}"', capture_output=True, text=True, timeout=10, shell=True)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._log_event('etw_process_create', event)
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка сбора событий процессов: {ex}')

    def _collect_file_events(self) -> None:
        """Собрать события файловой операций."""
        try:
            ps_script = "\n            $startTime = (Get-Date).AddMinutes(-1)\n            $events = Get-WinEvent -FilterHashtable @{\n                LogName = 'Security'\n                Id = 4663\n                StartTime = $startTime\n            } -MaxEvents 100 -ErrorAction SilentlyContinue\n            \n            foreach ($e in $events) {\n                $xml = [xml]$e.ToXml()\n                $data = @{}\n                foreach ($d in $xml.Event.EventData Data) {\n                    $data[$d.Name] = $d.'#text'\n                }\n                $data | ConvertTo-Json -Compress\n            }\n            "
            res = subprocess.run(f'powershell.exe -NoProfile -NonInteractive -Command "& {{ {ps_script} }}"', capture_output=True, text=True, timeout=10, shell=True)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._log_event('etw_file_access', event)
                        except json.JSONDecodeError:
                            continue
        except Exception as ex:
            logger.debug(f'Ошибка сбора событий файлов: {ex}')

    def _collect_network_events(self) -> None:
        """Собрать события сетевых соединений."""
        try:
            ps_script = '\n            $connections = Get-NetTCPConnection -State Listen,Established -ErrorAction SilentlyContinue\n            $connections | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess |\n                ConvertTo-Json -Compress\n            '
            res = subprocess.run(f'powershell.exe -NoProfile -NonInteractive -Command "& {{ {ps_script} }}"', capture_output=True, text=True, timeout=10, shell=True)
            if res.returncode == 0 and res.stdout.strip():
                try:
                    connections = json.loads(res.stdout.strip())
                    if isinstance(connections, list):
                        for conn in connections:
                            self._log_event('etw_network_connection', conn)
                    else:
                        self._log_event('etw_network_connection', connections)
                except json.JSONDecodeError:
                    pass
        except Exception as ex:
            logger.debug(f'Ошибка сбора сетевых событий: {ex}')

    def _collect_registry_events(self) -> None:
        """Собрать события реестра."""
        try:
            from apps.windows.core.process_audit_manager import ProcessAuditManager
            from apps.windows.api.wevtapi import WevtAPI
            manager = ProcessAuditManager(WevtAPI())
            events = manager.get_process_execution_history(limit=50)
            for event in events:
                self._log_event('etw_registry_access', event)
        except Exception as ex:
            logger.debug(f'Ошибка сбора событий реестра: {ex}')

    def _log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Записать событие в лог."""
        self._event_counter += 1
        event_data['event_id'] = f'etw_{int(time.time())}_{self._event_counter}'
        event_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        event_data['event_type'] = event_type
        log_file = Path(self.log_dir) / f"{event_type}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
        logger.debug(f"ETW: {event_type} - {event_data.get('event_id', 'N/A')}")

    def get_status(self) -> Dict[str, Any]:
        """Получить статус ETW сборщика."""
        return {'running': self._running, 'log_dir': self.log_dir, 'total_events': self._event_counter, 'settings': {'process_trace': self.enable_process_trace, 'disk_trace': self.enable_disk_trace, 'network_trace': self.enable_network_trace, 'registry_trace': self.enable_registry_trace}}
__all__ = ['AIW64ETWCollector']