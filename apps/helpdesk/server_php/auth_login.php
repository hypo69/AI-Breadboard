<?php
declare(strict_types=1);

/**
 * Точка входа для старта Google OAuth 2.0 авторизации в Helpdesk
 */

require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/GoogleAuthService.php';

try {
     = new \Helpdesk\GoogleAuthService();
     = ->getAuthUrl();
    header('Location: ' . );
    exit;
} catch (\Throwable ) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'status'  => 'error',
        'message' => ->getMessage()
    ], JSON_UNESCAPED_UNICODE);
    exit;
}
