# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Diagnostics
# =============================================================================
# Description:
#   Универсальный REST API эндпоинт для AI-диагностики, контекстного объяснения
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_diagnostics import DiagnosticExplainRequest
#
#     service = DiagnosticExplainRequest()
#
# File: router_diagnostics.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 11:40:00
# =============================================================================

from __future__ import annotations
"""Универсальный REST API эндпоинт для AI-диагностики, контекстного объяснения"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from header import __root__
from logger import logger


class DiagnosticExplainRequest(BaseModel):
    """Запрос на AI-объяснение элемента таблицы."""
    table_type: str = Field(default="generic", description="Тип таблицы (software, process, service, task, network, registry, user, website, rag_doc, disk)")
    panel_id: Optional[str] = Field(default=None, description="Идентификатор вызывающей панели интерфейса (например, panel-winadmin-users)")
    system_instruction: Optional[str] = Field(default=None, description="Пользовательская или переопределенная системная инструкция для LLM")
    title: str = Field(default="", description="Основное имя или заголовок элемента")
    subtitle: Optional[str] = Field(default="", description="Вторичный заголовок (издатель, путь, IP, статус)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Набор ключевых атрибутов записи")
    raw_data: Optional[str] = Field(default="", description="Сырая строка команды, пути или JSON")
    model: Optional[str] = Field(default=None, description="Опциональное имя конкретной модели")
    provider: Optional[str] = Field(default=None, description="Опциональный AI провайдер")
    web_search: bool = Field(default=True, description="Выполнять ли онлайн поиск для обогащения контекста")
    cache_only: bool = Field(default=False, description="Проверить только кэш/базу знаний WikiLLM без вызова LLM")
    force_refresh: bool = Field(default=False, description="Принудительно запросить модель ИИ для улучшения/обновления кэша")


class DiagnosticExplainResponse(BaseModel):
    """Структурированный ответ AI-диагностики элемента таблицы."""
    summary: str = Field(description="Краткое понятное описание назначения элемента")
    developer: str = Field(default="Неизвестен", description="Разработчик / принадлежность / вендор")
    category: str = Field(default="Системный компонент", description="Категория элемента")
    security_verdict: str = Field(description="Оценка безопасности, легитимности и рисков")
    performance_impact: str = Field(description="Влияние на производительность и ресурсы")
    recommendation: str = Field(description="Практическая рекомендация эксперта")
    action_steps: List[str] = Field(default_factory=list, description="Пошаговые рекомендуемые действия")
    canonical_key: Optional[str] = Field(default=None, description="Канонический ключ сущности в WikiLLM")
    source: str = Field(default="gemini", description="Источник ответа (wikillm / gemini / heuristic / not_found)")
    is_verified: bool = Field(default=False, description="Признак верификации знания в WikiLLM")



from apps.windows.api.diagnostics_prompt_manager import (
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

    def _resolve_diagnostic_model(requested_model: Optional[str] = None, web_search: bool = False) -> str:
        """Определяет модель для диагностики из запроса или активного файла конфигурации.

        Если модель не указана явно в запросе и не найдена в конфигурации,
        выбрасывает HTTPException(400) согласно стандартам разработки (запрет скрытого хардкода).

        Args:
            requested_model: Модель, переданная в запросе.
            web_search: Флаг использования веб-поиска.

        Returns:
            str: Имя валидной модели.

        Raises:
            HTTPException: Если модель не передана и не определена в конфигурации.
        """
        if requested_model and requested_model.strip():
            m = requested_model.strip()
            if m.startswith("gemini_cli:"):
                return m.split(":", 1)[1]
            return m

        # Поиск активного конфигурационного файла
        cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
        active_path: Optional[Path] = None
        if cfg_env:
            p = Path(cfg_env)
            active_path = p if p.is_absolute() else (__root__ / cfg_env)

        candidates = [
            active_path,
            __root__ / "apps" / "windows" / "config.json",
            __root__ / "start_scenarios_config" / "tc.json",
            __root__ / "config" / "tc.json",
            __root__ / "config.json",
        ]

        for candidate in candidates:
            if candidate and candidate.exists():
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        cfg = json.load(f)

                    # 1. Если включен web_search, проверяем секцию web_search
                    if web_search:
                        ws_cfg = cfg.get("web_search", {})
                        if isinstance(ws_cfg, dict) and ws_cfg.get("gemini_model"):
                            val = str(ws_cfg["gemini_model"]).strip()
                            if val:
                                return val

                    # 2. Проверяем ai_providers_and_models_configuration
                    ai_p_cfg = cfg.get("ai_providers_and_models_configuration", {})
                    if isinstance(ai_p_cfg, dict):
                        if ai_p_cfg.get("default_model"):
                            val = str(ai_p_cfg["default_model"]).strip()
                            if val:
                                return val
                        providers = ai_p_cfg.get("providers", {})
                        if isinstance(providers, dict):
                            gemini_p = providers.get("gemini", {})
                            if isinstance(gemini_p, dict) and gemini_p.get("model"):
                                val = str(gemini_p["model"]).strip()
                                if val:
                                    return val

                    # 3. Проверяем секцию ai
                    ai_sec = cfg.get("ai", {})
                    if isinstance(ai_sec, dict):
                        if ai_sec.get("default_model"):
                            val = str(ai_sec["default_model"]).strip()
                            if val:
                                return val
                        if ai_sec.get("model"):
                            val = str(ai_sec["model"]).strip()
                            if val:
                                return val
                        providers = ai_sec.get("providers", {})
                        if isinstance(providers, dict):
                            gemini_p = providers.get("gemini", {})
                            if isinstance(gemini_p, dict) and gemini_p.get("model"):
                                val = str(gemini_p["model"]).strip()
                                if val:
                                    return val
                except Exception as e:
                    logger.debug(f"[router_diagnostics] Ошибка чтения конфигурации {candidate}: {e}")

        # Если модель не указана и не найдена в конфиге - выбрасываем ошибку (Fail-Fast)
        raise HTTPException(
            status_code=400,
            detail="Модель AI не указана в запросе и не настроена в конфигурации (default_model / web_search.gemini_model)."
        )

    @router.post("/explain", response_model=DiagnosticExplainResponse)
    async def explain_table_item(req: DiagnosticExplainRequest) -> DiagnosticExplainResponse:
        """Генерирует AI-объяснение и оценку для выбранного элемента таблицы."""
        # 1. Вычисляем канонический ключ для базы знаний WikiLLM
        canonical_key: Optional[str] = None
        try:
            from apps.windows.wikillm.normalizer import CanonicalKeyNormalizer
            canonical_key = CanonicalKeyNormalizer.compute_key_from_parts(
                table_type=req.table_type,
                title=req.title,
                subtitle=req.subtitle or "",
            )
        except Exception as e:
            logger.debug(f"Ошибка вычисления канонического ключа WikiLLM: {e}")

        # 2. Проверяем наличие верифицированного знания в локальной базе WikiLLM
        if canonical_key and not req.force_refresh:
            try:
                from apps.windows.wikillm.router import get_engine
                engine = get_engine()
                entity = engine.storage.get_entity(canonical_key)
                if entity and (entity.provenance_source.value == "documented" or any(c.verified for c in entity.claims)):
                    rec_text = "Оставить без изменений."
                    for c in entity.claims:
                        if "Рекомендация:" in c.statement:
                            rec_text = c.statement.replace("Рекомендация:", "").strip()
                            break
                    actions = [s.title for s in entity.diagnostic_info.remediation_steps] if entity.diagnostic_info else []
                    sec_text = entity.diagnostic_info.symptoms[0] if entity.diagnostic_info and entity.diagnostic_info.symptoms else "Проверено в базе знаний WikiLLM"
                    dev_text = entity.diagnostic_info.related_components[0] if entity.diagnostic_info and entity.diagnostic_info.related_components else req.subtitle or "Верифицировано"

                    logger.info(f"[WikiLLM] Мгновенный ответ из базы знаний для '{canonical_key}' (верифицировано)")
                    return DiagnosticExplainResponse(
                        summary=entity.summary,
                        developer=dev_text,
                        category=entity.category,
                        security_verdict=sec_text,
                        performance_impact="В пределах нормы (из базы знаний WikiLLM)",
                        recommendation=rec_text,
                        action_steps=actions or ["Действий не требуется."],
                        canonical_key=canonical_key,
                        source="wikillm",
                        is_verified=True,
                    )
            except Exception as e:
                logger.debug(f"Проверка WikiLLM пропущена: {e}")

        # Если запрошена только проверка кэша базы знаний и запись не найдена
        if req.cache_only:
            return DiagnosticExplainResponse(
                summary="",
                developer="",
                category="",
                security_verdict="",
                performance_impact="",
                recommendation="",
                action_steps=[],
                canonical_key=canonical_key,
                source="not_found",
                is_verified=False,
            )

        # Получаем соответствующий шаблон промпта для типа таблицы
        tmpl = prompt_manager.get_template(req.table_type)
        sys_instruction = req.system_instruction.strip() if (req.system_instruction and req.system_instruction.strip()) else tmpl.system_instruction

        # 3. Вызов языковой модели через прямой GoogleGenerativeAI с Web Grounding
        try:
            from src.ai.gemini.generative_ai import GoogleGenerativeAI

            gen_cfg: Dict[str, Any] = {}
            if req.web_search:
                gen_cfg["use_google_search"] = True

            model_name = _resolve_diagnostic_model(
                requested_model=req.model,
                web_search=req.web_search,
            )

            ai = GoogleGenerativeAI(
                model_name=model_name,
                system_instruction=sys_instruction,
                generation_config=gen_cfg,
            )

            import asyncio
            prompt = tmpl.format_prompt(
                title=req.title,
                subtitle=req.subtitle or "",
                metadata=req.metadata,
                raw_data=req.raw_data or "",
            )

            resp_text = await asyncio.wait_for(
                ai.ask(prompt, attempts=1, generation_config=gen_cfg),
                timeout=6.0
            )

            if resp_text and not resp_text.startswith("Model error:"):
                cleaned = resp_text.strip()
                # Извлекаем JSON если вокруг есть Markdown блок
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
                if json_match:
                    cleaned = json_match.group(1).strip()

                # Извлекаем JSON по внешним фигурным скобкам
                if "{" in cleaned and "}" in cleaned:
                    start_idx = cleaned.find("{")
                    end_idx = cleaned.rfind("}") + 1
                    cleaned = cleaned[start_idx:end_idx]

                data = json.loads(cleaned)
                return DiagnosticExplainResponse(
                    summary=data.get("summary", ""),
                    developer=data.get("developer", req.subtitle or "Неизвестен"),
                    category=data.get("category", "Диагностика"),
                    security_verdict=data.get("security_verdict", "Оценка безопасности завершена."),
                    performance_impact=data.get("performance_impact", "В пределах нормы."),
                    recommendation=data.get("recommendation", "Оставить как есть."),
                    action_steps=data.get("action_steps", ["Проверьте актуальность конфигурации."]),
                    canonical_key=canonical_key,
                    source="gemini",
                    is_verified=False,
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"AI LLM generation fallback triggered for diagnostic '{req.title}': {e}")

        # Надежный эвристический fallback
        resp = _generate_heuristic_explanation(req)
        resp.canonical_key = canonical_key
        resp.source = "heuristic"
        resp.is_verified = False
        return resp

    @router.post("/approve")
    @router.post("/wikillm/approve")
    async def approve_knowledge_endpoint(req: Dict[str, Any]) -> Dict[str, Any]:
        """Одобряет результат диагностики и фиксирует его в базе знаний WikiLLM."""
        from apps.windows.wikillm.router import approve_knowledge as wikillm_approve, ApproveKnowledgeRequest
        req_obj = ApproveKnowledgeRequest(**req)
        return await wikillm_approve(req_obj)

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
        # Специфические утилиты мониторинга и разработки
        if "librehardwaremonitor" in title_lower:
            return DiagnosticExplainResponse(
                summary="Утилита мониторинга аппаратных компонентов и датчиков ПК с открытым исходным кодом (Open Source). Развилка проекта Open Hardware Monitor.",
                developer="LibreHardwareMonitor Community (GitHub Open Source)",
                category="Системная диагностика / Мониторинг аппаратных компонентов",
                security_verdict="Легитимное доверенное ПО с открытым исходным кодом. Для прямого чтения низкоуровневых датчиков материнской платы, CPU и GPU использует драйвер кольца ядра (Ring-0).",
                performance_impact=f"Минимальная нагрузка при стандартном интервале опроса сенсоров. CPU: {req.metadata.get('cpu_percent', req.metadata.get('cpu', '0.1'))}%, RAM: {req.metadata.get('memory_mb', req.metadata.get('memory', '35'))} MB.",
                recommendation="Безопасная утилита телеметрии. Необходима для отслеживания температур, напряжений, оборотов кулеров и нагрузки системы.",
                action_steps=[
                    "Используйте для контроля температурных режимов и предотвращения перегрева компонентов.",
                    "При необходимости закройте или остановите сбор телеметрии, если мониторинг больше не требуется.",
                ],
            )

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

    # 7. Пользователи и группы (Windows Admin & Identity)
    if tt in ("user", "user_account", "group"):
        if "defaultaccount" in title_lower or "-503" in sub_lower:
            return DiagnosticExplainResponse(
                summary="Встроенная системная учетная запись Windows (System Managed Account). Введена начиная с Windows 10 для выполнения изолированных многопользовательских процессов и приложений UWP/AppContainer.",
                developer="Microsoft Corporation (Операционная система Windows)",
                category="Встроенная системная учетная запись (RID 503)",
                security_verdict="Штатный системный аккаунт. По умолчанию отключен (Disabled), прямой интерактивный вход в систему заблокирован, пароль управляется ОС.",
                performance_impact="Не потребляет ресурсы в фоновом режиме. Активируется только при запуске контейнеризированных сценариев Windows.",
                recommendation="Не удаляйте и не включайте учетную запись вручную. Оставьте в исходном состоянии (Disabled), управляемом операционной системой.",
                action_steps=[
                    "Убедитесь, что аккаунт находится в состоянии 'Отключен' (Disabled).",
                    "Не назначайте учетной записи административные привилегии.",
                ],
            )
        if "wdagutilityaccount" in title_lower or "-504" in sub_lower:
            return DiagnosticExplainResponse(
                summary="Служебная учетная запись Windows Defender Application Guard (WDAG). Используется для запуска изолированных сессий браузера Edge и песочниц.",
                developer="Microsoft Corporation (Windows Security)",
                category="Служебная учетная запись изоляции (RID 504)",
                security_verdict="Легитимный изолированный аккаунт безопасности. Заблокирован для прямого входа.",
                performance_impact="Используется только во время активных изолированных сессий Application Guard.",
                recommendation="Оставьте под управлением Windows Defender.",
                action_steps=[
                    "Не изменяйте параметры аккаунта вручную.",
                ],
            )
        if "guest" in title_lower or "гость" in title_lower or "-501" in sub_lower:
            return DiagnosticExplainResponse(
                summary="Встроенная гостевая учетная запись Windows для временного доступа пользователей без собственного аккаунта.",
                developer="Microsoft Corporation",
                category="Встроенная гостевая учетная запись (RID 501)",
                security_verdict="По соображениям безопасности в современных версиях Windows должна быть строго отключена (Disabled).",
                performance_impact="Минимальное.",
                recommendation="Рекомендуется держать гостевую запись отключенной во избежание несанкционированного доступа.",
                action_steps=[
                    "Убедитесь, что учетная запись 'Гость' отключена.",
                ],
            )
        if "administrator" in title_lower or "администратор" in title_lower or "-500" in sub_lower:
            return DiagnosticExplainResponse(
                summary="Встроенная учетная запись главного локального администратора Windows (RID 500). Обладает полным безусловным контролем над операционной системой.",
                developer="Microsoft Corporation",
                category="Встроенный локальный администратор (RID 500)",
                security_verdict="Обладает максимальными привилегиями в системе. Требует строгого контроля и сложного пароля.",
                performance_impact="Зависит от выполняемых задач администратора.",
                recommendation="По рекомендациям Microsoft встроенного администратора лучше держать отключенным или переименованным, используя персонализированные учетные записи с UAC.",
                action_steps=[
                    "Установите надежный сложный пароль.",
                    "Используйте повседневную работу под стандартной учетной записью с подтверждением через UAC.",
                ],
            )

        is_admin = "admin" in title_lower or "администратор" in title_lower
        return DiagnosticExplainResponse(
            summary=f"Учетная запись / Группа безопасности Windows «{req.title}».",
            developer="Security Accounts Manager (SAM) / Active Directory",
            category="Учетная запись пользователя" if tt in ("user", "user_account") else "Группа безопасности",
            security_verdict="Обладает повышенными административными привилегиями в системе." if is_admin else "Обычная пользовательская учетная запись со стандартными правами доступа.",
            performance_impact=f"Профиль: {req.metadata.get('profile_path', 'Стандартный')}, Процессов: {req.metadata.get('process_count', 0)}.",
            recommendation="Соблюдайте принцип наименьших привилегий (Least Privilege). Не используйте права администратора для повседневной работы.",
            action_steps=[
                "Проверьте актуальность членства в группах безопасности.",
                "Убедитесь в наличии сложного пароля для учетной записи.",
            ],
        )

    # 8. События безопасности (Security Events)
    if tt in ("security_event", "event"):
        return DiagnosticExplainResponse(
            summary=f"Событие аудита безопасности Windows «{req.title}» ({req.subtitle or ''}).",
            developer="Подсистема безопасности Windows (LSA / SAM / Defender)",
            category="Событие журнала безопасности",
            security_verdict="Зафиксировано в журнале аудита безопасности Windows.",
            performance_impact="Не влияет на быстродействие ОС.",
            recommendation="Проверьте статус события и инициатора при наличии повторяющихся ошибок входа.",
            action_steps=[
                "Проверьте учетную запись инициатора события.",
                "Сопоставьте время события с активностью пользователя.",
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
