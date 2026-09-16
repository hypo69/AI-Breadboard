"""Dashboard CLI."""
import cmd
import sys
from textwrap import dedent
from .dashboard import Dashboard

class DashboardCLI(cmd.Cmd):
    """Central dashboard CLI."""
    intro = dedent("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║          Windows Diagnostic Dashboard                        ║
    ║         Integrated System Monitoring Interface               ║
    ║                  Type 'help' for commands                    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    prompt = "dashboard> "

    def __init__(self):
        super().__init__()
        self.dashboard = Dashboard()

    def do_overview(self, arg):
        """Show system overview."""
        overview = self.dashboard.get_system_overview()
        print("\nSystem Overview:")
        print(f"  Timestamp: {overview['timestamp']}")
        print(f"  Modules Loaded: {overview['modules_loaded']}")
        print(f"  Status: {overview['process_explorer']}")

    def do_modules(self, arg):
        """List all modules."""
        modules = self.dashboard.list_modules()
        print("\nAvailable Modules:")
        for name, cls in modules.items():
            print(f"  - {name}: {cls}")

    def do_processes(self, arg):
        """Access Process Explorer."""
        module = self.dashboard.get_module('processes')
        if module:
            print("Process Explorer available")
        else:
            print("Process Explorer not loaded")

    def do_performance(self, arg):
        """Access Performance Monitor."""
        module = self.dashboard.get_module('performance')
        if module:
            print("Performance Monitor available")
        else:
            print("Performance Monitor not loaded")

    def do_network(self, arg):
        """Access Network Diagnostics."""
        module = self.dashboard.get_module('network')
        if module:
            print("Network Diagnostics available")
        else:
            print("Network Diagnostics not loaded")

    def do_services(self, arg):
        """Access Services Manager."""
        module = self.dashboard.get_module('services')
        if module:
            print("Services Manager available")
        else:
            print("Services Manager not loaded")

    def do_status(self, arg):
        """Show dashboard status."""
        print("\n" + "="*60)
        print("SYSTEM DIAGNOSTICS DASHBOARD STATUS")
        print("="*60)
        overview = self.dashboard.get_system_overview()
        for key, value in overview.items():
            print(f"{key.upper():<30} {value}")
        print("="*60)

    def do_exit(self, arg):
        """Exit dashboard."""
        print("Exiting Dashboard...")
        return True

    def do_quit(self, arg):
        """Quit dashboard."""
        return self.do_exit(arg)

def main():
    try:
        cli = DashboardCLI()
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
