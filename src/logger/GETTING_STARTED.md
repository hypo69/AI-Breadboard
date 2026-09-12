# Getting Started with core.logger

Quick guide to using the refactored logging module in your AI-Breadboard project.

---

## Installation & Setup

The logger is already integrated. No additional installation needed.

### Basic Import
```python
from core.logger import logger

# Start using immediately
logger.info("Application started")
```

---

## Common Use Cases

### 1. Log Different Message Types

```python
from core.logger import logger

# Informational messages
logger.info("User logged in successfully")

# Success messages (highlighted in green)
logger.success("Data backup completed")

# Warning messages (highlighted in yellow)
logger.warning("Disk space running low")

# Debug messages (only in development)
logger.debug("Processing item #42")

# Error messages (red)
logger.error("Failed to connect to database", ex=connection_error)

# Critical errors (red on white)
logger.critical("System integrity check failed", ex=critical_error)
```

### 2. Handle Exceptions Properly

```python
try:
    result = risky_operation()
except ConnectionError as ex:
    # Log with full exception info
    logger.error("Connection failed, retrying...", ex=ex, exc_info=True)
except ValueError as ex:
    # Log without full traceback for known errors
    logger.error("Invalid configuration", ex=ex, exc_info=False)
```

### 3. Customize Message Colors

```python
# Green info message
logger.info("✓ Operation complete", text_color="light_green")

# Yellow warning with emphasis
logger.warning("⚠ Check this", text_color="white", bg_color="red")

# Cyan debug information
logger.debug("📍 Trace point", text_color="cyan")
```

### 4. Log from Different Modules

```python
# In FastAPI route
from core.logger import logger

@app.get("/users")
async def get_users():
    logger.info("Fetching user list")
    users = await db.get_users()
    logger.success(f"Retrieved {len(users)} users")
    return users
```

```python
# In AI/Gemini module
from core.logger import logger

async def generate_response(prompt):
    logger.debug(f"Calling Gemini with: {prompt[:50]}...")
    response = await ai_model.ask(prompt)
    logger.info(f"Generated response ({len(response)} chars)")
    return response
```

---

## Log Files Location

All logs are stored in: `{project_root}/tmp/logs/`

```
tmp/logs/
├── info.log           # Informational messages
├── debug.log          # Debug messages (dev mode only)
├── errors.log         # Errors and critical messages (auto-compressed)
├── log.json           # All logs in JSON format
├── fastapi.log        # FastAPI specific logs (auto-compressed)
├── gemini.log         # AI/Gemini specific logs (auto-compressed)
├── playwright.log     # Browser automation logs (auto-compressed)
└── yt_dlp.log         # Video download logs (auto-compressed)
```

### Automatic Log Compression

Repetitive log entries are automatically compressed on-the-fly:

```
Before compression:
ERROR: Connection timeout
ERROR: Connection timeout
ERROR: Connection timeout
ERROR: Connection timeout
ERROR: Connection timeout

After compression:
[5x] ERROR: Connection timeout
```

**Compression ratio:** ~72% reduction for repetitive errors

---

## Configuration

### Set Debug Mode

**In `.env` file:**
```bash
MODE=dev
DEBUG=true
```

**In `config.json`:**
```json
{
  "server": {
    "mode": "dev",
    "debug": true
  }
}
```

### Enable Log Analysis

**In `.env` file:**
```bash
GEMINI_API_KEY_NAMES=your-key-1,your-key-2
```

**In `config.json`:**
```json
{
  "logging": {
    "enable_log_analyzer": true,
    "max_size_mb": 10
  }
}
```

---

## Best Practices

### ✓ Do's

```python
# Use appropriate log levels
logger.info("Normal flow information")
logger.warning("Something unexpected happened")
logger.error("Operation failed", ex=exception)

# Pass exceptions to logger
try:
    operation()
except Exception as ex:
    logger.error("Failed", ex=ex)

# Use meaningful messages
logger.info("User account created", user_id=42)

# Color for emphasis when needed
logger.warning("⚠ Action required", text_color="white", bg_color="red")
```

### ✗ Don'ts

```python
# Don't use print() in production
print("This is bad")  # ✗ Wrong

# Don't concatenate exceptions
logger.error("Error: " + str(ex))  # ✗ Use ex parameter

# Don't ignore errors
try:
    risky_op()
except:
    pass  # ✗ At least log something

# Don't create multiple loggers
import logging
custom_logger = logging.getLogger("custom")  # ✗ Use core.logger instead
```

---

## Troubleshooting

### Problem: No log files created

**Solution:** Check that `tmp/logs/` directory can be created:
```python
from core.logger import logger
print(logger.log_files_path)  # Verify path exists
```

### Problem: DEBUG messages not appearing

**Solution:** Verify debug mode is enabled:
```python
from core.logger import logger
print(f"Debug mode: {logger.is_debug_mode}")

# Temporarily enable
logger.is_debug_mode = True
logger.debug("This should now appear")
```

### Problem: Colors not working in console

**Solution:** colorama is initialized automatically. If still not working:
```python
import colorama
colorama.init()  # Reinitialize

from core.logger import logger
logger.info("This should be colored", text_color="green")
```

### Problem: Log files growing too large

**Solution:** Configure automatic rotation:
```json
{
  "logging": {
    "max_size_mb": 5,
    "enable_log_analyzer": true
  }
}
```

---

## Performance Tips

1. **Don't log in tight loops**
   ```python
   # BAD - Millions of logs
   for i in range(1000000):
       logger.debug(f"Processing item {i}")  # ✗ Too much
   
   # GOOD - Log summary
   logger.debug(f"Processing {n} items")
   for i in range(n):
       # ... do work
   logger.success(f"Processed {n} items successfully")
   ```

2. **Use appropriate log levels**
   ```python
   # DEBUG is disabled in production
   logger.debug("Expensive operation")  # Won't run in prod
   
   # Use in dev, omit in prod
   if logger.is_debug_mode:
       logger.debug("Detailed info needed for debugging")
   ```

3. **Enable log analysis for long-running processes**
   ```python
   # In production
   # Logs automatically analyzed when > 10MB
   # Reports generated automatically
   # No manual intervention needed
   ```

---

## Integration Examples

### FastAPI Application

```python
from fastapi import FastAPI
from core.logger import logger

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("🚀 FastAPI server starting...")

@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 FastAPI server shutting down")

@app.get("/health")
async def health():
    logger.debug("Health check requested")
    return {"status": "ok"}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    logger.info(f"Fetching item {item_id}")
    try:
        item = await fetch_from_db(item_id)
        logger.success(f"Item {item_id} retrieved")
        return item
    except Exception as ex:
        logger.error(f"Failed to fetch item {item_id}", ex=ex)
        return {"error": "Not found"}
```

### Background Task

```python
import asyncio
from core.logger import logger

async def background_cleanup():
    while True:
        try:
            logger.info("Starting cleanup task...")
            
            deleted = await cleanup_old_files()
            logger.success(f"Cleanup complete: removed {deleted} files")
            
            await asyncio.sleep(3600)  # Every hour
        except Exception as ex:
            logger.error("Cleanup task failed", ex=ex)
            await asyncio.sleep(60)  # Retry after 1 minute
```

### AI Integration

```python
from core.logger import logger
from core.ai import GoogleGenerativeAI

async def generate_response(user_input):
    logger.info(f"Processing user input: {len(user_input)} chars")
    
    try:
        ai_model = GoogleGenerativeAI()
        logger.debug(f"Sending to Gemini: {user_input[:50]}...")
        
        response = await ai_model.ask(user_input)
        
        logger.success(f"Gemini generated {len(response)} chars response")
        return response
    except Exception as ex:
        logger.error("AI generation failed", ex=ex, exc_info=True)
        return "I apologize, I encountered an error"
```

---

## Advanced Features

### Module-Specific Logging

Different logs automatically collected per module:

```python
# This will be logged to gemini.log
from core.logger import logger
logger.info("Processing AI request")  # Will appear in both info.log and gemini.log

# This will be logged to fastapi.log
logger.info("HTTP request received")  # Will appear in both info.log and fastapi.log
```

### Log Compression

Repetitive errors automatically compressed:

```
Before:
[ERROR] Connection timeout
[ERROR] Connection timeout
[ERROR] Connection timeout
[ERROR] Connection timeout
[ERROR] Connection timeout

After:
[5x] Connection timeout
```

**Compression ratio:** 72% reduction for repetitive errors

### JSON Logging for Analysis

```python
import json
from pathlib import Path

log_file = Path("tmp/logs/log.json")
lines = log_file.read_text().strip().split('\n')

for line in lines[-10:]:  # Last 10 entries
    entry = json.loads(line)
    print(f"{entry['timestamp']} [{entry['level']}] {entry['message']}")
```

---

## Testing Your Logging

```python
# Quick test
from core.logger import logger

logger.info("✓ INFO working")
logger.success("✓ SUCCESS working")
logger.warning("✓ WARNING working")
logger.debug("✓ DEBUG working")
logger.error("✓ ERROR working", ex=ValueError("test error"))
logger.critical("✓ CRITICAL working")

print("\nAll log levels working correctly!")
```

Run the test:
```bash
cd {project_root}
python -c "exec(open('core/logger/test_example.py').read())"
```

---

## Next Steps

1. **Read comprehensive documentation:** `core/logger/README.md`
2. **Review refactoring details:** `core/logger/REFACTORING_REPORT.md`
3. **Run test suite:** `pytest core/logger/ -v`
4. **Enable log analysis:** Set `GEMINI_API_KEY_NAMES` environment variable
5. **Monitor logs:** Check `tmp/logs/` for real-time analysis

---

## Support

For issues or questions:

1. Check the README.md for detailed documentation
2. Review test files for usage examples
3. Consult REFACTORING_REPORT.md for architecture details
4. Run: `pytest core/logger/ -v` to verify installation

---

**Happy logging! 📝**
