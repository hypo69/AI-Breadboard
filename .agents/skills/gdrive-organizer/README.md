# Google Drive Organizer Skill (`gdrive-organizer`)

## Overview

The `gdrive-organizer` skill provides automated analysis, health auditing, and safe reorganization for Google Drive storage.

## Features

- **Recursive Tree Mapping**: Builds an in-memory parent-child graph of all Drive items.
- **Health Audit Engine**: Identifies structural problems:
  - Loose files in Root directory
  - Exact & near duplicates (MD5 checksum + Name/Size matching)
  - Copy and version clutter (`Copy of...`, `(1)`, `v2_final`)
  - Empty or generic folders (`New folder`, `misc`)
- **Actionable Plan Proposal**: Generates structured migration recommendations (Markdown & JSON).
- **Safe Execution**: Supports dry-run validation and non-destructive file relocation.

## Architecture

- [`scripts/gdrive_scanner.py`](scripts/gdrive_scanner.py): Google Drive API traversal and hierarchy builder.
- [`scripts/audit_engine.py`](scripts/audit_engine.py): Disorganization detection and health scoring.
- [`scripts/proposal_generator.py`](scripts/proposal_generator.py): Restructuring proposal and Markdown report builder.
- [`scripts/reorganize_executor.py`](scripts/reorganize_executor.py): Safe plan executor on Google Drive.
- [`scripts/main.py`](scripts/main.py): CLI interface.

## Usage

```powershell
# Run health audit
python skills/gdrive-organizer/scripts/main.py audit

# Generate restructuring plan
python skills/gdrive-organizer/scripts/main.py propose --out plan.json --report-out report.md

# Test run plan without changing files
python skills/gdrive-organizer/scripts/main.py apply --plan plan.json --dry-run
```
