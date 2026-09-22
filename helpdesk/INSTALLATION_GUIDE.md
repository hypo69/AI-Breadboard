# 🚀 Полное руководство по установке Helpdesk на провайдере

Это пошаговое руководство для установки автономного PHP Helpdesk-модуля на виртуальный хостинг или VPS.

---

## 📋 Предварительные требования

Перед установкой убедитесь, что у вас есть:

- ✅ Доступ к виртуальному хостингу или VPS
- ✅ Доменное имя (например: `helpdesk.yourdomain.com`)
- ✅ Доступ к phpMyAdmin или MySQL CLI
- ✅ FTP/SFTP доступ или SSH доступ
- ✅ PHP 8.0+ (обязательно)
- ✅ MariaDB/MySQL 5.7+ (обязательно)
- ✅ Composer (рекомендуется)

---

## 🎯 Варианты установки

Выберите один из вариантов:

| Вариант | Подходит для | Сложность | Время |
|---------|--------------|-----------|-------|
| **1. Через FTP** | Общий хостинг (cPanel) | ⭐⭐ | 15-20 мин |
| **2. Через SSH** | VPS/Dedicated сервер | ⭐⭐⭐ | 10-15 мин |
| **3. Автоматический** | Поддержка 1-click install | ⭐ | 5 мин |

---

## 📦 Вариант 1: Установка через FTP (cPanel)

### Шаг 1: Подготовка базы данных

1. Войдите в **cPanel**
2. Перейдите в раздел **MySQL Databases**
3. Создайте новую базу данных:
   - Имя базы: `yourdomain_helpdesk`
   - Пароль: `StrongPassword123!` (сохраните его!)

4. Создайте пользователя:
   - Имя пользователя: `yourdomain_helpdesk`
   - Пароль: тот же, что выше

5. Свяжите пользователя с базой:
   - Выберите пользователя и базу
   - Нажмите **Add**
   - Выберите **All Privileges**
   - Нажмите **Make Changes**

### Шаг 2: Загрузка файлов через FTP

1. Скачайте FTP-клиент (FileZilla, WinSCP, Cyberduck)
2. Подключитесь к серверу:
   - Host: `ftp.yourdomain.com` или IP-адрес
   - Username: ваш cPanel username
   - Password: ваш cPanel password
   - Port: 21 (FTP) или 22 (SFTP)

3. Загрузите файлы:
   - Локальная папка: `C:\Users\onela\AppData\Local\AI-Breadboard\helpdesk`
   - Удаленная папка: `public_html/helpdesk` (или `www/helpdesk`)

### Шаг 3: Настройка конфигурации

1. В FTP-клиенте найдите файл `config.php`
2. Правой кнопкой → **View/Edit**
3. Отредактируйте следующие строки:

```php
<?php
/**
 * Helpdesk Configuration
 */

// Database configuration
define('DB_HOST', 'localhost');           // Обычно localhost
define('DB_NAME', 'yourdomain_helpdesk'); // Имя вашей базы
define('DB_USER', 'yourdomain_helpdesk'); // Имя пользователя
define('DB_PASS', 'StrongPassword123!');  // Пароль базы
define('DB_CHARSET', 'utf8mb4');

// JWT configuration
define('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production');
// ЗАМЕНИТЕ НА СЛУ��АЙНУЮ СТРОКУ!
// Можно сгенерировать здесь: https://generate-secret.com/32/

// Application settings
define('APP_NAME', 'Helpdesk');
define('APP_URL', 'https://helpdesk.yourdomain.com'); // Ваш домен
define('TIMEZONE', 'Europe/Moscow'); // Ваш часовой пояс

// Error reporting (disable in production)
define('DEBUG_MODE', false); // ВАЖНО: false в продакшене!

// Paths
define('ROOT_DIR', __DIR__);
define('SRC_DIR', ROOT_DIR . '/src');
define('API_DIR', ROOT_DIR . '/api');
define('PUBLIC_DIR', ROOT_DIR . '/public');

// Session configuration
define('SESSION_NAME', 'helpdesk_session');
define('SESSION_LIFETIME', 3600 * 24 * 7);

// Email configuration (optional)
define('SMTP_HOST', '');
define('SMTP_PORT', 587);
define('SMTP_USER', '');
define('SMTP_PASS', '');
define('SMTP_FROM', 'noreply@yourdomain.com');
```

4. Сохраните файл

### Шаг 4: Инициализация базы данных

#### Вариант А: Через phpMyAdmin (проще)

1. В cPanel откройте **phpMyAdmin**
2. Выберите вашу базу данных `yourdomain_helpdesk`
3. Нажмите **Import**
4. Выберите файл: `db/schema.sql` (из загруженных файлов)
5. Нажмите **Go**

#### Вариант Б: Через SSH (если есть доступ)

```bash
# Подключитесь по SSH
ssh username@yourdomain.com

# Загрузите схему
mysql -u yourdomain_helpdesk -p yourdomain_helpdesk < public_html/helpdesk/db/schema.sql
```

### Шаг 5: Настройка прав доступа

В cPanel откройте **File Manager** или используйте FTP:

1. Перейдите в папку `helpdesk`
2. Правой кнопкой → **Permissions** (или **Change Permissions**)
3. Установите:
   - Папки: `755`
   - Файлы: `644`
   - `config.php`: `600` (для безопасности)

### Шаг 6: Проверка установки

1. Откройте браузер
2. Перейдите: `https://helpdesk.yourdomain.com`
3. Вы должны увидеть страницу входа

**Если ошибка "Database connection failed":**
- Проверьте настройки в `config.php`
- Убедитесь, что база создана и пользователь привязан
- Проверьте, что схема загружена

---

## 🖥️ Вариант 2: Установка через SSH (VPS/Dedicated)

### Шаг 1: Подключение к серверу

```bash
ssh root@your-server-ip
# или
ssh username@your-server-ip
```

### Шаг 2: Установка зависимостей

#### Ubuntu/Debian:

```bash
# Обновите систему
apt update && apt upgrade -y

# Установите LAMP stack
apt install -y apache2 mysql-server php php-mysql php-curl php-gd php-mbstring php-xml php-zip

# Проверьте версию PHP
php -v
# Должно быть PHP 8.0+
```

#### CentOS/RHEL:

```bash
# Установите LAMP stack
yum install -y httpd mariadb-server php php-mysqlnd php-curl php-gd php-mbstring php-xml php-zip

# Запустите службы
systemctl start httpd
systemctl enable httpd
systemctl start mariadb
systemctl enable mariadb
```

### Шаг 3: Создание базы данных

```bash
# Подключитесь к MySQL
mysql -u root -p

# Создайте базу
CREATE DATABASE helpdesk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Создайте пользователя
CREATE USER 'helpdesk_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';

# Выдайте права
GRANT ALL PRIVILEGES ON helpdesk.* TO 'helpdesk_user'@'localhost';
FLUSH PRIVILEGES;

# Выход
EXIT;
```

### Шаг 4: Загрузка файлов

```bash
# Перейдите в веб-директорию
cd /var/www/html

# Скачайте helpdesk (если на GitHub)
wget https://github.com/your-repo/helpdesk/archive/main.zip
unzip main.zip
mv helpdesk-main helpdesk

# Или скопируйте через SCP
scp -r /local/path/helpdesk username@server:/var/www/html/helpdesk
```

### Шаг 5: Настройка конфигурации

```bash
cd /var/www/html/helpdesk

# Отредактируйте config.php
nano config.php
```

```php
<?php
define('DB_HOST', 'localhost');
define('DB_NAME', 'helpdesk');
define('DB_USER', 'helpdesk_user');
define('DB_PASS', 'StrongPassword123!');
define('DB_CHARSET', 'utf8mb4');

define('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production');
define('APP_URL', 'https://helpdesk.yourdomain.com');
define('DEBUG_MODE', false);
```

### Шаг 6: Загрузка схемы

```bash
mysql -u helpdesk_user -p helpdesk < /var/www/html/helpdesk/db/schema.sql
```

### Шаг 7: Настройка прав

```bash
# Установите права
chown -R www-data:www-data /var/www/html/helpdesk
chmod -R 755 /var/www/html/helpdesk
chmod 600 /var/www/html/helpdesk/config.php

# Для CentOS
chown -R apache:apache /var/www/html/helpdesk
```

### Шаг 8: Настройка Apache/Nginx

#### Apache (.htaccess уже есть, но проверьте):

```bash
# Включите mod_rewrite
a2enmod rewrite

# Перезапустите Apache
systemctl restart apache2
```

#### Nginx (если используется):

```bash
nano /etc/nginx/sites-available/helpdesk
```

```nginx
server {
    listen 80;
    server_name helpdesk.yourdomain.com;
    root /var/www/html/helpdesk;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.0-fpm.sock;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

```bash
# Включите сайт
ln -s /etc/nginx/sites-available/helpdesk /etc/nginx/sites-enabled/
nginx -t  # Проверка конфигурации
systemctl restart nginx
```

### Шаг 9: Настройка SSL (обязательно!)

```bash
# Установите Certbot
apt install -y certbot python3-certbot-apache

# Получите сертификат
certbot --apache -d helpdesk.yourdomain.com

# Авто-обновление
systemctl enable certbot.timer
```

---

## 🤖 Вариант 3: Автоматическая установка (1-клик)

Некоторые хостинги поддерживают 1-click установку:

### Via Softaculous (cPanel):

1. В cPanel откройте **Softaculous Apps Installer**
2. Найдите **PHP Scripts** → **Custom Script**
3. Загрузите архив `helpdesk.zip`
4. Следуйте инструкциям

### Via Docker:

```bash
# Создайте docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  helpdesk:
    image: php:8.0-apache
    ports:
      - "8080:80"
    volumes:
      - ./helpdesk:/var/www/html
    depends_on:
      - mysql
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_DATABASE=helpdesk
      - MYSQL_USER=helpdesk
      - MYSQL_PASSWORD=StrongPassword123!

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=RootPassword123!
      - MYSQL_DATABASE=helpdesk
      - MYSQL_USER=helpdesk
      - MYSQL_PASSWORD=StrongPassword123!
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
EOF

# Запустите
docker-compose up -d

# Загрузите схему
docker exec -i helpdesk_mysql_1 mysql -u helpdesk -pStrongPassword123! helpdesk < /var/www/html/db/schema.sql
```

---

## 🔧 После установки

### 1. Проверка работоспособности

Откройте: `https://helpdesk.yourdomain.com`

**Должны увидеть:**
- ✅ Страницу входа
- ✅ Без ошибок PHP
- ✅ Без ошибок базы данных

### 2. Первый вход

- **Email:** `admin@helpdesk.local`
- **Password:** `admin123`

**Сразу после входа:**
1. Смените пароль админа
2. Создайте операторов
3. Настройте SMTP для уведомлений

### 3. Настройка SMTP (рекомендуется)

В `config.php`:

```php
define('SMTP_HOST', 'smtp.gmail.com'); // или ваш SMTP
define('SMTP_PORT', 587);
define('SMTP_USER', 'your-email@gmail.com');
define('SMTP_PASS', 'your-app-password');
define('SMTP_FROM', 'helpdesk@yourdomain.com');
```

Для Gmail используйте **App Password** (не пароль от аккаунта).

### 4. Настройка cron (для автоматических задач)

```bash
# Отредактируйте crontab
crontab -e

# Добавьте задачу (очистка старых сессий)
0 3 * * * curl -s https://helpdesk.yourdomain.com/api/cleanup.php > /dev/null 2>&1
```

---

## 🔒 Безопасность

### Обязательные настройки:

1. **Измените JWT_SECRET:**
   ```bash
   # Сгенерируйте случайную строку
   openssl rand -base64 32
   ```

2. **Отключите DEBUG_MODE:**
   ```php
   define('DEBUG_MODE', false);
   ```

3. **Настройте HTTPS:**
   - Используйте Let's Encrypt
   - Перенаправляйте HTTP → HTTPS

4. **Ограничьте доступ к config.php:**
   ```apache
   # В .htaccess
   <files "config.php">
       order allow,deny
       deny from all
   </files>
   ```

5. **Настройте firewall:**
   ```bash
   # Разрешите только HTTP/HTTPS
   ufw allow 'Apache Full'
   ufw enable
   ```

6. **Регулярные бэкапы:**
   ```bash
   # Добавьте в crontab
   0 2 * * * mysqldump -u helpdesk -pStrongPassword123! helpdesk | gzip > /backup/helpdesk_$(date +\%Y\%m\%d).sql.gz
   ```

---

## 🐛 Устранение неполадок

### Ошибка: "Database connection failed"

**Причины:**
1. Неверные данные в `config.php`
2. База не создана
3. Пользователь не привязан к базе
4. MySQL не запущен

**Решение:**
```bash
# Проверьте подключение к MySQL
mysql -u yourdomain_helpdesk -p -h localhost yourdomain_helpdesk

# Если ошибка, проверьте статус MySQL
systemctl status mysql
```

### Ошибка: "404 Not Found"

**Причины:**
1. `.htaccess` не работает
2. `mod_rewrite` отключен

**Решение:**
```bash
# Для Apache
a2enmod rewrite
systemctl restart apache2

# Проверьте AllowOverride
nano /etc/apache2/sites-available/000-default.conf
# Должно быть: AllowOverride All
```

### Ошибка: "500 Internal Server Error"

**Причины:**
1. Ошибки в PHP коде
2. Неверные права доступа
3. Недостаточно памяти PHP

**Решение:**
```bash
# Включите логирование ошибок
nano config.php
# define('DEBUG_MODE', true);

# Проверьте логи
tail -f /var/log/apache2/error.log
```

### Ошибка: "Class 'PDO' not found"

**Решение:**
```bash
# Установите расширение PDO
apt install php-pdo php-mysql
systemctl restart apache2
```

### Ошибка: "JWT library not found"

**Решение:**
```bash
# Установите Composer
curl -sS https://getcomposer.org/installer | php
mv composer.phar /usr/local/bin/composer

# Установите зависимости
cd /var/www/html/helpdesk
composer install
```

---

## 📊 Мониторинг

### Проверка статуса:

```bash
# Проверка PHP
php -v

# Проверка MySQL
mysql -u root -p -e "SHOW DATABASES;"

# Проверка файлов
ls -la /var/www/html/helpdesk
```

### Логи:

```bash
# Apache
tail -f /var/log/apache2/error.log

# PHP
tail -f /var/log/php8.0-fpm.log

# MySQL
tail -f /var/log/mysql/error.log
```

---

## 🔄 Обновление

### Через Git:

```bash
cd /var/www/html/helpdesk
git pull origin main
composer install
```

### Вручную:

1. Скачайте новую версию
2. Загрузите файлы (оставьте `config.php`)
3. Запустите миграции (если есть)
4. Проверьте работоспособность

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи ошибок
2. Убедитесь, что все зависимости установлены
3. Проверьте права доступа к файлам
4. Отключите DEBUG_MODE перед публикацией

---

## 📝 Чеклист после установки

- [ ] База данных создана
- [ ] Схема загружена
- [ ] `config.php` настроен
- [ ] `DEBUG_MODE = false`
- [ ] `JWT_SECRET` изменен
- [ ] HTTPS настроен
- [ ] Права доступа установлены
- [ ] Первый вход выполнен
- [ ] Пароль админа изменен
- [ ] SMTP настроен (опционально)
- [ ] Бэкапы настроены
- [ ] Мониторинг настроен

---

## 🎉 Готово!

Ваш Helpdesk-модуль установлен и готов к работе!

**Следующие шаги:**
1. Создайте учетные записи операторов
2. Настройте интеграцию с AI-Breadboard (если нужно)
3. Настраивайте уведомления
4. Начните использовать систему

---

**Удачи! 🚀**
