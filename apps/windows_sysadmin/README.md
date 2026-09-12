# Windows System Administrator Dashboard

**Status:** ✅ Active  
**Language:** English  
**Authors:** hypo69  

---

## 📋 Overview

The Windows System Administrator application provides comprehensive Windows system administration capabilities, including Active Directory management, user session monitoring, security event tracking, group policy administration, and real-time system health monitoring.

This application supports **dual-mode operation**:
- **Integrated Mode**: Runs as part of the main AI-Breadboard FastAPI application
- **Standalone Mode**: Runs as an independent FastAPI server for isolated deployments

---

## 🎯 Features

### Dual-Mode Architecture
- **Integrated Mode**: Part of main AI-Breadboard FastAPI application (/api/v1/windows-admin/*)
- **Standalone Mode**: Independent FastAPI server for isolated deployments or testing

### Core Capabilities

- **System Information Dashboard**
  - Real-time hostname and domain status
  - Active Directory connectivity monitoring
  - System uptime and performance metrics

- **User Session Management**
  - Active user sessions list with login times
  - Session ID tracking
  - IP address and connection information
  - Process count per session
  - Idle time detection

- **Security Event Monitoring**
  - Real-time Windows Security Event Log ingestion
  - Event ID categorization (4624, 4688, 4720, etc.)
  - Severity level filtering (Critical, Warning, Information)
  - Event source identification

- **Active Directory Integration**
  - Domain structure visualization
  - User and group enumeration
  - Computer account management
  - Group Policy object inspection
  - Security policy verification

- **Interactive Terminal UI**
  - Rich-based responsive dashboard
  - Real-time system metrics
  - Hotkey controls for navigation
  - Color-coded alerts

---

## 🚀 Usage

### Option 1: Integrated Mode (via main FastAPI application)

When running the main AI-Breadboard server, Windows System Administrator is automatically available:

```bash
# Start main AI-Breadboard server
python main.py

# Access admin panel at: http://localhost:8000/admin
# Windows Admin API endpoints: /api/v1/windows-admin/*
# API docs: http://localhost:8000/docs
```

### Option 2: Standalone Server Mode

Run Windows System Administrator as an independent FastAPI server:

```bash
# Start as standalone FastAPI server (default: localhost:8001)
python -m apps.windows_sysadmin --mode server

# Run on all interfaces (0.0.0.0) for external access
python -m apps.windows_sysadmin --mode server --host 0.0.0.0 --port 8001

# Run with auto-reload for development
python -m apps.windows_sysadmin --mode server --reload

# Run with multiple workers
python -m apps.windows_sysadmin --mode server --workers 4
```

Server will be available at:
- API: `http://localhost:8001/`
- API Docs (Swagger): `http://localhost:8001/docs`
- Alternative Docs (ReDoc): `http://localhost:8001/redoc`

### Option 3: Interactive Dashboard (Terminal UI)

Launch the interactive Rich-based dashboard:

```bash
python -m apps.windows_sysadmin --mode dashboard --interval 2.0
```

Options:
- `--interval` / `-i`: Dashboard refresh interval in seconds (default: 2.0)

### Quick Commands

```bash
# Check Active Directory connectivity
python -m apps.windows_sysadmin --ad-status

# Display security events from last 24 hours
python -m apps.windows_sysadmin --security-events --hours 24

# Get JSON output of security events
python -m apps.windows_sysadmin --security-events --json

# Audit users in domain
python -m apps.windows_sysadmin --audit users --domain CONTOSO

# Audit groups
python -m apps.windows_sysadmin --audit groups

# Audit computers
python -m apps.windows_sysadmin --audit machines

# Audit group policies
python -m apps.windows_sysadmin --audit policies
```

---

## 📊 Dashboard Components

### Top Panel: System Information
- **Hostname**: Computer name
- **Domain**: Active Directory domain
- **AD Status**: Connection status with visual indicator
- **Uptime**: System uptime in hours

### Left Panel: User Sessions
Table displaying:
- Username
- Session Status (Active/Idle)
- Session ID
- Login timestamp
- IP address
- Active process count

### Right Panel: Security Events
Recent security events with:
- Timestamp
- Event ID (Windows Event Log ID)
- Severity level (color-coded)
- Event source
- Description

### Bottom Right: Active Directory Structure
Tree visualization showing:
- Domain hierarchy
- User container
- Groups container
- Computer accounts
- Group Policy Objects
- Security settings

---

## 🔧 Architecture

### Module Structure

```
windows_sysadmin/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point with dual-mode support
├── router.py            # FastAPI router re-export
├── tui.py               # Interactive dashboard UI
└── README.md            # Documentation
```

### CLI Entry Point (`__main__.py`)

Supports three operational modes:

1. **Dashboard Mode** (default)
   - Interactive Rich-based TUI
   - Real-time system monitoring
   - Terminal-based interface

2. **Server Mode** (`--mode server`)
   - Standalone FastAPI application
   - REST API endpoints
   - WebSocket support
   - Uvicorn server

3. **Command Mode** (one-shot operations)
   - `--ad-status`: Check connectivity
   - `--security-events`: Display events
   - `--audit`: Perform audits
   - `--json`: JSON output

### Interactive UI (`tui.py`)

Built with the Rich library, featuring:
- `SystemAdminState`: Core state management
- `UserSession`: User session representation
- `SecurityEvent`: Security event model
- Layout panels for organized information display
- Real-time data refresh

### FastAPI Integration (`router.py`)

Exposes endpoints under `/api/v1/windows-admin/`:
- `GET /status`: System status
- `GET /sessions`: Active user sessions
- `GET /events`: Security events
- `GET /ad/users`: Active Directory users
- `GET /ad/groups`: Active Directory groups
- `GET /ad/computers`: Domain computers
- `GET /gpo`: Group Policy objects
- `POST /command/lock-session`: Lock user session
- `POST /command/logoff-session`: Log off session
- `POST /command/restart-computer`: Schedule restart
- `WebSocket /stream`: Real-time event stream

---

## 💻 Command Line Options

```
Usage: python -m apps.windows_sysadmin [OPTIONS]

Options:
  -m, --mode {dashboard|audit|ad-check|security|users|server}
                        Operation mode (default: dashboard)
  
  --audit {users|groups|machines|policies}
                        Audit target type
  
  -d, --domain DOMAIN   Active Directory domain name
  
  --ad-status          Check AD connectivity and exit
  
  --security-events    Show security events
  
  --hours HOURS        Hours lookback for events (default: 24)
  
  --json               Output as JSON
  
  -i, --interval SECS  Dashboard refresh interval (default: 2.0)
  
  --host HOST          Server bind address (default: 127.0.0.1)
  
  -p, --port PORT      Server bind port (default: 8001)
  
  --reload             Enable auto-reload (development only)
  
  --workers N          Number of Uvicorn workers (default: 1)
  
  -h, --help          Show help message
```

---

## 🛠️ Development

### Adding New Features

1. **System Information**: Extend `SystemAdminState` dataclass in `tui.py`
2. **UI Components**: Add new rendering functions in `tui.py`
3. **CLI Commands**: Update argument parser in `__main__.py`
4. **API Endpoints**: Extend `router_windows_admin.py` in `src/fastapi/`

### Dependencies

- `rich`: Terminal UI rendering
- `fastapi`: REST API framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `pywin32` (optional): Windows-specific APIs for deeper integration

---

## 🔐 Security Considerations

- **Privilege Requirements**: Some operations require Administrator privileges
- **Event Log Access**: May require specific permissions for Security Event Log
- **Active Directory**: Requires network connectivity to domain controller
- **Sensitive Data**: User sessions and events may contain sensitive information
- **Standalone Mode**: When running standalone, ensure proper firewall configuration

---

## 📝 Keyboard Controls

| Key | Action |
|-----|--------|
| `Q` | Quit dashboard |
| `U` | Focus user sessions panel |
| `E` | Focus security events panel |
| `A` | Focus Active Directory info |
| `R` | Manual refresh |
| `←/→` | Navigate between panels |

---

## 🧪 Testing

### Test Integrated Mode
```bash
python main.py
# Navigate to http://localhost:8000/admin
# Check /api/v1/windows-admin/ endpoints
```

### Test Standalone Mode
```bash
python -m apps.windows_sysadmin --mode server
# Visit http://localhost:8001/docs
# Try API endpoints
```

### Test CLI Checks
```bash
python -m apps.windows_sysadmin --ad-status
python -m apps.windows_sysadmin --security-events --json
```

### Test Interactive Dashboard
```bash
python -m apps.windows_sysadmin
# Interactive TUI should appear
# Press 'Q' to exit
```

---

## 📚 References

- [Windows Event IDs](https://docs.microsoft.com/en-us/windows/security/threat-protection/auditing/audit-policy-recommendations)
- [Active Directory Schema](https://docs.microsoft.com/en-us/windows/win32/adsi/active-directory-objects)
- [PyWin32 Documentation](https://pypi.org/project/pywin32/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- PowerShell integration for advanced admin tasks
- Real-time group policy application monitoring
- DHCP and DNS management UI
- Server role and feature management
- Firewall rule inspection and management
- Event log export and analysis
- Bulk user/group operations

---

## 📋 Deployment Scenarios

### Scenario 1: Enterprise Integrated Deployment
```bash
# Run main AI-Breadboard server
python main.py
# Windows Admin available as one of multiple applications
# Shared authentication and session management
```

### Scenario 2: Isolated Windows Admin Server
```bash
# Run standalone on dedicated port
python -m apps.windows_sysadmin --mode server --host 0.0.0.0 --port 8001
# Independent deployment, no dependencies on main server
```

### Scenario 3: Development/Testing
```bash
# Run with auto-reload
python -m apps.windows_sysadmin --mode server --reload
# Rapid development iteration
```

### Scenario 4: Terminal-Only Environment
```bash
# Run interactive dashboard without web browser
python -m apps.windows_sysadmin --mode dashboard
# TUI interface in terminal
```

---

**Last Updated:** 2026-09-12  
**Maintainer:** hypo69  
**Version:** 1.0.0
