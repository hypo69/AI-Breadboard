# `scripts/dev` Module — Development & Testing Utilities

## Purpose
Collection of utility scripts for developers and automated workflows:

| Script | Purpose | Command / Usage |
|---|---|---|
| `run_tests.py` | Runs the test suite via Pytest with coverage and summary reporting. | `python scripts/dev/run_tests.py` |
| `generate_coverage_report.py` | Generates detailed HTML/terminal code coverage reports. | `python scripts/dev/generate_coverage_report.py` |
| `analyze_dependencies.py` | Audits module imports and compares with `requirements.txt`. | `python scripts/dev/analyze_dependencies.py` |
| `search_code.py` | CLI search over codebase symbols and technical RAG index. | `python scripts/dev/search_code.py --query "UnifiedChatModel"` |
| `update_docs.py` | Regenerates and syncs MkDocs documentation. | `python scripts/dev/update_docs.py` |
| `update_scripts_documentation.py` | Updates markdown documentation across all utility scripts. | `python scripts/dev/update_scripts_documentation.py` |
| `scan_headers.py` | Validates file header docblock compliance with project standards. | `python scripts/dev/scan_headers.py` |
| `bot_runner.py` | Standalone runner for testing the Telegram voice assistant bot. | `python scripts/dev/bot_runner.py` |
| `assist_cli.py` | Unified CLI dispatcher for `assist` commands. | `python scripts/dev/assist_cli.py` |
