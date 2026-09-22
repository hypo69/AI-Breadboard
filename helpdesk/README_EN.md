# AI-Breadboard Helpdesk — Installation Guide

## 📦 Installation

### 1. Create TWO databases

```sql
-- Users database
CREATE DATABASE helpdesk_users CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tickets database
CREATE DATABASE helpdesk_tickets CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Load schemas

```bash
# Users schema
mysql -u root -p helpdesk_users < helpdesk/db/schema_users.sql

# Tickets schema
mysql -u root -p helpdesk_tickets < helpdesk/db/schema_tickets.sql
```

### 3. Configure

Edit `helpdesk/config.php`:

```php
<?php
// Database - USERS
define('DB_HOST', 'localhost');
define('DB_NAME', 'helpdesk_users');
define('DB_USER', 'helpdesk_user');
define('DB_PASS', 'StrongPassword123!');

// Database - TICKETS (NEW!)
define('DB_TICKETS_HOST', 'localhost');
define('DB_TICKETS_NAME', 'helpdesk_tickets');
define('DB_TICKETS_USER', 'helpdesk_user');
define('DB_TICKETS_PASS', 'StrongPassword123!');

// JWT
define('JWT_SECRET', 'your-super-secret-jwt-key');
define('JWT_EXPIRY', 3600 * 24 * 7);

// App
define('APP_URL', 'https://helpdesk.yourdomain.com');
define('DEBUG_MODE', false);
```

### 4. Run server

```bash
cd helpdesk
php -S localhost:8080
```

Open: `https://helpdesk.yourdomain.com`

---

## 🔐 Default Login

- **Email:** `admin@helpdesk.local`
- **Password:** `admin123`

---

## 📊 Database Structure

### helpdesk_users (Users)
| Table | Description |
|-------|-------------|
| `users` | Users (email, password_hash, role) |
| `sessions` | JWT tokens |
| `user_activity_log` | Activity log |

### helpdesk_tickets (Tickets)
| Table | Description |
|-------|-------------|
| `helpdesk_tickets` | Tickets (subject, status, priority) |
| `helpdesk_messages` | Messages |
| `helpdesk_operators` | Operator status |
| `helpdesk_sequences` | Auto-increment |

---

## 🎯 Separation of Concerns

| Database | Data | Responsibility |
|----------|------|----------------|
| `helpdesk_users` | Users, sessions, logs | Authentication |
| `helpdesk_tickets` | Tickets, messages, operators | Support |

---

## 🔧 Configuration

### Change admin password

```sql
UPDATE users 
SET password_hash = '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi' 
WHERE email = 'admin@helpdesk.local';
```

### Add operator

```sql
INSERT INTO users (email, password_hash, name, role, is_active) 
VALUES ('operator@helpdesk.local', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Operator', 'operator', 1);

INSERT INTO helpdesk_operators (id, user_id, display_name, role, is_online) 
VALUES ('op_001', LAST_INSERT_ID(), 'Support Operator', 'operator', 0);
```

---

## 📱 Interface

- **Login/Register** — Authentication
- **Dashboard** — Statistics and ticket creation
- **Ticket List** — Filter by status/priority
- **Messages** — Ticket conversation

---

## 🛡️ Security

- Passwords: bcrypt (10k iterations)
- Tokens: JWT with expiration
- SQL: prepared statements
- XSS: output escaping
- Sessions: secure cookies

---

## 🚀 Production

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

## 📝 License

MIT © 2026 hypo69
