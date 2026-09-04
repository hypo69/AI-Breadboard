# `core.logger` Module — Advanced Structured Logging System

## Overview

`core.logger` is a comprehensive, production-ready logging module that provides:

- **Unified logging interface** with support for multiple output formats
- **Colorized console output** for better readability during development
- **Structured JSON logging** for machine-readable log analysis
- **Automatic log rotation** by file size to prevent disk overflow
- **Module-specific routing** to separate logs by functionality (FastAPI, AI, Playwright, etc.)
- **Compression of repetitive log entries** on-the-fly to reduce disk usage
- **Intelligent log analysis** using Google Generative AI (Gemini)
- **Master Journal generation** from analyzed logs for system health monitoring

The module implements the **Singleton pattern** to guarantee a single, consistent logger instance throughout the entire application lifecycle.

---

## Architecture

### Core Components

```
core/logger/
├── logger.py          # Main Logger class with Singleton pattern and CompressingHandler
├── compress_logs.py   # Utility functions for log compression
├── log_analyzer.py    # AI-powered log analysis and Master Journal generation
├── header.py          # Project root detection and metadata initialization
├── __init__.py        # Module exports
└── README.md          # This file
```

### Class Hierarchy

#### `SingletonMeta` (Metaclass)
Ensures that only one instance of the Logger class exists across the entire application.

**Key Features:**
- Thread-safe instance creation using locks
- Automatic reuse of existing instance
- No need for explicit singleton initialization

#### `JsonFormatter` (logging.Formatter)
Converts log records into structured JSON format for machine-readable analysis.

**Output Format:**
```json
{
  "timestamp": "2024-01-15 10:30:45,123",
  "level": "ERROR",
  "message": "Database connection failed",
  "exc_info": null
}
```

#### `CompressingHandler` (logging.handlers.RotatingFileHandler)
File handler with automatic log rotation and compression of repetitive entries.

**Features:**
- Automatic rotation when file size exceeds limit (default: 10MB)
- Buffer-based compression: `[5x] Error message` instead of 5 separate lines
- Thread-safe operation with proper locking
- Graceful cleanup on application exit

#### `Logger` (Main Class)
Central logging facade providing all logging methods with colorization and routing.

**Logging Levels:**
- `info()` - Informational messages (green by default)
- `success()` - Successful operations (light green by default)
- `warning()` - Warning messages (black on yellow by default)
- `debug()` - Debug information (cyan, disabled in production)
- `error()` - Error messages (red by default)
- `critical()` - Critical errors (white on red by default)

---

## Quick Start

### Basic Usage

```python
from core.logger import logger

# Standard logging
logger.info("Application started successfully")
logger.success("User authentication completed")
logger.warning("Cache is nearly full")
logger.debug("Processing item 42")
logger.error("Failed to connect to database", ex=connection_error)
logger.critical("System integrity compromised", ex=critical_error)
```

### Customizing Colors

```python
# Change color of info message
logger.info("Important notification", text_color="light_yellow")

# Add background color
logger.warning("System warning", text_color="white", bg_color="red")
```

### Exception Handling

```python
try:
    result = risky_operation()
except Exception as ex:
    # Log with exception details
    logger.error("Operation failed", ex=ex, exc_info=True)
```

### Custom Log File Configuration

```python
from core.logger.logger import Logger

# Initialize with custom paths (optional)
custom_logger = Logger(
    info_log_path="custom_info.log",
    debug_log_path="custom_debug.log",
    errors_log_path="custom_errors.log",
    json_log_path="custom_log.json"
)
```

---

## Log File Organization

Logs are automatically organized in `tmp/logs/` directory:

```
tmp/logs/
├── info.log              # All INFO level messages
├── debug.log             # All DEBUG level messages
├── errors.log            # ERROR and CRITICAL messages (compressed)
├── log.json              # All messages in JSON format
├── fastapi.log           # FastAPI-specific logs
├── gemini.log            # AI (Gemini) API logs
├── playwright.log        # Browser automation logs
└── yt_dlp.log            # Video download logs
```

---

## Log Analysis with AI

The module includes intelligent log analysis powered by Google Generative AI (Gemini).

### Enabling Log Analysis

1. **Set environment variables:**
   ```bash
   GEMINI_API_KEY_NAMES=your-api-key-1,your-api-key-2
   ```

2. **Enable in config.json:**
   ```json
   {
     "logging": {
       "enable_log_analyzer": true,
       "max_size_mb": 10
     }
   }
   ```

### How It Works

1. **Monitors log files** - Checks size of log files every 60 seconds
2. **Triggers analysis** - When file exceeds size limit (default: 10MB)
3. **AI analysis** - Sends log content to Gemini for intelligent analysis
4. **Report generation** - Creates detailed Markdown report with:
   - Error identification and classification
   - Problem patterns and trends
   - Recommendations for fixes
5. **Master Journal** - Synthesizes latest reports into unified system health status

### Report Structure

**Individual Report** (`report_info_20240115_103045.md`):
```markdown
# Analysis Report for info.log

## Critical Issues
- Database connection timeout on 10:30:15
- Memory usage spike detected

## Trends
- Increasing number of failed requests
- Pattern: failures occur every 30 minutes

## Recommendations
1. Increase connection pool size
2. Investigate scheduled cleanup tasks
```

**Master Journal** (`master_journal.md`):
```markdown
# System Health Report

## Active Issues Requiring Attention
1. Database connectivity (recurring daily)
2. Memory leak in cache module

## Resolved Issues
- ✓ SSL certificate validation (fixed in v1.2)

## System Trends
- Overall stability: 94%
- Most common error: Timeout (42%)
```

---

## Configuration

### Environment Variables

```bash
# Required for log analysis feature
GEMINI_API_KEY_NAMES=key1,key2,key3

# Optional
MODE=dev                  # Set to "dev" or "debug" for verbose logging
DEBUG=true               # Enable debug mode
```

### Configuration File (config.json)

```json
{
  "logging": {
    "enable_log_analyzer": true,
    "max_size_mb": 10,
    "max_reports_in_journal": 10
  },
  "server": {
    "mode": "dev",
    "debug": true
  }
}
```

---

## Performance Considerations

### Log Compression

The `CompressingHandler` reduces disk usage for repetitive errors automatically on-the-fly:

```
Without compression:
Error: Connection timeout
Error: Connection timeout
Error: Connection timeout
Error: Connection timeout
Error: Connection timeout
(5 lines, 125 bytes)

With compression:
[5x] Error: Connection timeout
(1 line, 35 bytes)

Savings: 72%
```

**How it works:**
- Buffers incoming log records
- Counts identical messages
- Writes compressed format `[Nx] message` for repeated entries
- Automatically flushes when buffer reaches 100 unique entries
- Thread-safe with internal locking

### Debug Mode Impact

- **Development mode** (`mode=dev`): All DEBUG logs are written
- **Production mode**: DEBUG logs are skipped to improve performance
- **Recommendation**: Keep production in non-debug mode for 10-15% performance gain

### Log Rotation

Files automatically rotate when size exceeds limit:
- `error.log` → `error.log.1` (becomes backup)
- `error.log.1` → `error.log.2`
- Keep only 5 most recent backups

---

## Color Reference

### Text Colors
- `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- `light_gray`, `light_red`, `light_green`, `light_yellow`, `light_blue`, `light_magenta`, `light_cyan`

### Background Colors
Same names as text colors, used with `bg_color` parameter

### Example Combinations

```python
# Professional green info
logger.info("Service ready", text_color="light_green")

# Warning with emphasis
logger.warning("Action required", text_color="white", bg_color="red")

# Debug in distinct color
logger.debug("Trace point 42", text_color="cyan")
```

---

## Troubleshooting

### Issue: DEBUG logs not appearing in production

**Solution:** Check that `mode` is set to something other than `dev`/`debug` in config.json

```json
{
  "server": {
    "mode": "prod",
    "debug": false
  }
}
```

### Issue: Log files growing too large

**Solution:** Reduce `max_size_mb` or enable log analyzer:

```json
{
  "logging": {
    "enable_log_analyzer": true,
    "max_size_mb": 5
  }
}
```

### Issue: AI analysis not running

**Checklist:**
1. ✓ `GEMINI_API_KEY_NAMES` environment variable is set
2. ✓ `enable_log_analyzer: true` in config.json
3. ✓ Internet connection available (required for Gemini API)
4. ✓ API quota not exceeded

### Issue: Can't find log files

Default location: `{project_root}/tmp/logs/`

Verify with:
```python
from core.logger import logger
print(logger.log_files_path)
```

---

## Best Practices

### Do's ✓

```python
# Use structured messages
logger.info("User login successful", ex=None)

# Pass exceptions properly
try:
    risky_op()
except Exception as ex:
    logger.error("Operation failed", ex=ex, exc_info=True)

# Use appropriate levels
logger.info("Normal operation")
logger.warning("Something unexpected")
logger.error("Something broke")
logger.critical("System is broken")
```

### Don'ts ✗

```python
# Don't use print() in production code
print("User logged in")  # ✗ Bad

# Don't concatenate exceptions
logger.error("Failed: " + str(ex))  # ✗ Use ex parameter instead

# Don't ignore exceptions
try:
    operation()
except:
    pass  # ✗ At least log it

# Don't mix colored output
logger.info(colored("text", "green"))  # ✗ Already handled by logger
```

---

## Advanced Features

### On-the-Fly Log Compression

The `CompressingHandler` automatically compresses repetitive log entries as they are written:

```python
# Identical errors logged multiple times
for i in range(5):
    logger.error("Connection timeout")

# Result in errors.log:
# [5x] ERROR: Connection timeout
```

**Compression mechanism:**
- Buffers incoming log records in memory
- Counts identical messages using Counter
- Flushes buffer when 100 unique entries accumulated
- Writes `[Nx] message` format for repeated entries
- Single entries written as-is
- Thread-safe with internal locking

**Benefits:**
- Reduces disk I/O for repetitive errors
- Saves ~72% disk space for error logs
- Improves log readability
- No performance overhead

---

## Thread Safety

The logger is fully thread-safe:

```python
import threading

def worker(thread_id):
    logger.info(f"Thread {thread_id} working")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
```

All log writes are synchronized internally, ensuring no corruption or data loss.

---

## API Reference

### Logger Methods

#### `info(message, ex=None, exc_info=False, text_color="green", bg_color="")`
Logs an informational message.

#### `success(message, ex=None, exc_info=False, text_color="light_green", bg_color="")`
Logs a success message (used for completed operations).

#### `warning(message, ex=None, exc_info=False, text_color="black", bg_color="yellow")`
Logs a warning message.

#### `debug(message, ex=None, exc_info=False, text_color="cyan", bg_color="")`
Logs a debug message (suppressed in production mode).

#### `error(message, ex=None, exc_info=True, text_color="red", bg_color="")`
Logs an error message with exception details.

#### `critical(message, ex=None, exc_info=True, text_color="white", bg_color="red")`
Logs a critical error message.

#### `log(level, message, ex=None, exc_info=False, color=None)`
Low-level method for custom logging with specific level.

---

## Migration Guide

### From `print()` statements

```python
# Before
print("Processing item")
print(f"Item {id} processed")

# After
logger.info("Processing item")
logger.success(f"Item {id} processed")
```

### From other logging libraries

```python
# Before (using logging module directly)
import logging
logging.info("Message")

# After (using core.logger)
from core.logger import logger
logger.info("Message")
```

---

## Contributing

When adding new features to the logger:

1. Add proper type hints to all functions
2. Include docstrings with clear descriptions
3. Update this README with examples
4. Test with both colored and plain output
5. Ensure thread-safety with appropriate locks

---

## License

Part of the AI-Breadboard project. © 2026 Development Team.

For support and contributions, refer to the main project documentation.
