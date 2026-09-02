# 📦 AI Breadboard Cross-Platform Installation Instructions

This document specifies the exact installation lifecycle, platform rules, prerequisite validations, configuration steps, and troubleshooting remedies for **AI Breadboard** on Windows, Linux, and macOS.

> [!NOTE]
> This instruction is used by the **`project-installer`** AI agent skill (`.agents/skills/project-installer/SKILL.md`) and by humans for manual or automated installation.

---

## 🎯 Architecture & Guiding Principles

1. **Host-Native Execution:** Everything runs natively in a dedicated Python virtual environment (`venv`).
2. **Platform Scripts Baseline:** 
   - Windows execution and environment rules are governed by [`install.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install.ps1) and modular scripts in [`install/`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install).
   - Linux and macOS execution rules are governed by [`install.sh`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install.sh) and [`install/install.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install/install.py).
3. **Configuration over Hardcoding:** System parameters are read from `config.json` and secrets from `.env`.
4. **Cross-Platform Parity:** Core installation logic is unified across Windows (PowerShell/CMD) and Linux/macOS (Bash/Python).
5. **Resilient Self-Healing:** Any failure during dependency installation, SSL generation, or path configuration must trigger diagnostic checks and automated remedy steps.

---

## 🏗️ Phase 1: Pre-Flight Environment Inspection

### 1.1 Operating System & Architecture Detection
- **Windows:** Check Windows 10/11 x64, PowerShell 5.1+ or PowerShell 7+ (`$PSVersionTable`).
- **Linux:** Check distribution (Ubuntu/Debian, Fedora/RHEL, Arch, openSUSE) via `/etc/os-release`.
- **macOS:** Check Darwin kernel version and Apple Silicon / Intel architecture (`uname -m`).

### 1.2 Python Interpreter Discovery & Validation
- **Requirement:** Python 3.10 to 3.14 (Recommended: 3.12 or 3.13).
- **Windows:** 
  - Probe via `py -3.13`, `py -3.12`, `py -3.11`, `py -3`, `python.exe`.
  - Avoid Windows Store 0-byte execution aliases (`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe` without real installation).
- **Linux / macOS:**
  - Probe via `python3.13`, `python3.12`, `python3.11`, `python3.10`, `python3`, `python`.
  - Validate package headers (`python3-dev` / `python3-devel`) and virtual environment support (`python3-venv`).

---

## 🚀 Phase 2: Step-by-Step Installation Lifecycle

### Step 1: File Permission & Unblock (Windows Only)
On Windows, downloaded PowerShell scripts may be marked as blocked by the Zone identifier (per `install.ps1` step 1):
```powershell
Get-ChildItem -Path $InstallDir -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    Unblock-File -ErrorAction SilentlyContinue
```

### Step 2: Virtual Environment Creation (`venv`)
- Target location: `<ProjectRoot>/venv`
- Windows command: `& $PythonExe -m venv "$InstallDir\venv"`
- Linux / macOS command: `"$PYTHON" -m venv "$PROJECT_ROOT/venv"`
- **Self-Healing:** If `venv` creation fails on Linux with `ensurepip` error:
  - Ubuntu/Debian: `sudo apt-get install python3-venv python3-pip -y`
  - Fedora: `sudo dnf install python3-venv python3-pip -y`

### Step 3: Base Tooling Upgrade (`pip`, `setuptools`, `wheel`)
Upgrade core packaging tools inside the virtual environment:
- Windows: `& "$InstallDir\venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel`
- Linux/macOS: `"$PROJECT_ROOT/venv/bin/python" -m pip install --upgrade pip setuptools wheel`

### Step 4: Dependency Profiles Installation
Users can select their desired dependency profile:

| Profile | Description | Target Requirements Files |
|---|---|---|
| **1 (Full - Recommended)** | Full AI Breadboard suite (Core + AI + Utils) | `requirements.txt` |
| **2 (Core Only)** | Minimal lightweight server | `install/req/requirements-core.txt` |
| **3 (Core + AI)** | Server + AI Providers (Ollama, Gemini, Foundry) | `install/req/requirements-core.txt`, `install/req/requirements-ai.txt` |
| **4 (Full + Dev)** | Full suite + Tests + Docs | `requirements.txt`, `install/req/requirements-test.txt`, `install/req/requirements-docs.txt` |
| **5 (Skip)** | Skip dependency installation | None |

Installation command:
```bash
python -m pip install -r <requirements_file>
```

### Step 5: SSL Certificate Generation (HTTPS Support)
Generate local development SSL certificates for `localhost`, `127.0.0.1`, and local network IP:
- Windows: `.\install_ssl_cert.ps1`
- Python cross-platform: `python scripts/cli/install_ssl_certs.py` or fallback self-signed certificate generation via `cryptography`.

### Step 6: Global CLI Registration (`assist` & Environment Variables)
1. Set persistent user environment variable:
   - `AIBREADBOARD_DIR = <ProjectRoot>`
   - `ASSIST_DIR = <ProjectRoot>`
   - `PYTHONUTF8 = 1`
2. Create `assist.ps1`, `assist.cmd`, and `assist` (Bash wrapper).
3. Copy wrappers to `%USERPROFILE%\.local\bin` (Windows) or `~/.local/bin` / `/usr/local/bin` (Linux/macOS).
4. Add directory to user `PATH`.
5. Register helper functions in PowerShell profiles (`$PROFILE`) and shell rc files (`~/.bashrc`, `~/.zshrc`).

### Step 7: Configuration & Verification
1. Ensure `.env` is initialized (copy `.env.example` if `.env` does not exist).
2. Save language and default settings into `config.json`.
3. Verify importability of core packages: `fastapi`, `uvicorn`, `dotenv`, `pydantic`, `cryptography`, `aiohttp`, `platformdirs`.

---

## 🔍 Phase 3: Post-Installation Directory & Component Test

Run the verification test script to ensure complete structural and environment integrity:
```powershell
# Run verification script
python .agents/skills/project-installer/scripts/verify_installation.py

# Or via pytest
pytest tests/test_project_installer.py -v
```

### Required Directories Verified:
- `core/` (AI providers, routing, services, logger, database)
- `scripts/` (CLI tools, helpers, dev scripts)
- `install/` (Installer scripts and requirement manifests)
- `launchers/` (Unified launchers, Unicorn, Foundry, LightServer)
- `docs/` (System documentation)
- `tests/` (Test suite)
- `webinterface/` (Web frontend & static UI assets)
- `.ai/` (Rules, knowledge, architecture standards)
- `.agents/skills/` (Registered agent skills)
- `tmp/` & `logs/` (Logging & runtime scratchpad)
- `venv/` (Virtual environment)

### Required Core Files Verified:
- `header.py` (Root anchor & metadata)
- `config.json` (System configuration)
- `.env` or `.env.example` (Secrets declaration)
- `requirements.txt` (Main package dependencies)
- `assist.ps1` / `assist.cmd` / `assist` (CLI launchers)

---

## 🛠️ Phase 4: Troubleshooting & Self-Healing Matrix

| Symptom / Error | Root Cause | Automated Self-Healing Remedy |
|---|---|---|
| `running scripts is disabled on this system` (Windows) | ExecutionPolicy is Restricted | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force` |
| `No module named venv` (Ubuntu/Debian) | Python venv package not installed | Run `sudo apt-get install python3-venv python3-pip -y` |
| `Microsoft Visual C++ 14.0 or greater is required` | Missing compilation headers for binary wheels | Install pre-compiled wheel via `pip install --only-binary :all: <pkg>` or install build tools |
| `Port 8000 already in use` | Stray Uvicorn/FastAPI process | Run `assist stop` or terminate PID using `netstat -ano \| findstr :8000` / `lsof -i :8000` |
| `SSL certificate generation failed: mkcert not found` | `mkcert` binary not in PATH | Fallback to Python `cryptography` x509 self-signed certificate generator script |
| `Command assist not recognized` | `%USERPROFILE%\.local\bin` not in PATH | Add `%USERPROFILE%\.local\bin` to user PATH environment variable and restart terminal |
