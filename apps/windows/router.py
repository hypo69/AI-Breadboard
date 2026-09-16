# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Diagnostic & Audit Center FastAPI Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для комплексного аудита Windows, специализированных
#   режимов диагностики, расследования первопричин (Root-Cause) и SafeOps действий.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.windows.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для AI Windows Diagnostic & Administration Center."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.api.router_auth import require_admin_user
from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
from apps.windows.core.models import ActionType, RemediationAction, RiskLevel
from apps.windows.core.modules import (
    BaselineCollector,
    CleanCollector,
    DriverCollector,
    EventLogCollector,
    IntegrityCollector,
    NetworkCollector,
    PerformanceCollector,
    PostInstallCollector,
    ProcessCollector,
    SecurityCollector,
    ServicesCollector,
    SoftwareCollector,
    StorageCollector,
    TasksCollector,
    UpdateCollector,
)
from apps.windows.core.root_cause_engine import RootCauseEngine
from apps.windows.core.safe_executor import SafeExecutor

router = APIRouter(prefix="/api/windows", tags=["windows-diagnostics"])

# Синглтоны сервисов
_diagnostician = WindowsAIDiagnostician()
_investigator = WindowsAIRootCauseAnalyzer()
_engine = RootCauseEngine()
_executor = SafeExecutor()


class InvestigateRequest(BaseModel):
    """Модель запроса расследования симптома."""
    symptom: str


class ActionExecuteRequest(BaseModel):
    """Модель запроса выполнения SafeOps действия."""
    action_id: str
    action_type: str
    title: str
    description: str
    target: str
    risk: str
    execution_command: str = ""
    confirmed_by_user: bool = False


@router.get("/health")
async def get_system_health(mode: str = "quick") -> Dict[str, Any]:
    """Быстрая оценка здоровья системы (Health Score)."""
    report = _engine.run_full_audit(mode=mode)
    return {
        "health_score": report.health_score.to_dict(),
        "mode": mode,
        "timestamp": report.timestamp.isoformat(),
        "summary": f"Health Score: {report.health_score.score}/100 ({report.health_score.status_label})",
    }


@router.get("/audit/full")
async def get_full_audit() -> Dict[str, Any]:
    """Полный глубокий аудит по всем 15 доменам системы."""
    report = await _diagnostician.diagnose_system(mode="full")
    return report.to_dict()


@router.get("/audit/clean")
async def get_clean_audit() -> Dict[str, Any]:
    """Аудит временных файлов, кэшей и корзины."""
    collector = CleanCollector()
    return collector.collect().to_dict()


@router.get("/audit/performance")
async def get_performance_audit() -> Dict[str, Any]:
    """Аудит производительности, автозагрузки и очередей."""
    collector = PerformanceCollector()
    return collector.collect().to_dict()


@router.get("/audit/drivers")
async def get_drivers_audit() -> Dict[str, Any]:
    """Аудит драйверов, устройств PnP и пакетов DriverStore."""
    collector = DriverCollector()
    return collector.collect().to_dict()


@router.get("/audit/software")
async def get_software_audit() -> Dict[str, Any]:
    """Инвентарь установленных программ и связанных компонентов."""
    collector = SoftwareCollector()
    return collector.collect().to_dict()


@router.get("/audit/integrity")
async def get_integrity_audit() -> Dict[str, Any]:
    """Аудит целостности системы (SFC / DISM / Servicing)."""
    collector = IntegrityCollector()
    return collector.collect().to_dict()


@router.get("/audit/storage")
async def get_storage_audit() -> Dict[str, Any]:
    """Аудит дисков, томов, свободного места и файловой системы."""
    collector = StorageCollector()
    return collector.collect().to_dict()


@router.get("/audit/security")
async def get_security_audit() -> Dict[str, Any]:
    """Аудит безопасности: Defender, UAC, персистентность."""
    collector = SecurityCollector()
    return collector.collect().to_dict()


@router.get("/audit/events")
async def get_events_audit(hours: int = 24) -> Dict[str, Any]:
    """Анализ системных журналов и корреляция ошибок."""
    collector = EventLogCollector()
    return collector.collect(hours=hours).to_dict()


@router.get("/audit/processes")
async def get_processes_audit() -> Dict[str, Any]:
    """Интеллектуальный анализ запущенных процессов."""
    collector = ProcessCollector()
    return collector.collect().to_dict()


@router.get("/audit/services")
async def get_services_audit() -> Dict[str, Any]:
    """Инвентарь служб и выявление осиротевших сервисов."""
    collector = ServicesCollector()
    return collector.collect().to_dict()


@router.get("/audit/tasks")
async def get_tasks_audit() -> Dict[str, Any]:
    """Аудит задач Планировщика (Task Scheduler)."""
    collector = TasksCollector()
    return collector.collect().to_dict()


@router.get("/audit/network")
async def get_network_audit() -> Dict[str, Any]:
    """Аудит сетевых соединений и открытых портов."""
    collector = NetworkCollector()
    return collector.collect().to_dict()


@router.get("/audit/updates")
async def get_updates_audit() -> Dict[str, Any]:
    """Аудит версии Windows и обновлений KB."""
    collector = UpdateCollector()
    return collector.collect().to_dict()


@router.get("/audit/baseline")
async def get_baseline_audit() -> Dict[str, Any]:
    """Аудит эталонного снимка конфигурации и дрифта."""
    collector = BaselineCollector()
    return collector.collect().to_dict()


@router.get("/audit/postinstall")
async def get_postinstall_audit() -> Dict[str, Any]:
    """Чек-лист готовности системы после установки Windows."""
    collector = PostInstallCollector()
    return collector.collect().to_dict()


@router.post("/investigate")
async def investigate_symptom(req: InvestigateRequest) -> Dict[str, Any]:
    """Интеллектуальное расследование первопричины по симптому."""
    res = await _investigator.analyze_incident(req.symptom)
    return res.to_dict()


@router.post("/actions/simulate")
async def simulate_action(req: ActionExecuteRequest) -> Dict[str, Any]:
    """Dry-Run симуляция корректирующего действия SafeOps."""
    action = RemediationAction(
        action_id=req.action_id,
        action_type=ActionType(req.action_type),
        title=req.title,
        description=req.description,
        target=req.target,
        risk=RiskLevel(req.risk),
        execution_command=req.execution_command,
    )
    sim_res = _executor.simulate(action)
    return sim_res


@router.post("/actions/execute")
async def execute_action(request: Request, req: ActionExecuteRequest) -> Dict[str, Any]:
    """Безопасное выполнение действия (требуются права администратора)."""
    require_admin_user(request)
    action = RemediationAction(
        action_id=req.action_id,
        action_type=ActionType(req.action_type),
        title=req.title,
        description=req.description,
        target=req.target,
        risk=RiskLevel(req.risk),
        execution_command=req.execution_command,
    )
    result_action = _executor.execute(action, confirmed_by_user=req.confirmed_by_user)
    return result_action.to_dict()


# -----------------------------------------------------------------------------
# Hardware Diagnostics & Benchmark Endpoints
# -----------------------------------------------------------------------------

@router.get("/hardware/smart")
async def get_storage_smart() -> Dict[str, Any]:
    """Получение детальных S.M.A.R.T. данных и здоровья накопителей."""
    from apps.windows.hardware.smartctl_probe import SmartProber
    prober = SmartProber()
    drives = prober.scan_drives()
    return {"drives": [d.__dict__ for d in drives]}


@router.get("/hardware/gpu")
async def get_gpu_telemetry() -> Dict[str, Any]:
    """Получение телеметрии GPU (NVIDIA, AMD, Intel, WMI)."""
    from apps.windows.hardware.gpu_prober import GpuProber
    prober = GpuProber()
    gpus = prober.probe_all()
    return {"gpus": [g.__dict__ for g in gpus]}


@router.get("/hardware/audit")
async def get_hardware_audit() -> Dict[str, Any]:
    """Аппаратный аудит CPU/Motherboard через CPU-Z, AIDA64 или WMI."""
    from apps.windows.hardware.cpuz_aida_prober import CpuzAidaProber
    prober = CpuzAidaProber()
    report = prober.generate_report()
    return {"report": report.__dict__}


class StressTestRequest(BaseModel):
    target: str = "CPU"
    duration_seconds: int = 10
    max_safe_temp: float = 90.0


@router.post("/benchmark/stress")
async def run_stress_benchmark(req: StressTestRequest) -> Dict[str, Any]:
    """Безопасный запуск стресс-теста CPU или GPU."""
    from apps.windows.hardware.stress_benchmark import StressBenchmarkEngine
    engine = StressBenchmarkEngine(max_safe_temp_c=req.max_safe_temp)
    if req.target.upper() == "GPU":
        res = engine.run_gpu_stress(duration_sec=req.duration_seconds)
    else:
        res = engine.run_cpu_stress(duration_sec=req.duration_seconds)
    return res.__dict__


def init_router(app: Optional[Any] = None, state: Optional[Any] = None) -> APIRouter:
    """Инициализация FastAPI роутера."""
    return router


__all__ = [
    "init_router",
    "router",
]

