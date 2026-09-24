# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ninite Auto-Updater & Task Scheduler Router
# =============================================================================
# Description:
#   Управление автоматическим обновлением ПО через Ninite:
#   - Загрузка пользовательского инсталлятора, переименование в ninite.exe и размещение в Program Files\Ninite
#   - Настройка интервала (по умолчанию 2 недели) и времени (по умолчанию 20:00) обновления
#   - Создание и управление регламентной задачей в Windows Task Scheduler
#   - Ручной запуск и отслеживание статуса исполнения
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from src.api.router_ninite import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router_ninite.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для управления автоматическим обновлением ПО через Ninite и Windows Task Scheduler."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from logger import logger


# Пути по умолчанию
PROGRAM_FILES_DIR = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
NINITE_DIR = PROGRAM_FILES_DIR / "Ninite"
NINITE_EXE = NINITE_DIR / "ninite.exe"
NINITE_LOG = NINITE_DIR / "ninite_update.log"
TASK_NAME = "NiniteAutoUpdate"


class NiniteScheduleRequest(BaseModel):
    """Модель запроса настройки расписания Windows Task Scheduler."""

    interval_weeks: int = Field(default=2, ge=1, le=52, description="Интервал обновления в неделях")
    time_str: str = Field(default="20:00", pattern=r"^\d{2}:\d{2}$", description="Время запуска в формате ЧЧ:ММ")
    days_of_week: str = Field(default="Sunday", description="День недели для запуска (Sunday, Monday, etc.)")


def _run_powershell(command: str) -> subprocess.CompletedProcess[str]:
    """Выполняет PowerShell команду и возвращает результат.

    Args:
        command: Командная строка PowerShell.

    Returns:
        subprocess.CompletedProcess: Результат выполнения команды.
    """
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _get_task_status() -> Dict[str, Any]:
    """Получает статус регламентной задачи из Windows Task Scheduler.

    Returns:
        Dict[str, Any]: Данные о состоянии задачи (найдена ли, время след. запуска, статус).
    """
    cmd = (
        f"Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue | "
        "Select-Object TaskName, State, @{Name='NextRunTime';Expression={($_ | Get-ScheduledTaskInfo).NextRunTime}}, "
        "@{Name='LastRunTime';Expression={($_ | Get-ScheduledTaskInfo).LastRunTime}}, "
        "@{Name='LastTaskResult';Expression={($_ | Get-ScheduledTaskInfo).LastTaskResult}} | "
        "ConvertTo-Json -Compress"
    )
    res = _run_powershell(cmd)
    if res.returncode == 0 and res.stdout.strip():
        try:
            import json
            data = json.loads(res.stdout.strip())
            return {
                "exists": True,
                "task_name": data.get("TaskName", TASK_NAME),
                "state": str(data.get("State", "")),
                "next_run_time": str(data.get("NextRunTime", "")),
                "last_run_time": str(data.get("LastRunTime", "")),
                "last_result": str(data.get("LastTaskResult", "")),
            }
        except Exception as e:
            logger.warning(f"Ошибка парсинга статуса задачи Task Scheduler: {e}")

    return {
        "exists": False,
        "task_name": TASK_NAME,
        "state": "Не зарегистрирована",
        "next_run_time": "",
        "last_run_time": "",
        "last_result": "",
    }


def init_router() -> APIRouter:
    """Инициализирует и возвращает FastAPI роутер для Ninite.

    Returns:
        APIRouter: Сконфигурированный роутер.
    """
    router = APIRouter(prefix="/api/ninite", tags=["ninite-updater"])

    @router.get("/status")
    async def get_ninite_status() -> Dict[str, Any]:
        """Возвращает статус исполняемого файла Ninite и задачи в Task Scheduler."""
        exe_exists = NINITE_EXE.is_file()
        file_info: Dict[str, Any] = {
            "installed": exe_exists,
            "path": str(NINITE_EXE),
            "size_bytes": NINITE_EXE.stat().st_size if exe_exists else 0,
            "modified_time": (
                datetime.fromtimestamp(NINITE_EXE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                if exe_exists else ""
            ),
        }

        task_info = _get_task_status()

        log_content = ""
        if NINITE_LOG.is_file():
            try:
                log_content = NINITE_LOG.read_text(encoding="utf-8", errors="replace")[-2000:]
            except Exception:
                pass

        return {
            "success": True,
            "file": file_info,
            "task": task_info,
            "log": log_content,
        }

    @router.post("/upload")
    async def upload_ninite_installer(
        file: UploadFile = File(...),
        interval_weeks: int = Form(2),
        time_str: str = Form("20:00"),
    ) -> Dict[str, Any]:
        """Загружает файл инсталлятора, переименовывает в ninite.exe и копирует в Program Files.

        Args:
            file: Загружаемый файл инсталлятора Ninite.
            interval_weeks: Интервал обновления в неделях (по умолчанию 2).
            time_str: Время запуска (по умолчанию 20:00).

        Returns:
            Dict[str, Any]: Результат загрузки и установки.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Файл не передан")

        try:
            # Создаём целевую директорию, если её нет
            NINITE_DIR.mkdir(parents=True, exist_ok=True)

            # Сохраняем как ninite.exe
            with open(NINITE_EXE, "wb") as dst:
                shutil.copyfileobj(file.file, dst)

            logger.info(f"Файл Ninite успешно сохранён в {NINITE_EXE}")

            # Автоматически регистрируем задачу в Task Scheduler
            schedule_req = NiniteScheduleRequest(interval_weeks=interval_weeks, time_str=time_str)
            schedule_result = await schedule_ninite_task(schedule_req)

            return {
                "success": True,
                "message": f"Файл {file.filename} успешно установлен как {NINITE_EXE} и запланирован в Task Scheduler",
                "path": str(NINITE_EXE),
                "size_bytes": NINITE_EXE.stat().st_size,
                "schedule": schedule_result,
            }
        except PermissionError as pe:
            logger.error(f"Недостаточно прав для записи в {NINITE_DIR}: {pe}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка доступа к директории {NINITE_DIR}. Запустите сервер с правами Администратора: {pe}",
            )
        except Exception as e:
            logger.error(f"Ошибка сохранения файла Ninite: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось сохранить файл: {e}")

    @router.post("/schedule")
    async def schedule_ninite_task(req: NiniteScheduleRequest) -> Dict[str, Any]:
        """Создаёт или обновляет задачу в Windows Task Scheduler без дублирования.

        Args:
            req: Параметры расписания (интервал, время).

        Returns:
            Dict[str, Any]: Результат регистрации в Task Scheduler.
        """
        if not NINITE_EXE.is_file():
            # Если файл ещё не в Program Files, создаём директорию
            NINITE_DIR.mkdir(parents=True, exist_ok=True)

        existing_task = _get_task_status()
        is_update = existing_task.get("exists", False)

        # Команда PowerShell для безопасной регистрации / перезаписи задачи
        # Аргумент /silent запускает Ninite в фоновом тихом режиме
        target_path = str(NINITE_EXE).replace("'", "''")
        log_path = str(NINITE_LOG).replace("'", "''")

        ps_script = f"""
        # Если задача уже существует, удаляем старую регистрацию во избежание дублирования триггеров
        if (Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue) {{
            Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false -ErrorAction SilentlyContinue
        }}
        $action = New-ScheduledTaskAction -Execute '{target_path}' -Argument '/silent'
        $trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval {req.interval_weeks} -DaysOfWeek {req.days_of_week} -At '{req.time_str}'
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        $principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Автоматическое получение свежих версий ПО через Ninite (/silent)' -Force
        """

        res = _run_powershell(ps_script)
        if res.returncode != 0:
            # Попробуем резервный вариант через текущего пользователя
            fallback_ps = f"""
            if (Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue) {{
                Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false -ErrorAction SilentlyContinue
            }}
            $action = New-ScheduledTaskAction -Execute '{target_path}' -Argument '/silent'
            $trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval {req.interval_weeks} -DaysOfWeek {req.days_of_week} -At '{req.time_str}'
            Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $action -Trigger $trigger -Description 'Автоматическое получение свежих версий ПО через Ninite (/silent)' -Force
            """
            fallback_res = _run_powershell(fallback_ps)
            if fallback_res.returncode != 0:
                err_msg = fallback_res.stderr.strip() or res.stderr.strip()
                logger.error(f"Ошибка регистрации задачи Task Scheduler: {err_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка регистрации задачи в Task Scheduler: {err_msg}",
                )

        action_word = "обновлена" if is_update else "создана"
        logger.info(f"Задача {TASK_NAME} успешно {action_word} в Task Scheduler (Интервал: {req.interval_weeks} нед., Время: {req.time_str}, Флаг: /silent)")
        return {
            "success": True,
            "is_update": is_update,
            "message": f"Задача '{TASK_NAME}' успешно {action_word} в Windows Task Scheduler с флагом 'ninite.exe /silent' (без дублирования)",
            "interval_weeks": req.interval_weeks,
            "time": req.time_str,
            "days_of_week": req.days_of_week,
            "task_status": _get_task_status(),
        }

    @router.post("/run-now")
    async def run_ninite_now() -> Dict[str, Any]:
        """Принудительно запускает обновление через Ninite или задачу в Task Scheduler."""
        if not NINITE_EXE.is_file():
            raise HTTPException(status_code=404, detail=f"Файл {NINITE_EXE} не найден.")

        # Попробуем запустить через Task Scheduler, если задача зарегистрирована
        task_info = _get_task_status()
        if task_info.get("exists"):
            res = _run_powershell(f"Start-ScheduledTask -TaskName '{TASK_NAME}'")
            if res.returncode == 0:
                return {
                    "success": True,
                    "mode": "task_scheduler",
                    "message": f"Задача '{TASK_NAME}' запущена в Task Scheduler с флагом /silent",
                }

        # Резервный прямой запуск с флагом /silent
        try:
            cmd = f'"{NINITE_EXE}" /silent'
            proc = subprocess.Popen(cmd, shell=True)
            return {
                "success": True,
                "mode": "direct_process",
                "pid": proc.pid,
                "message": "Ninite запущен в фоновом режиме с флагом /silent",
            }
        except Exception as e:
            logger.error(f"Ошибка запуска Ninite: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось запустить Ninite: {e}")

    return router
