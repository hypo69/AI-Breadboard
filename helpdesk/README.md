# AI-Breadboard Helpdesk — Установка на провайдере

## 📦 Установка

### 1. Создать ДВЕ базы данных

```sql
-- База для пользователей
CREATE DATABASE helpdesk_users CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- База для тикетов
CREATE DATABASE helpdesk_tickets CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Загрузить схемы

```bash
# Схема пользователей
mysql -u root -p helpdesk_users < helpdesk/db/schema_users.sql

# Схема тикетов
mysql -u root -p helpdesk_tickets < helpdesk/db/schema_tickets.sql
```

### 3. Настроить конфигурацию

Отредактируйте `helpdesk/config.php`:

```php
<?php
/**
 * Helpdesk Configuration
 */

// Database configuration - USERS DATABASE
define('DB_HOST', 'localhost');
define('DB_NAME', 'helpdesk_users');  // ← База пользователей
define('DB_USER', 'helpdesk_user');
define('DB_PASS', 'StrongPassword123!');
define('DB_CHARSET', 'utf8mb4');

// Database configuration - TICKETS DATABASE (NEW!)
define('DB_TICKETS_HOST', 'localhost');
define('DB_TICKETS_NAME', 'helpdesk_tickets');  // ← База тикетов
define('DB_TICKETS_USER', 'helpdesk_user');
define('DB_TICKETS_PASS', 'StrongPassword123!');

// JWT configuration
define('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production');
define('JWT_ALGO', 'HS256');
define('JWT_EXPIRY', 3600 * 24 * 7); // 7 days

// Application settings
define('APP_NAME', 'Helpdesk');
define('APP_URL', 'https://helpdesk.yourdomain.com');
define('TIMEZONE', 'Europe/Moscow');

// Error reporting (disable in production)
define('DEBUG_MODE', false);

// Paths
define('ROOT_DIR', __DIR__);
define('SRC_DIR', ROOT_DIR . '/src');
define('API_DIR', ROOT_DIR . '/api');
define('PUBLIC_DIR', ROOT_DIR . '/public');

// Session configuration
define('SESSION_NAME', 'helpdesk_session');
define('SESSION_LIFETIME', 3600 * 24 * 7);
```

### 4. Запустить сервер

```bash
cd helpdesk
php -S localhost:8080
```

Откройте: `https://helpdesk.yourdomain.com`

---

## 🔐 Вход по умолчанию

- **Email:** `admin@helpdesk.local`
- **Password:** `admin123`

---

## 📊 Структура баз данных

### helpdesk_users (Пользователи)
| Таблица | Описание |
|---------|----------|
| `users` | Пользователи (email, password_hash, role) |
| `sessions` | JWT токены |
| `user_activity_log` | Лог активности |

### helpdesk_tickets (Тикеты)
| Таблица | Описание |
|---------|----------|
| `helpdesk_tickets` | Тикеты (subject, status, priority) |
| `helpdesk_messages` | Сообщения по тикетам |
| `helpdesk_operators` | Статус операторов |
| `helpdesk_sequences` | Авто-нумерация тикетов |

---

## 🎯 Разделение ответственности

| База | Данные | Ответственность |
|------|--------|-----------------|
| `helpdesk_users` | Пользователи, сессии, логи | Аутентификация |
| `helpdesk_tickets` | Тикеты, сообщения, операторы | Поддержка |

---

## 🔧 Настройка

### Сменить пароль админа

```sql
-- В helpdesk_users
UPDATE users 
SET password_hash = '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi' 
WHERE email = 'admin@helpdesk.local';
```

### Добавить оператора

```sql
-- В helpdesk_users
INSERT INTO users (email, password_hash, name, role, is_active) 
VALUES ('operator@helpdesk.local', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Operator', 'operator', 1);

-- В helpdesk_tickets
INSERT INTO helpdesk_operators (id, user_id, display_name, role, is_online) 
VALUES ('op_001', LAST_INSERT_ID(), 'Support Operator', 'operator', 0);
```

---

## 📱 Интерфейс

- **Логин/Регистрация** — вход в систему
- **Dashboard** — статистика и создание тикетов
- **Список тикетов** — фильтрация по статусу/приоритету
- **Сообщения** — переписка по тикету

---

## 🛡️ Безопасность

- Пароли: bcrypt (10k итераций)
- Токены: JWT с expiration
- SQL: prepared statements
- XSS: экранирование вывода
- Сессии: secure cookies

---

## 🚀 Продакшн

### Apache (.htaccess)

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php [QSA,L]
```

### Nginx

```nginx
location /helpdesk {
    try_files $uri $uri/ /helpdesk/index.php?$query_string;
}
```

---

## 📝 Лицензия

MIT © 2026 hypo69
