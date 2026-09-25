# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Application FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для приложения исследования телеметрии:
#   запуск комплексных исследовательских сценариев, проверка системных
#   гипотез, матрица корреляций, получение графиков, SVG и HTML дашборда.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для приложения глубокого исследования телеметрии."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response

from apps.common.csv_logger import AppCsvLogger
from apps.telemetry_research.engine import TelemetryResearchEngine
from apps.telemetry_research.models import (
    CorrelationMatrixItem,
    DeepResearchReport,
    HypothesisResult,
    ResearchScenarioRequest,
)
from apps.windows.telemetry.research.models import ChartConfig
from logger import logger


def init_router(
    engine: Optional[TelemetryResearchEngine] = None,
    state: Optional[Any] = None,
) -> APIRouter:
    """Инициализирует и настраивает FastAPI роутер для исследования телеметрии.

    Args:
        engine: Экземпляр аналитического движка TelemetryResearchEngine.
        state: Глобальное состояние приложения AppState (опционально).

    Returns:
        APIRouter: Сконфигурированный роутер приложения.
    """
    router = APIRouter(prefix="/apps/telemetry_research", tags=["telemetry-research"])
    _engine = engine or TelemetryResearchEngine()
    csv_logger = AppCsvLogger("telemetry_research")

    @router.get("/health")
    def health_check() -> Dict[str, str]:
        """Проверка работоспособности сервиса исследования телеметрии."""
        csv_logger.log_poll(
            poll_type="health",
            metric_name="service_health",
            value="ok",
            unit="status",
            status="ok",
            filename="telemetry_research_polls.csv",
        )
        return {"status": "ok", "app": "telemetry_research"}

    @router.post("/run-research", response_model=DeepResearchReport)
    @router.post("/report", response_model=DeepResearchReport)
    def run_deep_research(
        scenario: Optional[ResearchScenarioRequest] = None,
    ) -> DeepResearchReport:
        """Запустить комплексное глубокое исследование логов телеметрии."""
        try:
            report = _engine.run_deep_research(scenario)
            csv_logger.log_event(
                event_type="deep_research_completed",
                status="success",
                details=f"report_id={report.report_id},records={report.base_report.records_analyzed}",
                filename="telemetry_research_events.csv",
            )
            return report
        except Exception as e:
            logger.error(f"Ошибка при проведении исследования телеметрии: {e}", exc_info=True)
            csv_logger.log_event(
                event_type="deep_research_failed",
                status="error",
                details=f"error={str(e)}",
                filename="telemetry_research_events.csv",
            )
            raise HTTPException(status_code=500, detail=f"Ошибка исследования: {str(e)}")

    @router.get("/correlations", response_model=List[CorrelationMatrixItem])
    def get_correlations(
        source_path: Optional[str] = Query(default=None),
    ) -> List[CorrelationMatrixItem]:
        """Получить матрицу корреляций между системными метриками."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _engine.run_deep_research(req)
        return report.correlations

    @router.get("/hypotheses", response_model=List[HypothesisResult])
    def get_hypotheses(
        source_path: Optional[str] = Query(default=None),
    ) -> List[HypothesisResult]:
        """Получить результаты автоматической проверки системных гипотез."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _engine.run_deep_research(req)
        return report.hypotheses

    @router.get("/charts", response_model=List[ChartConfig])
    def get_charts(
        source_path: Optional[str] = Query(default=None),
    ) -> List[ChartConfig]:
        """Получить спецификации интерактивных графиков."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _engine.run_deep_research(req)
        return report.base_report.charts

    @router.get("/dashboard", response_class=Response)
    def get_html_dashboard(
        source_path: Optional[str] = Query(default=None),
    ) -> Response:
        """Получить сгенерированный HTML дашборд с интерактивной визуализацией."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _engine.run_deep_research(req)
        html_content = _engine.chart_generator.render_html_dashboard(report.base_report)
        return Response(content=html_content, media_type="text/html; charset=utf-8")

    @router.get("/svg/{chart_id}", response_class=Response)
    def get_svg_chart(
        chart_id: str,
        source_path: Optional[str] = Query(default=None),
    ) -> Response:
        """Получить конкретный график в векторном формате SVG."""
        req = ResearchScenarioRequest(source_path=source_path)
        report = _engine.run_deep_research(req)
        target = next((c for c in report.base_report.charts if c.id == chart_id), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"График '{chart_id}' не найден.")

        svg_content = _engine.chart_generator.render_svg_chart(target)
        return Response(content=svg_content, media_type="image/svg+xml; charset=utf-8")

    @router.get("/sources")
    def list_sources(
        source_path: Optional[str] = Query(default=None),
    ) -> List[Dict[str, Any]]:
        """Получить список доступных файлов и источников логов телеметрии."""
        files = _engine.extractor.discover_log_files(source_path)
        result = []
        for f in files:
            try:
                st = f.stat()
                result.append({
                    "name": f.name,
                    "path": str(f.resolve()),
                    "size_bytes": st.st_size,
                    "modified": st.st_mtime,
                    "extension": f.suffix.lower(),
                })
            except Exception:
                continue
        return sorted(result, key=lambda x: x["modified"], reverse=True)

    @router.get("/records")
    def get_records(
        source_path: Optional[str] = Query(default=None),
        query: Optional[str] = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        """Получить нормализованные записи телеметрии с поиском и пагинацией."""
        records = _engine.extractor.load_all_records(source_path)
        if query:
            q_lower = query.lower()
            records = [
                r for r in records
                if q_lower in " ".join(f"{k}:{v}" for k, v in r.items()).lower()
            ]

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

    logger.debug("Telemetry Research app router initialized.")
    return router
