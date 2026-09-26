# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LibreHardwareMonitor Router (Compatibility Layer)
# =============================================================================
from typing import Any, Dict
from fastapi import APIRouter
from apps.windows.hardware.lhm_service import LhmService
from apps.windows.hardware.lhm_auditor import LhmSensorAuditor

router = APIRouter(prefix="/api/v1/lhm", tags=["LibreHardwareMonitor"])
_lhm_service = LhmService()
_auditor = LhmSensorAuditor()


@router.get("/status")
async def get_lhm_status() -> Dict[str, Any]:
    return {
        "is_running": _lhm_service.is_running(),
        "is_binary_available": _lhm_service.is_binary_available(),
        "portable_guide": "http://localhost:8085/data.json",
    }


@router.get("/metrics")
async def get_lhm_metrics() -> Dict[str, Any]:
    metrics = await _lhm_service.get_metrics_async()
    return {"sensors": [s.model_dump() for s in metrics]} if metrics else {"sensors": []}


@router.post("/audit")
async def run_lhm_audit() -> Dict[str, Any]:
    return await _auditor.audit_sensors_with_ai()


@router.get("/audit/summary")
async def get_lhm_audit_summary() -> Dict[str, Any]:
    return _auditor.collect_and_aggregate_logs()


def init_router() -> APIRouter:
    return router
