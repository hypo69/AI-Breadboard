# `scripts/maintenance` Module — System Maintenance

## Purpose
Utilities for scheduled system maintenance, storage management, and diagnostic analysis:

| Script | Purpose | Usage |
|---|---|---|
| `analyze_logs.py` | Scans log files for recurring errors, warnings, and API quota limits. | `python scripts/maintenance/analyze_logs.py` |
| `compress_logs.py` | Compresses and archives historical log files to conserve disk space. | `python scripts/maintenance/compress_logs.py` |
| `rebuild_dev_rag.py` | Rebuilds the developer technical RAG index for agentic coding assistance. | `python scripts/maintenance/rebuild_dev_rag.py` |
