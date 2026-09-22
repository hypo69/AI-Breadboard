# Helpdesk - PHP Development Server

Simple PHP development server for helpdesk module.

## Usage

```bash
php -S localhost:8080 -t .
```

Then open: http://localhost:8080

## Configuration

Edit `config.php` before running:

```php
define('DB_HOST', 'localhost');
define('DB_NAME', 'ai_breadboard_helpdesk');
define('DB_USER', 'root');
define('DB_PASS', '');
define('JWT_SECRET', 'your-super-secret-jwt-key');
```

## Database Setup

Run the schema:

```bash
mysql -u root -p < db/schema.sql
```

Or use the migration:

```bash
mysql -u root -p ai_breadboard_helpdesk < db/migrations/0001_initial_schema.sql
```

## Default Login

- **Email:** admin@helpdesk.local
- **Password:** admin123

## API Testing with cURL

### Login

```bash
curl -X POST http://localhost:8080/api/auth.php \
  -H "Content-Type: application/json" \
  -d '{"action":"login","email":"admin@helpdesk.local","password":"admin123"}'
```

### Create Ticket

```bash
curl -X POST http://localhost:8080/api/tickets.php \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "subject": "Test Ticket",
    "category": "general",
    "priority": "normal",
    "message": "This is a test ticket"
  }'
```

### Get Tickets

```bash
curl http://localhost:8080/api/tickets.php \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Production Deployment

### Apache

```apache
<VirtualHost *:80>
    ServerName helpdesk.example.com
    DocumentRoot /var/www/html/helpdesk
    
    <Directory /var/www/html/helpdesk>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

### Nginx

```nginx
server {
    listen 80;
    server_name helpdesk.example.com;
    root /var/www/html/helpdesk;
    
    index index.php;
    
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.0-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
    }
}
```

## Security Checklist

- [ ] Change `JWT_SECRET` in `config.php`
- [ ] Use strong database password
- [ ] Enable HTTPS
- [ ] Set proper file permissions
- [ ] Disable `DEBUG_MODE` in production
- [ ] Configure firewall
- [ ] Enable error logging
- [ ] Regular database backups

## Support

For issues, check:
- PHP error logs
- Database connection
- File permissions
