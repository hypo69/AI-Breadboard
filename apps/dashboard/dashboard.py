"""Dashboard aggregating all monitoring tools."""
from typing import Dict, Any

class Dashboard:
    """Central dashboard for system diagnostics."""

    def __init__(self):
        self.modules = {}
        self._init_modules()

    def _init_modules(self) -> None:
        """Initialize all diagnostic modules."""
        try:
            from apps.process_explorer import ProcessExplorerUI
            from apps.memory_monitor import PerformanceMonitor
            from apps.network_diagnostics import NetworkDiagnostics
            from apps.services_manager import ServicesManager
            from apps.windows.registry import RegistryViewer
            from apps.security_analyzer import SecurityAnalyzer
            from apps.hardware_explorer import HardwareExplorer
            from apps.baseline_detector import BaselineDetector
            from apps.realtime_monitor import RealtimeMonitor

            self.modules = {
                'processes': ProcessExplorerUI(),
                'performance': PerformanceMonitor(),
                'network': NetworkDiagnostics(),
                'services': ServicesManager(),
                'registry': RegistryViewer(),
                'security': SecurityAnalyzer(),
                'hardware': HardwareExplorer(),
                'baseline': BaselineDetector(),
                'realtime': RealtimeMonitor(),
            }
        except Exception as e:
            print(f"Error initializing modules: {e}")

    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview from all modules."""
        overview = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'modules_loaded': len(self.modules),
            'process_explorer': 'Ready' if 'processes' in self.modules else 'N/A',
            'memory_monitor': 'Ready' if 'performance' in self.modules else 'N/A',
            'network': 'Ready' if 'network' in self.modules else 'N/A',
            'services': 'Ready' if 'services' in self.modules else 'N/A',
        }
        return overview

    def get_module(self, name: str) -> Any:
        """Get specific module."""
        return self.modules.get(name)

    def list_modules(self) -> Dict[str, str]:
        """List all available modules."""
        return {name: type(module).__name__ for name, module in self.modules.items()}
