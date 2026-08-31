# ~installer

Web-based installer for AI Breadboard. Provides a browser UI for guided installation, Python detection, and environment setup.

## Structure

```
~installer/
├── server/          — FastAPI mini-server serving the installer UI
│   ├── main.py      — Server entry point and API routes
│   └── __init__.py
├── services/        — Business logic for installation steps
│   ├── environment_manager.py  — Virtual environment creation and management
│   ├── python_detector.py      — Python interpreter detection across platforms
│   └── python_installer.py     — Automated Python installation helpers
├── web/
│   └── index.html   — Single-page installer UI
├── install.ps1      — PowerShell bootstrap that launches this installer
├── install.py       — Python entry point
└── installer.json   — Installer configuration and step definitions
```

## Usage

```powershell
# Launch the web installer
python ~installer/install.py
```

The installer opens a local browser page guiding the user through Python detection, venv creation, and dependency installation.

## Related

- `install/` — Module-based PowerShell installer (primary installer for Windows)
- `scripts/cli/installer.py` — Cross-platform CLI installer
