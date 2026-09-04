# `core.utils` Module — Common Utility Library

## Purpose
The `core.utils` directory is a collection of reusable helper modules, data converters, and low-level system utilities shared across the entire application.

---

## Module Index

| File / Subdirectory | Description |
|---|---|
| `convertors/` | Format conversion utilities (JSON, Dict, Markdown, XML, CSV, Base64, SimpleNamespace). |
| `file.py` | Safe file read/write operations, recursive path traversals, and file locking. |
| `jjson.py` | Resilient JSON serialization, deserialization, and `SimpleNamespace` conversions with repair capabilities. |
| `date_time.py` | Timestamp parsing, UTC normalization, and human-readable time elapsed formatting. |
| `get_free_port.py` | Dynamic TCP port availability scanning and conflict resolution. |
| `image.py` | Image resizing, thumbnail generation, and format conversion via Pillow. |
| `video.py` | Video metadata extraction, aspect ratio parsing, and duration probing. |
| `pdf.py` | PDF document parsing, text extraction, and report compilation. |
| `versioning.py` | Semantic Versioning (SemVer) parsing, comparator utilities, and version tag ranking. |
