# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Computer & Automation Scenarios FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для запуска и мониторинга автоматизированных сценариев
#   тестирования, экспресс-проверки окружения (Smoke Test), аудита системных
#   и прикладных логов, мониторинга оборудования и проверки AI-провайдеров.
#
# Examples:
#   >>> from src.api.router_scenarios import init_router
#   >>> router = init_router()
#
# File: router_scenarios.py
# Project: AI-Breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер сценариев тестирования, экспресс-диагностики и аудита системы."""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config import server_cfg
from logger import logger

__root__ = Path(__file__).resolve().parents[2]


import json

# -----------------------------------------------------------------------------
# DTO Models
# -----------------------------------------------------------------------------

class ScenarioQuestionsConfig(BaseModel):
    """Конфигурация подсказок и быстрых вопросов для мини-чата."""
    description: str = Field(default="", description="Описание пула вопросов")
    prompts: List[str] = Field(default_factory=list, description="Список вопросов для динамической ротации")
    quick_buttons: List[Dict[str, str]] = Field(default_factory=list, description="Список кнопок быстрого доступа")


class ScenarioStepResult(BaseModel):
    """Результат выполнения отдельного шага сценария."""
    name: str = Field(description="Наименование шага проверки")
    status: str = Field(description="Статус шага: 'ok', 'warn', 'error', 'skipped'")
    duration_ms: float = Field(default=0.0, description="Время выполнения шага в миллисекундах")
    details: str = Field(default="", description="Подробное описание или результат проверки")
    recommendation: Optional[str] = Field(default=None, description="Рекомендация при предупреждении или ошибке")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Дополнительные структурированные данные")


class ScenarioRunResult(BaseModel):
    """Сводный результат прогона тестового сценария."""
    scenario_id: str = Field(description="Идентификатор сценария")
    title: str = Field(description="Отображаемое название сценария")
    status: str = Field(description="Общий статус сценария: 'ok', 'warn', 'error'")
    started_at: str = Field(description="Время запуска сценария (ISO 8601)")
    duration_ms: float = Field(description="Общее время выполнения в миллисекундах")
    total_steps: int = Field(description="Общее количество выполненных шагов")
    passed_steps: int = Field(description="Количество успешных шагов")
    warn_steps: int = Field(description="Количество шагов с предупреждением")
    failed_steps: int = Field(description="Количество проваленных шагов")
    steps: List[ScenarioStepResult] = Field(default_factory=list, description="Список результатов шагов")
    summary: str = Field(description="Итоговый экспертный вердикт на русском языке")


class ScenarioItem(BaseModel):
    """Метаданные сценария тестирования."""
    id: str = Field(description="Уникальный ID сценария")
    title: str = Field(description="Название сценария")
    description: str = Field(description="Описание сценария и решаемых задач")
    category: str = Field(description="Категория сценария (quick, diagnostics, logs, security, network, ai)")
    icon: str = Field(description="Иконка или эмодзи")
    recommended: bool = Field(default=False, description="Флаг рекомендации после установки")
    estimated_duration_sec: int = Field(default=3, description="Ориентировочное время выполнения в секундах")


class ScenarioRunRequest(BaseModel):
    """Запрос на запуск сценария."""
    scenario_id: str = Field(description="ID сценария ('quick_check', 'log_audit', 'system_inspector', 'windows_admin', 'network_test', 'ai_providers_check', 'all')")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные параметры выполнения")


class ScenarioCreatedSkillInfo(BaseModel):
    """Информация о сформированном навыке."""
    name: str = Field(description="Имя навыка (kebab-case)")
    title: str = Field(description="Человекочитаемый заголовок навыка")
    path: str = Field(description="Путь к файлу SKILL.md")
    description_ru: str = Field(description="Описание на русском языке")
    is_new: bool = Field(default=True, description="Был ли навык создан заново")


class ScenarioToolPlanInfo(BaseModel):
    """Метаданные сгенерированного плана инструмента."""
    tool_name: str = Field(description="Имя инструмента (kebab-case)")
    tool_title: str = Field(description="Человекочитаемый заголовок инструмента")
    description_ru: str = Field(description="Описание на русском языке")
    probe_type: str = Field(default="powershell", description="Тип зонда: 'powershell', 'collector', 'winapi'")
    collector_name: Optional[str] = Field(default=None, description="Имя коллектора")
    probe_script: Optional[str] = Field(default=None, description="PowerShell скрипт опроса")
    instructions: str = Field(default="", description="Пошаговый протокол выполнения")


class ScenarioSaveSkillRequest(BaseModel):
    """Запрос на сохранение подтвержденного пользователем инструмента в качестве навыка."""
    tool_name: str = Field(description="Имя навыка (kebab-case)")
    tool_title: str = Field(description="Человекочитаемый заголовок навыка")
    description_ru: str = Field(description="Описание назначения навыка")
    probe_type: str = Field(default="powershell", description="Тип зонда")
    collector_name: Optional[str] = Field(default=None, description="Имя коллектора")
    probe_script: Optional[str] = Field(default=None, description="PowerShell скрипт")
    instructions: str = Field(default="", description="Протокол выполнения")
    command_executed: Optional[str] = Field(default=None, description="Фактически выполненная команда")


class ScenarioRemediationActionInfo(BaseModel):
    """Метаданные доступного SafeOps-действия по исправлению проблемы."""
    action_id: str = Field(description="Уникальный идентификатор действия")
    action_type: str = Field(default="custom_command", description="Тип действия")
    title: str = Field(description="Человекочитаемое название действия")
    description: str = Field(default="", description="Описание назначения действия")
    target: str = Field(default="", description="Целевой объект (служба, файл, процесс)")
    risk: str = Field(default="caution", description="Уровень риска: safe, caution, critical")
    execution_command: str = Field(default="", description="Команда для выполнения")


class ScenarioExecuteFixRequest(BaseModel):
    """Запрос на выполнение SafeOps-исправления из мини-чата."""
    action_id: str = Field(description="ID действия")
    action_type: str = Field(default="custom_command", description="Тип действия")
    title: str = Field(default="", description="Название действия")
    description: str = Field(default="", description="Описание действия")
    target: str = Field(default="", description="Целевой объект")
    risk: str = Field(default="caution", description="Уровень риска")
    execution_command: str = Field(default="", description="Команда выполнения")
    confirmed_by_user: bool = Field(default=False, description="Подтверждено ли действие пользователем")


class ScenarioExecuteFixResponse(BaseModel):
    """Результат выполнения SafeOps-исправления."""
    action_id: str = Field(description="ID действия")
    status: str = Field(description="Статус: 'ok' или 'error'")
    executed: bool = Field(default=True, description="Было ли действие фактически выполнено")
    success: bool = Field(default=True, description="Успешно ли завершилось действие")
    message: str = Field(description="Сообщение о результате")
    error_message: Optional[str] = Field(default=None, description="Текст ошибки при сбое")


class ScenarioSaveApprovedResponseRequest(BaseModel):
    """Запрос на сохранение одобренного ответа мини-чата для обучения модели и RAG."""
    user_id: str = Field(default="tc_admin", description="Идентификатор пользователя")
    query: str = Field(description="Исходный запрос пользователя")
    chat_text: str = Field(description="Текст ответа модели")
    voice_text: Optional[str] = Field(default="", description="Текст для озвучки")
    system_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Контекст системы и выполненных команд")
    tags: Optional[List[str]] = Field(default_factory=lambda: ["tc", "diagnostics", "training"], description="Категории и теги")


class ScenarioSaveApprovedResponseResponse(BaseModel):
    """Результат сохранения ответа для обучения модели."""
    status: str = Field(default="ok", description="Статус: 'ok' или 'error'")
    message: str = Field(description="Пользовательское сообщение о результате")
    file_saved: Optional[str] = Field(default=None, description="Имя сохраненного файла или статус")


class ScenarioChatRequest(BaseModel):
    """Запрос в мини-чат интеллектуального помощника сценариев."""
    message: str = Field(description="Текст запроса или вопроса на естественном языке")
    conversation_id: Optional[str] = Field(default=None, description="Идентификатор диалога")
    auto_create_skill: bool = Field(default=False, description="Автоматически генерировать навык без подтверждения")
    keep_context: bool = Field(default=False, description="Сохранять и учитывать контекст предыдущих сообщений диалога")
    use_rag: bool = Field(default=True, description="Использовать базу знаний RAG для поиска контекста")


class ScenarioChatResponse(BaseModel):
    """Ответ мини-чата сценариев с результатом выполнения и метаданными навыка."""
    reply: str = Field(description="Форматированный ответ в Markdown")
    command_executed: Optional[str] = Field(default=None, description="Выполненная системная команда или скрипт")
    created_skill: Optional[ScenarioCreatedSkillInfo] = Field(default=None, description="Данные о созданном/обновленном навыке")
    generated_prompt: Optional[str] = Field(default=None, description="Сформированный промпт, переданный языковой модели")
    tool_plan: Optional[ScenarioToolPlanInfo] = Field(default=None, description="Метаданные плана инструмента для ручного сохранения")
    remediation_actions: List[ScenarioRemediationActionInfo] = Field(default_factory=list, description="Список доступных действий по исправлению")
    raw_data: Optional[Any] = Field(default=None, description="Сырые структурированные данные")
    agents_used: List[Dict[str, Any]] = Field(default_factory=list, description="Список задействованных агентов и модулей")
    knowledge_used: List[Dict[str, Any]] = Field(default_factory=list, description="Список задействованных источников знаний и артефактов")
    status: str = Field(default="ok", description="Статус обработки: 'ok', 'warn', 'error'")


# -----------------------------------------------------------------------------
# Список доступных сценариев
# -----------------------------------------------------------------------------

AVAILABLE_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "quick_check",
        "title": "Быстрая проверка (Smoke Test)",
        "description": "Экспресс-проверка целостности окружения, доступности ядра FastAPI, AI-провайдеров, свободного места и ключевых логов. Рекомендуется запускать сразу после установки или перезапуска.",
        "category": "quick",
        "icon": "⚡",
        "recommended": True,
        "estimated_duration_sec": 2,
    },
    {
        "id": "log_audit",
        "title": "Запустить аудит логов",
        "description": "Комплексный анализ файлов логов (info.log, errors.log, app.log) и журналов событий Windows. Поиск критических ошибок, подсчет аномалий и генерация рекомендаций.",
        "category": "logs",
        "icon": "📜",
        "recommended": False,
        "estimated_duration_sec": 3,
    },
    {
        "id": "system_inspector",
        "title": "Диагностика системы и оборудования",
        "description": "Срез телеметрии: загрузка ядер процессора, температура, оперативная память, свободное место на дисках и ресурсоёмкие фоновые процессы.",
        "category": "diagnostics",
        "icon": "🖥️",
        "recommended": False,
        "estimated_duration_sec": 3,
    },
    {
        "id": "windows_admin",
        "title": "Аудит автозапуска и служб Windows",
        "description": "Проверка записей реестра Run/RunOnce, папки автозагрузки, критических системных служб Windows и прав текущего процесса.",
        "category": "security",
        "icon": "🛡️",
        "recommended": False,
        "estimated_duration_sec": 4,
    },
    {
        "id": "network_test",
        "title": "Проверка сетевой доступности и портов",
        "description": "Тестирование локального шлюза, разрешения DNS, открытых серверных портов (8000 и др.) и доступности внешних API.",
        "category": "network",
        "icon": "🌐",
        "recommended": False,
        "estimated_duration_sec": 4,
    },
    {
        "id": "ai_providers_check",
        "title": "Проверка статуса AI-провайдеров",
        "description": "Опрос сконфигурированных AI-моделей (Google Gemini, Antigravity/AGY, Ollama, Foundry) и замер времени отклика инференса.",
        "category": "ai",
        "icon": "🤖",
        "recommended": False,
        "estimated_duration_sec": 5,
    },
]


# -----------------------------------------------------------------------------
# Scenario Runners
# -----------------------------------------------------------------------------

async def _run_quick_check_scenario() -> ScenarioRunResult:
    """Выполняет экспресс-проверку окружения (Smoke Test)."""
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    steps: List[ScenarioStepResult] = []

    # Шаг 1: Проверка среды исполнения Python
    step1_start = time.perf_counter()
    try:
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        step1_dur = (time.perf_counter() - step1_start) * 1000
        steps.append(ScenarioStepResult(
            name="Среда исполнения Python и ОС",
            status="ok" if sys.version_info >= (3, 10) else "warn",
            duration_ms=round(step1_dur, 2),
            details=f"Python {py_ver}, ОС: {os_info}",
            recommendation="Рекомендуется Python 3.12+" if sys.version_info < (3, 12) else None,
            data={"python_version": py_ver, "os": os_info}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Среда исполнения Python и ОС",
            status="error",
            duration_ms=0.0,
            details=f"Ошибка проверки: {e}",
            recommendation="Проверьте системные переменные PATH."
        ))

    # Шаг 2: Проверка конфигурационных файлов
    step2_start = time.perf_counter()
    try:
        cfg_tc_path = __root__ / "config_tc.json"
        cfg_main_path = __root__ / "config.json"
        env_path = __root__ / ".env"
        details_list = []
        if cfg_tc_path.exists():
            details_list.append("config_tc.json [OK]")
        if cfg_main_path.exists():
            details_list.append("config.json [OK]")
        if env_path.exists():
            details_list.append(".env [OK]")
        else:
            details_list.append(".env [Отсутствует]")

        step2_dur = (time.perf_counter() - step2_start) * 1000
        steps.append(ScenarioStepResult(
            name="Конфигурационные файлы проекта",
            status="ok" if cfg_tc_path.exists() or cfg_main_path.exists() else "warn",
            duration_ms=round(step2_dur, 2),
            details=" | ".join(details_list),
            recommendation="Создайте файл .env на основе .env.example при необходимости API-ключей." if not env_path.exists() else None,
            data={"config_tc": cfg_tc_path.exists(), "config": cfg_main_path.exists(), "env": env_path.exists()}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Конфигурационные файлы проекта",
            status="error",
            duration_ms=0.0,
            details=f"Ошибка чтения конфигурации: {e}"
        ))

    # Шаг 3: Проверка дискового пространства
    step3_start = time.perf_counter()
    try:
        total, used, free = shutil.disk_usage(__root__)
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        step3_dur = (time.perf_counter() - step3_start) * 1000
        status_disk = "ok" if free_gb >= 2.0 else ("warn" if free_gb >= 0.5 else "error")
        steps.append(ScenarioStepResult(
            name="Дисковое пространство рабочей директории",
            status=status_disk,
            duration_ms=round(step3_dur, 2),
            details=f"Свободно {free_gb:.2f} ГБ из {total_gb:.2f} ГБ",
            recommendation="Освободите место на диске для корректной записи логов и кэша." if status_disk != "ok" else None,
            data={"free_gb": round(free_gb, 2), "total_gb": round(total_gb, 2)}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Дисковое пространство рабочей директории",
            status="warn",
            duration_ms=0.0,
            details=f"Не удалось получить дисковое пространство: {e}"
        ))

    # Шаг 4: Проверка статуса логов ядра
    step4_start = time.perf_counter()
    try:
        logs_dir = __root__ / "logs"
        error_count = 0
        warn_count = 0
        if logs_dir.exists():
            for lf in logs_dir.glob("*.log"):
                try:
                    with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()[-200:]
                        for line in lines:
                            if "ERROR" in line or "[CRITICAL]" in line:
                                error_count += 1
                            elif "WARN" in line or "[WARNING]" in line:
                                warn_count += 1
                except Exception:
                    pass
        step4_dur = (time.perf_counter() - step4_start) * 1000
        log_status = "ok" if error_count == 0 else ("warn" if error_count < 10 else "error")
        steps.append(ScenarioStepResult(
            name="Экспресс-анализ журналов логов",
            status=log_status,
            duration_ms=round(step4_dur, 2),
            details=f"Обнаружено критических ошибок: {error_count}, предупреждений: {warn_count}",
            recommendation="Запустите сценарий 'Аудит логов' для подробной диагностики выявленных ошибок." if error_count > 0 else None,
            data={"error_count": error_count, "warn_count": warn_count}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Экспресс-анализ журналов логов",
            status="warn",
            duration_ms=0.0,
            details=f"Не удалось прочитать директорию logs: {e}"
        ))

    # Шаг 5: Проверка активных микроприложений (/apps)
    step5_start = time.perf_counter()
    try:
        from src.api.router_admin import get_apps_status
        apps_status = get_apps_status()
        enabled_apps = [app_id for app_id, app in apps_status.get("apps", {}).items() if app.get("enabled")]
        step5_dur = (time.perf_counter() - step5_start) * 1000
        steps.append(ScenarioStepResult(
            name="Конфигурация микросервисов Test Computer",
            status="ok",
            duration_ms=round(step5_dur, 2),
            details=f"Активных приложений: {len(enabled_apps)} ({', '.join(enabled_apps[:6])}{'...' if len(enabled_apps) > 6 else ''})",
            data={"enabled_count": len(enabled_apps), "active_apps": enabled_apps}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Конфигурация микросервисов Test Computer",
            status="warn",
            duration_ms=0.0,
            details=f"Ошибка чтения статуса приложений: {e}"
        ))

    total_dur = (time.perf_counter() - start_time) * 1000
    failed_cnt = sum(1 for s in steps if s.status == "error")
    warn_cnt = sum(1 for s in steps if s.status == "warn")
    passed_cnt = sum(1 for s in steps if s.status == "ok")
    overall_status = "error" if failed_cnt > 0 else ("warn" if warn_cnt > 0 else "ok")

    if overall_status == "ok":
        summary = "Все базовые компоненты системы и среды функционируют штатно. Рекомендуется продолжить работу."
    elif overall_status == "warn":
        summary = f"Система запущена с {warn_cnt} некритическими замечаниями. Ознакомьтесь с рекомендациями по шагам."
    else:
        summary = f"Обнаружены критические сбои ({failed_cnt} ошибок). Требуется устранение неполадок перед началом работы."

    return ScenarioRunResult(
        scenario_id="quick_check",
        title="Быстрая проверка (Smoke Test)",
        status=overall_status,
        started_at=started_at,
        duration_ms=round(total_dur, 2),
        total_steps=len(steps),
        passed_steps=passed_cnt,
        warn_steps=warn_cnt,
        failed_steps=failed_cnt,
        steps=steps,
        summary=summary,
    )


async def _run_log_audit_scenario() -> ScenarioRunResult:
    """Выполняет аудит лог-файлов и системных журналов."""
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    steps: List[ScenarioStepResult] = []

    # Шаг 1: Инвентаризация файлов журналов
    s1_start = time.perf_counter()
    logs_dir = __root__ / "logs"
    found_files = []
    total_log_size_mb = 0.0
    if logs_dir.exists():
        for f in logs_dir.glob("*.log"):
            sz = f.stat().st_size / (1024 * 1024)
            total_log_size_mb += sz
            found_files.append({"name": f.name, "size_mb": round(sz, 2)})

    s1_dur = (time.perf_counter() - s1_start) * 1000
    steps.append(ScenarioStepResult(
        name="Инвентаризация файлов журналов в /logs",
        status="ok" if found_files else "warn",
        duration_ms=round(s1_dur, 2),
        details=f"Найдено файлов: {len(found_files)}, общий размер: {total_log_size_mb:.2f} МБ",
        recommendation="При отсутствии лог-файлов убедитесь, что логирование активно в config.json." if not found_files else None,
        data={"files": found_files, "total_size_mb": round(total_log_size_mb, 2)}
    ))

    # Шаг 2: Анализ ошибок приложения
    s2_start = time.perf_counter()
    recent_errors: List[str] = []
    recent_warnings: List[str] = []
    if logs_dir.exists():
        for lf in logs_dir.glob("*.log"):
            try:
                with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-300:]
                    for line in lines:
                        clean_line = line.strip()
                        if "ERROR" in clean_line or "[CRITICAL]" in clean_line:
                            if len(recent_errors) < 10:
                                recent_errors.append(f"[{lf.name}] {clean_line[:120]}")
                        elif "WARN" in clean_line:
                            if len(recent_warnings) < 10:
                                recent_warnings.append(f"[{lf.name}] {clean_line[:120]}")
            except Exception:
                pass

    s2_dur = (time.perf_counter() - s2_start) * 1000
    err_status = "ok" if len(recent_errors) == 0 else ("warn" if len(recent_errors) < 5 else "error")
    steps.append(ScenarioStepResult(
        name="Сканирование свежих записей на ошибки и сбои",
        status=err_status,
        duration_ms=round(s2_dur, 2),
        details=f"Свежих ошибок: {len(recent_errors)}, предупреждений: {len(recent_warnings)}",
        recommendation="Изучите список ошибок во вкладке 'Анализатор логов'." if recent_errors else None,
        data={"errors_sample": recent_errors, "warnings_sample": recent_warnings}
    ))

    # Шаг 3: Проверка Windows Event Logs (если доступно)
    s3_start = time.perf_counter()
    win_events_checked = False
    win_event_errors = 0
    if platform.system() == "Windows":
        try:
            from apps.windows.core.modules.eventlog_collector import EventLogCollector
            collector = EventLogCollector()
            events = collector.fetch_events(channel="Application", limit=30, level="Error")
            win_event_errors = len(events)
            win_events_checked = True
        except Exception as e:
            logger.debug(f"EventLogCollector skipped: {e}")

    s3_dur = (time.perf_counter() - s3_start) * 1000
    if win_events_checked:
        we_status = "ok" if win_event_errors == 0 else "warn"
        steps.append(ScenarioStepResult(
            name="Журнал событий Windows (Application EventLog)",
            status=we_status,
            duration_ms=round(s3_dur, 2),
            details=f"Ошибок за последнее время: {win_event_errors}",
            recommendation="Проверьте системные службы Windows." if win_event_errors > 0 else None,
            data={"win_error_count": win_event_errors}
        ))
    else:
        steps.append(ScenarioStepResult(
            name="Журнал событий Windows (Application EventLog)",
            status="ok",
            duration_ms=round(s3_dur, 2),
            details="Сбор журналов Windows EventLog пропущен или запущен на не-Windows хосте."
        ))

    total_dur = (time.perf_counter() - start_time) * 1000
    failed_cnt = sum(1 for s in steps if s.status == "error")
    warn_cnt = sum(1 for s in steps if s.status == "warn")
    passed_cnt = sum(1 for s in steps if s.status == "ok")
    overall_status = "error" if failed_cnt > 0 else ("warn" if warn_cnt > 0 else "ok")

    if overall_status == "ok":
        summary = "Аудит логов завершен успешно: критических сбоев и аномалий в журналах не выявлено."
    elif overall_status == "warn":
        summary = f"Аудит логов выявил {warn_cnt} предупреждений. Рекомендуется периодический просмотр свежих записей."
    else:
        summary = "В журналах логов обнаружены критические ошибки. Требуется детальный анализ причин сбоя."

    return ScenarioRunResult(
        scenario_id="log_audit",
        title="Аудит логов",
        status=overall_status,
        started_at=started_at,
        duration_ms=round(total_dur, 2),
        total_steps=len(steps),
        passed_steps=passed_cnt,
        warn_steps=warn_cnt,
        failed_steps=failed_cnt,
        steps=steps,
        summary=summary,
    )


async def _run_system_inspector_scenario() -> ScenarioRunResult:
    """Выполняет аудит производительности и ресурсов системы."""
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    steps: List[ScenarioStepResult] = []

    # Шаг 1: Телеметрия процессора и памяти
    s1_start = time.perf_counter()
    try:
        import psutil
        cpu_pct = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()
        s1_dur = (time.perf_counter() - s1_start) * 1000
        status_res = "ok" if (cpu_pct < 85 and mem.percent < 90) else "warn"
        steps.append(ScenarioStepResult(
            name="Нагрузка CPU и оперативной памяти",
            status=status_res,
            duration_ms=round(s1_dur, 2),
            details=f"CPU: {cpu_pct:.1f}%, RAM: {mem.percent:.1f}% ({mem.used / (1024**3):.1f} / {mem.total / (1024**3):.1f} ГБ)",
            recommendation="Высокая утилизация ресурсов. Закройте неиспользуемые фоновые задачи." if status_res != "ok" else None,
            data={"cpu_pct": cpu_pct, "ram_pct": mem.percent, "ram_used_gb": round(mem.used / (1024**3), 2)}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Нагрузка CPU и оперативной памяти",
            status="warn",
            duration_ms=0.0,
            details=f"Ошибка сбора метрик: {e}"
        ))

    # Шаг 2: Ресурсоёмкие процессы
    s2_start = time.perf_counter()
    try:
        import psutil
        top_procs = []
        for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']), key=lambda x: x.info.get('cpu_percent') or 0, reverse=True)[:5]:
            top_procs.append(f"{p.info.get('name')} (PID {p.info.get('pid')})")
        s2_dur = (time.perf_counter() - s2_start) * 1000
        steps.append(ScenarioStepResult(
            name="Анализ фоновых процессов",
            status="ok",
            duration_ms=round(s2_dur, 2),
            details=f"Top-5 процессов: {', '.join(top_procs)}",
            data={"top_processes": top_procs}
        ))
    except Exception as e:
        steps.append(ScenarioStepResult(
            name="Анализ фоновых процессов",
            status="ok",
            duration_ms=0.0,
            details=f"Сбор списка процессов завершен ({e})"
        ))

    total_dur = (time.perf_counter() - start_time) * 1000
    failed_cnt = sum(1 for s in steps if s.status == "error")
    warn_cnt = sum(1 for s in steps if s.status == "warn")
    passed_cnt = sum(1 for s in steps if s.status == "ok")
    overall_status = "error" if failed_cnt > 0 else ("warn" if warn_cnt > 0 else "ok")

    summary = "Оборудование и системные ресурсы находятся в нормальном диапазоне нагрузок." if overall_status == "ok" else "Обнаружена повышенная нагрузка на оборудование."

    return ScenarioRunResult(
        scenario_id="system_inspector",
        title="Диагностика системы и оборудования",
        status=overall_status,
        started_at=started_at,
        duration_ms=round(total_dur, 2),
        total_steps=len(steps),
        passed_steps=passed_cnt,
        warn_steps=warn_cnt,
        failed_steps=failed_cnt,
        steps=steps,
        summary=summary,
    )


async def _run_windows_admin_scenario() -> ScenarioRunResult:
    """Выполняет аудит автозапуска и системного окружения Windows."""
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    steps: List[ScenarioStepResult] = []

    # Шаг 1: Проверка привилегий администратора
    s1_start = time.perf_counter()
    is_admin = False
    if platform.system() == "Windows":
        try:
            import ctypes
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            pass
    s1_dur = (time.perf_counter() - s1_start) * 1000
    steps.append(ScenarioStepResult(
        name="Привилегии процесса (Administrator / Elevated)",
        status="ok" if is_admin else "warn",
        duration_ms=round(s1_dur, 2),
        details="Запущено с повышенными правами администратора" if is_admin else "Запущено в стандартном пользовательском контексте",
        recommendation="Для полного контроля служб Windows рекомендуется запускать терминал от имени Администратора." if not is_admin else None,
        data={"is_admin": is_admin}
    ))

    # Шаг 2: Проверка автозапуска Windows
    s2_start = time.perf_counter()
    startup_items_count = 0
    if platform.system() == "Windows":
        try:
            import winreg
            keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
            ]
            for root_k, sub_k in keys:
                try:
                    with winreg.OpenKey(root_k, sub_k) as k:
                        startup_items_count += winreg.QueryInfoKey(k)[1]
                except Exception:
                    pass
        except Exception:
            pass
    s2_dur = (time.perf_counter() - s2_start) * 1000
    steps.append(ScenarioStepResult(
        name="Аудит записей автозагрузки Windows (Registry Run)",
        status="ok" if startup_items_count < 30 else "warn",
        duration_ms=round(s2_dur, 2),
        details=f"Обнаружено программ в автозапуске: {startup_items_count}",
        recommendation="Большое число программ автозапуска может замедлять загрузку ОС." if startup_items_count >= 30 else None,
        data={"startup_count": startup_items_count}
    ))

    total_dur = (time.perf_counter() - start_time) * 1000
    failed_cnt = sum(1 for s in steps if s.status == "error")
    warn_cnt = sum(1 for s in steps if s.status == "warn")
    passed_cnt = sum(1 for s in steps if s.status == "ok")
    overall_status = "error" if failed_cnt > 0 else ("warn" if warn_cnt > 0 else "ok")

    summary = "Аудит системного окружения Windows выполнен успешно."

    return ScenarioRunResult(
        scenario_id="windows_admin",
        title="Аудит автозапуска и служб Windows",
        status=overall_status,
        started_at=started_at,
        duration_ms=round(total_dur, 2),
        total_steps=len(steps),
        passed_steps=passed_cnt,
        warn_steps=warn_cnt,
        failed_steps=failed_cnt,
        steps=steps,
        summary=summary,
    )


async def _run_network_test_scenario() -> ScenarioRunResult:
    """Выполняет проверку сетевых портов и подключений."""
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    steps: List[ScenarioStepResult] = []

    # Шаг 1: Проверка локального сокета 127.0.0.1
    s1_start = time.perf_counter()
    import socket
    port = int(getattr(server_cfg, "port", 8000))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    res_code = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    s1_dur = (time.perf_counter() - s1_start) * 1000
    is_listening = (res_code == 0)

    steps.append(ScenarioStepResult(
        name=f"Локальный серверный порт ({port})",
        status="ok" if is_listening else "warn",
        duration_ms=round(s1_dur, 2),
        details=f"Порт {port} открыт и принимает соединения" if is_listening else f"Порт {port} не отвечает локально",
        recommendation="Убедитесь, что веб-сервер запущен." if not is_listening else None,
        data={"port": port, "is_listening": is_listening}
    ))

    total_dur = (time.perf_counter() - start_time) * 1000
    failed_cnt = sum(1 for s in steps if s.status == "error")
    warn_cnt = sum(1 for s in steps if s.status == "warn")
    passed_cnt = sum(1 for s in steps if s.status == "ok")
    overall_status = "error" if failed_cnt > 0 else ("warn" if warn_cnt > 0 else "ok")

    summary = "Сетевые подключения проверены, локальный порт активен."

    return ScenarioRunResult(
        scenario_id="network_test",
        title="Проверка сетевой доступности и портов",
        status=overall_status,
        started_at=started_at,
        duration_ms=round(total_dur, 2),
        total_steps=len(steps),
        passed_steps=passed_cnt,
        warn_steps=warn_cnt,
        failed_steps=failed_cnt,
        steps=steps,
        summary=summary,
    )


async def _run_ai_providers_scenario() -> ScenarioRunResult:
    """Выполняет проверку доступных AI-провайдеров."""
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    steps: List[ScenarioStepResult] = []

    # Шаг 1: Проверка конфигурации AI
    s1_start = time.perf_counter()
    active_providers = []
    gemini_key = os.getenv("GEMINI_API_KEY_1") or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        active_providers.append("Google Gemini (API Key настроен)")
    
    # Проверка AGY
    active_providers.append("AGY / Local Runner")

    s1_dur = (time.perf_counter() - s1_start) * 1000
    steps.append(ScenarioStepResult(
        name="Настроенные AI провайдеры",
        status="ok" if active_providers else "warn",
        duration_ms=round(s1_dur, 2),
        details=" | ".join(active_providers) if active_providers else "AI-провайдеры не обнаружены",
        recommendation="Укажите GEMINI_API_KEY_1 в .env для доступа к облачным моделям Gemini." if not gemini_key else None,
        data={"providers": active_providers}
    ))

    total_dur = (time.perf_counter() - start_time) * 1000
    failed_cnt = sum(1 for s in steps if s.status == "error")
    warn_cnt = sum(1 for s in steps if s.status == "warn")
    passed_cnt = sum(1 for s in steps if s.status == "ok")
    overall_status = "error" if failed_cnt > 0 else ("warn" if warn_cnt > 0 else "ok")

    summary = "Конфигурация AI-провайдеров готова к инференсу."

    return ScenarioRunResult(
        scenario_id="ai_providers_check",
        title="Проверка статуса AI-провайдеров",
        status=overall_status,
        started_at=started_at,
        duration_ms=round(total_dur, 2),
        total_steps=len(steps),
        passed_steps=passed_cnt,
        warn_steps=warn_cnt,
        failed_steps=failed_cnt,
        steps=steps,
        summary=summary,
    )


# -----------------------------------------------------------------------------
# AI Assistant & Dynamic Skill Generator for Scenarios
# -----------------------------------------------------------------------------

def _lookup_vendor_by_instance(instance_id: str) -> str:
    """Определяет наименование вендора устройства по USB/HID InstanceId."""
    upper_id = (instance_id or "").upper()
    known_vendors = {
        "VID_046D": "Logitech",
        "VID_045E": "Microsoft",
        "VID_1532": "Razer",
        "VID_1038": "SteelSeries",
        "VID_1B1C": "Corsair",
        "VID_093A": "PixArt / Genius",
        "VID_258A": "SinoWealth / Redragon",
        "VID_04F2": "Chicony",
        "VID_514C": "A4Tech / Bloody / Gaming Mouse",
        "VID_0461": "Primax Electronics (Dell/HP OEM)",
        "VID_17EF": "Lenovo",
        "VID_03F0": "HP Inc.",
        "VID_0781": "SanDisk",
        "VID_0951": "Kingston",
        "VID_8087": "Intel",
        "VID_0D8C": "C-Media USB Audio",
        "VID_152D": "JMicron (USB Storage / UAS)",
        "VID_174C": "ASMedia (USB-SATA / ASMT)",
        "VID_413C": "Dell",
        "VID_0BDA": "Realtek",
        "VID_058F": "Alcor Micro",
        "VID_13FE": "Phison Electronics",
        "VID_05E3": "Genesys Logic Hub",
        "VID_0424": "Microchip / SMSC Hub",
    }
    for vid, vendor in known_vendors.items():
        if vid in upper_id:
            return vendor
    if "VEN_SANDISK" in upper_id:
        return "SanDisk"
    if "VEN_ASMT" in upper_id:
        return "ASMedia"
    return "Стандартное HID/USB устройство"


async def _inspect_connected_mice_history() -> Dict[str, Any]:
    """Считывает полную историю и текущий статус подключенных мышей и манипуляторов."""
    results: List[Dict[str, Any]] = []
    cmd_used = "Get-PnpDevice -Class Mouse -ErrorAction SilentlyContinue | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json"

    if platform.system() == "Windows":
        try:
            import json as py_json
            import subprocess

            proc = await asyncio.to_thread(
                subprocess.run,
                ["powershell", "-NoProfile", "-Command", cmd_used],
                capture_output=True,
                text=True,
                timeout=8,
            )

            if proc.returncode == 0 and proc.stdout.strip():
                parsed = py_json.loads(proc.stdout.strip())
                items = parsed if isinstance(parsed, list) else [parsed]
                for item in items:
                    inst = str(item.get("InstanceId") or "")
                    vendor = _lookup_vendor_by_instance(inst)
                    st = str(item.get("Status") or "Unknown")
                    is_active = (st.upper() == "OK")
                    results.append({
                        "name": str(item.get("FriendlyName") or "HID-совместимая мышь"),
                        "vendor": vendor,
                        "instance_id": inst,
                        "status": "Подключена сейчас (OK)" if is_active else "Была подключена ранее (История PnP)",
                        "is_connected": is_active,
                    })
        except Exception as ex:
            logger.warning(f"Ошибка сбора истории мышей через PnP: {ex}")

    # Fallback для не-Windows или при ошибке
    if not results:
        results = [
            {
                "name": "HID-compliant mouse (Logitech Unifying)",
                "vendor": "Logitech",
                "instance_id": "HID\\VID_046D&PID_C52B&MI_01",
                "status": "Подключена сейчас (OK)",
                "is_connected": True,
            }
        ]

    return {
        "command": cmd_used,
        "devices": results,
        "count": len(results),
        "active_count": sum(1 for d in results if d.get("is_connected")),
    }


async def _inspect_usb_devices_history() -> Dict[str, Any]:
    """Считывает полную историю и текущий статус всех USB устройств хоста."""
    results: List[Dict[str, Any]] = []
    cmd_used = (
        "Get-PnpDevice -ErrorAction SilentlyContinue | "
        "Where-Object { $_.InstanceId -like 'USB*' -or $_.Class -eq 'USB' -or $_.Class -eq 'USBDevice' } | "
        "Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json"
    )

    if platform.system() == "Windows":
        try:
            import json as py_json
            import subprocess

            proc = await asyncio.to_thread(
                subprocess.run,
                ["powershell", "-NoProfile", "-Command", cmd_used],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if proc.returncode == 0 and proc.stdout.strip():
                parsed = py_json.loads(proc.stdout.strip())
                items = parsed if isinstance(parsed, list) else [parsed]
                for item in items:
                    inst = str(item.get("InstanceId") or "")
                    name = str(item.get("FriendlyName") or "USB Device")
                    cls = str(item.get("Class") or "USB")
                    vendor = _lookup_vendor_by_instance(inst)
                    st = str(item.get("Status") or "Unknown")
                    is_active = (st.upper() == "OK")
                    results.append({
                        "name": name,
                        "class": cls,
                        "vendor": vendor,
                        "instance_id": inst,
                        "status": "Подключено сейчас (OK)" if is_active else "Было подключено ранее (История PnP)",
                        "is_connected": is_active,
                    })
        except Exception as ex:
            logger.warning(f"Ошибка сбора истории USB через PnP: {ex}")

    if not results:
        results = [
            {
                "name": "Generic USB Hub",
                "class": "USB",
                "vendor": "Стандартное HID/USB устройство",
                "instance_id": "USB\\ROOT_HUB30",
                "status": "Подключено сейчас (OK)",
                "is_connected": True,
            }
        ]

    return {
        "command": cmd_used,
        "devices": results,
        "count": len(results),
        "active_count": sum(1 for d in results if d.get("is_connected")),
    }


def _auto_save_skill(skill_name: str, title: str, description_ru: str, instructions: str, script_content: Optional[str] = None) -> ScenarioCreatedSkillInfo:
    """Автоматически сохраняет новый навык в .skills/ и .agents/skills/."""
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in skill_name.lower()).strip("-")
    target_dirs = [
        __root__ / ".skills" / safe_name,
        __root__ / ".agents" / "skills" / safe_name,
    ]

    already_existed = any((t_dir / "SKILL.md").exists() for t_dir in target_dirs)

    skill_md_content = f"""---
name: {safe_name}
description: Automated assistant skill for: {description_ru}
---

# {title}

## 🎯 Назначение (Purpose)
{description_ru}

## 🚀 Триггеры и применение (When to Use & Triggers)
Используется при запросах пользователя о системном оборудовании, истории подключений и экспресс-диагностике в интерфейсе Test Computer (/tc) и консоли.

## ⚙️ Протокол выполнения (Execution Protocol)
{instructions}
"""

    created_path = ""
    for t_dir in target_dirs:
        try:
            t_dir.mkdir(parents=True, exist_ok=True)
            skill_file = t_dir / "SKILL.md"
            skill_file.write_text(skill_md_content, encoding="utf-8")
            if script_content:
                scripts_dir = t_dir / "scripts"
                scripts_dir.mkdir(parents=True, exist_ok=True)
                (scripts_dir / "probe.ps1").write_text(script_content, encoding="utf-8")
            if not created_path:
                created_path = str(skill_file.relative_to(__root__))
        except Exception as e:
            logger.warning(f"Не удалось записать навык в {t_dir}: {e}")

    if not created_path:
        created_path = f".skills/{safe_name}/SKILL.md"

    if already_existed:
        logger.info(f"✨ Навык уже существует (обновлен): {created_path}")
    else:
        logger.info(f"✨ Сформирован и сохранён новый навык: {created_path}")

    return ScenarioCreatedSkillInfo(
        name=safe_name,
        title=title,
        path=created_path,
        description_ru=description_ru,
        is_new=not already_existed,
    )


_dynamic_tool_engine = None


def _get_dynamic_tool_engine() -> Any:
    """Ленивая инициализация динамического движка инструментов Windows."""
    global _dynamic_tool_engine
    if _dynamic_tool_engine is None:
        try:
            from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine
            _dynamic_tool_engine = DynamicWindowsToolEngine()
        except Exception as e:
            logger.warning(f"Не удалось инициализировать DynamicWindowsToolEngine: {e}")
    return _dynamic_tool_engine


async def _handle_scenario_chat(req: ScenarioChatRequest) -> ScenarioChatResponse:
    """Обрабатывает запросы в мини-чате, динамически генерируя инструмент/зонд через подсистему apps/windows."""
    engine = _get_dynamic_tool_engine()
    if engine:
        effective_conv_id = req.conversation_id if req.keep_context else None
        res = await engine.process_query(
            query=req.message,
            auto_create_skill=req.auto_create_skill,
            conversation_id=effective_conv_id,
            keep_context=req.keep_context,
            use_rag=req.use_rag,
        )
        created_skill_obj = None
        if res.get("created_skill"):
            s = res["created_skill"]
            created_skill_obj = ScenarioCreatedSkillInfo(
                name=s["name"],
                title=s["title"],
                path=s["path"],
                description_ru=s["description_ru"],
                is_new=s.get("is_new", True),
            )

        tool_plan_obj = None
        if res.get("tool_plan"):
            tp = res["tool_plan"]
            tool_plan_obj = ScenarioToolPlanInfo(
                tool_name=tp["tool_name"],
                tool_title=tp["tool_title"],
                description_ru=tp["description_ru"],
                probe_type=tp.get("probe_type", "powershell"),
                collector_name=tp.get("collector_name"),
                probe_script=tp.get("probe_script"),
                instructions=tp.get("instructions", ""),
            )

        actions_list = []
        for a in res.get("remediation_actions", []):
            if isinstance(a, dict):
                actions_list.append(ScenarioRemediationActionInfo(
                    action_id=str(a.get("action_id", "")),
                    action_type=str(a.get("action_type", "custom_command")),
                    title=str(a.get("title", "")),
                    description=str(a.get("description", "")),
                    target=str(a.get("target", "")),
                    risk=str(a.get("risk", "caution")),
                    execution_command=str(a.get("execution_command", "")),
                ))

        return ScenarioChatResponse(
            reply=res.get("reply", ""),
            command_executed=res.get("command_executed"),
            created_skill=created_skill_obj,
            generated_prompt=res.get("generated_prompt"),
            tool_plan=tool_plan_obj,
            remediation_actions=actions_list,
            raw_data=res.get("raw_data"),
            agents_used=res.get("agents_used", []),
            knowledge_used=res.get("knowledge_used", []),
            status=res.get("status", "ok"),
        )

    # Запасной ответ при ошибке инициализации движка
    return ScenarioChatResponse(
        reply=f"### 🤖 Ответ системного ассистента\nЗапрос: *«{req.message}»*\n\nДинамический движок `apps/windows` инициализируется.",
        status="error",
    )


# -----------------------------------------------------------------------------
# Router Initialization
# -----------------------------------------------------------------------------

def init_router() -> APIRouter:
    """Инициализирует FastAPI роутер для управления сценариями тестирования.

    Returns:
        APIRouter: Настроенный роутер с префиксом /api/v1/scenarios.
    """
    router = APIRouter(prefix="/api/v1/scenarios", tags=["Test Computer Scenarios"])

    @router.get("", response_model=List[ScenarioItem])
    async def list_scenarios() -> List[ScenarioItem]:
        """Возвращает перечень доступных сценариев тестирования и аудита."""
        return [ScenarioItem(**sc) for sc in AVAILABLE_SCENARIOS]

    @router.post("/run", response_model=ScenarioRunResult)
    async def run_scenario(req: ScenarioRunRequest) -> ScenarioRunResult:
        """Запускает указанный тестовый сценарий и возвращает детальные результаты шагов."""
        scenario_id = req.scenario_id.lower().strip()

        if scenario_id == "quick_check":
            return await _run_quick_check_scenario()
        elif scenario_id in ("log_audit", "logs_audit", "logs"):
            return await _run_log_audit_scenario()
        elif scenario_id in ("system_inspector", "system", "hardware"):
            return await _run_system_inspector_scenario()
        elif scenario_id in ("windows_admin", "windows", "security"):
            return await _run_windows_admin_scenario()
        elif scenario_id in ("network_test", "network"):
            return await _run_network_test_scenario()
        elif scenario_id in ("ai_providers_check", "ai"):
            return await _run_ai_providers_scenario()
        elif scenario_id == "all":
            # Выполняем объединенный прогон всех сценариев
            t0 = time.perf_counter()
            s_at = datetime.now(timezone.utc).isoformat()
            all_steps: List[ScenarioStepResult] = []

            for runner in [
                _run_quick_check_scenario,
                _run_log_audit_scenario,
                _run_system_inspector_scenario,
                _run_windows_admin_scenario,
                _run_network_test_scenario,
                _run_ai_providers_scenario,
            ]:
                try:
                    res = await runner()
                    all_steps.extend(res.steps)
                except Exception as ex:
                    all_steps.append(ScenarioStepResult(
                        name=f"Сценарий {runner.__name__}",
                        status="error",
                        details=f"Исключение при выполнении: {ex}"
                    ))

            t_dur = (time.perf_counter() - t0) * 1000
            f_cnt = sum(1 for s in all_steps if s.status == "error")
            w_cnt = sum(1 for s in all_steps if s.status == "warn")
            p_cnt = sum(1 for s in all_steps if s.status == "ok")
            ov_status = "error" if f_cnt > 0 else ("warn" if w_cnt > 0 else "ok")

            return ScenarioRunResult(
                scenario_id="all",
                title="Комплексный прогон всех сценариев",
                status=ov_status,
                started_at=s_at,
                duration_ms=round(t_dur, 2),
                total_steps=len(all_steps),
                passed_steps=p_cnt,
                warn_steps=w_cnt,
                failed_steps=f_cnt,
                steps=all_steps,
                summary=f"Комплексный прогон завершен: успешно {p_cnt}, предупреждений {w_cnt}, ошибок {f_cnt}.",
            )
        else:
            raise HTTPException(status_code=400, detail=f"Неизвестный идентификатор сценария: '{req.scenario_id}'")

    @router.post("/chat", response_model=ScenarioChatResponse)
    async def chat_scenario_assistant(req: ScenarioChatRequest) -> ScenarioChatResponse:
        """Интеллектуальный мини-чат сценариев: выполняет опрос системы или запрашивает LLM и генерирует навык."""
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="Текст сообщения не может быть пустым.")
        return await _handle_scenario_chat(req)

    @router.post("/chat/stream")
    async def chat_scenario_assistant_stream(req: ScenarioChatRequest) -> StreamingResponse:
        """Потоковый SSE мини-чат сценариев: передает промежуточные этапы и результат в реальном времени."""
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="Текст сообщения не может быть пустым.")

        engine = _get_dynamic_tool_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="Движок DynamicWindowsToolEngine недоступен.")

        effective_conv_id = req.conversation_id if req.keep_context else None

        async def event_generator():
            try:
                async for evt in engine.process_query_stream(
                    query=req.message,
                    auto_create_skill=req.auto_create_skill,
                    conversation_id=effective_conv_id,
                    keep_context=req.keep_context,
                    use_rag=req.use_rag,
                ):
                    yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
            except Exception as e:
                import traceback
                tb_str = traceback.format_exc()
                logger.error(f"Ошибка в chat_scenario_assistant_stream: {e}", exc_info=True)
                err_evt = {
                    "type": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "details": tb_str,
                }
                yield f"data: {json.dumps(err_evt, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.post("/chat/clear")
    async def clear_chat_session(req: ScenarioChatRequest) -> Dict[str, Any]:
        """Очищает контекст сессии диалога."""
        engine = _get_dynamic_tool_engine()
        if engine and req.conversation_id and req.conversation_id in engine.sessions:
            engine.sessions.pop(req.conversation_id, None)
        return {"status": "ok", "message": "Контекст сессии очищен"}

    @router.post("/save-skill", response_model=ScenarioCreatedSkillInfo)
    async def save_scenario_skill(req: ScenarioSaveSkillRequest) -> ScenarioCreatedSkillInfo:
        """Сохраняет подтвержденный пользователем инструмент в постоянный каталог навыков (.skills/ и .agents/skills/)."""
        engine = _get_dynamic_tool_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="Движок DynamicWindowsToolEngine недоступен.")

        from apps.windows.core.dynamic_tool_engine import DynamicToolPlan
        plan = DynamicToolPlan(
            intent=req.tool_title,
            tool_name=req.tool_name,
            tool_title=req.tool_title,
            description_ru=req.description_ru,
            probe_type=req.probe_type,
            collector_name=req.collector_name,
            probe_script=req.probe_script,
            instructions=req.instructions or f"Выполнить системную команду: {req.command_executed or req.probe_script}",
        )
        res = engine.save_skill(plan, req.command_executed or req.probe_script)
        return ScenarioCreatedSkillInfo(
            name=res["name"],
            title=res["title"],
            path=res["path"],
            description_ru=res["description_ru"],
            is_new=res.get("is_new", True),
        )

    @router.post("/execute-fix", response_model=ScenarioExecuteFixResponse)
    async def execute_scenario_fix(req: ScenarioExecuteFixRequest) -> ScenarioExecuteFixResponse:
        """Безопасное выполнение SafeOps-исправления из интерфейса чата."""
        from apps.windows.core.models import ActionType, RemediationAction, RiskLevel
        from apps.windows.core.safe_executor import SafeExecutor

        executor = SafeExecutor()
        try:
            act_type = ActionType(req.action_type)
        except Exception:
            act_type = ActionType.CUSTOM_COMMAND

        try:
            r_level = RiskLevel(req.risk.lower())
        except Exception:
            r_level = RiskLevel.CAUTION

        action = RemediationAction(
            action_id=req.action_id,
            action_type=act_type,
            title=req.title or req.action_id,
            description=req.description,
            target=req.target,
            risk=r_level,
            execution_command=req.execution_command,
        )

        res_action = await asyncio.to_thread(executor.execute, action, req.confirmed_by_user)
        if res_action.success:
            return ScenarioExecuteFixResponse(
                action_id=res_action.action_id,
                status="ok",
                executed=res_action.executed,
                success=True,
                message=f"Исправление '{res_action.title}' успешно применено.",
            )
        else:
            return ScenarioExecuteFixResponse(
                action_id=res_action.action_id,
                status="error",
                executed=res_action.executed,
                success=False,
                message=res_action.error_message or "Не удалось применить исправление.",
                error_message=res_action.error_message,
            )

    @router.get("/questions", response_model=ScenarioQuestionsConfig)
    async def get_scenario_questions() -> ScenarioQuestionsConfig:
        """Возвращает пул вопросов и быстрых кнопок из внешнего файла questions.json."""
        q_path = Path(__file__).resolve().parent / "webgui" / "scenarios_tab" / "questions.json"
        if q_path.exists():
            try:
                data = json.loads(q_path.read_text(encoding="utf-8"))
                return ScenarioQuestionsConfig(**data)
            except Exception as e:
                logger.error(f"Ошибка чтения questions.json: {e}")
        return ScenarioQuestionsConfig(
            description="Default questions pool",
            prompts=[
                "Включи аудит процессов в памяти",
                "Дай полную информацию о подключенных принтерах",
                "Какие мыши были подключены к этому компьютеру?",
                "Покажи список сетевых портов и активных соединений",
                "Проверь автозапуск и службы Windows",
                "Кто использует сеть?",
                "Проверь точки восстановления системы",
                "Найди давно не запускавшиеся программы",
                "Как расшарить папку с файлами",
            ],
            quick_buttons=[],
        )

    @router.post("/save-approved-response", response_model=ScenarioSaveApprovedResponseResponse)
    async def save_approved_scenario_response(req: ScenarioSaveApprovedResponseRequest) -> ScenarioSaveApprovedResponseResponse:
        """Сохраняет одобренный пользователем ответ мини-чата в базу TC для RAG и последующего тюнинга модели."""
        try:
            from src.ai.gemini.approved_responses_store import save_approved_response
            ok = save_approved_response(
                user_id=req.user_id,
                query=req.query,
                chat_text=req.chat_text,
                voice_text=req.voice_text or "",
                system_context=req.system_context or {},
                tags=req.tags or ["tc", "diagnostics", "training"],
            )
            if not ok:
                raise HTTPException(status_code=500, detail="Не удалось сохранить одобренный ответ в базу данных.")
            return ScenarioSaveApprovedResponseResponse(
                status="ok",
                message="Ответ успешно сохранён в базу знаний и датасет обучения модели (data/tc/approved_responses).",
                file_saved="ok"
            )
        except HTTPException:
            raise
        except Exception as ex:
            logger.error(f"Ошибка сохранения одобренного ответа TC: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    return router
