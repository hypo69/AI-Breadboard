# AI-Breadboard Architecture

## Overview

This document describes the modular architecture of the AI-Breadboard FastAPI application.

## Architecture Principles

1. **Single Responsibility**: Each module has one clear responsibility
2. **Separation of Concerns**: Different concerns are separated into different modules
3. **Auto-Discovery**: Routers and pages are auto-discovered to reduce boilerplate
4. **Factory Pattern**: Application is built using factory functions
5. **Testability**: Modules are designed for easy unit testing

## Directory Structure

```
AI-Breadboard/
├── main.py                          # Application entry point (65 lines)
├── docs/
│   └── ARCHITECTURE.md              # This file
├── src/
│   ├── app/
│   │   ├── __init__.py             # Application factory (create_app, register_pages)
│   │   ├── initialization.py       # FastAPI initialization, middleware, CORS
│   │   ├── config_api.py           # AI provider configuration endpoints
│   │   ├── versioning.py           # Version check and update logic
│   │   ├── server_config.py        # Server configuration and startup
│   │   ├── routers/                # Auto-discovered API routers
│   │   │   └── __init__.py
│   │   ├── pages/                  # UI page handlers
│   │   │   └── __init__.py
│   │   └── tests/                  # Application tests
│   │       ├── __init__.py
│   │       ├── test_initialization.py
│   │       ├── test_versioning.py
│   │       ├── test_config_api.py
│   │       └── test_pages.py
│   ├── api/                        # API router modules (router_*.py)
│   │   ├── router_auth.py
│   │   ├── router_chat.py
│   │   ├── router_admin.py
│   │   └── ...
│   └── ...
└── apps/                           # Application-specific routers
    └── trading_terminal/
```

## Core Modules

### 1. `src/app/__init__.py` - Application Factory

Provides the main application factory pattern:

```python
from src.app import create_app, register_pages

app = create_app()
register_pages(app)
```

Key functions:
- `create_app()` - Creates and configures FastAPI app
- `register_pages(app)` - Registers all UI pages
- `register_config_api(app)` - Registers AI provider config endpoints
- `_auto_discover_routers()` - Auto-discovers routers

### 2. `src/app/initialization.py` - FastAPI Setup

Handles FastAPI initialization and middleware:

```python
from src.app.initialization import create_app, mount_static_files

app = create_app()
mount_static_files(app)
```

Features:
- CORS configuration
- Windows asyncio noise suppression
- Auto-login middleware for localhost
- Static file mounting
- Favicon setup

### 3. `src/app/versioning.py` - Version Management

Handles version checking and updates:

```python
from src.app.versioning import check_updates, prompt_and_perform_update

result = check_updates()  # Check if update available
updated = prompt_and_perform_update()  # Prompt user to update
```

Features:
- GitHub API version checking
- Git pull with FF-only merge
- Backup and restore on update
- Interactive and auto-update modes

### 4. `src/app/config_api.py` - AI Provider Configuration

Configuration endpoints for AI providers:

- `GET/POST /api/foundry/config` - Foundry configuration
- `GET/POST /api/ollama/config` - Ollama configuration
- `GET/POST /api/agy/config` - AGY configuration
- `GET/POST /api/onnx/config` - ONNX configuration
- `GET /api/onnx/providers` - Available ONNX providers

### 6. `src/app/server_config.py` - Server Configuration

Server configuration and startup utilities:

```python
from src.app.server_config import run_server, get_server_config

config = get_server_config()  # Get server configuration dict
run_server(app)  # Run the FastAPI server
```

Features:
- Port configuration from `server_cfg.port`
- SSL certificate paths from config or environment variables
- Host binding configuration
- Reload setting
- Path to default certificates (`~/.certs/localhost+2.pem`)

### 7. `src/app/pages/__init__.py` - UI Pages

All UI pages are registered here:

- `/` - Main page (user dashboard or login)
- `/login` - Login/registration page
- `/admin` - Admin panel
- `/user/*` - User static files
- `/tgmini/*` - Telegram Mini App
- `/rc/*` - Remote Control
- `/mic/*` - Voice Remote Control
- `/helpdesk/*` - Helpdesk
- `/tv/*` - TV Player
- And more...

### 8. `src/app/routers/__init__.py` - Router Discovery

Auto-discovers and registers routers from `src/api/`:

```python
from src.app.routers import auto_discover_routers

auto_discover_routers(app)
```

## Entry Point (`main.py`)

The main entry point is kept minimal (65 lines):

```python
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

from src.app import create_app, register_pages, register_config_api
from src.app.server_config import run_server
from src.app.versioning import check_updates, prompt_and_perform_update
from src.logger import logger

app = create_app()
register_pages(app)
register_config_api(app)

@app.on_event("startup")
async def startup_event():
    from src.utils.scheduler import scheduler
    await scheduler.start()
    
    try:
        result = check_updates()
        if result.get("is_update_available"):
            logger.warning(f"Update available: {result.get('remote_version')}")
        else:
            logger.info(f"Application is up to date: version {result.get('current_version')}")
    except Exception:
        pass

if __name__ == '__main__':
    import sys
    
    branch = str(os.getenv('GIT_BRANCH', 'main'))
    
    if '--check-update' in sys.argv[1:]:
        prompt_and_perform_update(branch=branch)
        sys.exit(0)
    
    if '--check-update-and-run' in sys.argv[1:]:
        prompt_and_perform_update(branch=branch)
    
    try:
        prompt_and_perform_update(branch=branch)
    except Exception:
        pass
    
    run_server(app)
```

## Adding New Routers

Create a new file `src/api/router_my_feature.py`:

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-feature")
async def my_feature():
    return {"message": "Hello from my feature!"}
```

The router will be automatically discovered and registered.

## Adding New Pages

Create a new handler in `src/app/pages/__init__.py`:

```python
@app.get('/my-page')
async def my_page():
    content = read_text_file(webinterface_dir / 'my-page' / 'index.html')
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)
```

## Testing

Tests are located in `src/app/tests/`:

```
src/app/tests/
├── __init__.py
├── test_initialization.py
├── test_versioning.py
├── test_config_api.py
└── test_pages.py
```

Run tests:

```bash
pytest src/app/tests/
```

## Benefits of This Architecture

1. **Maintainability**: Each module has a clear responsibility
2. **Scalability**: Easy to add new routers/pages without touching main.py
3. **Testability**: Modules can be tested independently
4. **Auto-Discovery**: Reduced boilerplate for new features
5. **Documentation**: Clear structure makes documentation easier
6. **Separation of Concerns**: UI, API, config are separated
7. **Reusability**: Modules can be reused in other projects

## Migration from Old `main.py`

The old `main.py` had ~1500 lines with:
- 30+ router initializations
- 20+ UI page handlers
- Version check logic
- Config endpoints
- Static file mounting

The new architecture separates these into:
- `src/app/initialization.py` - ~250 lines
- `src/app/versioning.py` - ~200 lines  
- `src/app/config_api.py` - ~150 lines
- `src/app/server_config.py` - ~80 lines
- `src/app/pages/__init__.py` - ~300 lines
- `src/app/__init__.py` - ~150 lines
- `main.py` - 65 lines (down from 1500)

Total: ~1135 lines, but now properly organized and testable.
