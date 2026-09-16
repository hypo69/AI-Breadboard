<?php
declare(strict_types=1);

/**
 * Точка возврата Google OAuth 2.0 (Redirect URI Callback)
 */

require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/GoogleAuthService.php';

 = ['code'] ?? null;
 = ['state'] ?? null;
 = ['error'] ?? null;

if () {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'status'  => 'error',
        'error'   => 'Google OAuth Error: ' . htmlspecialchars((string))
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

if (! || !) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'status'  => 'error',
        'error'   => 'Отсутствуют обязательные параметры (code, state).'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

try {
     = new \Helpdesk\GoogleAuthService();
     = ->handleCallback((string), (string));

    // Установка защищенной Cookie сессии
    setcookie('hd_session', (string)['session_id'], [
        'expires'  => time() + (86400 * 14),
        'path'     => '/',
        'domain'   => '',
        'secure'   => true,
        'httponly' => true,
        'samesite' => 'Lax'
    ]);

    // Перенаправление на личный кабинет или выдача JSON результата
    if (isset(['format']) && ['format'] === 'json') {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        exit;
    }

    header('Location: /helpdesk/');
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
