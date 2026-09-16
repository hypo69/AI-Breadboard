# Testing Guide

## Running Tests

### Unit Tests
```bash
python -m pytest tests/ -v
python -m unittest discover tests/ -v
```

### Individual Test Suites
```bash
python -m pytest tests/test_core.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_apps.py -v
```

### Test Coverage
```bash
python -m pytest tests/ --cov=apps.windows --cov-report=html
```

## Test Structure

### Core Tests (test_core.py)
- Data model creation and validation
- Correlation engine functionality
- Diagnostic checks execution

### API Tests (test_api.py)
- Kernel32 API initialization
- PSAPI functions
- Registry access
- Service enumeration

### Application Tests (test_apps.py)
- Process Explorer functionality
- Performance Monitor initialization
- Services Manager features
- Dashboard module loading

## Manual Testing

### Test Process Explorer
```bash
python -m apps.windows.apps.process_explorer
> tree
> ps
> select 1234
> info
```

### Test Memory Monitor
```bash
python -m apps.windows.apps.memory_monitor
> status
> memory
> top 10
> leaks
```

### Test Network Diagnostics
```bash
python -m apps.windows.apps.network_diagnostics
> connections
> ports
> suspicious
> firewall_rules
```

### Test Services Manager
```bash
python -m apps.windows.apps.services_manager
> services running
> drivers
> search spooler
> unsigned
```

### Test Registry Viewer
```bash
python -m apps.windows.apps.registry_viewer
> hive HKEY_LOCAL_MACHINE
> cd Software\Microsoft
> ls
> find_key Run
> find_value Windows
```

### Test Dashboard
```bash
python -m apps.windows.apps.dashboard
> overview
> modules
> status
```

## Test Requirements

- Windows 7+
- Python 3.8+
- Administrative privileges for some tests
- pytest (optional, for advanced testing)

## Continuous Integration

Run full test suite:
```bash
python -m unittest discover tests/ -v
```

## Known Limitations

- Some tests require administrative privileges
- Network tests may fail in restricted environments
- Registry tests depend on user permissions
- Security tests may trigger antivirus alerts

## Troubleshooting

**Import Errors:**
- Ensure PYTHONPATH includes workspace root
- Check all __init__.py files are present

**Permission Errors:**
- Run tests as Administrator
- Check registry permissions

**Timeout Errors:**
- Increase timeout values for slow systems
- Check system load
