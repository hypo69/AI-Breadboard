# 🚀 AI Breadboard Installation Guide

## Quick Start

### Windows
```powershell
# Option 1: PowerShell (native)
.\install.ps1

# Option 2: Python (universal)
python install.py
```

### Linux / macOS
```bash
# Option 1: Bash (native)
bash install.sh

# Option 2: Python (universal)
python install.py
```

---

## Installation Methods Comparison

| Feature | Python | Bash | PowerShell |
|---------|--------|------|------------|
| **Platform** | All | Linux/macOS | Windows |
| **Dependencies** | Python 3.10+ | Bash 4+ | PowerShell 5.1+ |
| **Multilingual** | ✅ RU/EN/ES/HE | ✅ RU/EN/ES | ✅ RU/EN/ES/HE |
| **Remote Bootstrap** | ❌ | ❌ | ✅ |
| **Native Integration** | ⚠️ | ✅ | ✅ |
| **Code Size** | ~400 lines | ~300 lines | ~1000 lines |

---

## Supported Languages

All installers support the following languages:

- 🇷🇺 **Русский** (Russian) — `ru`
- 🇬🇧 **English** — `en`
- 🇪🇸 **Español** (Spanish) — `es`
- 🇮🇱 **עברית** (Hebrew) — `he`

Language selection is interactive during installation.

---

## Installation Profiles

All installers offer the same dependency profiles:

| Profile | Contents | Use Case |
|---------|----------|----------|
| **1** (Default) | Core + AI + Utils | Full-featured setup |
| **2** | Core only | Minimal server |
| **3** | Core + AI | Server + AI models |
| **4** | Full + Dev | Development environment |
| **5** | Skip | Manual setup |

---

## Python Installer (`install.py`)

### Basic Usage
```bash
python install.py
```

### With Options
```bash
python install.py --language en --install-dir /opt/ai-breadboard
```

### Features
- ✅ Cross-platform (Windows/Linux/macOS)
- ✅ Automatic Python discovery (3.13, 3.12, 3.11, 3.10)
- ✅ Virtual environment creation
- ✅ Dependency installation with profile selection
- ✅ Environment verification
- ✅ Multilingual output

### Code Structure
```python
class Installer:
    - find_python()      # Discover Python interpreter
    - create_venv()      # Create virtual environment
    - upgrade_pip()      # Update pip and tools
    - install_dependencies()  # Install packages
    - verify_environment()    # Verify installation
    - run()              # Main installation flow
```

---

## Bash Installer (`install.sh`)

### Basic Usage
```bash
bash install.sh
```

### With Options
```bash
bash install.sh --language ru --install-dir ~/ai-breadboard
```

### Features
- ✅ Native Unix shell integration
- ✅ Lightweight (no Python required)
- ✅ Color-coded output
- ✅ Automatic Python discovery
- ✅ Multilingual support

### Functions
```bash
select_language()        # Interactive language selection
find_python()           # Discover Python interpreter
create_venv()           # Create virtual environment
upgrade_pip()           # Update pip and tools
install_dependencies()  # Install packages
verify_environment()    # Verify installation
main()                  # Main installation flow
```

---

## PowerShell Installer (`install.ps1`)

### Basic Usage
```powershell
.\install.ps1
```

### Remote Bootstrap
```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install/install.ps1 | iex
```

### Features
- ✅ Native Windows integration
- ✅ Automatic PATH management
- ✅ PowerShell profile injection
- ✅ Full multilingual support
- ✅ Remote execution support

---

## Troubleshooting

### Python Not Found
**Error:** `Python not found. Install Python 3.10+`

**Solution:**
1. Install Python from https://www.python.org/downloads/
2. Ensure "Add python.exe to PATH" is checked during installation
3. Restart terminal and try again

### Permission Denied (Linux/macOS)
**Error:** `Permission denied: ./install.sh`

**Solution:**
```bash
chmod +x install.sh
bash install.sh
```

### Virtual Environment Creation Failed
**Error:** `Failed to create virtual environment`

**Solution:**
```bash
# Ensure venv module is available
python -m venv --help

# If missing, install python3-venv (Linux)
sudo apt-get install python3-venv
```

### Dependency Installation Failed
**Error:** `pip install failed`

**Solution:**
1. Check internet connection
2. Try profile 2 (Core only) for minimal setup
3. Install manually: `pip install -r requirements.txt`

---

## Environment Variables

After installation, the following environment variables are set:

| Variable | Purpose | Example |
|----------|---------|---------|
| `AIBREADBOARD_DIR` | Project root directory | `/opt/ai-breadboard` |
| `ASSIST_DIR` | Assistant directory | `/opt/ai-breadboard` |
| `PYTHONUTF8` | UTF-8 encoding | `1` |

---

## Next Steps

After successful installation:

1. **Start the server:**
   ```bash
   python -m scripts.dev.assist_cli start
   ```

2. **Access the web interface:**
   ```
   http://localhost:8000
   ```

3. **Configure AI models:**
   - Edit `config.json` for model settings
   - Set API keys in `.env` file

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

---

## Architecture Notes

### Multilingual System (I18N)
All installers use a unified message dictionary system:

```python
# Python
MESSAGES = {
    "ru": {"step_1": "..."},
    "en": {"step_1": "..."},
    ...
}

# Bash
declare -A MESSAGES_RU=(...)
declare -A MESSAGES_EN=(...)
```

### Cross-Platform Path Handling
- **Windows:** `venv\Scripts\python.exe`
- **Linux/macOS:** `venv/bin/python`

### Dependency Profiles
All installers support the same profiles:
- Profile 1: `requirements.txt`
- Profile 2: `install/req/requirements-core.txt`
- Profile 3: Core + AI requirements
- Profile 4: Full + Dev requirements

---

## Development

### Adding New Languages
1. Add translations to `MESSAGES` dictionary
2. Update language selection logic
3. Test with `--language` option

### Adding New Installation Steps
1. Create new method in `Installer` class
2. Add corresponding message keys
3. Call from `run()` method
4. Update documentation

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review installation logs
3. Open issue on GitHub
4. Contact support team

---

**Last Updated:** 2026-08-20  
**Status:** ✅ Production Ready  
**Supported Platforms:** Windows, Linux, macOS  
**Supported Languages:** RU, EN, ES, HE
