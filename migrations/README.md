# Database Migrations Repository (`migrations/`)

## 📋 Overview
This directory houses version-controlled schema migrations for project SQLite databases.

## 📁 Organization
Each managed database has its own subdirectory named after the logical database identifier:
- `users/` - Migrations for `src/user_manager/users.db`

## 📝 Naming Convention
- Files must be sequentially prefixed with 4 digits: `0001_<description>.sql` or `0002_<description>.py`.
- **SQL files (`.sql`)**: Raw SQL statements executed as a script within an automatic transaction.
- **Python files (`.py`)**: Must define a function `def upgrade(conn: sqlite3.Connection) -> bool` returning `True` on success.

## 🚀 Creating New Migrations
Use the project management CLI:
```bash
# Create a new SQL migration
py manage_tools.py db create users add_user_avatar_column

# Create a new Python migration
py manage_tools.py db create users recalculate_user_storage --py
```
