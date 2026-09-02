---
name: project-installer
description: Interactive full-project installer and environment configurator for AI Breadboard. Guides through pre-flight checks, venv creation, dependency installation, SSL certs, global CLI setup, error self-healing, and post-installation directory verification.
---

# 🚀 AI Breadboard Project Installer Skill

This skill enables AI agents and Gemini CLI (using `gemini-3.1-flash-lite`) to interactively install, configure, troubleshoot, and verify the entire **AI Breadboard** project across Windows, Linux, and macOS.

---

## 💻 Invoking via Gemini CLI

To launch the installer interactively with Gemini CLI and the requested model:

```powershell
# Windows (PowerShell)
gemini --model "gemini-3.1-flash-lite" --prompt "Execute the project-installer skill. Read INSTALL-INSTRUCTION.md and guide me through full AI Breadboard installation interactively with error checks and directory verification."

# Or using the launcher script:
.\.agents\skills\project-installer\scripts\run_installer_gemini.ps1
```

```bash
# Linux / macOS (Bash)
gemini --model "gemini-3.1-flash-lite" --prompt "Execute the project-installer skill. Read INSTALL-INSTRUCTION.md and guide me through full AI Breadboard installation interactively with error checks and directory verification."

# Or using the launcher script:
bash .agents/skills/project-installer/scripts/run_installer_gemini.sh
```

---

## 📖 Mandatory Reference

Before executing any installation step, the agent **MUST** inspect:
- [INSTALL-INSTRUCTION.md](file:///c:/Users/onela/AppData/Local/AI-Breadboard/.agents/skills/project-installer/INSTALL-INSTRUCTION.md) (Skill copy) or [INSTALL-INSTRUCTION.md](file:///c:/Users/onela/AppData/Local/AI-Breadboard/INSTALL-INSTRUCTION.md) (Root copy).
- Windows baseline: [`install.ps1`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install.ps1) and [`install/`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install).
- Linux / macOS baseline: [`install.sh`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install.sh), [`install/install.sh`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/install/install.sh), and [`INSTALL_LINUX.md`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/INSTALL_LINUX.md).

---

## 🤖 Agent Execution Protocol (Interactive Mode)

When this skill is activated, the model must execute the following workflow step-by-step, asking the user for choices where needed and diagnosing failures:

### Phase 1: Pre-Flight Environment Inspection
1. Detect host OS (`platform.system()`) and architecture.
2. Probe available Python interpreters:
   - Must be Python 3.10+ (Preferred: 3.12 / 3.13).
   - On Windows: ensure Python is in PATH, avoid Microsoft Store execution aliases (`WindowsApps\python.exe`).
   - On Linux/macOS: check `python3-venv` and development headers.
3. Check Git presence and internet connectivity for dependency fetching.

### Phase 2: Interactive Installation Steps
Follow the platform rules derived from `install.ps1` and `install.sh`:

1. **Language & Configuration Selection:**
   - Ask user for interface language (`ru`, `en`, `es`, `he`).
   - Confirm target installation directory (Default: `%LOCALAPPDATA%\AI Breadboard` on Windows, current directory or `/opt/ai-breadboard` on Linux).

2. **File Permissions & Unblock (Windows):**
   - Execute `Unblock-File` on project PowerShell scripts.

3. **Virtual Environment Setup:**
   - Check if `venv/` exists. If not, create via `python -m venv venv`.
   - Validate `<project_root>/venv/Scripts/python.exe` (Windows) or `<project_root>/venv/bin/python` (Linux/macOS).

4. **Tooling & Dependencies Installation:**
   - Upgrade `pip`, `setuptools`, `wheel`.
   - Present profile choice to user:
     - `1`: Full installation (`requirements.txt`) — Recommended
     - `2`: Core only (`install/req/requirements-core.txt`)
     - `3`: Core + AI (`requirements-core.txt` + `requirements-ai.txt`)
     - `4`: Full + Dev (`requirements.txt` + test & docs requirements)
     - `5`: Skip
   - Run `pip install` and monitor output for errors.

5. **SSL Certificates Setup:**
   - Check for `localhost+2.pem` and `localhost+2-key.pem`.
   - Run `install_ssl_cert.ps1` or Python certificate generator if missing.

6. **Environment & Secrets (`.env`):**
   - Ensure `.env` exists (copy from `.env.example` if absent).
   - Check key variables: `GEMINI_API_KEY_NAMES`, `JWT_SECRET`, `AIBREADBOARD_DIR`.

7. **Global CLI Integration (`assist`):**
   - Verify `assist.ps1`, `assist.cmd`, and `assist` wrappers.
   - Set persistent `AIBREADBOARD_DIR` environment variable.
   - Add `%USERPROFILE%\.local\bin` or `~/.local/bin` to `PATH`.

---

## 🛠️ Dynamic Error Checking & Self-Healing Matrix

During execution, if any command fails, the model must match the error against the matrix and apply the remedy before continuing:

| Error Pattern | Identified Issue | Dynamic Self-Healing Action |
|---|---|---|
| `running scripts is disabled` | Windows PowerShell ExecutionPolicy | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force` |
| `ensurepip is not available` / `No module named venv` | Missing Linux venv package | Prompt user to run `sudo apt-get install python3-venv python3-pip -y` (or run if permitted) |
| `Permission denied` | Missing Linux/macOS executable bit | Run `chmod +x install.sh assist run` |
| `Failed building wheel for ...` | Missing C++ build tools | Retry with `--only-binary :all:` or suggest Visual C++ Build Tools / `build-essential` |
| `Address already in use :8000` | Port conflict | Identify PID with `assist status` / `netstat -ano` and terminate or execute `assist stop` |
| `mkcert: command not found` | Missing mkcert binary | Fallback to internal Python self-signed certificate generator |

---

## 🧪 Post-Installation Directory & Component Verification

After completing installation, the agent **MUST** run the automated verification tool to prove that all directories and modules are valid:

```powershell
# Execute verification tool
python .agents/skills/project-installer/scripts/verify_installation.py

# Or with JSON output for automated agent parsing:
python .agents/skills/project-installer/scripts/verify_installation.py --json
```

### Verification Checklist:
- [ ] Required directories: `core/`, `scripts/`, `install/`, `launchers/`, `docs/`, `tests/`, `webinterface/`, `.ai/`, `.agents/skills/`, `tmp/`, `venv/`.
- [ ] Core configuration files: `header.py`, `config.json`, `.env`/`.env.example`, `requirements.txt`, `INSTALL-INSTRUCTION.md`.
- [ ] Virtual environment binaries and pip availability.
- [ ] Importability of `fastapi`, `uvicorn`, `pydantic`, `dotenv`, `cryptography`, `aiohttp`, `platformdirs`.
- [ ] Exit code is `0`.
