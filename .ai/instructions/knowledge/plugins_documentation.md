# Plugins Architecture & Documentation (`plugins_documentation.md`)

**Project:** `AI-Breadboard`  
**Location:** [`plugins/`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/plugins)  
**Status:** ✅ Up to date (September 2026)

The plugin subsystem allows modular features to be plugged into the AI routing pipeline and chat interfaces. Plugins inherit from [`BasePlugin`](file:///C:/Users/onela/AppData/Local/AI-Breadboard/plugins/base.py) and can register intent handlers, tools, and background processing routines.

---

## 🧩 Active Plugins Directory

### 1. **`rag_cleaner`** — Document Sanitizer & Ingestion Parser
**Path:** `plugins/rag_cleaner/`  
**Description:**
Parses and cleans varied file formats (PDF, DOCX, ZIP, HTML, CSV, JSON, TXT) into structured text chunks optimized for RAG embedding generation.

### 2. **`generate_rag_from_codebase`** — Codebase Vectorizer
**Path:** `plugins/generate_rag_from_codebase/`  
**Description:**
Scans project source files, extracts function signatures and docstrings, and compiles semantic index entries for codebase Q&A.

### 3. **`log_analyzer`** — Diagnostic Log Classifier
**Path:** `plugins/log_analyzer/`  
**Description:**
Analyzes system error logs, performs error clustering, calculates failure metrics, and produces AI-assisted diagnostic reports.

### 4. **`telegram_bot`** — Remote Notification & Control Bot
**Path:** `plugins/telegram_bot/`  
**Description:**
Integrates with Telegram Bot API to deliver notifications, system alerts, and remote chat interaction.

### 5. **`media_organizer`** — Media Indexer & Metadata Classifier
**Path:** `plugins/media_organizer/`  
**Description:**
Filesystem scanning and metadata categorization for audio/video assets with SQLite storage.

### 6. **`facebook`** — Social Graph Adapter
**Path:** `plugins/facebook/`  
**Description:**
Adapter for querying social graph feeds and data points.

---

## 🏗️ Creating a New Plugin

All plugins implement `BasePlugin`:

```python
from plugins.base import BasePlugin

class MyCustomPlugin(BasePlugin):
    name: str = "custom_plugin"
    enabled: bool = True

    async def handle(self, message: str, **kwargs) -> str:
        """Handle incoming chat messages or triggers."""
        return f"Handled by {self.name}"
```

---

## 🛠️ Plugin Development & Testing

1. **Directory Structure:** Place plugins under `plugins/<plugin_name>/`.
2. **Inheritance:** Subclass `BasePlugin` and implement `async def handle(self, message: str, **kwargs) -> str:`.
3. **Logging:** Use `from src.logger import logger`.
4. **Configuration:** Read options via `self.config`.

---

**Status:** ✅ Up to date (September 2026)  
**Version:** 3.0