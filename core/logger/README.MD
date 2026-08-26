# `core.logger` Module — Structured Logging System

## Overview
The `core.logger` module provides a flexible, unified logging system supporting colorized console output, rotating file logs, and JSON-structured log dumps.

It implements the Singleton pattern (`SingletonMeta`) to guarantee consistent logger state and formatting throughout the entire application lifecycle.

---

## Core Classes

- **`SingletonMeta`**: Metaclass enforcing singleton instantiation across all module imports.
- **`JsonFormatter`**: Formats log records into JSON strings containing timestamp, level, caller info, and messages.
- **`Logger`**: Central logger managing console, file, and JSON handlers with colorization via `colorama`.

---

## Methods & Signature

```python
from core.logger import logger

# Logging at standard levels
logger.info("Application initialized successfully.")
logger.success("Model cache warm-up completed.")
logger.warning("Quota threshold approaching for API key.")
logger.debug("Received payload", exc_info=False)
logger.error("Failed to connect to external service", ex=exc)
logger.critical("Unrecoverable system error", ex=exc)
```

---

## File Logging Configuration

File destinations are configured at startup via `initialize_loggers()`:

```python
from core.logger import logger

logger.initialize_loggers(
    info_log_path="logs/info.log",
    debug_log_path="logs/debug.log",
    errors_log_path="logs/errors.log",
    json_log_path="logs/log.json"
)
```

---

## Guidelines for AI Agents & Developers

1. Always import `logger` directly from `core.logger`.
2. Do not use raw `print()` statements in production code.
3. Pass exceptions explicitly using the `ex` parameter: `logger.error("Message", ex=e)`.
