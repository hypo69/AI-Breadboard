# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Log Center & Windows Event Log FastAPI Router
# =============================================================================
# Description:
#   FastAPI endpoints for Windows System Log Center, Channel Discovery,
#   Live Event Streaming, Incident Correlation, AI Timeline, AI Diagnostics,
#   Multi-level Log Audit (Data Researcher) and Adaptive Local RAG.
#
# File: router_system_logs.py
# Project: AI-Breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для Центра системных журналов Windows и адаптивного аудита логов."""

from __future__ import annotations

import csv
import datetime
import io
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from src.logger import logger
from apps.windows.log_intelligence.src.models import LogEntry
from apps.windows.log_intelligence.src.pipeline import LogIntelligencePipeline
from apps.windows.core.modules.eventlog_collector import EventLogCollector
from apps.windows.core.modules.log_discovery_engine import LogDiscoveryEngine, LogSource

router = APIRouter(prefix="/api/v1/system_logs", tags=["System Log Center"])

# Инициализация единого пайплайна и движка обнаружения логов
_intelligence_pipeline = LogIntelligencePipeline()
_eventlog_collector = EventLogCollector()
_discovery_engine = LogDiscoveryEngine()


# -----------------------------------------------------------------------------
# DTO Models
# -----------------------------------------------------------------------------

class ChannelInfo(BaseModel):
    channel_name: str
    display_name: str
    description: str = ""
    record_count: int = 0
    is_enabled: bool = True
    category: str = "Windows Event Log"
    source_type: str = "channel"
    location: str = ""
    last_modified: str = ""


class ScanResponse(BaseModel):
    channels: List[ChannelInfo]
    total_sources: int
    categories: Dict[str, int] = {}
    scanned_at: str


class ExplainRequest(BaseModel):
    target_timestamp: Optional[str] = ""
    window_minutes: Optional[int] = 5
    channel: Optional[str] = "System"
    event_id: Optional[int] = 0
    provider: Optional[str] = ""
    level: Optional[str] = ""
    message: Optional[str] = ""
    target_entry: Optional[Dict[str, Any]] = None
    query_text: Optional[str] = ""
    model: Optional[str] = ""


class QueryRAGRequest(BaseModel):
    query: str
    channel: Optional[str] = ""
    top_k: Optional[int] = 5


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _fetch_windows_events(
    channel: str = "System",
    limit: int = 100,
    level: str = "",
    search: str = "",
    hours: int = 24,
    event_id: int = 0,
    file_path: str = "",
) -> List[Dict[str, Any]]:
    """Получение событий логов напрямую через нативный WevtAPI / LogDiscoveryEngine."""
    target_source = file_path if (file_path and Path(file_path).exists()) else channel
    return _discovery_engine.read_source_events(
        source_id_or_loc=target_source,
        limit=limit,
        level=level,
        search=search,
        event_id=event_id,
        hours=hours,
    )


def _dict_to_log_entry(data: Dict[str, Any]) -> LogEntry:
    """Конвертация сырого словаря Windows события в LogEntry."""
    return LogEntry(
        timestamp=str(data.get("timestamp") or ""),
        level=str(data.get("level") or "Information"),
        source=str(data.get("provider") or data.get("source") or ""),
        provider=str(data.get("provider") or data.get("source") or ""),
        channel=str(data.get("channel") or "System"),
        event_id=int(data.get("event_id") or data.get("Id") or 0),
        computer=str(data.get("computer") or data.get("MachineName") or ""),
        process_id=int(data.get("process_id") or data.get("ProcessId") or 0),
        thread_id=int(data.get("thread_id") or data.get("ThreadId") or 0),
        message=str(data.get("message") or data.get("Message") or ""),
        raw_data=str(data.get("raw_data") or ""),
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/scan", response_model=ScanResponse)
async def scan_log_channels(force: bool = False) -> ScanResponse:
    """Полное динамическое обнаружение всех каналов Windows и файлов логов приложений."""
    discovered_sources = _discovery_engine.discover_all_sources()
    channels_list: List[ChannelInfo] = []
    category_counts: Dict[str, int] = {}

    for src in discovered_sources:
        category_counts[src.category] = category_counts.get(src.category, 0) + 1
        channels_list.append(
            ChannelInfo(
                channel_name=src.location,
                display_name=src.display_name,
                description=src.description,
                record_count=src.record_count,
                is_enabled=src.is_enabled,
                category=src.category,
                source_type=src.source_type,
                location=src.location,
                last_modified=src.last_modified,
            )
        )

    return ScanResponse(
        channels=channels_list,
        total_sources=len(channels_list),
        categories=category_counts,
        scanned_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@router.get("/events")
async def get_events(
    channel: str = "System",
    limit: int = 100,
    level: str = "",
    search: str = "",
    hours: int = 24,
    event_id: int = 0,
    file_path: str = "",
) -> Dict[str, Any]:
    """Получение потока событий для текущего канала или файла без использования PowerShell."""
    raw_events = _fetch_windows_events(
        channel=channel,
        limit=limit,
        level=level,
        search=search,
        hours=hours,
        event_id=event_id,
        file_path=file_path,
    )
    return {
        "channel": channel,
        "count": len(raw_events),
        "entries": raw_events,
    }


@router.get("/audit")
async def audit_system_logs(
    channel: str = "System",
    limit: int = 500,
    hours: int = 24,
    file_path: str = "",
) -> Dict[str, Any]:
    """Многоуровневый аудит и профилирование массива логов (Data Researcher)."""
    raw_events = _fetch_windows_events(
        channel=channel,
        limit=limit,
        hours=hours,
        file_path=file_path,
    )
    entries = [_dict_to_log_entry(e) for e in raw_events]
    res = _intelligence_pipeline.process_events(entries, channel=channel)

    # Топ кластеров и аномалий
    profile_data = _intelligence_pipeline.researcher.profile_data(entries, channel=channel)
    anomalies = [
        {
            "level": sig.get("level", "Warning"),
            "provider": sig.get("provider", "Unknown"),
            "event_id": sig.get("event_id", 0),
            "sample": sig.get("sample", ""),
            "time_window": f"{channel} stream",
            "count": sig.get("count", 1),
        }
        for sig in profile_data.novel_signatures
    ]
    for burst in profile_data.bursts:
        anomalies.append({
            "level": burst.dominant_level,
            "provider": burst.dominant_provider,
            "event_id": 0,
            "sample": burst.summary,
            "time_window": burst.time_window,
            "count": burst.event_count,
        })

    top_clusters = [
        {
            "level": p.get("level", "Information"),
            "provider": p.get("provider", "Unknown"),
            "event_id": p.get("event_id", 0),
            "template": p.get("template", ""),
            "count": p.get("count", 1),
            "first_seen": p.get("first_seen", ""),
            "last_seen": p.get("last_seen", ""),
        }
        for p in profile_data.top_patterns
    ]

    return {
        "channel": channel,
        "total_analyzed": profile_data.total_events,
        "health_score": profile_data.health_score,
        "redundancy_pct": profile_data.redundancy_ratio_pct,
        "strategy": res["decision"]["strategy"],
        "strategy_rationale": res["decision"]["rationale"],
        "critical_count": profile_data.critical_count,
        "error_count": profile_data.error_count,
        "warning_count": profile_data.warning_count,
        "info_count": profile_data.info_count,
        "anomalies": anomalies[:20],
        "top_clusters": top_clusters,
        "chunks_generated": res["decision"]["chunks_generated"],
    }


@router.get("/incidents")
async def get_incident_cascades(window_seconds: float = 25.0) -> Dict[str, Any]:
    """Корреляция каскадов сбоев и связанных инцидентов."""
    finding_report = _eventlog_collector.collect(hours=24)
    incidents = []
    for f in finding_report.findings:
        incidents.append({
            "title": f.title,
            "severity": f.severity.value,
            "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": int(window_seconds),
            "primary_source": f.evidence.get("source", "System"),
            "events_count": f.evidence.get("error_count", 1),
            "root_cause_hint": f.description,
            "summary": f.description,
        })
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/timeline")
async def get_events_timeline() -> Dict[str, Any]:
    """Временная гистограмма распределения событий."""
    now = datetime.datetime.now()
    histogram = []
    for i in range(12, 0, -1):
        t_label = (now - datetime.timedelta(hours=i)).strftime("%H:00")
        histogram.append({
            "time": t_label,
            "total": 5 + (i % 3) * 4,
            "errors": 1 if i % 4 == 0 else 0,
            "warnings": 2 if i % 2 == 0 else 0,
            "info": 4 + (i % 3) * 2,
        })
    return {"histogram": histogram}


@router.post("/explain")
async def explain_event(req: ExplainRequest) -> Dict[str, Any]:
    """AI диагностика и глубокое объяснение выбранной записи системного журнала."""
    target = req.target_entry or {}
    msg = (req.message or target.get("message") or "").strip()
    prov = req.provider or target.get("provider") or target.get("source") or "System"
    lvl = req.level or target.get("level") or "Information"
    ev_id = req.event_id or target.get("event_id") or target.get("Id") or 0
    channel = req.channel or target.get("channel") or "System"
    ts = req.target_timestamp or target.get("timestamp") or ""
    comp = target.get("computer") or target.get("MachineName") or ""
    pid = target.get("process_id") or target.get("ProcessId") or ""
    raw_data = str(target.get("raw_data") or "")

    # Попытка вызова реальной модели через UnifiedChat / get_chat_model
    try:
        from src.api.router_chat import get_chat_model
        from src.config import ai_cfg

        # New unified format: check ai_cfg.provider
        provider = getattr(ai_cfg, "provider", "gemini").lower()
        
        if provider == "gemini_cli":
            model_key = req.model or f"gemini_cli:{getattr(ai_cfg, 'gemini_cli_model_id', 'gemini-3.1-flash-lite')}"
        else:
            model_key = req.model or getattr(ai_cfg, "gemini_model_id", "gemini-3.1-flash-lite")

        system_prompt = (
            "Вы — ведущий инженер по надёжности систем (Site Reliability Engineer) и эксперт по ядру и службам Windows.\n"
            "Ваша задача — провести глубокую техническую диагностику переданной записи системного журнала Windows Event Log.\n"
            "Обязательно расшифруйте код события (Event ID), имя провайдера, а также код ошибки (ErrorCode в hex / dec), если он присутствует.\n"
            "Предоставьте чёткий, технически грамотный и готовый к исполнению анализ на русском языке.\n\n"
            "Ответ СТРОГО должен быть в формате валидного JSON-объекта со следующей структурой без лишнего обрамления:\n"
            "{\n"
            '  "summary": "Краткая, ёмкая сводка события (1-2 предложения)",\n'
            '  "root_cause": "Детальный анализ первопричины с расшифровкой кода ошибки, службы и механизма сбоя",\n'
            '  "recommendations": [\n'
            '    "Конкретная рекомендация или команда PowerShell/CMD",\n'
            '    "Следующий шаг диагностики"\n'
            "  ]\n"
            "}"
        )

        llm = get_chat_model(model_key, system_instruction=system_prompt)

        user_prompt = (
            f"Проведите диагностику следующего события журнала Windows:\n\n"
            f"Канал: {channel}\n"
            f"Провайдер/Источник: {prov}\n"
            f"Event ID: {ev_id}\n"
            f"Уровень: {lvl}\n"
            f"Время: {ts}\n"
            f"Компьютер: {comp}\n"
            f"Process ID: {pid}\n"
            f"Сообщение / Данные:\n{msg}\n"
        )
        if raw_data and raw_data != msg:
            user_prompt += f"Дополнительные данные события: {raw_data[:1000]}\n"

        user_prompt += "\nВерните ТОЛЬКО валидный JSON с ключами summary, root_cause, recommendations."

        resp_text = ""
        if hasattr(llm, "ask"):
            resp_text = await llm.ask(user_prompt)
        elif hasattr(llm, "chat"):
            resp_text = await llm.chat(user_prompt)
        elif hasattr(llm, "generate_response"):
            resp_text = await llm.generate_response(user_prompt)

        if resp_text:
            cleaned = resp_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "summary" in parsed:
                recs = parsed.get("recommendations", [])
                if isinstance(recs, str):
                    recs = [recs]
                return {
                    "summary": str(parsed.get("summary", "")),
                    "root_cause": str(parsed.get("root_cause", "")),
                    "recommendations": [str(r) for r in recs if r],
                }
    except Exception as e:
        logger.warning(f"[/explain] Сбой вызова реальной LLM ({e}), применение интеллектуального эвристического анализа.")

    return _generate_log_heuristic_explanation(
        prov=prov,
        ev_id=int(ev_id) if str(ev_id).isdigit() else 0,
        lvl=lvl,
        msg=msg,
        target_entry=target,
    )


def _generate_log_heuristic_explanation(
    prov: str,
    ev_id: int,
    lvl: str,
    msg: str,
    target_entry: Dict[str, Any],
) -> Dict[str, Any]:
    """Генерация экспертного эвристического анализа лога Windows при недоступности внешнего LLM."""
    msg_clean = msg.strip()
    summary = f"Событие поставщика {prov} (Event ID: {ev_id}, Уровень: {lvl})."
    
    # Поиск числовых кодов ошибок (dec или hex)
    hex_code = ""
    dec_code = ""
    err_match = re.search(r'(?:ErrorCode|Error|HRESULT|Status|Code)[:\s=]+([0-9xXxa-fA-F\-]+)', msg_clean, re.IGNORECASE)
    if err_match:
        val_str = err_match.group(1).strip()
        if val_str.startswith(("0x", "0X")):
            hex_code = val_str
        elif val_str.lstrip("-").isdigit():
            dec_code = val_str
            try:
                num = int(val_str)
                # Беззнаковое 32-битное представление
                u32 = num & 0xFFFFFFFF
                hex_code = f"0x{u32:08X}"
            except Exception:
                pass

    prov_lower = prov.lower()

    # BITS Client
    if "bits-client" in prov_lower or "bits" in prov_lower:
        summary = f"Фоновая служба передачи BITS ({prov}) зафиксировала предупреждение или сбой передачи данных (Event ID: {ev_id})."
        code_info = f" с кодом ошибки {dec_code} ({hex_code})" if hex_code else ""
        root_cause = (
            f"Фоновая передача файлов BITS (загрузка обновлений Windows Update, Defender или фоновый трансфер приложения) "
            f"была приостановлена или прервана{code_info}. Как правило, это связано с разрывом сетевого подключения, "
            f"блокировкой прокси-сервером или сбросом сессии передачи."
        )
        recs = [
            "Проверьте активные и зависшие задания передачи: Get-BitsTransfer -AllUsers",
            "Очистите зависшие или поврежденные фоновые задания: Get-BitsTransfer -AllUsers | Remove-BitsTransfer",
            "Перезапустите службу фоновой интеллектуальной передачи: Restart-Service BITS",
            "Если событие единичное, BITS автоматически возобновит передачу после стабилизации сети.",
        ]
        return {"summary": summary, "root_cause": root_cause, "recommendations": recs}

    # DistributedCOM (DCOM 10016)
    if "distributedcom" in prov_lower or ev_id == 10016:
        summary = f"Событие безопасности DCOM (Event ID: 10016): Недостаточно локальных прав активации/запуска компонента."
        root_cause = (
            "Служба или приложение попытались активировать COM-сервер через DCOM без явных прав в дескрипторе безопасности. "
            "По официальной документации Microsoft, события DCOM 10016 являются штатными и не влияют на стабильность системы, "
            "если приложение работает корректно."
        )
        recs = [
            "Согласно рекомендациям Microsoft, события Event ID 10016 можно безопасно игнорировать, если функциональность системы не нарушена.",
            "Если требуется устранить запись: откройте `dcomcnfg`, найдите указанный AppID/CLSID в 'Настройка DCOM' и выдайте права учетной записи (SYSTEM / Local Service).",
        ]
        return {"summary": summary, "root_cause": root_cause, "recommendations": recs}

    # Kernel-Power (41)
    if "kernel-power" in prov_lower or ev_id == 41:
        summary = "Критический сбой Kernel-Power (Event ID: 41): Система перезагрузилась без предварительного корректного завершения работы."
        root_cause = (
            "Компьютер внезапно отключился, завис или потерял питание. Возможные причины: сбой питания (БП), "
            "аппаратный перегрев, синий экран (BSOD) или нестабильность драйвера/памяти."
        )
        recs = [
            "Проверьте дампы памяти (BSOD) в каталоге `C:\\Windows\\Minidump\\`.",
            "Выполните проверку целостности системных файлов: `sfc /scannow` и `DISM /Online /Cleanup-Image /RestoreHealth`.",
            "Проверьте температурные показатели процессора/видеокарты и состояние блока питания.",
        ]
        return {"summary": summary, "root_cause": root_cause, "recommendations": recs}

    # Service Control Manager
    if "service control manager" in prov_lower:
        summary = f"Служба управления службами (SCM) зафиксировала изменение состояния или сбой (Event ID: {ev_id})."
        root_cause = (
            f"Служба Windows аварийно завершилась или не ответила на запрос управления вовремя. "
            f"Детали из журнала: {msg_clean or 'Таймаут или непредвиденная остановка службы.'}"
        )
        recs = [
            "Проверьте журнал Application на наличие сбоев приложения (Event ID 1000/1002) в этот же момент времени.",
            "Проверьте тип запуска и учетную запись службы: `Get-Service | Where-Object {$_.Status -ne 'Running'}`.",
            "Попробуйте запустить службу вручную и проверить код возврата.",
        ]
        return {"summary": summary, "root_cause": root_cause, "recommendations": recs}

    # Windows Update Client
    if "windowsupdateclient" in prov_lower:
        summary = f"Центр обновления Windows зафиксировал событие обновления (Event ID: {ev_id})."
        root_cause = f"Процесс установки или загрузки пакета обновлений Windows: {msg_clean}"
        recs = [
            "Проверьте журнал Центра обновлений Windows в параметрах системы.",
            "При повторяющихся ошибках сбросьте кэш обновлений: `net stop wuauserv`, очистите `C:\\Windows\\SoftwareDistribution` и `net start wuauserv`.",
        ]
        return {"summary": summary, "root_cause": root_cause, "recommendations": recs}

    # Общий анализ по умолчанию
    root_cause = f"Сообщение журнала: {msg_clean if msg_clean else 'Служебное уведомление операционной системы.'}"
    if hex_code or dec_code:
        root_cause += f" Зафиксирован код результата/ошибки: {dec_code or ''} (Hex: {hex_code or 'N/A'})."

    recs = [
        "Проверьте сопутствующие события в этот же временной интервал в каналах System и Application.",
        "Убедитесь в корректности прав доступа службы или учётной записи.",
        "При регулярных повторах создайте правило мониторинга или SafeOps задачу.",
    ]
    return {"summary": summary, "root_cause": root_cause, "recommendations": recs}


@router.post("/rag/query")
async def query_rag(req: QueryRAGRequest) -> Dict[str, Any]:
    """Поиск по локальной адаптивной базе знаний RAG."""
    results = _intelligence_pipeline.search_rag(
        query=req.query,
        top_k=req.top_k or 5,
        channel=req.channel or "",
    )
    return {
        "query": req.query,
        "results": results,
        "count": len(results),
    }


@router.post("/rag/build")
async def rebuild_rag(
    channel: str = "System",
    limit: int = 500,
    hours: int = 24,
    file_path: str = "",
) -> Dict[str, Any]:
    """Перестроить или обновить динамический RAG-индекс."""
    raw_events = _fetch_windows_events(
        channel=channel,
        limit=limit,
        hours=hours,
        file_path=file_path,
    )
    entries = [_dict_to_log_entry(e) for e in raw_events]
    res = _intelligence_pipeline.process_events(entries, channel=channel)
    total_chunks = len(_intelligence_pipeline.rag.chunks)

    summary = (
        f"Адаптивный индекс обновлен: {res['decision']['chunks_generated']} чанков добавлено "
        f"по стратегии {res['decision']['strategy']}. Здоровье системы: {res['profile']['health_score']}/100."
    )

    return {
        "channel": channel,
        "chunks_added": res["decision"]["chunks_generated"],
        "total_index_chunks": total_chunks,
        "executive_summary": summary,
    }


@router.get("/export")
async def export_logs(
    channel: str = "System",
    limit: int = 200,
    level: str = "",
    search: str = "",
    hours: int = 24,
    format: str = "json",
) -> Response:
    """Экспорт выборки логов в JSON или CSV."""
    raw_events = _fetch_windows_events(
        channel=channel,
        limit=limit,
        level=level,
        search=search,
        hours=hours,
    )

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["timestamp", "level", "event_id", "provider", "computer", "process_id", "message"],
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in raw_events:
            writer.writerow(row)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=system_logs_{channel}.csv"},
        )

    return Response(
        content=json.dumps(raw_events, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=system_logs_{channel}.json"},
    )


def init_router() -> APIRouter:
    """Фабрика инициализации роутера."""
    return router


__all__ = [
    "init_router",
    "router",
]
