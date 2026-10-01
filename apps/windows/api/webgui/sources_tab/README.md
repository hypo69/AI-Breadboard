# `webinterface/sources_tab` — Drive Scanning & Media Library Audit

## Purpose
Administrative tab for managing scan directories, triggering disk analysis, resolving orphaned torrents, and consolidating metadata.

---

## Capabilities
- Add/remove storage scan paths and external drive mountpoints.
- Trigger full library scans with Gemini-assisted media classification.
- Database integrity checks: identify missing files, incomplete seasons, and duplicate records.
- Download Markdown and CSV summary reports.

---

## Files
- `index.html`: Scan configuration and audit summary tables.
- `main.js`: Communication with `/api/media-admin` endpoints.
