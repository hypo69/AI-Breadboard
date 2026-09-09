# System Updater Skill

## 📋 Overview
The `system-updater` skill provides autonomous capabilities for checking remote application releases, creating pre-update filesystem backups, pulling and merging latest updates, and running pending database schema migrations across all SQLite databases.

## 🚀 Key Capabilities
- **Version Discovery**: Compares local Git tags and commit hashes with remote repository references (`git ls-remote`).
- **Safety Backups**: Generates pre-update filesystem snapshots before applying remote changes.
- **Automated Database Migrations**: Automatically applies pending `.sql` and `.py` migrations through `MigrationManager`.
- **Automated Rollback**: Restores original files and database state if merge conflicts or migration errors occur.

## 🛠️ Usage
```bash
# Check version status
python .agents/skills/system-updater/scripts/update.py --check

# Apply update
python .agents/skills/system-updater/scripts/update.py --apply
```
