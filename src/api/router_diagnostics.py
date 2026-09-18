# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Universal Diagnostic & Table Explanation Router
# =============================================================================
# Description:
#   Универсальный REST API эндпоинт для AI-диагностики, контекстного объяснения
#   и оценки безопасности записей любых таблиц системы (ПО, процессы, службы,
#   задачи планировщика, сетевые соединения, ключи реестра, пользователи, сайты, RAG).
#
# Examples:
#   >>> from src.api.router_diagnostics import init_router
#   >>> router = init_router()
#
# File: router_diagnostics.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер универсального AI-объяснения и диагностики записей таблиц."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.logger import logger


class DiagnosticExplainRequest(BaseModel):
    """Запрос на AI-объяснение элемента таблицы."""
    table_type: str = Field(default="generic", description="Тип таблицы (software, process, service, task, network, registry, user, website, rag_doc, disk)")
    title: str = Field(default="", description="Основное имя или заголовок элемента")
    subtitle: Optional[str] = Field(default="", description="Вторичный заголовок (издатель, путь, IP, статус)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Набор ключевых атрибутов записи")
    raw_data: Optional[str] = Field(default="", description="Сырая строка команды, пути или JSON")
    model: Optional[str] = Field(default=None, description="Опциональное имя конкретной модели")
    provider: Optional[str] = Field(default=None, description="Опциональный AI провайдер")
    web_search: bool = Field(default=True, description="Выполнять ли онлайн поиск для обогащения контекста")


class DiagnosticExplainResponse(BaseModel):
    """Структурированный ответ AI-диагностики элемента таблицы."""
    summary: str = Field(description="Краткое понятное описание назначения элемента")
    developer: str = Field(default="Неизвестен", description="Разработчик / принадлежность / вендор")
    category: str = Field(default="Системный компонент", description="Категория элемента")
    security_verdict: str = Field(description="Оценка безопасности, легитимности и рисков")
    performance_impact: str = Field(description="Влияние на производительность и ресурсы")
    recommendation: str = Field(description="Практическая рекомендация эксперта")
    action_steps: List[str] = Field(default_factory=list, description="Пошаговые рекомендуемые действия")


from src.api.diagnostics_prompt_manager import (
    DiagnosticPromptTemplate,
    prompt_manager,
)


class DiagnosticPromptUpdateRequest(BaseModel):
    """Запрос на обновление шаблона промпта для таблицы."""
    system_instruction: str = Field(description="Системная инструкция для LLM")
    prompt_template: str = Field(description="Шаблон текста промпта с переменными {title}, {subtitle}, {metadata}, {raw_data}")
    name: Optional[str] = Field(default=None, description="Опциональное отображаемое имя")
    description: Optional[str] = Field(default=None, description="Опциональное описание")


def init_router() -> APIRouter:
    """Инициализирует и возвращает FastAPI роутер универсальной диагностики.

    Returns:
        APIRouter: Настроенный роутер с префиксом /api/v1/diagnostics.
    """
    router = APIRouter(prefix="/api/v1/diagnostics", tags=["Universal Diagnostics"])

    @router.get("/prompts", response_model=List[DiagnosticPromptTemplate])
    async def list_diagnostic_prompts() -> List[DiagnosticPromptTemplate]:
        """Возвращает список всех шаблонов промптов для таблиц системы."""
        return prompt_manager.list_templates()

    @router.get("/prompts/{table_type}", response_model=DiagnosticPromptTemplate)
    async def get_diagnostic_prompt(table_type: str) -> DiagnosticPromptTemplate:
        """Возвращает шаблон промпта для конкретного типа таблицы."""
        return prompt_manager.get_template(table_type)

    @router.post("/prompts/{table_type}", response_model=DiagnosticPromptTemplate)
    async def save_diagnostic_prompt(table_type: str, req: DiagnosticPromptUpdateRequest) -> DiagnosticPromptTemplate:
        """Сохраняет пользовательский шаблон промпта для типа таблицы."""
        return prompt_manager.save_template(
            table_type=table_type,
            system_instruction=req.system_instruction,
            prompt_template=req.prompt_template,
            name=req.name,
            description=req.description,
        )

    @router.post("/prompts/{table_type}/reset", response_model=DiagnosticPromptTemplate)
    async def reset_diagnostic_prompt(table_type: str) -> DiagnosticPromptTemplate:
        """Сбрасывает шаблон промпта к дефолтной системной версии."""
        return prompt_manager.reset_template(table_type)

    @router.post("/explain", response_model=DiagnosticExplainResponse)
    async def explain_table_item(req: DiagnosticExplainRequest) -> DiagnosticExplainResponse:
        """Генерирует AI-объяснение и оценку для выбранного элемента таблицы."""
        # Получаем соответствующий шаблон промпта для типа таблицы
        tmpl = prompt_manager.get_template(req.table_type)

        # Попытка вызова языковой модели через чат-роутер
        try:
            from src.api.router_chat import get_chat_model
            model_key = req.model or "gemini_cli:gemini-2.5-flash"
            llm = get_chat_model(
                model_key,
                system_instruction=tmpl.system_instruction,
            )

            # Обогащение веб-поиском при необходимости
            web_context = ""
            if req.web_search and req.title:
                try:
                    from src.ai.agents.tools import web_search as run_web_search
                    search_query = f"{req.title} {req.subtitle or ''} {req.table_type} software security purpose"
                    web_res = await run_web_search(search_query.strip())
                    if web_res and not str(web_res).startswith('{"error"'):
                        web_context = f"\n\nСВЕДЕНИЯ ИЗ ИНТЕРНЕТА (Web Search):\n{web_res[:1500]}"
                except Exception as ws_err:
                    logger.debug(f"Веб-поиск для '{req.title}' завершился с ошибкой: {ws_err}")

            raw_with_web = (req.raw_data or "") + web_context

            prompt = tmpl.format_prompt(
                title=req.title,
                subtitle=req.subtitle or "",
                metadata=req.metadata,
                raw_data=raw_with_web or "",
            )

            resp_text = ""
            if hasattr(llm, "ask"):
                resp_text = await llm.ask(prompt)
            elif hasattr(llm, "chat"):
                resp_text = await llm.chat(prompt)
            elif hasattr(llm, "generate_response"):
                resp_text = await llm.generate_response(prompt)

            if resp_text:
                cleaned = resp_text.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                data = json.loads(cleaned)
                return DiagnosticExplainResponse(
                    summary=data.get("summary", ""),
                    developer=data.get("developer", req.subtitle or "Неизвестен"),
                    category=data.get("category", "Диагностика"),
                    security_verdict=data.get("security_verdict", "Оценка безопасности завершена."),
                    performance_impact=data.get("performance_impact", "В пределах нормы."),
                    recommendation=data.get("recommendation", "Оставить как есть."),
                    action_steps=data.get("action_steps", ["Проверьте актуальность конфигурации."]),
                )
        except Exception as e:
            logger.debug(f"AI LLM generation fallback triggered for diagnostic '{req.title}': {e}")

        # Надежный эвристический fallback
        return _generate_heuristic_explanation(req)

    return router


def _generate_heuristic_explanation(req: DiagnosticExplainRequest) -> DiagnosticExplainResponse:
    """Генерирует экспертное контекстное объяснение на основе эвристики и доменных правил."""
    tt = (req.table_type or "generic").lower()
    title_lower = (req.title or "").lower()
    raw_lower = (req.raw_data or "").lower()
    sub_lower = (req.subtitle or "").lower()

    # 1. Установленное ПО (Software Audit)
    if tt == "software":
        is_ms = "microsoft" in sub_lower or "windows" in title_lower or "microsoft" in title_lower
        is_google = "google" in sub_lower or "chrome" in title_lower
        dev = "Microsoft Corporation" if is_ms else ("Google LLC" if is_google else (req.subtitle or "Неизвестный разработчик"))
        sec = "Официальное ПО, подписанное доверенным разработчиком." if (is_ms or is_google) else "Установленное стороннее приложение. Проверьте актуальность версии."
        return DiagnosticExplainResponse(
            summary=f"Программа «{req.title}». Зарегистрирована в реестре установленного программного обеспечения Windows.",
            developer=dev,
            category="Установленное приложение",
            security_verdict=sec,
            performance_impact="Занимает дисковое пространство. Проверьте наличие фоновых служб обновления.",
            recommendation="Если приложение активно используется — оставьте и следите за обновлениями. Если не используется — рекомендуется удалить через «Панель управления».",
            action_steps=[
                "Проверьте дату установки и регулярность использования.",
                "При неактуальности удалите для освобождения диска.",
            ],
        )

    # 2. Процессы Windows (System Inspector)
    if tt == "process":
        is_system_proc = title_lower in ("explorer.exe", "svchost.exe", "services.exe", "lsass.exe", "system", "csrss.exe", "winlogon.exe", "smss.exe", "dwm.exe")
        is_temp = "temp" in raw_lower or "appdata" in raw_lower
        sec = "Критический системный процесс ядра Windows. Завершение приведет к сбою ОС." if is_system_proc else (
            "Внимание: процесс запущен из временного каталога (%TEMP%/AppData). Рекомендуется проверка!" if is_temp else "Штатный процесс пользовательской сессии или фонового сервиса."
        )
        rec = "Не завершать процесс (системный компонент)." if is_system_proc else "При аномальной нагрузке на CPU/память процесс можно завершить через диспетчер."
        return DiagnosticExplainResponse(
            summary=f"Процесс «{req.title}» (PID: {req.metadata.get('pid', 'N/A')}). Активно выполняется в операционной системе.",
            developer="Microsoft Corporation" if is_system_proc else "Разработчик приложения",
            category="Системный процесс" if is_system_proc else "Пользовательский процесс",
            security_verdict=sec,
            performance_impact=f"Потребление CPU: {req.metadata.get('cpu_percent', req.metadata.get('cpu', 'N/A'))}%, Память: {req.metadata.get('memory_mb', req.metadata.get('memory', 'N/A'))} MB.",
            recommendation=rec,
            action_steps=[
                "Оцените текущую нагрузку на процессор и оперативную память.",
                "При зависании или утечке памяти завершите процесс.",
            ],
        )

    # 3. Службы Windows (System Control Center)
    if tt == "service":
        status = req.metadata.get("status", "Running")
        start_type = req.metadata.get("start_type", "Auto")
        return DiagnosticExplainResponse(
            summary=f"Системная служба Windows «{req.title}» ({req.subtitle or req.title}). Обеспечивает фоновое выполнение задач ОС или установленного ПО.",
            developer="Операционная система Windows" if "system32" in raw_lower else "Сторонний разработчик",
            category="Фоновая служба (Windows Service)",
            security_verdict=f"Исполняемый файл: {req.raw_data or 'Системный бинарник'}. Статус службы: {status}.",
            performance_impact=f"Тип запуска: {start_type}. Служба активна в фоне.",
            recommendation="Не отключайте системные службы Windows без уверенности в последствиях. Сторонние ненужные службы можно перевести в ручной режим (Manual).",
            action_steps=[
                "При необходимости измените тип запуска (Auto / Manual / Disabled).",
                "Перезапустите службу при сбоях в работе связанного ПО.",
            ],
        )

    # 4. Задачи планировщика (Scheduled Tasks)
    if tt == "task":
        return DiagnosticExplainResponse(
            summary=f"Запланированная задача Windows Task Scheduler «{req.title}». Выполняется по расписанию или событию в системе.",
            developer="Microsoft / Стороннее ПО",
            category="Задача планировщика",
            security_verdict="Регулярно инициирует запуск связанного процесса или скрипта.",
            performance_impact="Кратковременная нагрузка на диск и CPU в момент срабатывания триггера.",
            recommendation="Отключите задачу, если соответствующее приложение больше не используется или вызывает нежелательные фоновые пробуждения ПК.",
            action_steps=[
                "Проверьте расписание и триггеры запуска задачи.",
                "Отключите задачу, если она вызывает избыточную нагрузку.",
            ],
        )

    # 5. Сетевые соединения (Network Monitor)
    if tt == "network":
        r_addr = req.metadata.get("remote_address", req.metadata.get("remote", req.subtitle or "Внешний узел"))
        l_addr = req.metadata.get("local_address", req.metadata.get("local", "Локальный узел"))
        proto = req.metadata.get("protocol", "TCP")
        is_loopback = "127.0.0.1" in str(r_addr) or "localhost" in str(r_addr)
        sec = "Локальное межпроцессное соединение (Loopback/IPC). Безопасно." if is_loopback else f"Внешнее сетевое соединение с узлом {r_addr}."
        return DiagnosticExplainResponse(
            summary=f"Сетевой сокет {proto}: {l_addr} ➔ {r_addr}. Состояние: {req.metadata.get('state', 'ESTABLISHED')}.",
            developer="Сетевой стек Windows",
            category="Сетевое соединение",
            security_verdict=sec,
            performance_impact="Занимает сетевой сокет и потребляет сетевой трафик.",
            recommendation="Если удаленный IP-адрес или порт вызывают подозрения, заблокируйте соединение через Брандмауэр Windows (Windows Defender Firewall).",
            action_steps=[
                "Проверьте имя процесса, открывшего данное соединение.",
                "При неизвестном внешнем адресе проверьте IP через Whois / AbuseIPDB.",
            ],
        )

    # 6. Ключи и параметры реестра (Registry Viewer)
    if tt == "registry":
        return DiagnosticExplainResponse(
            summary=f"Параметр системного реестра «{req.title}» (Тип: {req.metadata.get('type', 'REG_SZ')}).",
            developer="Реестр Windows",
            category="Параметр реестра",
            security_verdict=f"Значение параметра: {req.raw_data or req.subtitle or 'Не задано'}. Влияет на конфигурацию компонентов ОС или ПО.",
            performance_impact="Низкое — считывается при старте или запросе конфигурации.",
            recommendation="Редактируйте параметры реестра с осторожностью. Перед изменением создайте точку восстановления или резервную копию ветки (REG экспорт).",
            action_steps=[
                "Создайте резервную копию ветки реестра перед правкой.",
                "Проверьте документацию по конкретному параметру перед изменением.",
            ],
        )

    # 7. Пользователи и группы (Windows Admin)
    if tt == "user" or tt == "group":
        is_admin = "admin" in title_lower or "администратор" in title_lower
        return DiagnosticExplainResponse(
            summary=f"Учетная запись / Группа безопасности Windows «{req.title}».",
            developer="Security Accounts Manager (SAM) / Active Directory",
            category="Учетная запись" if tt == "user" else "Группа безопасности",
            security_verdict="Обладает повышенными административными привилегиями в системе." if is_admin else "Обычная пользовательская учетная запись со стандартными правами доступа.",
            performance_impact="Низкое — аутентификация при входе в сессию.",
            recommendation="Соблюдайте принцип наименьших привилегий (Least Privilege). Не используйте права администратора для повседневной работы.",
            action_steps=[
                "Проверьте актуальность членства в группах безопасности.",
                "Убедитесь в наличии сложного пароля для учетной записи.",
            ],
        )

    # 8. Мониторинг веб-сайтов (Website Monitor)
    if tt == "website":
        http_code = req.metadata.get("status_code", req.metadata.get("status", "200"))
        latency = req.metadata.get("latency_ms", req.metadata.get("response_time", "N/A"))
        is_ok = str(http_code).startswith("2") or str(http_code).startswith("3")
        return DiagnosticExplainResponse(
            summary=f"Веб-ресурс «{req.title}» ({req.subtitle or req.raw_data}). Код ответа: {http_code}, задержка: {latency} ms.",
            developer="Веб-сервер / Хостинг",
            category="Веб-сервис",
            security_verdict="Ресурс доступен и отвечает по защищенному протоколу HTTPS." if is_ok else "Внимание: зафиксирован сбой или ошибка доступности ресурса!",
            performance_impact=f"Время отклика: {latency} ms.",
            recommendation="Ресурс функционирует нормально." if is_ok else "Проверьте логи веб-сервера, срок действия SSL-сертификата и настройки DNS.",
            action_steps=[
                "Проверьте доступность узла с разных сетевых провайдеров.",
                "Проверьте статус SSL-сертификата и конфигурацию Nginx / Cloudflare.",
            ],
        )

    # 9. RAG документы базы знаний (RAG Tab)
    if tt == "rag_doc":
        chunks = req.metadata.get("chunks", req.metadata.get("chunk_count", "N/A"))
        size = req.metadata.get("size", "N/A")
        return DiagnosticExplainResponse(
            summary=f"Документ базы знаний RAG «{req.title}». Содержит {chunks} семантических чанков, размер: {size}.",
            developer="RAG Knowledge Store",
            category="Документ базы знаний",
            security_verdict="Документ проиндексирован в локальном векторном хранилище и доступен для семантического поиска ИИ.",
            performance_impact="Занимает место в векторной базе данных и кэше эмбеддингов.",
            recommendation="Документ активен. При обновлении исходного файла выполните переиндексацию чанков для поддержания актуальности контекста.",
            action_steps=[
                "Проверьте качество найденных чанков в тесте RAG поиска.",
                "При необходимости обновите или переиндексируйте файл.",
            ],
        )

    # 10. Дисковые тома и накопители (Disks / Storage)
    if tt == "disk":
        free = req.metadata.get("free", req.metadata.get("free_gb", "N/A"))
        total = req.metadata.get("total", req.metadata.get("total_gb", "N/A"))
        return DiagnosticExplainResponse(
            summary=f"Дисковый накопитель / том «{req.title}» ({req.subtitle or 'Локальный диск'}). Свободно: {free} из {total}.",
            developer="Storage Controller",
            category="Дисковый том",
            security_verdict="Файловая система смонтирована и доступна для чтения/записи.",
            performance_impact=f"Использование диска: {req.metadata.get('percent', 'N/A')}% занято.",
            recommendation="Поддерживайте не менее 15-20% свободного места на системном диске для корректной работы виртуальной памяти и обновлений Windows.",
            action_steps=[
                "Очистите временные файлы (%TEMP%) при дефиците дискового пространства.",
                "Проверьте SMART-статус накопителя при подозрительных задержках ввода-вывода.",
            ],
        )

    # 11. Общий шаблон по умолчанию
    return DiagnosticExplainResponse(
        summary=f"Запись «{req.title}» ({req.subtitle or req.table_type}). Данные зарегистрированы в системе.",
        developer=req.subtitle or "Системный компонент",
        category="Элемент данных",
        security_verdict="Параметры записи соответствуют штатной конфигурации.",
        performance_impact="Штатное использование ресурсов.",
        recommendation="Оставьте запись активной или скорректируйте параметры при необходимости.",
        action_steps=[
            "Проверьте актуальность метаданных.",
            "При необходимости выполните пересканирование.",
        ],
    )


__all__ = ["init_router"]
