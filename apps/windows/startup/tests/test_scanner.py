"""Тесты сканера автозапуска StartupScanner."""
from apps.windows.startup.core.models import StartupLocationType
from apps.windows.startup.core.scanner import StartupScanner

def test_monitored_locations_list() -> None:
    """Проверка возврата списка контролируемых точек автозапуска."""
    scanner = StartupScanner()
    locations = scanner.get_monitored_locations()
    assert len(locations) >= 8
    location_types = [loc.location_type for loc in locations]
    assert StartupLocationType.REGISTRY_RUN in location_types
    assert StartupLocationType.STARTUP_FOLDER_USER in location_types
    assert StartupLocationType.IFEO in location_types
    assert StartupLocationType.WINLOGON in location_types

def test_parse_command_line() -> None:
    """Проверка парсинга исполняемого пути и аргументов из командной строки."""
    scanner = StartupScanner()
    exe, args = scanner._parse_command_line('"C:\\Program Files\\App\\app.exe" /minimized --autostart')
    assert exe == 'C:\\Program Files\\App\\app.exe'
    assert args == '/minimized --autostart'
    exe2, args2 = scanner._parse_command_line('C:\\Windows\\notepad.exe C:\\test.txt')
    assert exe2 == 'C:\\Windows\\notepad.exe'
    assert args2 == 'C:\\test.txt'
    exe3, args3 = scanner._parse_command_line('')
    assert exe3 == ''
    assert args3 == ''

def test_scan_all_returns_entries() -> None:
    """Проверка выполнения полного сканирования на текущей хост-системе."""
    scanner = StartupScanner()
    entries = scanner.scan_all()
    assert isinstance(entries, list)
    for e in entries:
        assert e.id
        assert e.name
        assert e.location_type