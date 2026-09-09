# Database Management & Schema Migrations (`src/db`)

## 📋 Overview
The `src/db` package provides unified schema migration management, version tracking, and automated database backups for all SQLite databases across the AI Breadboard ecosystem.

## 🚀 Core Features
- **Transactional Migrations**: All migration files are executed inside transactions to prevent partial updates.
- **SQL & Python Migrations**: Supports both declarative `.sql` DDL/DML scripts and programmatic `.py` data transformation scripts.
- **Automatic Backups**: Creates a pre-migration timestamped snapshot of the target database and automatically restores it on any migration failure.
- **Automated Update Hook**: Integrated directly into `run.ps1`, `launchers/Run-Unicorn.ps1`, `src/version_manager.py`, and `manage_tools.py`.

## 📁 Migration Structure
Migrations are stored in the project-level `migrations/` directory organized by database name:
```text
migrations/
  └── users/
      ├── 0001_initial_users_schema.sql
      └── 0002_add_new_feature.sql
```

## 🛠️ Usage
```python
from src.db import get_migration_manager

manager = get_migration_manager()
# Apply all pending migrations
results = manager.apply_all_pending()
print(results)
```
