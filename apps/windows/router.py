# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.router import InvestigateRequest
#
#     service = InvestigateRequest()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""# Description:"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("windows_router")
from apps.windows.ai.diagnostician import WindowsAIDiagnostician
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer
from apps.windows.core.models import ActionType, RemediationAction, RiskLevel
from apps.windows.core.audits import CleanCollector, DriverCollector, EventLogCollector, IntegrityCollector, NetworkCollector, PerformanceCollector, PostInstallCollector, ProcessCollector, SecurityCollector, ServicesCollector, SoftwareCollector, StorageCollector, TasksCollector, UpdateCollector
from apps.windows.core.root_cause_engine import RootCauseEngine
from apps.windows.core.safe_executor import SafeExecutor
router = APIRouter(prefix='/api/windows', tags=['windows-diagnostics'])
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
    execution_command: str = ''
    confirmed_by_user: bool = False

@router.get('/health')
async def get_system_health(mode: str='quick') -> Dict[str, Any]:
    """Быстрая оценка здоровья системы (Health Score)."""
    report = _engine.run_full_audit(mode=mode)
    return {'health_score': report.health_score.to_dict(), 'mode': mode, 'timestamp': report.timestamp.isoformat(), 'summary': f'Health Score: {report.health_score.score}/100 ({report.health_score.status_label})'}

@router.get('/audit/full')
async def get_full_audit() -> Dict[str, Any]:
    """Полный глубокий аудит по всем 15 доменам системы."""
    report = await _diagnostician.diagnose_system(mode='full')
    return report.to_dict()

@router.get('/audit/clean')
async def get_clean_audit() -> Dict[str, Any]:
    """Аудит временных файлов, кэшей и корзины."""
    collector = CleanCollector()
    res = collector.collect()
    return res.to_dict()

@router.get('/audit/performance')
async def get_performance_audit() -> Dict[str, Any]:
    """Аудит производительности, автозагрузки и очередей."""
    collector = PerformanceCollector()
    res = collector.collect()
    return res.to_dict()

@router.get('/audit/drivers')
async def get_drivers_audit() -> Dict[str, Any]:
    """Аудит драйверов, устройств PnP и пакетов DriverStore."""
    collector = DriverCollector()
    res = collector.collect()
    return res.to_dict()

@router.get('/audit/software')
async def get_software_audit() -> Dict[str, Any]:
    """Инвентарь установленных программ и связанных компонентов."""
    collector = SoftwareCollector()
    return collector.collect().to_dict()

@router.get('/software')
async def get_installed_software(category: Optional[str]=None, unused_only: bool=False, limit: int=500) -> List[Dict[str, Any]]:
    """Получение списка установленных программ с историей запусков и назначением."""
    from apps.windows.core.software_audit import SoftwareAuditEngine
    engine = SoftwareAuditEngine()
    apps = engine.get_installed_applications()
    if category:
        c_lower = category.lower()
        apps = [a for a in apps if c_lower in (a.category.value if hasattr(a.category, 'value') else str(a.category)).lower()]
    if unused_only:
        apps = [a for a in apps if not a.was_launched]
    return [a.to_dict() for a in apps[:limit]]

@router.get('/software/audit')
async def get_software_audit_summary() -> Dict[str, Any]:
    """Сводный аналитический отчет аудита программного обеспечения."""
    from apps.windows.core.software_audit import SoftwareAuditEngine
    engine = SoftwareAuditEngine()
    report = engine.generate_audit_report()
    return report.to_dict()

@router.get('/audit/integrity')
async def get_integrity_audit() -> Dict[str, Any]:
    """Аудит целостности системы (SFC / DISM / Servicing)."""
    collector = IntegrityCollector()
    return collector.collect().to_dict()

@router.get('/audit/storage')
async def get_storage_audit() -> Dict[str, Any]:
    """Аудит дисков, томов, свободного места и файловой системы."""
    collector = StorageCollector()
    return collector.collect().to_dict()

@router.get('/audit/security')
async def get_security_audit() -> Dict[str, Any]:
    """Аудит безопасности: Defender, UAC, персистентность."""
    collector = SecurityCollector()
    return collector.collect().to_dict()

@router.get('/audit/events')
async def get_events_audit(hours: int=24) -> Dict[str, Any]:
    """Анализ системных журналов и корреляция ошибок."""
    collector = EventLogCollector()
    return collector.collect(hours=hours).to_dict()

@router.get('/audit/processes')
async def get_processes_audit() -> Dict[str, Any]:
    """Интеллектуальный анализ запущенных процессов."""
    collector = ProcessCollector()
    return collector.collect().to_dict()

@router.get('/audit/services')
async def get_services_audit() -> Dict[str, Any]:
    """Инвентарь служб и выявление осиротевших сервисов."""
    collector = ServicesCollector()
    return collector.collect().to_dict()

@router.get('/audit/tasks')
async def get_tasks_audit() -> Dict[str, Any]:
    """Аудит задач Планировщика (Task Scheduler)."""
    collector = TasksCollector()
    return collector.collect().to_dict()

@router.get('/audit/network')
async def get_network_audit() -> Dict[str, Any]:
    """Аудит сетевых соединений и открытых портов."""
    collector = NetworkCollector()
    return collector.collect().to_dict()

@router.get('/audit/updates')
async def get_updates_audit() -> Dict[str, Any]:
    """Аудит версии Windows и обновлений KB."""
    collector = UpdateCollector()
    return collector.collect().to_dict()

@router.get('/audit/postinstall')
async def get_postinstall_audit() -> Dict[str, Any]:
    """Чек-лист готовности системы после установки Windows."""
    collector = PostInstallCollector()
    return collector.collect().to_dict()

@router.post('/investigate')
async def investigate_symptom(req: InvestigateRequest) -> Dict[str, Any]:
    """Заглушка для расследования симптома (POST → GET)."""
    return {
        'symptom': req.symptom,
        'status': 'stub',
        'message': 'POST endpoint stub: Use GET /api/windows/audit/full for analysis',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@router.post('/actions/simulate')
async def simulate_action(req: ActionExecuteRequest) -> Dict[str, Any]:
    """Заглушка для симуляции действия (POST → GET)."""
    return {
        'action_id': req.action_id,
        'status': 'stub',
        'message': 'POST endpoint stub: Simulation not available, use GET /api/windows/audit/* for information'
    }

@router.post('/actions/execute')
async def execute_action(request: Request, req: ActionExecuteRequest) -> Dict[str, Any]:
    """Заглушка для выполнения действия (POST → GET)."""
    return {
        'action_id': req.action_id,
        'status': 'stub',
        'message': 'POST endpoint stub: Execution not available, use GET endpoints for read-only operations'
    }

class DefenderScanRequest(BaseModel):
    """Модель запроса сканирования Defender."""
    scan_type: str = 'quick'
    custom_path: Optional[str] = None

class DefenderToggleFeatureRequest(BaseModel):
    """Модель запроса переключения CFA / PUA."""
    mode: str = 'enabled'

@router.get('/defender/status')
async def get_defender_detailed_status() -> Dict[str, Any]:
    """Детальный статус Microsoft Defender: защита, версионность и ASR."""
    from apps.windows.core.defender_manager import DefenderManager
    mgr = DefenderManager()
    status = mgr.get_detailed_status()
    prefs = mgr.get_preferences()
    return {'status': status, 'preferences': prefs}

@router.get('/defender/threats')
async def get_defender_threats() -> Dict[str, Any]:
    """История обнаружений и активных угроз Microsoft Defender."""
    from apps.windows.core.defender_manager import DefenderManager
    mgr = DefenderManager()
    threats = mgr.get_threat_detections()
    return {'threats': threats, 'count': len(threats)}

@router.post('/defender/scan')
async def start_defender_scan(request: Request, req: DefenderScanRequest) -> Dict[str, Any]:
    """Заглушка для сканирования Defender (POST → GET)."""
    return {
        'status': 'stub',
        'scan_type': req.scan_type,
        'message': 'POST endpoint stub: Defender scan not available, use GET /api/windows/defender/status for information'
    }

@router.post('/defender/update-signatures')
async def update_defender_signatures(request: Request) -> Dict[str, Any]:
    """Заглушка для обновления сигнатур Defender (POST → GET)."""
    return {
        'status': 'stub',
        'message': 'POST endpoint stub: Signature update not available, use GET /api/windows/defender/status for information'
    }

@router.post('/defender/cfa')
async def toggle_controlled_folder_access(request: Request, req: DefenderToggleFeatureRequest) -> Dict[str, Any]:
    """Заглушка для Controlled Folder Access (POST → GET)."""
    return {
        'status': 'stub',
        'mode': req.mode,
        'message': 'POST endpoint stub: CFA toggle not available, use GET /api/windows/defender/status for information'
    }

@router.post('/defender/pua')
async def toggle_pua_protection(request: Request, req: DefenderToggleFeatureRequest) -> Dict[str, Any]:
    """Заглушка для PUA Protection (POST → GET)."""
    return {
        'status': 'stub',
        'mode': req.mode,
        'message': 'POST endpoint stub: PUA protection toggle not available, use GET /api/windows/defender/status for information'
    }

@router.get('/hardware/monitor')
async def get_hardware_monitor_snapshot(include_smart: bool=True) -> Dict[str, Any]:
    """Полный моментальный снимок аппаратного состояния системы (CPU, RAM, GPU, Disks, Sensors, Network, Battery)."""
    from apps.windows.hardware.hardware_monitor import HardwareMonitor
    monitor = HardwareMonitor()
    snapshot = monitor.get_snapshot(include_smart=include_smart)
    return snapshot.to_dict()

@router.get('/hardware/monitor/summary')
async def get_hardware_monitor_summary() -> Dict[str, Any]:
    """Краткая сводка здоровья и пороговых предупреждений оборудования."""
    from apps.windows.hardware.hardware_monitor import HardwareMonitor
    monitor = HardwareMonitor()
    summary = monitor.get_summary()
    return summary

@router.get('/hardware/sensors')
async def get_hardware_sensors_list() -> Dict[str, Any]:
    """Список всех обнаруженных аппаратных датчиков (температуры, кулеры, напряжения)."""
    from apps.windows.hardware.hardware_monitor import HardwareMonitor
    monitor = HardwareMonitor()
    sensors = monitor.get_sensor_metrics()
    return {'sensors': [s.__dict__ for s in sensors], 'count': len(sensors)}

@router.get('/hardware/smart')
async def get_storage_smart() -> Dict[str, Any]:
    """Получение детальных S.M.A.R.T. данных и здоровья накопителей через нативный Windows Storage API."""
    try:
        from apps.windows.storage.windows_storage_sensor import WindowsStorageSensor
        sensor = WindowsStorageSensor()
        drives = sensor.get_physical_disks()
        return {'drives': drives}
    except Exception as ex:
        logger.warning(f'Ошибка получения состояния дисков: {ex}')
        return {'drives': []}

@router.get('/hardware/gpu')
async def get_gpu_telemetry() -> Dict[str, Any]:
    """Получение телеметрии GPU (NVIDIA, AMD, Intel, WMI)."""
    from apps.windows.modules.hardware.gpu_prober import GpuProber
    prober = GpuProber()
    gpus = prober.probe_all()
    return {'gpus': [g.__dict__ for g in gpus]}

@router.get('/hardware/providers')
async def get_hardware_providers() -> Dict[str, Any]:
    """Получение списка всех аппаратных провайдеров и их статуса."""
    from apps.windows.hardware.registry import HardwareProviderRegistry
    reg = HardwareProviderRegistry()
    return {'providers': [p.get_provider_info() for p in reg.get_all_providers()], 'total': len(reg.get_all_providers()), 'available_count': len(reg.get_available_providers())}

@router.get('/hardware/cross-check')
async def get_hardware_cross_check() -> Dict[str, Any]:
    """Запуск перекрестной проверки данных оборудования от всех провайдеров."""
    from apps.windows.hardware.cross_validator import CrossValidator
    validator = CrossValidator()
    report = validator.run_cross_check()
    return report.to_dict()

@router.get('/hardware/audit')
async def get_hardware_audit() -> Dict[str, Any]:
    """Аппаратный аудит CPU/Motherboard через CPU-Z, AIDA64 или WMI."""
    from apps.windows.hardware.cpuz_aida_prober import CpuzAidaProber
    prober = CpuzAidaProber()
    report = prober.generate_report()
    return {'report': report.__dict__}

class StressTestRequest(BaseModel):
    """Модель запроса для стресс-теста."""
    target: str = 'cpu'
    duration_seconds: int = 30
    intensity: float = 1.0

@router.post('/benchmark/stress')
async def run_stress_benchmark(req: StressTestRequest) -> Dict[str, Any]:
    """Заглушка для стресс-теста (POST → GET)."""
    return {
        'status': 'stub',
        'target': req.target,
        'message': 'POST endpoint stub: Stress test not available, use GET /api/windows/hardware/monitor for real-time data'
    }

class AIBenchmarkRequest(BaseModel):
    """Модель запроса для AI бенчмарка."""
    provider: str = 'gemini'
    model_name: str = 'gemini-2.5-flash'
    prompt: str = 'Тестовый запрос для замера скорости инференса.'
    max_tokens: int = 150
    temperature: float = 0.7

@router.post('/benchmark/ai')
async def run_ai_benchmark(req: AIBenchmarkRequest) -> Dict[str, Any]:
    """Заглушка для AI benchmark (POST → GET)."""
    return {
        'status': 'stub',
        'provider': req.provider,
        'model': req.model_name,
        'message': 'POST endpoint stub: AI benchmark not available, use GET /api/windows/benchmark/ai/history for historical data'
    }

_stress_engine = None

def _get_stress_engine():
    """Получение или инициализация экземпляра StressBenchmarkEngine."""
    global _stress_engine
    if _stress_engine is None:
        from apps.windows.modules.hardware.stress_benchmark import StressBenchmarkEngine
        _stress_engine = StressBenchmarkEngine()
    return _stress_engine

@router.get('/benchmark/ai/history')
async def get_ai_benchmark_history() -> List[Dict[str, Any]]:
    """Получение истории замеров производительности инференса ИИ."""
    engine = _get_stress_engine()
    return engine.get_ai_benchmark_history()

@router.get('/audit/process-telemetry/status')
async def get_process_telemetry_status() -> Dict[str, Any]:
    """Проверка доступности и статуса сенсоров телеметрии (Sysmon, Security 4688, CommandLine)."""
    from apps.windows.core.process_audit_manager import ProcessAuditManager
    manager = ProcessAuditManager()
    status = manager.get_telemetry_status()
    return status.to_dict()

@router.get('/audit/process-telemetry/history')
async def get_process_telemetry_history(limit: int=100, process: Optional[str]=None, user: Optional[str]=None) -> List[Dict[str, Any]]:
    """Получение структурированной истории запуска процессов с командной строкой и PID."""
    from apps.windows.core.process_audit_manager import ProcessAuditManager
    manager = ProcessAuditManager()
    return manager.get_process_execution_history(limit=limit, filter_process=process, filter_user=user)

@router.get('/audit/process-telemetry/tree')
async def get_process_telemetry_tree(limit: int=100) -> List[Dict[str, Any]]:
    """Построение иерархического дерева выполнения процессов (Parent -> Child)."""
    from apps.windows.core.process_audit_manager import ProcessAuditManager
    manager = ProcessAuditManager()
    tree = manager.build_process_tree(limit=limit)
    return [node.to_dict() for node in tree]

@router.get('/audit/process-telemetry/file-activity')
async def get_process_telemetry_file_activity(limit: int=50) -> List[Dict[str, Any]]:
    """Получение файловых операций (создание/удаление) с привязкой к процессам."""
    from apps.windows.core.process_audit_manager import ProcessAuditManager
    manager = ProcessAuditManager()
    return manager.get_file_activity_with_processes(limit=limit)

@router.get('/reboots')
async def get_reboots_report(limit: int = 20, hours: int = 720) -> Dict[str, Any]:
    """Сводный отчет анализа и корреляции причин перезагрузок и выключений ОС."""
    from apps.windows.telemetry.reboot_analyzer import WindowsRebootAnalyzer
    analyzer = WindowsRebootAnalyzer()
    report = analyzer.collect_reboot_history(limit=limit, hours=hours, persist_to_storage=True)
    return report.model_dump()

@router.get('/reboots/latest')
async def get_latest_reboot_info() -> Dict[str, Any]:
    """Детальная информация о последней перезагрузке текущей сессии."""
    from apps.windows.telemetry.reboot_analyzer import WindowsRebootAnalyzer
    analyzer = WindowsRebootAnalyzer()
    session = analyzer.analyze_current_boot()
    if not session:
        return {'status': 'no_data', 'message': 'Данные о последней перезагрузке недоступны'}
    return session.model_dump()

@router.get('/reboots/history')
async def get_reboots_stored_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Получение персистентной истории всех перезагрузок из базы данных телеметрии."""
    from apps.windows.telemetry.sqlite import TelemetryStorage
    storage = TelemetryStorage.get_instance()
    return storage.get_reboot_history(limit=limit)

def init_router(app: Optional[Any]=None, state: Optional[Any]=None) -> APIRouter:
    """Инициализация FastAPI роутера."""
    from apps.windows.core.software_transparency import init_software_transparency_router
    from apps.windows.api.router_capabilities import init_router as init_capabilities_router
    from apps.windows.wikillm.router import init_router as init_wikillm_router
    from apps.windows.modules.programms_history_deep_researh.router import router as prog_history_router
    router.include_router(init_capabilities_router())
    router.include_router(init_wikillm_router())
    router.include_router(prog_history_router)
    chat_prov = state.chat_model if state and hasattr(state, 'chat_model') else None
    router.include_router(init_software_transparency_router(chat_provider=chat_prov))
    return router
__all__ = ['init_router', 'router']