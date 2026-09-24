# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender FastAPI Router
# =============================================================================
# Description:
#   REST API эндпоинты для мониторинга Microsoft Defender Antivirus,
#   управления антивирусным сканированием, аудита правил ASR, Controlled Folder Access,
#   проверки исключений, истории угроз, журнала событий и AI-диагностики безопасности.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows.defender.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.defender
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI REST API роутер для Microsoft Defender & Security Center."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from logger import logger
from apps.windows.defender.core.ai_diagnostician import AIDiagnostician
from apps.windows.defender.core.asr_manager import ASRManager
from apps.windows.defender.core.cfa_manager import ControlledFolderAccessManager
from apps.windows.defender.core.defender_service import DefenderService
from apps.windows.defender.core.event_correlator import EventCorrelator
from apps.windows.defender.core.exclusions_auditor import ExclusionsAuditor
from apps.windows.defender.core.models import (
    ASRRuleInfo,
    ControlledFolderAccessInfo,
    DefenderDiagnosticReport,
    DefenderEventRecord,
    DefenderStatus,
    ExclusionsAuditReport,
    ScanRequest,
    ScanResponse,
    ScanType,
    SuspiciousProcessChain,
    ThreatRecord,
)
from apps.windows.defender.core.process_tree_watcher import ProcessTreeWatcher
from apps.windows.defender.core.threat_manager import ThreatManager
from apps.common.csv_logger import AppCsvLogger

_csv_logger = AppCsvLogger("windows_defender")


def init_router() -> APIRouter:
    """Инициализация и сборка маршрутов FastAPI роутера Defender.

    Returns:
        APIRouter: Сконфигурированный роутер приложения.
    """
    router = APIRouter(prefix="/api/v1/defender", tags=["Windows Defender Security"])


    defender_svc = DefenderService()
    asr_mgr = ASRManager(defender_svc)
    cfa_mgr = ControlledFolderAccessManager(defender_svc)
    exclusions_aud = ExclusionsAuditor(defender_svc)
    threat_mgr = ThreatManager(defender_svc)
    event_corr = EventCorrelator()
    process_watch = ProcessTreeWatcher()
    ai_diag = AIDiagnostician(
        defender_service=defender_svc,
        asr_manager=asr_mgr,
        cfa_manager=cfa_mgr,
        exclusions_auditor=exclusions_aud,
        threat_manager=threat_mgr,
        event_correlator=event_corr,
        process_watcher=process_watch,
    )

    @router.get("/status", response_model=DefenderStatus, summary="Получить статус Microsoft Defender")
    async def get_status() -> DefenderStatus:
        """Возвращает комплексное состояние защиты Microsoft Defender, версии баз и связанных процессов."""
        try:
            st = defender_svc.get_defender_status()
            _csv_logger.log_poll(
                poll_type="defender_status",
                metric_name="realtime_protection",
                value=st.real_time_protection_enabled,
                unit="bool",
                status="OK" if st.real_time_protection_enabled else "ATTENTION",
                details={"antivirus_enabled": st.antivirus_enabled, "engine_ver": st.engine_version},
                filename="windows_defender_status_polls.csv",
            )
            return st
        except Exception as e:
            logger.error(f"Ошибка получения статуса Defender: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось получить статус Defender: {e}",
            )

    @router.post("/scan", response_model=ScanResponse, summary="Запустить сканирование Defender")
    async def run_scan(req: ScanRequest) -> ScanResponse:
        """Запускает быстрое, полное или выборочное сканирование файловой системы через MpCmdRun / PowerShell."""
        try:
            res = defender_svc.trigger_scan(req)
            _csv_logger.log_event(
                event_type="scan_triggered",
                status="SUCCESS" if res.success else "FAILED",
                details={"scan_type": req.scan_type.value, "path": req.custom_path, "msg": res.message},
                filename="windows_defender_scan_events.csv",
            )
            return res
        except Exception as e:
            logger.error(f"Ошибка запуска сканирования: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка сканирования: {e}",
            )

    @router.post("/update-signatures", response_model=ScanResponse, summary="Обновить антивирусные базы")
    async def update_signatures() -> ScanResponse:
        """Инициирует загрузку и применение свежих баз сигнатур Defender."""
        try:
            res = defender_svc.update_signatures()
            _csv_logger.log_event(
                event_type="signatures_update",
                status="SUCCESS" if res.success else "FAILED",
                details={"message": res.message},
                filename="windows_defender_scan_events.csv",
            )
            return res
        except Exception as e:
            logger.error(f"Ошибка обновления сигнатур: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка обновления баз: {e}",
            )


    @router.get("/asr", response_model=List[ASRRuleInfo], summary="Аудит правил Attack Surface Reduction")
    async def get_asr_rules() -> List[ASRRuleInfo]:
        """Возвращает статус правил Attack Surface Reduction (ASR) с каталогом GUID и рекомендациями."""
        try:
            return asr_mgr.get_asr_rules()
        except Exception as e:
            logger.error(f"Ошибка получения правил ASR: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка получения ASR: {e}",
            )

    @router.get("/cfa", response_model=ControlledFolderAccessInfo, summary="Статус Controlled Folder Access (Ransomware)")
    async def get_cfa() -> ControlledFolderAccessInfo:
        """Возвращает конфигурацию Controlled Folder Access, список защищенных папок и доверенных приложений."""
        try:
            return cfa_mgr.get_cfa_status()
        except Exception as e:
            logger.error(f"Ошибка получения статуса CFA: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка получения CFA: {e}",
            )

    @router.get("/exclusions", response_model=ExclusionsAuditReport, summary="Аудит исключений антивируса")
    async def get_exclusions() -> ExclusionsAuditReport:
        """Выполняет аудит исключений (пути, расширения, процессы) и выявляет потенциально опасные конфигурации."""
        try:
            return exclusions_aud.audit_exclusions()
        except Exception as e:
            logger.error(f"Ошибка аудита исключений: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка аудита исключений: {e}",
            )

    @router.get("/threats", response_model=List[ThreatRecord], summary="История обнаружения угроз")
    async def get_threats(limit: int = Query(50, ge=1, le=200)) -> List[ThreatRecord]:
        """Возвращает список зафиксированных угроз, активных инцидентов и объектов в карантине."""
        try:
            return threat_mgr.get_threats_history(limit=limit)
        except Exception as e:
            logger.error(f"Ошибка получения истории угроз: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка получения угроз: {e}",
            )

    @router.get("/events", response_model=List[DefenderEventRecord], summary="События журнала Defender Operational")
    async def get_events(limit: int = Query(50, ge=1, le=200)) -> List[DefenderEventRecord]:
        """Возвращает недавние записи из журнала Microsoft-Windows-Windows Defender/Operational."""
        try:
            return event_corr.get_recent_events(max_events=limit)
        except Exception as e:
            logger.error(f"Ошибка чтения журнала событий: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка чтения событий: {e}",
            )

    @router.get("/process-tree", response_model=List[SuspiciousProcessChain], summary="Подозрительные цепочки процессов")
    async def get_process_tree() -> List[SuspiciousProcessChain]:
        """Анализирует активные процессы и возвращает подозрительные цепочки родитель-потомок (Fileless индикаторы)."""
        try:
            return process_watch.scan_suspicious_chains()
        except Exception as e:
            logger.error(f"Ошибка сканирования процессов: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка анализа процессов: {e}",
            )

    @router.get("/diagnostics", response_model=DefenderDiagnosticReport, summary="Комплексный AI-анализ защищенности")
    async def get_diagnostics() -> DefenderDiagnosticReport:
        """Формирует итоговый отчет защищенности с оценкой Security Score (0-100) и списком рекомендаций."""
        try:
            return ai_diag.generate_diagnostic_report()
        except Exception as e:
            logger.error(f"Ошибка генерации диагностического отчета: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка генерации отчета: {e}",
            )

    return router
