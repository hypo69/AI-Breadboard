<?php
/**
 * Helpdesk Configuration
 * Autonoums PHP module for support ticket management
 */

// Database configuration
define('DB_HOST', 'localhost');
define('DB_NAME', 'ai_breadboard_helpdesk');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_CHARSET', 'utf8mb4');

// JWT configuration
define('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production');
define('JWT_ALGO', 'HS256');
define('JWT_EXPIRY', 3600 * 24 * 7); // 7 days

// Application settings
define('APP_NAME', 'Helpdesk');
define('APP_URL', 'http://localhost:8080/helpdesk');
define('TIMEZONE', 'UTC');

// Error reporting (disable in production)
define('DEBUG_MODE', true);

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
