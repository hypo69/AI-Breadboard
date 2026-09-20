# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Software Transparency Scanner FastAPI Router
# =============================================================================
# Description:
#   REST API эндпоинты для сканирования ПО, инспекции конфигураций,
#   проверки хранилищ данных, сетевых доменов и AI-исследования через Gemini.
#
# File: router.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для AI Software Transparency Scanner."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.logger import logger
from apps.software_transparency_scanner.core.config_inspector import ConfigInspector
from apps.software_transparency_scanner.core.gemini_researcher import GeminiResearcher
from apps.software_transparency_scanner.core.inventory import SoftwareInventory
from apps.software_transparency_scanner.core.models import (
    ConfigFile,
    FullScanReport,
    GeminiAppResearch,
    NetworkEndpoint,
    ResearchRequest,
    ScanSummary,
    SoftwareItem,
    StorageDirectory,
)
from apps.software_transparency_scanner.core.network_tracker import NetworkTracker
from apps.software_transparency_scanner.core.storage_analyzer import StorageAnalyzer
from apps.common.csv_logger import AppCsvLogger


def init_router(chat_provider: Optional[Any] = None) -> APIRouter:
    """Инициализация FastAPI роутера сканера прозрачности ПО."""
    router = APIRouter(prefix="/api/v1/software-scanner", tags=["AI Software Transparency Scanner"])
    csv_logger = AppCsvLogger("software_transparency_scanner")

    inventory = SoftwareInventory()
    storage_analyzer = StorageAnalyzer()
    config_inspector = ConfigInspector()
    network_tracker = NetworkTracker()
    researcher = GeminiResearcher(chat_provider=chat_provider)

    # Кэш последнего сканирования
    _cache: Dict[str, SoftwareItem] = {}
    _last_summary: Optional[ScanSummary] = None

    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        """Возвращает статус доступности сканера прозрачности."""
        csv_logger.log_poll(
            poll_type="status",
            metric_name="cached_apps_count",
            value=len(_cache),
            unit="count",
            status="online",
            details="service_status_check",
            filename="software_transparency_polls.csv",
        )
        return {
            "status": "online",
            "service": "AI Software Transparency Scanner",
            "version": "1.0.0",
            "cached_apps_count": len(_cache),
        }

    @router.get("/scan", response_model=FullScanReport)
    async def run_full_scan(force_refresh: bool = Query(False, description="Принудительно пересканировать")) -> FullScanReport:
        """Выполняет инвентаризацию установленного ПО и аудит конфигураций/хранилищ/сети."""
        nonlocal _cache, _last_summary
        start_time = time.time()

        if not _cache or force_refresh:
            apps = inventory.scan_installed_software()
            _cache = {}

            total_configs = 0
            total_domains = 0
            total_bytes = 0

            for app in apps:
                # 1. Поиск хранилищ
                dirs = storage_analyzer.discover_storage_for_app(app)
                app.data_directories = dirs
                for d in dirs:
                    total_bytes += d.total_size_bytes

                # 2. Поиск конфигов
                cfgs = config_inspector.inspect_directories_for_configs(dirs)
                app.config_files = cfgs
                total_configs += len(cfgs)

                # 3. Сетевые точки
                nets = network_tracker.track_app_network(app, cfgs)
                app.network_endpoints = nets
                total_domains += len(nets)

                _cache[app.id] = app

            dur = round(time.time() - start_time, 2)
            _last_summary = ScanSummary(
                total_apps=len(_cache),
                total_configs_found=total_configs,
                total_network_domains=total_domains,
                total_storage_bytes=total_bytes,
                scan_duration_sec=dur,
                last_scan_time=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )
            csv_logger.log_event(
                event_type="full_scan_completed",
                status="success",
                details=f"apps={len(_cache)},configs={total_configs},domains={total_domains},storage_mb={round(total_bytes/(1024*1024),2)},duration_s={dur}",
                filename="software_transparency_scans.csv",
            )

        return FullScanReport(
            summary=_last_summary or ScanSummary(total_apps=len(_cache)),
            apps=list(_cache.values()),
        )

    @router.get("/apps", response_model=List[SoftwareItem])
    async def get_apps() -> List[SoftwareItem]:
        """Возвращает список всех найденных программ."""
        if not _cache:
            await run_full_scan()
        return list(_cache.values())

    @router.get("/apps/{app_id}", response_model=SoftwareItem)
    async def get_app_details(app_id: str) -> SoftwareItem:
        """Возвращает подробные сведения об одной программе."""
        if not _cache:
            await run_full_scan()

        if app_id in _cache:
            return _cache[app_id]

        # Поиск по подстроке ID или имени
        for k, v in _cache.items():
            if app_id.lower() in k.lower() or app_id.lower() in v.name.lower():
                return v

        raise HTTPException(status_code=404, detail=f"Программа с ID '{app_id}' не найдена")

    @router.post("/research", response_model=GeminiAppResearch)
    async def research_app(req: ResearchRequest) -> GeminiAppResearch:
        """Запускает исследование программы через Gemini."""
        if not _cache:
            await run_full_scan()

        target_app = _cache.get(req.app_id)
        if not target_app:
            for k, v in _cache.items():
                if req.app_id.lower() in k.lower() or req.app_id.lower() in v.name.lower():
                    target_app = v
                    break

        if not target_app:
            csv_logger.log_event(
                event_type="app_research_failed",
                status="not_found",
                details=f"app_id={req.app_id}",
                filename="software_transparency_scans.csv",
            )
            raise HTTPException(status_code=404, detail=f"Программа '{req.app_id}' не найдена для исследования")

        if target_app.ai_research and not req.force_refresh:
            return target_app.ai_research

        research_res = await researcher.research_software(target_app)
        target_app.ai_research = research_res
        csv_logger.log_event(
            event_type="app_research_completed",
            status="success",
            details=f"app_id={req.app_id},app_name={target_app.name},risk={getattr(research_res, 'risk_score', 'N/A')}",
            filename="software_transparency_scans.csv",
        )
        return research_res

    return router
