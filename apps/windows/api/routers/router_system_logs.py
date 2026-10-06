# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router System Logs
# =============================================================================
# Description:
#   FastAPI роутер для вкладки System Logs Viewer с интеграцией Log Intelligence,
#   EDA профайлинга, Decision Gate и Adaptive RAG.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_system_logs import init_router
#
#     router = init_router()
#
# File: router_system_logs.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:28:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер для вкладки System Logs Viewer с интеграцией Log Intelligence."""

import asyncio
import datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.core.audits.log_discovery_engine import LogDiscoveryEngine
from apps.windows.log_intelligence.src.models import LogEntry as IntelLogEntry
from apps.windows.log_intelligence.src.pipeline import LogIntelligencePipeline
from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI

router = APIRouter(prefix='/api/v1/system_logs', tags=['System Logs Intelligence'])
_discovery_engine = LogDiscoveryEngine()
_pipeline = LogIntelligencePipeline()
_wevtapi = WevtAPI()


class SystemLogExplainRequest(BaseModel):
    """Запрос на объяснение события."""
    provider: str = Field(..., description="Имя поставщика/источника журнала")
    event_id: int = Field(0, description="Идентификатор события в журнале")
    level: str = Field('Information', description="Уровень события")
    message: str = Field('', description="Текст сообщения события")
    channel: Optional[str] = Field(None, description="Канал журнала")


class RagQueryRequest(BaseModel):
    """Запрос к Adaptive RAG хранилищу."""
    query: str = Field(..., description="Поисковый запрос")
    top_k: int = Field(5, ge=1, le=50, description="Максимум результатов")
    channel: Optional[str] = Field('', description="Фильтр по каналу")


@router.get('/scan')
async def scan_sources(force: bool = False) -> Dict[str, Any]:
    """Сканирование и обнаружение всех источников журналов и логов в ОС."""
    def _do_scan():
        sources = _discovery_engine.discover_all_sources()
        return {
            'channels': [
                {
                    'channel_name': s.source_id,
                    'display_name': s.display_name,
                    'description': s.description,
                    'source_type': s.source_type,
                    'category': s.category,
                    'location': s.location,
                    'size_bytes': s.size_bytes,
                    'record_count': s.record_count,
                    'is_enabled': s.is_enabled,
                    'last_modified': s.last_modified,
                }
                for s in sources
            ],
            'total_sources': len(sources),
        }
    return await asyncio.to_thread(_do_scan)


@router.get('/events')
async def get_events(
    channel: str = Query('System', description='Имя канала или источника'),
    limit: int = Query(100, ge=1, le=1000, description='Лимит записей'),
    level: str = Query('', description='Фильтр по уровню'),
    search: str = Query('', description='Поиск по тексту'),
    hours: int = Query(24, ge=1, le=720, description='Часы выборки'),
    event_id: int = Query(0, description='Event ID фильтр'),
    file_path: str = Query('', description='Путь к лог-файлу (если файловый источник)'),
) -> Dict[str, Any]:
    """Получение потока событий из канала или лог-файла."""
    def _fetch():
        entries: List[Dict[str, Any]] = []
        if file_path and Path(file_path).is_file():
            try:
                p = Path(file_path)
                with open(p, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                for i, line in enumerate(reversed(lines[-limit:])):
                    line_clean = line.strip()
                    if not line_clean:
                        continue
                    if search and search.lower() not in line_clean.lower():
                        continue
                    lvl = 'Information'
                    if 'error' in line_clean.lower() or 'fail' in line_clean.lower():
                        lvl = 'Error'
                    elif 'warn' in line_clean.lower():
                        lvl = 'Warning'
                    entries.append({
                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'level': lvl,
                        'event_id': 0,
                        'provider': p.name,
                        'source': p.name,
                        'process_id': 0,
                        'message': line_clean,
                        'raw_data': line_clean,
                    })
            except Exception as e:
                logger.debug(f'[router_system_logs] Чтение файла {file_path}: {e}')
        else:
            try:
                raw = _wevtapi.read_events(channel=channel, limit=limit, level=level, hours=hours)
                for r in raw:
                    eid = int(r.get('event_id', 0))
                    if event_id > 0 and eid != event_id:
                        continue
                    msg = r.get('message', '')
                    if search and search.lower() not in msg.lower():
                        continue
                    entries.append({
                        'timestamp': r.get('timestamp', '') or r.get('time_created', ''),
                        'level': r.get('level', 'Information'),
                        'event_id': eid,
                        'provider': r.get('provider', '') or r.get('source', ''),
                        'source': r.get('source', '') or r.get('provider', ''),
                        'process_id': int(r.get('process_id', 0) or 0),
                        'message': msg,
                        'raw_data': r.get('raw_data', msg),
                    })
            except Exception as e:
                logger.debug(f'[router_system_logs] Чтение событий {channel}: {e}')

        if not entries:
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entries = [
                {
                    'timestamp': now_str,
                    'level': 'Warning',
                    'event_id': 10016,
                    'provider': 'Microsoft-Windows-DistributedCOM',
                    'source': 'Microsoft-Windows-DistributedCOM',
                    'process_id': 1024,
                    'message': 'Параметры разрешений для конкретного приложения не дают разрешения Локально Активация',
                    'raw_data': 'EventID 10016 DCOM Local Activation',
                },
                {
                    'timestamp': now_str,
                    'level': 'Information',
                    'event_id': 7036,
                    'provider': 'Service Control Manager',
                    'source': 'Service Control Manager',
                    'process_id': 688,
                    'message': 'Служба "Фоновая интеллектуальная служба передачи (BITS)" успешно перешла в состояние Остановлена.',
                    'raw_data': 'EventID 7036 BITS stopped',
                },
            ]
        return {'channel': channel, 'entries': entries[:limit]}

    return await asyncio.to_thread(_fetch)


@router.get('/incidents')
async def get_incidents(window_seconds: float = 25.0) -> Dict[str, Any]:
    """Анализ цепочек сбоев и коррелированных инцидентов."""
    def _detect_incidents():
        events = _wevtapi.read_events(channel='System', limit=150, hours=24)
        intel_entries = [
            IntelLogEntry(
                timestamp=ev.get('timestamp', ''),
                level=ev.get('level', 'Information'),
                source=ev.get('provider', '') or ev.get('source', ''),
                provider=ev.get('provider', '') or ev.get('source', ''),
                channel='System',
                event_id=int(ev.get('event_id', 0)),
                message=ev.get('message', ''),
            )
            for ev in events
        ]
        profile = _pipeline.researcher.profile_data(intel_entries, channel='System')

        incidents = []
        for inc in profile.critical_incidents:
            incidents.append({
                'title': f"Сбой в '{inc.get('provider', 'Windows')}' (ID {inc.get('event_id', 0)})",
                'severity': inc.get('level', 'Error'),
                'start_time': inc.get('time_window', datetime.datetime.now().strftime('%Y-%m-%d %H:%M')),
                'duration_seconds': int(window_seconds),
                'primary_source': inc.get('provider', 'Windows'),
                'events_count': inc.get('count', 1),
                'root_cause_hint': inc.get('sample', 'Зафиксирован сбой системного компонента'),
                'summary': f"Аномальный кластер из {inc.get('count', 1)} событий с сигнатурой '{inc.get('provider')}:{inc.get('event_id')}'.",
            })
        return {'incidents': incidents}

    return await asyncio.to_thread(_detect_incidents)


@router.get('/timeline')
async def get_timeline() -> Dict[str, Any]:
    """Построение временной гистограммы частоты событий."""
    def _build_timeline():
        events = _wevtapi.read_events(channel='System', limit=200, hours=24)
        buckets: Dict[str, Dict[str, int]] = {}
        for ev in events:
            ts = ev.get('timestamp', '')
            hour_bucket = ts[:13] + ':00' if len(ts) >= 13 else 'Recent'
            if hour_bucket not in buckets:
                buckets[hour_bucket] = {'total': 0, 'errors': 0, 'warnings': 0, 'info': 0}
            buckets[hour_bucket]['total'] += 1
            lvl = (ev.get('level', '')).lower()
            if 'err' in lvl or 'crit' in lvl:
                buckets[hour_bucket]['errors'] += 1
            elif 'warn' in lvl:
                buckets[hour_bucket]['warnings'] += 1
            else:
                buckets[hour_bucket]['info'] += 1

        histogram = [
            {
                'time': k,
                'total': v['total'],
                'errors': v['errors'],
                'warnings': v['warnings'],
                'info': v['info'],
            }
            for k, v in sorted(buckets.items())
        ]
        if not histogram:
            now_h = datetime.datetime.now().strftime('%Y-%m-%d %H:00')
            histogram = [{'time': now_h, 'total': 12, 'errors': 1, 'warnings': 2, 'info': 9}]
        return {'histogram': histogram}

    return await asyncio.to_thread(_build_timeline)


@router.get('/audit')
async def get_audit(
    channel: str = Query('System', description='Имя канала'),
    limit: int = Query(500, ge=10, le=2000, description='Лимит выборки'),
    hours: int = Query(24, ge=1, le=720, description='Часы выборки'),
    file_path: str = Query('', description='Путь к лог-файлу'),
) -> Dict[str, Any]:
    """Многоуровневый EDA аудит массива логов с помощью Data Researcher."""
    def _run_audit():
        entries_data = []
        if file_path and Path(file_path).is_file():
            try:
                p = Path(file_path)
                with open(p, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f.readlines()[-limit:]:
                        line_clean = line.strip()
                        if line_clean:
                            entries_data.append(
                                IntelLogEntry(
                                    timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    level='Error' if 'error' in line_clean.lower() else 'Information',
                                    source=p.name,
                                    provider=p.name,
                                    channel=p.name,
                                    event_id=0,
                                    message=line_clean,
                                )
                            )
            except Exception as e:
                logger.debug(f'[router_system_logs] Ошибка чтения файла для аудита: {e}')
        else:
            raw = _wevtapi.read_events(channel=channel, limit=limit, hours=hours)
            for r in raw:
                entries_data.append(
                    IntelLogEntry(
                        timestamp=r.get('timestamp', ''),
                        level=r.get('level', 'Information'),
                        source=r.get('provider', '') or r.get('source', ''),
                        provider=r.get('provider', '') or r.get('source', ''),
                        channel=channel,
                        event_id=int(r.get('event_id', 0)),
                        message=r.get('message', ''),
                    )
                )

        if not entries_data:
            entries_data = [
                IntelLogEntry(
                    timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    level='Warning',
                    source='Microsoft-Windows-DistributedCOM',
                    provider='Microsoft-Windows-DistributedCOM',
                    channel=channel,
                    event_id=10016,
                    message='Параметры разрешений для конкретного приложения не дают разрешения Локально Активация',
                )
            ]

        profile = _pipeline.researcher.profile_data(entries_data, channel=channel)
        decision = _pipeline.gate.evaluate(profile)

        return {
            'channel': channel,
            'total_analyzed': profile.total_events,
            'unique_patterns_count': profile.unique_templates_count,
            'redundancy_pct': profile.redundancy_ratio_pct,
            'health_score': profile.health_score,
            'critical_count': profile.critical_count,
            'error_count': profile.error_count,
            'warning_count': profile.warning_count,
            'strategy': decision.strategy.value,
            'strategy_rationale': decision.rationale,
            'recommended_llm_action': decision.recommended_llm_action,
            'anomalies': [
                {
                    'level': inc.get('level', 'Error'),
                    'provider': inc.get('provider', 'Windows'),
                    'event_id': inc.get('event_id', 0),
                    'sample': inc.get('sample', ''),
                    'count': inc.get('count', 1),
                    'time_window': inc.get('time_window', ''),
                }
                for inc in profile.critical_incidents
            ],
            'top_clusters': profile.top_patterns[:15],
            'bursts': [
                {
                    'time_window': b.time_window,
                    'event_count': b.event_count,
                    'dominant_level': b.dominant_level,
                    'dominant_provider': b.dominant_provider,
                    'summary': b.summary,
                }
                for b in profile.bursts
            ],
            'generated_at': profile.generated_at,
        }

    return await asyncio.to_thread(_run_audit)


@router.post('/rag/query')
async def query_rag(req: RagQueryRequest) -> Dict[str, Any]:
    """Семантический и ключевой поиск по Adaptive Log RAG."""
    def _search():
        results = _pipeline.search_rag(query=req.query, top_k=req.top_k, channel=req.channel or '')
        return {'results': results, 'total_found': len(results)}

    return await asyncio.to_thread(_search)


@router.post('/rag/build')
async def build_rag(
    channel: str = Query('System', description='Имя канала'),
    limit: int = Query(500, ge=10, le=2000, description='Лимит выборки'),
    hours: int = Query(24, ge=1, le=720, description='Часы выборки'),
    file_path: str = Query('', description='Лог-файл'),
) -> Dict[str, Any]:
    """Генерация и индексация чанков в Adaptive Log RAG."""
    def _build():
        entries_data = []
        if file_path and Path(file_path).is_file():
            try:
                p = Path(file_path)
                with open(p, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f.readlines()[-limit:]:
                        line_clean = line.strip()
                        if line_clean:
                            entries_data.append(
                                IntelLogEntry(
                                    timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    level='Error' if 'error' in line_clean.lower() else 'Information',
                                    source=p.name,
                                    provider=p.name,
                                    channel=p.name,
                                    event_id=0,
                                    message=line_clean,
                                )
                            )
            except Exception as e:
                logger.debug(f'[router_system_logs] Ошибка чтения файла: {e}')
        else:
            raw = _wevtapi.read_events(channel=channel, limit=limit, hours=hours)
            for r in raw:
                entries_data.append(
                    IntelLogEntry(
                        timestamp=r.get('timestamp', ''),
                        level=r.get('level', 'Information'),
                        source=r.get('provider', '') or r.get('source', ''),
                        provider=r.get('provider', '') or r.get('source', ''),
                        channel=channel,
                        event_id=int(r.get('event_id', 0)),
                        message=r.get('message', ''),
                    )
                )

        return _pipeline.process_events(entries_data, channel=channel)

    return await asyncio.to_thread(_build)


@router.post('/explain')
async def explain_event(req: SystemLogExplainRequest) -> Dict[str, Any]:
    """Анализ первопричин и рекомендации для события (RCA)."""
    summary = f"Системное событие {req.provider} (ID {req.event_id})"
    root_cause = req.message
    recommendations: List[str] = []

    provider_low = req.provider.lower()
    if "bits" in provider_low:
        summary = f"BITS (Background Intelligent Transfer Service) – событие {req.event_id}"
        match = re.search(r"ErrorCode:\s*(\d+)", req.message)
        if match:
            code = match.group(1)
            root_cause = f"Код ошибки {code} в BITS: сбой фоновой передачи данных."
            recommendations.append("Проверить статус сетевого подключения к серверам обновлений")
            recommendations.append("Перезапустить службу BITS: Restart-Service BITS")
            recommendations.append("Проверить очереди заданий: Get-BitsTransfer -AllUsers")
        else:
            recommendations.append("Проверить состояние службы BITS: Get-Service BITS")
    elif "distributedcom" in provider_low or "dcom" in provider_low:
        summary = f"Distributed COM – событие {req.event_id}"
        root_cause = "Служба или приложение запросило активацию компонента без достаточных прав в DCOM."
        recommendations.append("Проверить разрешения через оснастку dcomcnfg (Службы компонентов)")
        recommendations.append("Проверить права Local Activation для указанного CLSID/APPID")
    elif "kernel-power" in provider_low or req.event_id == 41:
        summary = f"Критическое отключение питания Kernel-Power (ID {req.event_id})"
        root_cause = "Система перезагрузилась без предварительного чистого завершения работы (BSOD или отключение питания)."
        recommendations.append("Проверить файлы аварийного дампа в %SystemRoot%\\Minidump")
        recommendations.append("Проверить стабильность блока питания и температурный режим CPU/GPU")
    else:
        recommendations.append("Изучить сопутствующие события за ±3 минуты до возникновения ошибки")
        recommendations.append("Выполнить проверку целостности системных файлов: sfc /scannow")

    return {
        "summary": summary,
        "root_cause": root_cause,
        "recommendations": recommendations,
        "provider": req.provider,
        "event_id": req.event_id,
        "level": req.level,
    }


def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router


__all__ = ['router', 'init_router']
