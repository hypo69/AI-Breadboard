# `core.user_manager` Module — User Profiles, Session & Storage Management

## Purpose
The `core.user_manager` package manages user identities, preferences, authentication records, interaction history, and isolated personal user file storage directories.

---

## Components

| File / Resource | Purpose |
|---|---|
| `user_profile.py` | Data models and schemas for user credentials, roles, and UI settings. |
| `__init__.py` | `UserManager` class implementing SQLite CRUD operations and user workspace filesystem management. |
| `users.db` | Local SQLite database storing user profiles, tokens, and settings. |

---

## User Personal Storage Hierarchy

Each user has an isolated workspace under `data/users/<user_id>/` (configurable via `config.json` -> `storage.users_dir`):

```text
data/users/<user_id>/
├── files/        # Uploaded files and documents
├── rag/          # User-specific RAG vector databases and indexes
├── profile/      # User profile JSON and state files
└── temp/         # Temporary processing workspace
```

### Key Directory API Methods:
- `get_user_directory(user_id, subfolder, create=True)`: Resolves or creates user directories safely.
- `init_user_workspace(user_id)`: Initializes standard subfolders for a new user.
- `get_user_storage_stats(user_id)`: Calculates disk usage and file breakdown.
- `delete_user_workspace(user_id, remove_files=True)`: Cleanly purges or archives user directories on user deletion.
- `get_orphaned_user_directories()`: Scans `data/users/` for orphaned workspaces not associated with active database users.
- `cleanup_orphaned_user_directories(dir_names=None)`: Safely purges specified or all dead user workspaces and frees storage.

---

## Automatic Cleanup & Database Triggers

- SQLite does not have direct OS filesystem access natively; `UserManager` registers a Python User-Defined Function (UDF) `delete_user_workspace_udf(user_id)` upon connection.
- An `AFTER DELETE ON users` trigger (`trg_cleanup_user_dir`) executes this UDF on any SQL delete, ensuring that deleted users immediately have their personal workspaces and index artifacts purged.

---

## Architectural Guidelines

- Passwords and sensitive session hashes are never stored in plaintext.
- User personal directories are automatically partitioned and created during registration, admin user creation, and OAuth logins.
---

## Интеграция с Auth API (`src/api/router_auth.py`)
`UserManager` является основным провайдером данных для модуля аутентификации.

- **Аутентификация**: Используется для проверки учетных данных при входе, верификации прав (is_admin, role) и управления сессиями.
- **OAuth**: Делегирует сохранение токенов доступа к сервисам Google (Drive, Calendar, Docs) после успешной авторизации.
- **CLI Support**: Поддерживает проверки прав администратора, инициированные через `router_auth`, позволяя CLI-инструментам выполнять действия от имени админа при передаче корректного `ADMIN_PASSWORD` в заголовке `Authorization`.
- **Настройки**: Хранит и предоставляет пользовательские предпочтения (тема, язык, tts-настройки, избранные модели) через методы `get_user_settings` и `update_user_settings`.

