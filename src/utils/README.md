# `src.utils` Module — Common Utility Library

## Purpose
The `src.utils` directory is a collection of reusable helper modules, data converters, and low-level system utilities shared across the entire AI Breadboard application.

---

## Module Index

| File / Subdirectory | Description |
|---|---|
| `printer.py` | Pretty printing and string formatting (`pformat`, `pprint`) with ANSI color/styling, automated embedded JSON scanning (`<text> <JSON> <text>`), and syntax indentation. |
| `convertors/` | Format conversion utilities (JSON, Dict, Markdown, XML, CSV, Base64, SimpleNamespace). |
| `file.py` | Safe file read/write operations, recursive path traversals, and file locking. |
| `jjson.py` | Resilient JSON serialization, deserialization, and `SimpleNamespace` conversions with repair capabilities. |
| `date_time.py` | Timestamp parsing, UTC normalization, and human-readable time elapsed formatting. |
| `get_free_port.py` | Dynamic TCP port availability scanning and conflict resolution. |
| `image.py` | Image resizing, thumbnail generation, and format conversion via Pillow. |
| `video.py` | Video metadata extraction, aspect ratio parsing, and duration probing. |
| `pdf.py` | PDF document parsing, text extraction, and report compilation. |
| `pdf_extractor.py` | Advanced PDF text and tabular extraction engine. |
| `docx.py` | Word document text extraction and parsing. |
| `archive.py` | ZIP/TAR archive extraction and inspection utilities. |
| `versioning.py` | Semantic Versioning (SemVer) parsing, comparator utilities, and version tag ranking. |
| `smtp.py` | SMTP client helpers for automated notification dispatches. |
| `ftp.py` | Secure FTP file transfer and synchronization helpers. |
| `url.py` | URL manipulation, sanitization, and parsing utilities. |

