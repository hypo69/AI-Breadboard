# DLQ (Dead Letter Queue) Skill for AI Breadboard & Gemini CLI

The `dlq` skill provides a resilient Dead Letter Queue mechanism and an interactive Rich-based TUI dashboard for monitoring, retrying, and managing failed AI agent tasks, API errors, and network timeouts.

## Features
- **SQLite Storage**: Persistent local store (`dlq_store.db`) with fast indexing by status and source.
- **Interactive TUI**: Live dashboard powered by `Rich` showing summary metrics, status breakdown, and detailed error logs.
- **CLI Management**: Command-line interface for `push`, `list`, `retry`, `set-status`, and `purge` operations.
- **Status Lifecycle**: Track message states (`PENDING`, `RETRYING`, `RESOLVED`, `FAILED`).

## Quick Start
```bash
# Launch interactive TUI
python .agents/skills/dlq/scripts/tui.py

# Push a new error entry
python .agents/skills/dlq/scripts/manager.py push --source "agent-task" --error "Task failed" --payload '{"task_id": 42}'

# List pending messages in JSON format
python .agents/skills/dlq/scripts/manager.py list --status PENDING --json
```
