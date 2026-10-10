# Contracts (Слой 1: Единые контракты и DTO подсистемы Windows)

> **Пакет:** `apps.windows.contracts`  
> **Статус:** ✅ Active (Production Ready)  
> **Обновлено:** 2026-10-10 05:31:00  
> **Принцип:** Zero-Dependency, Data Transfer Objects (DTO), строгая типизация (Pydantic / Dataclasses / Enums)

---

## 📋 Описание

Пакет `apps.windows.contracts` представляет собой базовый слой типизации (Слой 1) для всей подсистемы Windows в платформе **AI-Breadboard**.

Все контракты, модели данных (DTO) и перечисления (Enums) спроектированы в концепции **Zero-Dependency** (не имеют внешних связей с логикой сбора данных, нативным API или сервисами), что предотвращает циклические импорты и обеспечивает строгий контракт взаимодействия между модулями сбора телеметрии, аудита, аппаратного мониторинга, выполнения команд и контура ИИ (WikiLLM / AI Diagnostics).

---

## 📂 Структура пакета

| Модуль | Описание | Основные сущности |
|---|---|---|
| [`enums.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/contracts/enums.py) | Единые перечисления и константы | `RiskLevel`, `PrivilegeLevel`, `ExecutionMethod`, `HttpMethod`, `CapabilityCategory`, `CapabilityLevel`, `ActionType`, `ProcessState`, `ThreadState`, `ServiceState`, `TelemetryTier`, `AccessType`, `SamplingMode`, `ArtifactType`, `KnowledgeSource`, `LookupLevel` |
| [`audit.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/contracts/audit.py) | Модели аудита, диагностики и безопасного исполнения SafeOps | `RemediationAction`, `AuditFinding`, `DomainAuditResult`, `HealthScoreSummary`, `FullAuditReport`, `InvestigationReport`, `AtomicOperation`, `ExecutionRequest`, `ExecutionResult` |
| [`hardware.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/contracts/hardware.py) | Паспорта оборудования, датчики и телеметрия компонентов | `CpuInventoryInfo`, `ContractCpuMetrics`, `CpuTelemetrySample`, `RamModuleInventoryInfo`, `ContractMemoryMetrics`, `RamTelemetrySample`, `GpuInventoryInfo`, `ContractGpuMetrics`, `GpuTelemetrySample`, `NpuMetrics`, `StorageDriveInventoryInfo`, `ContractDiskPartitionMetrics`, `ContractDiskIoMetrics`, `DiskTelemetrySample`, `NetworkAdapterInventoryInfo`, `NetworkTelemetrySample`, `MotherboardInventoryInfo`, `SystemHardwareInventory`, `ContractHardwareSensor` |
| [`telemetry.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/contracts/telemetry.py) | DTO-контракты процессов, потоков, дескрипторов, системных срезов и аварийных дампов | `MemoryInfo`, `ThreadInfo`, `ModuleInfo`, `HandleInfo`, `ProcessInfo`, `ContractSystemSnapshot`, `ContractTelemetryIncident`, `ContractProcessMetrics`, `ContractProcessTokenInfo`, `ProcessNetworkConnection`, `ProcessIoCounters`, `ProcessThreadDetail`, `RebootIncident`, `CrashDumpArtifact` |
| [`ai.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/apps/windows/contracts/ai.py) | Контракты базы знаний WikiLLM, фактов, гипотез и отчетов ИИ-диагноста | `ResolutionAction`, `Claim`, `Evidence`, `KnowledgeEntity`, `ResolutionResult`, `ArtifactInput`, `AnomalyHypothesis`, `AiDiagnosticReport` |

---

## 🚀 Примеры использования в Python API

### Импорт через корневой пакет
Все основные контракты экспортируются напрямую через корневой `__init__.py`:

```python
from apps.windows.contracts import (
    RiskLevel,
    PrivilegeLevel,
    AuditFinding,
    DomainAuditResult,
    ContractSystemSnapshot,
    ContractCpuMetrics,
    ContractGpuMetrics,
    AiDiagnosticReport,
)

# Создание инцидента аудита безопасности
finding = AuditFinding(
    id="SEC-001",
    title="Небезопасная служба найдена",
    description="Обнаружена служба с правами LocalSystem и незащищенным путем",
    risk_level=RiskLevel.HIGH,
    domain="security_acl"
)

# Проверка уровня риска
if finding.risk_level == RiskLevel.HIGH:
    print(f"Критическая уязвимость: {finding.title}")
```

### Использование аппаратных и телеметрических срезов

```python
from apps.windows.contracts import ContractCpuMetrics, ContractMemoryMetrics

cpu_stats = ContractCpuMetrics(
    usage_percent=42.5,
    temperature_celsius=65.0,
    clock_speed_mhz=3600.0,
    core_utilizations=[40.0, 45.0, 42.0, 43.0]
)

ram_stats = ContractMemoryMetrics(
    total_bytes=34359738368,
    available_bytes=17179869184,
    used_bytes=17179869184,
    usage_percent=50.0
)
```
