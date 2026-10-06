# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Windows Service Entry
# =============================================================================
# Description:
#   Точка входа и обертка Windows Service для фоновой службы AITelemetry.
#   Поддерживает исполнение под управлением Service Control Manager (SCM),
#   а также интерактивный запуск через консоль и CLI-команды win32serviceutil.
#
# Usage Examples:
#   CLI:
#     AITelemetry.exe install
#     AITelemetry.exe start
#     AITelemetry.exe stop
#     AITelemetry.exe restart
#     AITelemetry.exe remove
#     AITelemetry.exe --mode hybrid
#
# File: win_service.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 07:58:00
# =============================================================================

from __future__ import annotations
"""Windows Service реализация для фонового демона сбора телеметрии AI-Breadboard."""

import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Обеспечиваем корректные пути импорта для автономного и скомпилированного режима
_current_dir = Path(__file__).resolve().parent
_project_root = str(_current_dir.parents[2]) if len(_current_dir.parents) >= 3 else str(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Настройка системного логгера для службы
def _setup_service_logging() -> None:
    """Настраивает логирование службы в файл ProgramData и консоль."""
    programdata = os.environ.get('ProgramData') or os.environ.get('ALLUSERSPROFILE')
    if programdata and os.path.exists(programdata):
        base_dir = Path(programdata)
    else:
        appdata = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
        base_dir = Path(appdata) if appdata and os.path.exists(appdata) else Path.home()

    log_dir = base_dir / 'AITelemetry' / 'logs'
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'telemetry.log'
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(file_handler)

        # Stream handler for interactive execution
        if not getattr(sys, 'frozen', False) or sys.stdout is not None:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            ))
            root_logger.addHandler(console_handler)
    except Exception:
        pass


try:
    from logger import logger
except ImportError:
    _setup_service_logging()
    logger = logging.getLogger('AITelemetryService')

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False


if PYWIN32_AVAILABLE:
    class AITelemetryWindowsService(win32serviceutil.ServiceFramework):
        """Windows Service адаптер для службы сбора системной телеметрии AI-Breadboard."""
        _svc_name_ = 'AITelemetry'
        _svc_display_name_ = 'AI-Breadboard Telemetry Service'
        _svc_description_ = 'Фоновая служба мониторинга, сбора телеметрии и аналитики метрик AI-Breadboard'

        def __init__(self, args: List[str]) -> None:
            """Инициализирует экземпляр службы Windows Service."""
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.is_alive = True
            self._service_thread: Optional[threading.Thread] = None

        def SvcStop(self) -> None:
            """Обрабатывает сигнал остановки службы от Service Control Manager (SCM)."""
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            logger.info('SCM запросил остановку службы AITelemetry...')
            self.is_alive = False
            win32event.SetEvent(self.hWaitStop)

            # Сигнализируем главному циклу
            try:
                from apps.windows.telemetry.main import _stop_event
                _stop_event.set()
            except Exception:
                pass

        def SvcShutdown(self) -> None:
            """Обрабатывает сигнал выключения ОС Windows."""
            logger.info('Система выключается. Остановка службы AITelemetry...')
            self.SvcStop()

        def SvcDoRun(self) -> None:
            """Основной метод исполнения службы Windows Service."""
            _setup_service_logging()
            logger.info('Служба AITelemetry запускается под управлением Windows SCM...')
            try:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
            except Exception:
                pass

            self.ReportServiceStatus(win32service.SERVICE_RUNNING)

            try:
                from apps.windows.telemetry.main import run_telemetry_service
                from apps.windows.telemetry.telemetry_config import TelemetryConfigManager

                cfg_mgr = TelemetryConfigManager()
                mode = cfg_mgr.get_mode()
                interval = cfg_mgr.get_interval_seconds()
                heavy_interval = cfg_mgr.get_heavy_interval_seconds()
                top_processes = cfg_mgr.get_effective_process_limit()
                heavy_collectors = cfg_mgr.get_heavy_collectors()

                logger.info(f'Запуск цикла телеметрии (режим: {mode}, интервал: {interval}с, тяжелый: {heavy_interval}с)')
                run_telemetry_service(
                    mode=mode,
                    interval=interval,
                    heavy_interval=heavy_interval,
                    top_processes=top_processes,
                    heavy_collectors=heavy_collectors,
                )
            except Exception as ex:
                logger.error(f'Критическая ошибка при работе службы: {ex}', exc_info=True)
            finally:
                logger.info('Служба AITelemetry завершила работу.')
                self.ReportServiceStatus(win32service.SERVICE_STOPPED)


def run_interactive() -> int:
    """Запускает телеметрию в интерактивном консольном режиме."""
    _setup_service_logging()
    from apps.windows.telemetry.main import main
    return main()


def main_entry() -> int:
    """Главная точка входа исполняемого файла AITelemetry.exe.

    Returns:
        int: Код возврата.
    """
    _setup_service_logging()

    # Проверяем запуск диспетчером SCM без параметров
    if len(sys.argv) == 1:
        if PYWIN32_AVAILABLE:
            try:
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(AITelemetryWindowsService)
                servicemanager.StartServiceCtrlDispatcher()
                return 0
            except Exception as ex:
                # Если запущен не из SCM, переключаемся в консольный режим
                logger.debug(f'Запуск через SCM не удался ({ex}), переход в консольный режим.')
                return run_interactive()
        else:
            return run_interactive()

    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else ''

    # Команды управления службой
    if cmd in ('install', 'update', 'remove', 'start', 'stop', 'restart', 'status'):
        if PYWIN32_AVAILABLE:
            win32serviceutil.HandleCommandLine(AITelemetryWindowsService)
            return 0
        else:
            logger.error('Модуль pywin32 недоступен. Управление службой через SCM невозможно.')
            return 1

    if cmd in ('run', 'interactive', '--mode', '--minimal', '--interval', '--once', '-v', '--verbose', '--help', '-h'):
        return run_interactive()

    # По умолчанию передаем аргументы в главный CLI
    return run_interactive()


if __name__ == '__main__':
    sys.exit(main_entry())
