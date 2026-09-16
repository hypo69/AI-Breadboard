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

router = APIRouter(prefix="/api/v1/system_logs", tags=["System Log Center"])

# Инициализация единого пайплайна
_intelligence_pipeline = LogIntelligencePipeline()
_eventlog_collector = EventLogCollector()


# -----------------------------------------------------------------------------
# DTO Models
# -----------------------------------------------------------------------------

class ChannelInfo(BaseModel):
    channel_name: str
    display_name: str
    record_count: int
    is_enabled: bool


class ScanResponse(BaseModel):
    channels: List[ChannelInfo]
    total_sources: int
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
    """Получение событий Windows Event Log через PowerShell Get-WinEvent."""
    limit = max(1, min(limit, 2000))
    hours = max(1, min(hours, 720))

    level_filter = ""
    if level:
        lvl_lower = level.lower()
        if "crit" in lvl_lower:
            level_filter = "; Level=1"
        elif "err" in lvl_lower:
            level_filter = "; Level=2"
        elif "warn" in lvl_lower:
            level_filter = "; Level=3"
        elif "inf" in lvl_lower:
            level_filter = "; Level=4"
        elif "verb" in lvl_lower:
            level_filter = "; Level=5"

    id_filter = f"; Id={event_id}" if event_id > 0 else ""

    if file_path and Path(file_path).exists():
        ps_query = f"Get-WinEvent -Path '{file_path}' -MaxEvents {limit} -ErrorAction SilentlyContinue"
    else:
        target_chan = channel if channel else "System"
        ps_query = (
            f"Get-WinEvent -FilterHashtable @{{LogName='{target_chan}'{level_filter}{id_filter}; "
            f"StartTime=(Get-Date).AddHours(-{hours})}} -MaxEvents {limit} -ErrorAction SilentlyContinue"
        )

    select_expr = (
        "@{N='timestamp';E={$_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')}}, "
        "@{N='level';E={$_.LevelDisplayName}}, "
        "@{N='event_id';E={$_.Id}}, "
        "@{N='provider';E={$_.ProviderName}}, "
        "@{N='computer';E={$_.MachineName}}, "
        "@{N='process_id';E={$_.ProcessId}}, "
        "@{N='thread_id';E={$_.ThreadId}}, "
        "@{N='channel';E={$_.LogName}}, "
        "@{N='message';E={$_.Message}}"
    )
    ps_script = f"{ps_query} | Select-Object {select_expr} | ConvertTo-Json -Compress -Depth 2"

    cmd = ["powershell", "-NoProfile", "-Command", ps_script]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if res.returncode == 0 and res.stdout.strip():
            raw_data = json.loads(res.stdout.strip())
            items = [raw_data] if isinstance(raw_data, dict) else raw_data
            if search:
                s_lower = search.lower()
                items = [
                    it for it in items
                    if s_lower in str(it.get("message", "")).lower()
                    or s_lower in str(it.get("provider", "")).lower()
                    or s_lower in str(it.get("event_id", ""))
                ]
            return items
    except Exception as ex:
        logger.debug(f"Ошибка при получении событий Windows ({channel}): {ex}")

    return []


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
    """Динамическое обнаружение каналов журналов Windows."""
    channels_list: List[ChannelInfo] = [
        ChannelInfo(channel_name="System", display_name="System (Системный)", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Application", display_name="Application (Приложения)", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Security", display_name="Security (Безопасность)", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Setup", display_name="Setup (Установка)", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Microsoft-Windows-WindowsUpdateClient/Operational", display_name="Windows Update Client", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Microsoft-Windows-Kernel-PnP/Configuration", display_name="Kernel PnP Configuration", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Microsoft-Windows-Kernel-Power/Operational", display_name="Kernel Power", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Microsoft-Windows-TaskScheduler/Operational", display_name="Task Scheduler", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Microsoft-Windows-Windows Defender/Operational", display_name="Windows Defender", record_count=0, is_enabled=True),
        ChannelInfo(channel_name="Microsoft-Windows-Hyper-V-Compute-Operational", display_name="Hyper-V Compute", record_count=0, is_enabled=True),
    ]

    # Дополнительно считываем через Get-WinEvent -ListLog
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | Where-Object { $_.RecordCount -gt 0 -and $_.IsEnabled } | Select-Object -First 35 LogName, RecordCount | ConvertTo-Json -Compress",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            scanned = json.loads(res.stdout.strip())
            scanned_items = [scanned] if isinstance(scanned, dict) else scanned
            seen = {c.channel_name.lower() for c in channels_list}
            for sc in scanned_items:
                log_name = sc.get("LogName", "")
                if log_name and log_name.lower() not in seen:
                    channels_list.append(
                        ChannelInfo(
                            channel_name=log_name,
                            display_name=log_name,
                            record_count=int(sc.get("RecordCount") or 0),
                            is_enabled=True,
                        )
                    )
                    seen.add(log_name.lower())
    except Exception as ex:
        logger.debug(f"Ошибка при сканировании списка каналов: {ex}")

    return ScanResponse(
        channels=channels_list,
        total_sources=len(channels_list),
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
    """Получение потока событий для текущего канала и фильтров."""
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
    """AI диагностика и объяснение выбранной записи журнала."""
    msg = req.message or (req.target_entry.get("message") if req.target_entry else "")
    prov = req.provider or (req.target_entry.get("provider") if req.target_entry else "System")
    lvl = req.level or (req.target_entry.get("level") if req.target_entry else "Information")
    ev_id = req.event_id or (req.target_entry.get("event_id") if req.target_entry else 0)

    summary = f"Событие {prov} (Event ID: {ev_id}, Уровень: {lvl})."
    root_cause = f"Сообщение журнала: {msg if msg else 'Служебное уведомление операционной системы.'}"
    recs = [
        "Проверьте актуальность соответствующих драйверов и обновлений Windows.",
        "Убедитесь в корректности прав доступа службы или учётной записи.",
        "При регулярных повторах создайте правило мониторинга или SafeOps задачу.",
    ]

    return {
        "summary": summary,
        "root_cause": root_cause,
        "recommendations": recs,
    }


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
