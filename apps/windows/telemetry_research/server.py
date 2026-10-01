# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Server
# =============================================================================
# Description:
#   FastAPI сервер и веб-интерфейс для исследования телеметрии с поддержкой AI-чата.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.server import TelemetryChatRequest
#
#     service = TelemetryChatRequest()
#
# File: server.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""FastAPI сервер и веб-интерфейс для исследования телеметрии с поддержкой AI-чата."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .analyzer import TelemetryResearcher
from .assistant import TelemetryAssistant
from .charts import TelemetryChartGenerator
from .extractor import TelemetryDataExtractor
from .models import DeepResearchReport, ResearchScenarioRequest, TelemetryResearchReport
from .query_engine import TelemetryQueryEngine


class TelemetryChatRequest(BaseModel):
    """Схема запроса к AI-ассистенту телеметрии."""

    message: str = Field(..., description="Текст запроса пользователя")
    source_path: Optional[str] = Field(None, description="Путь к файлу базы данных или логов")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="История диалога")


class SqlQueryRequest(BaseModel):
    """Схема запроса для выполнения SELECT SQL."""

    sql: str = Field(..., description="Текст SQL-запроса (SELECT)")
    db_path: Optional[str] = Field(None, description="Опциональный путь к telemetry.db")
    limit: int = Field(500, ge=1, le=1000, description="Максимум возвращаемых строк")


app = FastAPI(
    title="Telemetry Research API & Web GUI",
    description="Веб-интерфейс, API и AI-ассистент для аналитического исследования телеметрии Windows",
    version="1.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_extractor = TelemetryDataExtractor()
_query_engine = TelemetryQueryEngine(extractor=_extractor)
_assistant = TelemetryAssistant(query_engine=_query_engine)
_researcher = TelemetryResearcher(extractor=_extractor)
_chart_gen = TelemetryChartGenerator()
_web_dir = Path(__file__).parent / "web"

if _web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_web_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index() -> HTMLResponse:
    """Отдает главную страницу Web GUI."""
    index_file = _web_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web GUI template not found")
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Проверка доступности сервиса."""
    return {"status": "ok", "service": "telemetry_research"}


@app.post("/api/chat")
@app.post("/apps/telemetry_research/chat")
async def chat_endpoint(request: TelemetryChatRequest) -> Dict[str, Any]:
    """Диалоговый эндпоинт AI-ассистента для аналитики и визуализации телеметрии."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Текст запроса не может быть пустым")

    try:
        response = await _assistant.handle_query(
            user_message=request.message,
            source_path=request.source_path,
            history=request.history,
        )
        return response
    except Exception as ex:
        logger.error(f"Ошибка в AI-чате телеметрии: {ex}", exc_info=True)
        return {
            "status": "error",
            "reply": f"⚠️ Произошла внутренняя ошибка при обработке запроса: {str(ex)}",
            "chart": None,
            "sql_queries": [],
            "metrics_summary": {},
            "quick_followups": ["Покажи график загрузки ЦПУ по времени"],
        }


@app.get("/api/telemetry-sql/power")
@app.get("/apps/telemetry_research/tools/power")
async def get_power_data_endpoint(
    db_path: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
) -> Dict[str, Any]:
    """Возвращает расчет энергопотребления и конфигурацию круговой диаграммы."""
    try:
        return _query_engine.calculate_power_consumption_24h(db_path=db_path, hours=hours)
    except Exception as ex:
        logger.error(f"Ошибка вычисления энергопотребления: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/api/telemetry-sql/cpu-timeline")
@app.get("/apps/telemetry_research/tools/cpu-timeline")
async def get_cpu_timeline_endpoint(
    db_path: Optional[str] = Query(None),
    limit: int = Query(120, ge=10, le=2000),
) -> Dict[str, Any]:
    """Возвращает временной ряд загрузки и частоты процессора для графика."""
    try:
        return _query_engine.get_cpu_timeline(limit=limit, db_path=db_path)
    except Exception as ex:
        logger.error(f"Ошибка вычисления таймлайна CPU: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/api/telemetry-sql/query")
@app.post("/apps/telemetry_research/tools/query")
async def execute_sql_endpoint(request: SqlQueryRequest) -> Dict[str, Any]:
    """Выполняет безопасный SELECT SQL-запрос к базе telemetry.db."""
    try:
        return _query_engine.execute_safe_sql(
            sql_query=request.sql, db_path=request.db_path, limit=request.limit
        )
    except Exception as ex:
        logger.error(f"Ошибка выполнения SQL: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/api/sources")
@app.get("/apps/telemetry_research/sources")
async def get_sources() -> List[Dict[str, Any]]:
    """Возвращает список обнаруженных файлов и баз данных телеметрии."""
    files = _researcher.extractor.discover_log_files()
    result = []
    for f in files:
        try:
            stat = f.stat()
            result.append(
                {
                    "name": f.name,
                    "path": str(f.resolve()),
                    "size_bytes": stat.st_size,
                    "modified_at": stat.st_mtime,
                }
            )
        except Exception:
            continue
    result.sort(key=lambda x: x.get("modified_at", 0), reverse=True)
    return result


@app.get("/api/current-state")
@app.get("/apps/telemetry_research/current-state")
async def get_current_state_endpoint(
    db_path: Optional[str] = Query(None),
    limit: int = Query(100, ge=10, le=2000),
) -> Dict[str, Any]:
    """Возвращает актуальное состояние системы и последние замеры из telemetry.db."""
    try:
        data = _researcher.extractor.get_current_system_state(db_path=db_path, limit=limit)
        return data
    except Exception as ex:
        logger.error(f"Ошибка получения текущего состояния: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/api/run-research", response_model=DeepResearchReport)
@app.post("/apps/telemetry_research/run-research", response_model=DeepResearchReport)
async def run_research_endpoint(request: Optional[ResearchScenarioRequest] = None) -> DeepResearchReport:
    """Запускает глубокое аналитическое исследование телеметрии и проверку гипотез."""
    try:
        report = _researcher.run_deep_research(scenario=request, chart_generator=_chart_gen)
        return report
    except Exception as ex:
        logger.error(f"Ошибка аналитического исследования телеметрии: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/api/records")
@app.get("/apps/telemetry_research/records")
async def get_records_endpoint(
    source_path: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Возвращает пагинированный список сырых записей телеметрии."""
    try:
        all_records = _researcher.extractor.load_all_records(source_path)
        if query:
            q_lower = query.lower()
            all_records = [r for r in all_records if q_lower in json.dumps(r, ensure_ascii=False).lower()]

        total = len(all_records)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = all_records[start_idx:end_idx]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as ex:
        logger.error(f"Ошибка чтения записей: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/api/dashboard", response_class=HTMLResponse)
@app.get("/apps/telemetry_research/dashboard", response_class=HTMLResponse)
async def get_dashboard_html(source_path: Optional[str] = Query(None)) -> HTMLResponse:
    """Генерирует и возвращает автономный HTML-отчет с графиками."""
    try:
        report = _researcher.analyze(source_path)
        records = _researcher.extractor.load_all_records(source_path)
        ts_map = _researcher._extract_time_series(records)
        report.charts = _chart_gen.generate_chart_configs(ts_map, report)
        html = _chart_gen.render_html_dashboard(report)
        return HTMLResponse(content=html)
    except Exception as ex:
        logger.error(f"Ошибка генерации HTML дашборда: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))
