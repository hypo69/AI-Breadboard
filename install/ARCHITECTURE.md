# 🏗️ Installer Architecture & Logic Documentation

## Overview

The AI Breadboard installation system consists of three complementary installers:

1. **Python Installer** (`install.py`) — Universal, cross-platform
2. **Bash Installer** (`install.sh`) — Unix-like systems (Linux/macOS)
3. **PowerShell Installer** (`install.ps1`) — Windows native

All installers follow the same logical flow and support identical features.

---

## Core Logic Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Language Selection (I18N)                                │
│    └─ Interactive prompt: RU / EN / ES / HE                │
├─────────────────────────────────────────────────────────────┤
│ 2. Installation Directory Selection                         │
│    └─ Default: current directory or user input             │
├─────────────────────────────────────────────────────────────┤
│ 3. Python Interpreter Discovery                            │
│    ├─ Try: python3.13, python3.12, python3.11, python3.10 │
│    ├─ Fallback: python, python3                            │
│    └─ Error: Exit if not found                             │
├─────────────────────────────────────────────────────────────┤
│ 4. Virtual Environment Creation                            │
│    ├─ Check: venv already exists?                          │
│    ├─ Create: python -m venv <dir>                         │
│    └─ Verify: venv/bin/python exists                       │
├─────────────────────────────────────────────────────────────┤
│ 5. Pip & Tools Upgrade                                     │
│    └─ pip install --upgrade pip setuptools wheel           │
├─────────────────────────────────────────────────────────────┤
│ 6. Dependency Profile Selection                            │
│    ├─ [1] Full (Core + AI + Utils) — Default              │
│    ├─ [2] Core only                                        │
│    ├─ [3] Core + AI                                        │
│    ├─ [4] Full + Dev                                       │
│    └─ [5] Skip                                             │
├─────────────────────────────────────────────────────────────┤
│ 7. Dependency Installation                                 │
│    └─ pip install -r <requirements-file>                   │
├─────────────────────────────────────────────────────────────┤
│ 8. Environment Verification                                │
│    └─ Test imports: fastapi, uvicorn, dotenv, pydantic    │
├─────────────────────────────────────────────────────────────┤
│ 9. Success Banner                                          │
│    └─ Display completion message in selected language      │
└─────────────────────────────────────────────────────────────┘
```

---

## Multilingual System (I18N)

### Message Dictionary Structure

**Python:**
```python
class I18N:
    MESSAGES = {
        \"ru\": {\"step_1\": \"[1/6] Проверка Python...\"},
        \"en\": {\"step_1\": \"[1/6] Checking Python...\"},
        \"es\": {\"step_1\": \"[1/6] Verificando Python...\"},
        \"he\": {\"step_1\": \"[1/6] בדיקת Python...\"},
    }
```

**Bash:**
```bash
declare -A MESSAGES_RU=(
    [step_1]=\"[1/6] Проверка Python...\"
)
declare -A MESSAGES_EN=(
    [step_1]=\"[1/6] Checking Python...\"
)
```

### Message Keys

All installers use consistent message keys:

| Key | Purpose | Example |
|-----|---------|----------|
| `welcome` | Initial greeting | \"🚀 Welcome to AI Breadboard Installer\" |
| `select_lang` | Language selection prompt | \"Select installation language:\" |
| `lang_selected` | Confirmation of language | \"✓ Selected language: en\" |
| `step_1` to `step_6` | Installation steps | \"[1/6] Checking Python interpreter...\" |
| `step_X_ok` | Step success | \"✓ Virtual environment created\" |
| `step_X_error` | Step failure | \"✗ Python not found\" |
| `finish` | Completion message | \"✅ Installation completed successfully!\" |
| `error` | Generic error | \"✗ Error: {msg}\" |

---

## Python Interpreter Discovery Logic

### Algorithm

```python
def find_python():
    # Step 1: Try specific versions in order
    for version in [\"3.13\", \"3.12\", \"3.11\", \"3.10\"]:
        if command_exists(f\"python{version}\"):
            return path_to_python
    
    # Step 2: Fallback to generic python/python3
    if command_exists(\"python\"):
        return path_to_python
    if command_exists(\"python3\"):
        return path_to_python
    
    # Step 3: Not found
    return False
```

### Platform-Specific Behavior

**Windows:**
- Uses Python Launcher (`py -3.13`, `py -3.12`, etc.)
- Fallback: `python` from PATH

**Linux/macOS:**
- Direct command lookup: `python3.13`, `python3.12`, etc.
- Fallback: `python3`, `python`

---

## Virtual Environment Management

### Creation Logic

```python
def create_venv(python_path):
    # Check if venv already exists
    if venv_dir.exists():
        return True  # Reuse existing
    
    # Create new venv
    subprocess.run([python_path, \"-m\", \"venv\", venv_dir])
    
    # Verify creation
    if venv_python.exists():
        return True
    return False
```

### Platform-Specific Paths

| Platform | Python Path | Activation |
|----------|-------------|------------|
| Windows | `venv\\Scripts\\python.exe` | `venv\\Scripts\\activate.bat` |
| Linux/macOS | `venv/bin/python` | `source venv/bin/activate` |

---

## Dependency Installation Profiles

### Profile Mapping

```python
profiles = {
    \"1\": [\"requirements.txt\"],  # Full
    \"2\": [\"install/req/requirements-core.txt\"],  # Core
    \"3\": [\"install/req/requirements-core.txt\", \"install/req/requirements-ai.txt\"],  # Core+AI
    \"4\": [\"requirements.txt\", \"install/req/requirements-test.txt\", \"install/req/requirements-docs.txt\"],  # Full+Dev
    \"5\": [],  # Skip
}
```

### Installation Logic

```python
def install_dependencies(profile):
    req_files = profiles.get(profile, [])
    
    if not req_files:
        return True  # Skip
    
    cmd = [python_path, \"-m\", \"pip\", \"install\"]
    for req_file in req_files:
        if Path(req_file).exists():
            cmd.extend([\"-r\", req_file])
    
    subprocess.run(cmd)
```

---

## Environment Verification

### Verification Steps

```python
def verify_environment():
    modules = [\"fastapi\", \"uvicorn\", \"dotenv\", \"pydantic\"]
    
    for module in modules:
        try:
            subprocess.run(
                [python_path, \"-c\", f\"import {module}\"],
                check=True,
                timeout=10
            )
        except:
            return False
    
    return True
```

### Verification Modules

| Module | Purpose | Package |
|--------|---------|----------|
| `fastapi` | Web framework | fastapi |
| `uvicorn` | ASGI server | uvicorn |
| `dotenv` | Environment variables | python-dotenv |
| `pydantic` | Data validation | pydantic |

---

## Error Handling Strategy

### Early Return Pattern

All installers follow the \"Early Return\" pattern (per CODE_RULES):

```python
def create_venv(python_path):
    if venv_dir.exists():
        return True
    
    try:
        subprocess.run([python_path, \"-m\", \"venv\", venv_dir], check=True)
        return True
    except:
        return False  # Not None, not exception propagation
```

### Error Messages

All errors are:
1. Logged with context
2. Returned as `False` (not exceptions)
3. Displayed in user's selected language
4. Actionable (include next steps)

---

## Code Quality Standards (CODE_RULES Compliance)

### ✅ Implemented Standards

1. **No `None` usage:**
   - Variables initialized with empty values: `''`, `0`, `[]`, `{}`
   - Functions return `False` on error, not `None`
   - No `is None` comparisons

2. **Configuration over Hardcode:**
   - All paths from `install.json`
   - All messages from I18N dictionaries
   - All versions from configuration

3. **Single Responsibility:**
   - Each method does one thing
   - Each function has clear purpose
   - Separation of concerns maintained

4. **Early Return:**
   - Validation at function start
   - Immediate return on error
   - No deep nesting

5. **Explicit Dependencies:**
   - All parameters passed explicitly
   - No global state
   - Clear function signatures

### ✅ Documentation Standards

1. **File Headers:**
   - Process name and description
   - Examples of usage
   - File metadata (author, copyright)

2. **Docstrings (hypo69 format):**
   - Short description
   - Args with types
   - Returns with type
   - Examples

3. **Comments:**
   - Explain \"why\", not \"what\"
   - Use noun forms (not verbs)
   - Minimal but clear

---

## Testing & Validation

### Validation Script

Run `validate_installers.py` to check:

```bash
python validate_installers.py
```

Checks performed:
1. Python installer structure
2. Bash installer structure
3. Configuration validity
4. Consistency between installers
5. Language support
6. Method/function presence

### Manual Testing

```bash
# Test Python installer
python install.py --language en

# Test Bash installer
bash install.sh --language ru

# Test PowerShell installer
.\\install.ps1
```

---

## Maintenance & Extension

### Adding New Languages

1. Add translations to all three installers
2. Update `supported_languages` in `install.json`
3. Test with `--language` option
4. Update documentation

### Adding New Installation Steps

1. Create new method in `Installer` class
2. Add message keys to I18N
3. Call from `run()` method
4. Update flow diagram
5. Add validation checks

### Updating Dependencies

1. Modify `requirements*.txt` files
2. Update `install.json` paths if needed
3. Test all profiles
4. Update documentation

---

## Performance Considerations

### Optimization Strategies

1. **Parallel Operations:** Could parallelize pip installs (future)
2. **Caching:** Could cache Python discovery results
3. **Lazy Loading:** Only load needed modules
4. **Timeouts:** All subprocess calls have timeouts

### Resource Usage

| Operation | Time | Space |
|-----------|------|-------|
| Python discovery | ~1-2s | Minimal |
| venv creation | ~5-10s | ~100MB |
| pip upgrade | ~10-20s | Minimal |
| Full install (profile 1) | ~2-5 min | ~500MB-1GB |
| Verification | ~5-10s | Minimal |

---

## Security Considerations

1. **No Hardcoded Secrets:** All secrets in `.env`
2. **Safe Subprocess Calls:** All use `check=True` and timeouts
3. **Path Validation:** All paths validated before use
4. **Input Sanitization:** User input validated
5. **SSL Certificates:** Handled separately by `install_ssl_certs.py`

---

**Last Updated:** 2026-08-20  
**Status:** ✅ Production Ready  
**Maintainer:** hypo69
