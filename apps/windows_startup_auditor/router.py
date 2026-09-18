# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Auditor FastAPI Router
# =============================================================================
# Description:
#   REST API и WebSocket эндпоинты для сканирования, аудита безопасности,
#   управления состоянием элементов автозагрузки и выгрузки отчетов.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows_startup_auditor.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows_startup_auditor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для аудита и управления автозагрузкой Windows."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from src.logger import logger
from apps.windows_startup_auditor.core.auditor import StartupAuditor
from apps.windows_startup_auditor.core.manager import StartupManager
from apps.windows_startup_auditor.core.models import (
    AuditReport,
    AuditSummary,
    LocationInfo,
    RiskLevel,
    StartupEntry,
    StartupExplainRequest,
    StartupExplainResponse,
    StartupLocationType,
    ToggleRequest,
    ToggleResponse,
)
from apps.windows_startup_auditor.core.scanner import StartupScanner


def init_router() -> APIRouter:
    """Инициализирует и настраивает FastAPI роутер для Startup Auditor.

    Returns:
        APIRouter: Сконфигурированный экземпляр APIRouter.
    """
    router = APIRouter(prefix="/api/v1/startup-auditor", tags=["Windows Startup Auditor"])
    scanner = StartupScanner()
    auditor = StartupAuditor(scanner=scanner)
    manager = StartupManager()

    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        """Возвращает статус доступности сервиса аудита автозапуска."""
        return {
            "status": "online",
            "service": "Windows Startup Auditor",
            "version": "1.0.0",
            "monitored_locations_count": len(scanner.get_monitored_locations()),
        }

    @router.get("/locations", response_model=List[LocationInfo])
    async def get_locations() -> List[LocationInfo]:
        """Возвращает список всех контролируемых мест автозагрузки."""
        return scanner.get_monitored_locations()

    @router.get("/audit", response_model=AuditReport)
    async def run_full_audit() -> AuditReport:
        """Запускает полный аудит автозапуска и возвращает структурированный отчет."""
        try:
            return auditor.run_audit()
        except Exception as e:
            logger.error(f"Ошибка при выполнении аудита автозагрузки: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/summary", response_model=AuditSummary)
    async def get_summary() -> AuditSummary:
        """Возвращает краткую сводку аудита и показатель чистоты (Health Score)."""
        report = auditor.run_audit()
        return report.summary

    @router.get("/entries", response_model=List[StartupEntry])
    async def get_entries(
        category: Optional[str] = Query(default=None, description="Фильтр по категории"),
        risk_level: Optional[str] = Query(default=None, description="Фильтр по уровню риска (clean, warning, suspicious, critical)"),
        location_type: Optional[str] = Query(default=None, description="Фильтр по типу локации"),
        enabled_only: Optional[bool] = Query(default=None, description="Фильтр только активных элементов"),
        search: Optional[str] = Query(default=None, description="Поисковый запрос по имени, команде или пути"),
    ) -> List[StartupEntry]:
        """Возвращает список элементов автозагрузки с фильтрацией."""
        report = auditor.run_audit()
        entries = report.entries

        if category:
            entries = [e for e in entries if category.lower() in (e.category.value if hasattr(e.category, "value") else str(e.category)).lower()]

        if risk_level:
            entries = [e for e in entries if risk_level.lower() == (e.risk_level.value if hasattr(e.risk_level, "value") else str(e.risk_level)).lower()]

        if location_type:
            entries = [e for e in entries if location_type.lower() == (e.location_type.value if hasattr(e.location_type, "value") else str(e.location_type)).lower()]

        if enabled_only is not None:
            entries = [e for e in entries if e.is_enabled == enabled_only]

        if search:
            q = search.lower()
            entries = [
                e for e in entries
                if q in e.name.lower() or q in e.command.lower() or q in e.executable_path.lower() or q in e.publisher.lower()
            ]

        return entries

    @router.post("/explain", response_model=StartupExplainResponse)
    async def explain_startup_entry(req: StartupExplainRequest) -> StartupExplainResponse:
        """Генерирует подробный AI-анализ, оценку безопасности и рекомендации для выбранной программы."""
        # Попытка интеллектуального анализа через доступную языковую модель
        try:
            from src.api.router_chat import get_chat_model
            model_key = req.model or "gemini_cli:gemini-2.5-flash"
            llm = get_chat_model(
                model_key,
                system_instruction="Ты — эксперт по безопасности Windows и оптимизации автозагрузки. Отвечай строго в формате JSON.",
            )

            prompt = f"""Проведи детальный аудит и объясни назначение программы в автозагрузке Windows.

Параметры элемента автозапуска:
- Имя программы: {req.name}
- Издатель / Разработчик: {req.publisher or 'Неизвестен'}
- Исполняемый файл: {req.executable_path or 'Не указан'}
- Команда запуска: {req.command or 'Не указана'}
- Аргументы: {req.arguments or 'Нет'}
- Точка автозапуска: {req.location_type or 'Реестр'} (Путь: {req.location_path or 'Не указан'})
- Существует ли файл на диске: {'Да' if req.file_exists else 'НЕТ (битая ссылка)'}
- Цифровая подпись: {'Действительна' if req.is_signed else 'Без подписи / Неизвестно'}
- Влияние на запуск: {req.boot_impact or 'Среднее'}
- Уровень риска: {req.risk_level or 'clean'}

Верни СТРОГО JSON со следующей структурой (без markdown-оберток):
{{
  "summary": "Краткое понятное описание программы и её назначения на русском языке",
  "developer": "Имя разработчика или компании",
  "category": "Категория ПО (например, Системный компонент, Драйвер, Браузер, Облачный диск, AI Runtime)",
  "security_verdict": "Оценка безопасности, легитимности и надежности",
  "boot_impact_analysis": "Анализ влияния на скорость старта Windows и потребление памяти",
  "startup_recommendation": "Четкая рекомендация: оставить в автозагрузке или отключить, с пояснением почему",
  "action_steps": ["Рекомендованный шаг 1", "Рекомендованный шаг 2"]
}}
"""
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
                return StartupExplainResponse(
                    summary=data.get("summary", ""),
                    developer=data.get("developer", req.publisher or "Неизвестен"),
                    category=data.get("category", "Приложение"),
                    security_verdict=data.get("security_verdict", "Оценка безопасности завершена."),
                    boot_impact_analysis=data.get("boot_impact_analysis", "Влияние на запуск в пределах нормы."),
                    startup_recommendation=data.get("startup_recommendation", "Оставить как есть."),
                    action_steps=data.get("action_steps", ["Проверьте актуальность программы."]),
                )
        except Exception as e:
            logger.debug(f"AI LLM generation fallback triggered for startup entry '{req.name}': {e}")

        # Надежный эвристический анализ при недоступности LLM
        return _generate_heuristic_explanation(req)

    @router.post("/toggle", response_model=ToggleResponse)
    async def toggle_startup_entry(req: ToggleRequest) -> ToggleResponse:
        """Включает или отключает элемент автозагрузки."""
        report = auditor.run_audit()
        target_entry = next((e for e in report.entries if e.id == req.entry_id), None)

        if not target_entry:
            raise HTTPException(status_code=404, detail=f"Элемент с ID '{req.entry_id}' не найден")

        return manager.toggle_item(target_entry, req.enable)

    @router.get("/export")
    async def export_report(
        format: str = Query(default="json", pattern="^(json|csv)$", description="Формат выгрузки: json или csv"),
    ) -> Response:
        """Экспортирует отчет аудита в формате JSON или CSV."""
        report = auditor.run_audit()

        if format == "csv":
            csv_content = manager.export_to_csv(report)
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=startup_audit_{report.timestamp[:10]}.csv"},
            )

        json_content = manager.export_to_json(report)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=startup_audit_{report.timestamp[:10]}.json"},
        )

    @router.websocket("/stream")
    async def stream_audit_progress(websocket: WebSocket) -> None:
        """WebSocket поток обновлений аудита автозапуска."""
        await websocket.accept()
        try:
            while True:
                summary = auditor.run_audit().summary
                await websocket.send_json({"event": "summary_update", "data": summary.model_dump()})
                await asyncio.sleep(5.0)
        except WebSocketDisconnect:
            logger.debug("Startup auditor websocket disconnected")
        except Exception as e:
            logger.debug(f"Startup auditor websocket closed: {e}")
            await websocket.close()

    return router


def _generate_heuristic_explanation(req: StartupExplainRequest) -> StartupExplainResponse:
    """Генерирует экспертное контекстное объяснение на основе эвристического анализа метаданных программы."""
    name_lower = (req.name or "").lower()
    path_lower = (req.executable_path or req.command or "").lower()
    publisher = req.publisher or "Неизвестный разработчик"

    # 1. Битая ссылка (Orphan entry)
    if req.file_exists is False or "битая ссылка" in name_lower or "файл не найден" in path_lower:
        return StartupExplainResponse(
            summary=f"Элемент автозапуска «{req.name}» ссылается на отсутствующий файл на диске ({req.executable_path or req.command}). Это остаточная («мёртвая») запись после неполного удаления или перемещения программы.",
            developer=publisher,
            category="Битая ссылка (файл не найден)",
            security_verdict="Прямой вредоносной активности нет, однако битая ссылка замедляет инициализацию реестра и может генерировать скрытые ошибки при входе в Windows.",
            boot_impact_analysis="Низкое/Среднее — Windows тратит время на безуспешные попытки поиска и запуска отсутствующего исполняемого файла.",
            startup_recommendation="Рекомендуется отключить или удалить данную запись из автозагрузки для очистки реестра.",
            action_steps=[
                "Отключите автозапуск с помощью переключателя в таблице.",
                "При необходимости удалите остаточный ключ реестра.",
                "Проверьте, не остались ли пустые директории приложения в Program Files / AppData.",
            ],
        )

    # 2. Критические угрозы / IFEO / Подозрительные скрипты
    if (req.risk_level or "").lower() == "critical" or "ifeo" in str(req.location_type).lower():
        return StartupExplainResponse(
            summary=f"Обнаружен критический элемент автозапуска «{req.name}» через системный механизм перехвата (IFEO) или скрытые скрипты.",
            developer=publisher,
            category="Подозрительный перехват / IFEO",
            security_verdict="Критический уровень риска! Механизм Image File Execution Options (IFEO) и скрытые командные сценарии часто используются вредоносным ПО для подмены системных процессов или обхода контроля учетных записей.",
            boot_impact_analysis="Высокое — перехватывает выполнение системных процессов или запускает фоновые интерпретаторы.",
            startup_recommendation="Срочно отключите данную запись и выполните полное антивирусное сканирование.",
            action_steps=[
                "Немедленно переведите тумблер автозапуска в положение ОТКЛ.",
                "Проверьте исполняемый файл и аргументы в онлайн-сканере (например, VirusTotal).",
                "Выполните сканирование системы с помощью Microsoft Defender.",
            ],
        )

    # 3. Известные распространенные приложения
    if "onedrive" in name_lower or "onedrive" in path_lower:
        return StartupExplainResponse(
            summary="Microsoft OneDrive — официальный клиент облачного хранилища Microsoft для синхронизации файлов пользователя и резервного копирования рабочих папок.",
            developer="Microsoft Corporation",
            category="Облачное хранилище",
            security_verdict="Безопасный системный компонент Microsoft, подписан доверенным сертификатом.",
            boot_impact_analysis="Среднее — фоновая инициализация сетевого сокета и индексация локальных папок при входе в систему.",
            startup_recommendation="Оставить включенным, если вы активно используете синхронизацию файлов OneDrive. Можно отключить, если синхронизация требуется только периодически.",
            action_steps=[
                "Оставьте активным для непрерывной синхронизации файлов в облаке.",
                "Отключите, если запускаете OneDrive только вручную по мере необходимости.",
            ],
        )

    if "googledrive" in name_lower or "googledrive" in path_lower or "google drive" in name_lower:
        return StartupExplainResponse(
            summary="Google Drive for Desktop — клиент синхронизации и виртуального диска Google Workspace.",
            developer="Google LLC",
            category="Облачный диск",
            security_verdict="Доверенное официальное приложение Google, цифровая подпись валидна.",
            boot_impact_analysis="Среднее — монтирует виртуальный диск и запускает проверку локального кэша.",
            startup_recommendation="Оставьте включенным при постоянной работе с файлами Google Диска.",
            action_steps=[
                "Оставить в автозагрузке для постоянного доступа к облачным дискам.",
                "При нехватке RAM на старте можно запускать вручную.",
            ],
        )

    if "chrome" in name_lower or "chrome" in path_lower:
        return StartupExplainResponse(
            summary="Google Chrome AutoLaunch — фоновый агент предварительного запуска или проверки уведомлений браузера Google Chrome.",
            developer="Google LLC",
            category="Браузер / Фоновый агент",
            security_verdict="Доверенное приложение Google, рисков безопасности не обнаружено.",
            boot_impact_analysis="Среднее — запускает фоновые процессы Chrome в памяти еще до открытия пользователем.",
            startup_recommendation="Рекомендуется отключить. Браузер запускается быстро и без автозапуска, отключение сбережет оперативную память.",
            action_steps=[
                "Отключите автозапуск для ускорения старта системы.",
                "Браузер продолжит работать в штатном режиме при обычном открытии с ярлыка.",
            ],
        )

    if "msedge" in name_lower or "edge" in name_lower:
        return StartupExplainResponse(
            summary="Microsoft Edge AutoLaunch — фоновый процесс ускорения запуска и обновления браузера Microsoft Edge.",
            developer="Microsoft Corporation",
            category="Браузер / Фоновый агент",
            security_verdict="Официальный доверенный компонент операционной системы Windows.",
            boot_impact_analysis="Низкое/Среднее — резервирует память под предварительный запуск.",
            startup_recommendation="Можно безопасно отключить для минимизации фоновых процессов при входе в систему.",
            action_steps=[
                "Отключите автозапуск, если открываете браузер вручную.",
            ],
        )

    if "ollama" in name_lower or "ollama" in path_lower:
        return StartupExplainResponse(
            summary="Ollama — локальный сервер и среда выполнения больших языковых моделей (LLM) с REST API на порту 11434.",
            developer="Ollama / Community",
            category="AI Runtime / Сервер LLM",
            security_verdict="Безопасный инструмент разработки и запуска локальных нейросетей.",
            boot_impact_analysis="Среднее — запускает локальный HTTP-демон в фоновом режиме.",
            startup_recommendation="Оставить включенным, если вы используете AI Breadboard или локальные модели постоянно.",
            action_steps=[
                "Оставьте активным для постоянной готовности AI-сервисов.",
                "Отключите, если запускаете модели только время от времени.",
            ],
        )

    if "lm studio" in name_lower or "lm studio" in path_lower:
        return StartupExplainResponse(
            summary="LM Studio — графическая среда и локальный инференс-сервер для моделей GGUF и MLX.",
            developer="LM Studio Community",
            category="AI Runtime",
            security_verdict="Доверенная локальная среда для работы с открытыми моделями.",
            boot_impact_analysis="Среднее — стартует фоновый сервис моделирования.",
            startup_recommendation="Оставить включенным при постоянной работе с моделями или отключить для экономии системных ресурсов.",
            action_steps=[
                "Управляйте состоянием в зависимости от регулярности использования LM Studio.",
            ],
        )

    if "qbittorrent" in name_lower or "torrent" in name_lower:
        return StartupExplainResponse(
            summary="qBittorrent — BitTorrent-клиент с открытым исходным кодом для загрузки и раздачи файлов по протоколу P2P.",
            developer="qBittorrent project",
            category="P2P Клиент",
            security_verdict="Проверенное безопасное ПО с открытым исходным кодом.",
            boot_impact_analysis="Высокое — при старте открывает сетевые сокеты, проверяет хэши недокачанных торрентов и создает нагрузку на диск и сеть.",
            startup_recommendation="Рекомендуется отключить из автозапуска и запускать только по необходимости, чтобы не замедлять старт Windows.",
            action_steps=[
                "Отключите автозапуск в таблице для плавного старта Windows.",
                "Запускайте торрент-клиент вручную перед началом закачек.",
            ],
        )

    if "keepass" in name_lower:
        return StartupExplainResponse(
            summary="KeePass Password Safe — защищенный менеджер паролей для безопасного локального хранения учетных записей.",
            developer="Dominik Reichl / KeePass",
            category="Безопасность / Менеджер паролей",
            security_verdict="Высоконадёжное безопасное приложение с открытым кодом и шифрованием базы.",
            boot_impact_analysis="Низкое — быстро загружает базу ключей в защищенную память.",
            startup_recommendation="Оставить включенным для мгновенного доступа к автозаполнению учетных записей.",
            action_steps=[
                "Оставьте в автозагрузке для быстрого входа в аккаунты.",
            ],
        )

    if "logi" in name_lower or "logitech" in name_lower:
        return StartupExplainResponse(
            summary="Logitech Download Assistant / G HUB — служебная утилита управления периферийными устройствами Logitech (мыши, клавиатуры, гарнитуры).",
            developer="Logitech Inc.",
            category="Драйвер / Утилита оборудования",
            security_verdict="Официальное подписанное ПО производителя оборудования.",
            boot_impact_analysis="Низкое/Среднее — опрашивает USB-устройства и проверяет обновления драйверов.",
            startup_recommendation="Оставить включенным при использовании кастомных макросов, RGB-подсветки или DPI-профилей Logitech.",
            action_steps=[
                "Оставьте активным, если используете специфические настройки мыши/клавиатуры Logitech.",
            ],
        )

    if "securityhealth" in name_lower or "defender" in name_lower:
        return StartupExplainResponse(
            summary="Windows Security Health — системный сервис мониторинга безопасности и отображения значка защитника Windows в трее.",
            developer="Microsoft Corporation",
            category="Системный компонент",
            security_verdict="Критически важный доверенный компонент Windows.",
            boot_impact_analysis="Низкое — системный трей-сервис.",
            startup_recommendation="Обязательно оставить включенным для поддержания защиты и уведомлений безопасности системы.",
            action_steps=[
                "Оставить в автозагрузке (системный компонент).",
            ],
        )

    # 4. Общий эвристический анализ для прочих программ
    is_trusted_dir = "program files" in path_lower or "system32" in path_lower
    sec_verdict = (
        "Программа расположена в стандартной системной директории. Явных аномалий не обнаружено."
        if is_trusted_dir
        else "Программа расположена в пользовательском каталоге (AppData/Temp). Рекомендуется убедиться в подлинности источника."
    )
    rec = (
        "Если программа не требуется сразу после включения ПК, её можно безопасно отключить для ускорения старта системы."
        if req.boot_impact in ("Высокое", "Среднее")
        else "Низкое влияние на запуск. Можно оставить включенным или отключить по желанию."
    )

    return StartupExplainResponse(
        summary=f"Элемент автозапуска «{req.name}». Команда запуска: {req.command or req.executable_path}.",
        developer=publisher,
        category="Установленное приложение",
        security_verdict=sec_verdict,
        boot_impact_analysis=f"Влияние на запуск оценено как {req.boot_impact or 'Низкое'}. Занимает ресурсы при старте сессии пользователя.",
        startup_recommendation=rec,
        action_steps=[
            "Оцените регулярность использования программы.",
            "Отключите автозапуск, если программа не нужна постоянно в фоновом режиме.",
        ],
    )



__all__ = ["init_router"]
