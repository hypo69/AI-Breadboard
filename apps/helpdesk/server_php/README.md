# Helpdesk Backend & Google OAuth 2.0 (PHP 8)

Модуль бэкенда службы технической поддержки (Helpdesk), схемы удаленной базы данных MySQL и авторизации/регистрации через Google OAuth 2.0 на PHP 8.

---

## 📁 Структура файлов (`apps/helpdesk/server_php/`)

- `schema.sql` — Полная структура таблиц (MySQL 8 / MariaDB InnoDB utf8mb4)
- `Database.php` — PDO класс соединения с удаленной БД и чтением secrets.json
- `GoogleAuthService.php` — Сервис аутентификации, генерации ссылок и callback Google OAuth 2.0
- `auth_login.php` — Точка входа для перенаправления пользователя в Google
- `oauth_callback.php` — Endpoint обработки ответа Google и создания пользовательской сессии
- `migrate.php` — CLI скрипт применения миграций и создания таблиц в БД
- `README.md` — Документация и руководство по настройке

---

## 🗄️ База данных

Схема `schema.sql` включает следующие таблицы:
1. `users` — пользователи, роли (user, operator, admin), статусы и аватары.
2. `user_oauth_providers` — токены и привязка Google ID к учетной записи.
3. `user_sessions` — активные пользовательские сессии и токены устройств.
4. `categories` — категории обращений (общие, тех. проблемы, биллинг, доступ).
5. `tickets` — тикеты, номера, приоритеты (low, normal, high, urgent), статусы и назначения.
6. `ticket_messages` — переписка внутри тикета (пользователь, оператор, внутренние заметки).
7. `ticket_attachments` — прикрепленные файлы и скриншоты.
8. `ticket_audit_logs` — история изменений и действий по тикетам.

### Применение структуры к БД
```bash
php apps/helpdesk/server_php/migrate.php
```

---

## 🔐 Настройка Google OAuth 2.0

В файле `apps/helpdesk/secrets.json` (или корневом файле секретов) задайте учетные данные Google Cloud Console:

```json
{
  "db": {
    "hostname": "77.37.35.16",
    "db": "u177424397_ai_bb_helpdesk",
    "user": "u177424397_ai_bb_helpdesk",
    "password": "@Davidka#1969"
  },
  "google_oauth": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "GOCSPX-YOUR_CLIENT_SECRET",
    "redirect_uri": "https://davidka.net/helpdesk/oauth_callback.php"
  }
}
```

---

## 🚀 Поток авторизации

1. Пользователь переходит по ссылке `auth_login.php`.
2. Сервис генерирует CSRF state токен и редиректит на экран выбора аккаунта Google.
3. Google возвращает пользователя на `oauth_callback.php?code=...&state=...`.
4. Сервис обменивает `code` на Access Token, запрашивает профиль из Google UserInfo API.
5. Выполняется автоматическая регистрация или вход существующего пользователя в транзакции БД.
6. Создается защищенная Cookie-сессия (`hd_session`).
