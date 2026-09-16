# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│          Windows Diagnostic Dashboard                   │
│  (Central Hub - apps/dashboard/)                        │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼──────┐  ┌──────▼───┐  ┌─────▼────┐
    │ Process   │  │ Memory   │  │ Network  │
    │ Explorer  │  │ Monitor  │  │ Diag.    │
    └────┬──────┘  └──────┬───┘  └─────┬────┘
         │                 │            │
    ┌────▼──────────────────┼────────────▼────┐
    │  Process Intelligence Module             │
    │  (Unified System API)                    │
    └────┬────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────────┐
    │      Core WinAPI Layer                    │
    │  (kernel32, psapi, advapi32, ntdll, etw) │
    └─────────────────────────────────────────┘
```

## Directory Structure

```
apps/windows/
├── __init__.py
├── README.md
├── ARCHITECTURE.md
├── INSTALLATION.md
├── TESTING.md
├── core/
│   ├── winapi.py (Capability detection)
│   ├── data_model.py (Normalized structures)
│   ├── correlation_engine.py (Analysis)
│   ├── diagnostics.py (80+ checks)
│   └── __init__.py
├── api/
│   ├── kernel32.py (Process enumeration)
│   ├── psapi.py (Memory & modules)
│   ├── advapi32.py (Registry, services)
│   ├── ntdll.py (Native NT API)
│   ├── etw.py (Event tracing)
│   └── __init__.py
├── process_intelligence.py (Unified API)
├── apps/
│   ├── dashboard/ (Central hub - Task #12)
│   ├── process_explorer/ (Task #3)
│   ├── memory_monitor/ (Task #5)
│   ├── network_diagnostics/ (Task #6)
│   ├── services_manager/ (Task #4)
│   ├── registry_viewer/ (Task #7)
│   ├── security_analyzer/ (Task #8)
│   ├── hardware_explorer/ (Task #9)
│   ├── baseline_detector/ (Task #10)
│   └── realtime_monitor/ (Task #11)
└── tests/
    ├── test_core.py
    ├── test_api.py
    ├── test_apps.py
    └── __init__.py
```

## Component Details

### Core Layer (core/)
- **winapi.py**: Capability level detection (Kernel to Driver)
- **data_model.py**: ProcessInfo, ThreadInfo, MemoryInfo
- **correlation_engine.py**: Cross-component relationships
- **diagnostics.py**: 80+ checks across 10 categories

### API Layer (api/)
- **kernel32.py**: Toolhelp32, process/thread/module enumeration
- **psapi.py**: Memory info, module enumeration
- **advapi32.py**: Registry, services, security
- **ntdll.py**: Native NT API, version info
- **etw.py**: Event Tracing for Windows

### Process Intelligence (process_intelligence.py)
Unified interface combining all APIs:
- Process enumeration with full details
- Memory trend analysis
- Dependency tracking
- Real-time monitoring

### Application Modules (apps/)

#### Process Explorer
- Tree view with parent-child relationships
- Real-time memory monitoring
- Thread and module enumeration
- Interactive CLI

#### Memory & Performance Monitor
- System and process metrics
- Memory leak detection
- Alert system
- Trend analysis

#### Network & Firewall Diagnostics
- Connection enumeration
- Firewall rule inspection
- Suspicious activity detection
- Adapter information

#### Services & Drivers Manager
- Service enumeration and filtering
- Driver analysis (unsigned detection)
- Dependency tracking
- Registry-based configuration

#### Registry & Events Viewer
- Registry browser with search
- Event log querying
- Statistics and trending
- PowerShell integration

#### Security & Tokens Analyzer
- Process elevation status
- Token information
- Privilege enumeration
- Risk identification

#### Hardware & Devices Explorer
- CPU, RAM, storage info
- Device enumeration
- WMIC integration

#### Baseline Detector
- Configuration snapshot
- Drift detection
- Change tracking
- Baseline persistence

#### Real-Time Monitor
- Process lifecycle tracking
- Service changes
- Event notification
- Change history

#### Dashboard
- Central hub
- Module aggregation
- System overview
- Unified interface

## Data Flow

```
System Events
    ↓
WinAPI Layer (kernel32, psapi, etc.)
    ↓
Process Intelligence (unified interface)
    ↓
Application Modules (PE, Memory, Network, etc.)
    ↓
User Interface (CLI)
```

## Design Patterns

### 1. Capability Level Detection
Auto-selects best available API based on system

### 2. Normalized Data Model
Consistent structures across all modules

### 3. Correlation Engine
Analyzes relationships between components

### 4. Registry Pattern (Diagnostics)
Registers checks by ID for easy extension

### 5. Event-Driven Monitoring
Real-time updates via background threads

### 6. Pluggable Architecture
Modules independent, can be used standalone

## Technology Stack

- **Language**: Python 3.8+
- **Windows APIs**: ctypes (kernel32, psapi, advapi32, ntdll)
- **System Integration**: WMI, PowerShell, ETW
- **CLI**: Python cmd module
- **Threading**: threading, collections.deque
- **Data Processing**: dataclasses, enums

## Performance Characteristics

- **Process enumeration**: ~100-200ms
- **Memory monitoring**: ~50-100ms per cycle
- **Network connection scan**: ~500-1000ms
- **Registry search**: 1-5 seconds (depth-dependent)
- **Memory overhead**: ~50-100 MB
- **CPU usage**: <2% idle, <5% during enumeration

## Security Considerations

1. **Privilege Requirements**: Some operations need admin
2. **Data Sensitivity**: Handles process/security info
3. **System Impact**: Minimal (read-only operations mostly)
4. **API Safe Usage**: All calls have error handling

## Extensibility

### Adding New Checks
1. Define in diagnostics.py
2. Register in DiagnosticsEngine
3. Return DiagnosticResult

### Adding New Application
1. Create module in apps/
2. Implement analyzer/explorer
3. Create CLI interface
4. Add to dashboard

### Custom Metrics
1. Define in data_model.py
2. Collect in process_intelligence.py
3. Display in application

## Testing Strategy

- **Unit Tests**: Core and API layers
- **Integration Tests**: Multi-module workflows
- **Manual Tests**: Each CLI application
- **Regression Tests**: Known issue cases
