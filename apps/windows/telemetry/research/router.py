# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Telemetry Research FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для запуска исследования логов телеметрии,
#   получения спецификаций графиков, SVG-диаграмм и интерактивного HTML-дашборда.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows.telemetry.research.router import init_research_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_research_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для модуля исследования логов телеметрии."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from apps.windows.telemetry.research.analyzer import TelemetryResearcher
from apps.windows.telemetry.research.charts import TelemetryChartGenerator
from apps.windows.telemetry.research.models import (
    ChartConfig,
    CorrelationMatrixItem,
    DeepResearchReport,
    HypothesisResult,
    ResearchScenarioRequest,
    TelemetryResearchReport,
)


class AnalyzeRequest(BaseModel):
    """Модель запроса запуска исследования."""

    source_path: Optional[str] = Field(default=None, description="Путь к файлу или папке логов")
    records: Optional[List[Dict[str, Any]]] = Field(default=None, description="Опциональный массив записей в памяти")


def init_research_router(
    researcher: Optional[TelemetryResearcher] = None,
    chart_generator: Optional[TelemetryChartGenerator] = None,
) -> APIRouter:
    """Инициализация роутера исследования телеметрии с внедрением зависимостей."""
    router = APIRouter(prefix="/api/windows/telemetry/research", tags=["telemetry-research"])
    _researcher = researcher or TelemetryResearcher()
    _chart_gen = chart_generator or TelemetryChartGenerator()

    @router.get("/health")
    def health_check() -> Dict[str, str]:
        """Проверка работоспособности сервиса исследования телеметрии."""
        return {"status": "ok", "app": "telemetry_research"}

    @router.post("/report", response_model=TelemetryResearchReport)
    def run_research(request: Optional[AnalyzeRequest] = None) -> TelemetryResearchReport:
        """Запустить комплексное исследование логов телеметрии и получить отчет с графиками."""
        source = None
        if request:
            source = request.records if request.records is not None else request.source_path

        report = _researcher.analyze(source)
        records = _researcher.extractor.load_all_records(source)
        ts_map = _researcher._extract_time_series(records)
        report.charts = _chart_gen.generate_chart_configs(ts_map, report)
        return report

    @router.post("/run-research", response_model=DeepResearchReport)
    def run_deep_research(
        scenario: Optional[ResearchScenarioRequest] = None,
    ) -> DeepResearchReport:
        """Запустить комплексное глубокое исследование логов телеметрии (с корреляциями и гипотезами)."""
        try:
            return _researcher.run_deep_research(scenario=scenario, chart_generator=_chart_gen)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка исследования: {str(e)}")

    @router.get("/correlations", response_model=List[CorrelationMatrixItem])
    def get_correlations(
        source_path: Optional[str] = Query(default=None),
    ) -> List[CorrelationMatrixItem]:
        """Получить матрицу корреляций между системными метриками."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _researcher.run_deep_research(scenario=req, chart_generator=_chart_gen)
        return report.correlations

    @router.get("/hypotheses", response_model=List[HypothesisResult])
    def get_hypotheses(
        source_path: Optional[str] = Query(default=None),
    ) -> List[HypothesisResult]:
        """Получить результаты автоматической проверки системных гипотез."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _researcher.run_deep_research(scenario=req, chart_generator=_chart_gen)
        return report.hypotheses

    @router.get("/dashboard", response_class=Response)
    def get_html_dashboard(source_path: Optional[str] = Query(default=None)) -> Response:
        """Сгенерировать и вернуть интерактивный HTML-дашборд с графиками."""
        report = _researcher.analyze(source_path)
        records = _researcher.extractor.load_all_records(source_path)
        ts_map = _researcher._extract_time_series(records)
        report.charts = _chart_gen.generate_chart_configs(ts_map, report)

        html_content = _chart_gen.render_html_dashboard(report)
        return Response(content=html_content, media_type="text/html; charset=utf-8")

    @router.get("/charts", response_model=List[ChartConfig])
    def get_charts(source_path: Optional[str] = Query(default=None)) -> List[ChartConfig]:
        """Получить список спецификаций графиков в формате JSON."""
        report = _researcher.analyze(source_path)
        records = _researcher.extractor.load_all_records(source_path)
        ts_map = _researcher._extract_time_series(records)
        return _chart_gen.generate_chart_configs(ts_map, report)

    @router.get("/svg/{chart_id}", response_class=Response)
    def get_svg_chart(chart_id: str, source_path: Optional[str] = Query(default=None)) -> Response:
        """Получить конкретный график в виде векторного SVG изображения."""
        report = _researcher.analyze(source_path)
        records = _researcher.extractor.load_all_records(source_path)
        ts_map = _researcher._extract_time_series(records)
        charts = _chart_gen.generate_chart_configs(ts_map, report)

        target = next((c for c in charts if c.id == chart_id), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"График с id '{chart_id}' не найден.")

        svg_content = _chart_gen.render_svg_chart(target)
        return Response(content=svg_content, media_type="image/svg+xml; charset=utf-8")

    @router.get("/files")
    @router.get("/sources")
    def list_log_files(source_path: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
        """Получить список обнаруженных файлов логов с метаданными."""
        files = _researcher.extractor.discover_log_files(source_path)
        result = []
        for f in files:
            try:
                stat = f.stat()
                result.append({
                    "name": f.name,
                    "path": str(f.resolve()),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": f.suffix.lower(),
                })
            except Exception:
                continue
        return sorted(result, key=lambda x: x["modified"], reverse=True)

    @router.get("/records")
    def get_log_records(
        source_path: Optional[str] = Query(default=None),
        query: Optional[str] = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        """Получить нормализованные записи логов с пагинацией и поисковым фильтром."""
        records = _researcher.extractor.load_all_records(source_path)
        
        if query:
            q_lower = query.lower()
            filtered = []
            for r in records:
                txt = " ".join(f"{k}:{v}" for k, v in r.items()).lower()
                if q_lower in txt:
                    filtered.append(r)
            records = filtered

        total = len(records)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = records[start_idx:end_idx]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
            "items": items,
        }

    return router

