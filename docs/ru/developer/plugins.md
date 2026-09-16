# Plugin Development Guide

## Plugin Structure

A plugin is a Python module that exposes a `PLUGIN_META` dict and optionally an `init_router()` function.

```python
# plugins/my_plugin.py

PLUGIN_META = {
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "My custom plugin",
    "author": "Your Name",
}

def init_router():
    """Optional: expose HTTP endpoints."""
    from fastapi import APIRouter
    router = APIRouter(prefix="/plugin/my-plugin", tags=["my-plugin"])

    @router.get("")
    async def index():
        return {"plugin": "my_plugin", "status": "active"}

    return router
```

## Hot Reload

Place your plugin in the `plugins/` directory. The server automatically detects changes and reloads the plugin without restart.

You can also trigger reload manually:

```bash
curl -X POST http://localhost:8000/admin/plugins/reload/my_plugin \
  -H "Cookie: auth_token=..."
```

## Plugin Lifecycle

1. **Load**: Module imported, `PLUGIN_META` read, `init_router()` called if present
2. **Active**: Router registered with FastAPI app
3. **Reload**: Old module removed from `sys.modules`, re-imported
4. **Unload**: Router unregistered, module removed from `sys.modules`

## Example Plugins

See `plugins/example_plugin.py` for a minimal working example.
