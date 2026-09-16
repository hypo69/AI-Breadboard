# Windows API Layer Module

Modular, type-safe wrappers for Windows API functions used in Process Explorer implementation.

## Structure

### `kernel32.py`
Process enumeration and snapshot operations.

**Functions:**
- `enumerate_processes()` - Get all running processes
- `enumerate_threads(pid)` - Get threads for a process
- `enumerate_modules(pid)` - Get loaded modules (DLLs)
- `get_process_priority_class(pid)` - Get process priority
- `get_process_times(pid)` - Get creation/exit times

**Data Classes:**
- `ProcessInfo` - Process details from Toolhelp32
- `ThreadInfo` - Thread information
- `ModuleInfo` - Loaded module information

### `psapi.py`
Process memory and module information.

**Functions:**
- `enumerate_processes()` - Get all process IDs
- `get_process_memory_info(pid)` - Memory statistics (working set, page faults, pool usage)
- `enumerate_process_modules(pid, filter_type)` - Get loaded modules with filter options
- `get_process_image_filename(pid)` - Get process executable path

**Data Classes:**
- `MemoryInfo` - Process memory counters

### `advapi32.py`
Registry, services, and security operations.

**Functions:**
- `read_registry_value(hive, path, value_name)` - Read registry value
- `enumerate_registry_values(hive, path)` - Enumerate registry key values
- `enumerate_services()` - List all services with status

**Data Classes:**
- `RegistryValue` - Registry value information
- `ServiceInfo` - Service status and configuration

### `ntdll.py`
Native NT API functions for low-level system information.

**Functions:**
- `get_windows_version()` - Get Windows version details
- `query_system_information(info_class)` - Query system information structures
- `query_object_name(handle)` - Get name of kernel object
- `query_process_basic_info(pid)` - Get basic process information

**Data Classes:**
- `VersionInfo` - Windows version information

### `etw.py`
Event Tracing for Windows for real-time monitoring.

**Functions:**
- `start_kernel_logger(enable_flags)` - Start ETW Kernel Logger session
- `stop_kernel_logger()` - Stop ETW session
- `register_event_callback(event_type, callback)` - Register event handler
- `unregister_event_callback(event_type, callback)` - Unregister event handler

**Constants:**
- `EVENT_TRACE_FLAG_*` - Event category flags (Process, Thread, Disk I/O, etc.)

**Data Classes:**
- `EtwEvent` - Event information

## Usage

```python
from apps.windows.api import Kernel32API, PsapiAPI, NtdllAPI

# Get process list
k32 = Kernel32API()
processes = k32.enumerate_processes()

# Get memory info
psapi = PsapiAPI()
for proc in processes:
    mem = psapi.get_process_memory_info(proc.pid)
    if mem:
        print(f"PID {proc.pid}: {mem.working_set / 1024 / 1024:.2f} MB")

# Get Windows version
ntdll = NtdllAPI()
version = ntdll.get_windows_version()
print(f"Windows {version.major}.{version.minor} Build {version.build}")
```

## Error Handling

All API wrappers follow these patterns:
- Return `None` on errors
- Return empty lists/tuples on enumeration errors
- Use ctypes exception handling with graceful fallbacks
- Log errors to console (can be redirected)

## Integration with Core Modules

The API layer integrates with:
- **ProcessIntelligence** - Combines all APIs into unified interface
- **CorrelationEngine** - Uses API data for relationship analysis
- **DiagnosticsEngine** - Diagnostic checks use API data
- **Data Models** - Normalized data structures from APIs

## Platform Support

- Windows 7+
- Tested on: Windows 10, Windows 11
- Requires: Administrative privileges for some operations

## License

Part of Windows Diagnostic Engine (Process Explorer implementation)
