# `core.user_manager` Module — User Profiles & Session Management

## Purpose
The `core.user_manager` package manages user identities, preferences, authentication records, and interaction history.

---

## Components

| File / Resource | Purpose |
|---|---|
| `user_profile.py` | Data models and schemas for user credentials, roles, and UI settings. |
| `__init__.py` | `UserManager` class implementing SQLite CRUD operations. |
| `users.db` | Local SQLite database storing user profiles and tokens. |

---

## Architectural Guidelines

- Passwords and sensitive session hashes are never stored in plaintext.
- Default users and initial permission tables are initialized automatically if `users.db` does not exist.
