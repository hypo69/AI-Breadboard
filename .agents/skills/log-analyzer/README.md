# Log Analyzer Skill

## Overview
The `log-analyzer` skill provides comprehensive static and AI-assisted analysis for application and system logs across the AI Breadboard environment.

## Features
- **Multi-Format Parsing**: Supports standard text logs and structured JSON Lines logs.
- **Error Clustering & Normalization**: Strips variable numbers, UUIDs, and memory addresses to cluster duplicate stack traces and errors.
- **AI Diagnostics**: Leverages Google Gemini to formulate executive summaries and actionable remediation steps.
- **Real-Time Log Watcher**: Live tail utility with ANSI severity highlighting.
- **Markdown & JSON Export**: Outputs human-readable markdown reports or machine-readable JSON metrics.

## Package Layout
```text
.agents/skills/log-analyzer/
├── SKILL.md                 # Agent instructions & YAML frontmatter
├── README.md                # Developer documentation
├── scripts/
│   ├── analyze.py           # Core CLI analysis engine
│   └── watch_logs.py        # Real-time tail monitor
├── references/
│   └── log_patterns.md      # Pattern references & normalization rules
└── dist/
    └── log-analyzer.skill   # Packaged distributable skill archive
```

## Quick Start
```powershell
# Basic summary of default log directory
python .agents/skills/log-analyzer/scripts/analyze.py

# Filter only errors and output JSON
python .agents/skills/log-analyzer/scripts/analyze.py --level ERROR --json

# Full AI diagnostics with report saving
python .agents/skills/log-analyzer/scripts/analyze.py --ai --save-report
```
