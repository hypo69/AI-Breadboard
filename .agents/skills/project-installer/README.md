# Project Installer Skill

Package containing the interactive project installer skill for AI Breadboard.

## Overview
This skill empowers AI models running via Gemini CLI (`gemini --model "gemini-3.1-flash-lite"`) or Antigravity to perform end-to-end installation of the AI Breadboard repository, handle platform-specific environment settings, resolve installation errors interactively, and verify that all system directories and dependencies are installed.

## Directory Structure
```
.agents/skills/project-installer/
├── README.md                     # Package documentation
├── SKILL.md                      # Agent skill definition and execution protocol
├── INSTALL-INSTRUCTION.md        # Comprehensive installation rules and diagnostics
└── scripts/
    ├── verify_installation.py    # Directory & dependency verification tool
    ├── run_installer_gemini.ps1  # Windows PowerShell Gemini CLI launcher
    └── run_installer_gemini.sh   # Linux/macOS Bash Gemini CLI launcher
```

## Usage
Run the verification tool:
```powershell
python .agents/skills/project-installer/scripts/verify_installation.py
```

Run interactive installation via Gemini CLI:
```powershell
.\.agents\skills\project-installer\scripts\run_installer_gemini.ps1
```
