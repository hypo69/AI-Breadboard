# `core.utils.convertors` — Data Converters & Transformers

## Overview
The `core.utils.convertors` package provides specialized transformation utilities for converting structured data between Python objects, JSON, XML, CSV, Markdown, and `SimpleNamespace`.

---

## Files & Transformers

- `dict.py` — Dictionary manipulation, recursive flattening, and `SimpleNamespace` conversions.
- `json.py` — Robust JSON serialization with fallback for non-serializable objects.
- `csv.py` — CSV parsing and tabular record normalization.
- `md.py` — Markdown formatting, HTML to Markdown conversion, and table generators.

---

## Dependencies & Rules
- Used across all layers to normalize payloads before sending to AI models or persisting to SQLite.
- Built on standard library (`json`, `xml`, `types`) and resilient utilities (`pandas`, `json_repair`).
