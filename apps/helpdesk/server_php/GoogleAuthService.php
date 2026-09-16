<?php
declare(strict_types=1);

namespace Helpdesk;

use PDO;
use Exception;
use RuntimeException;

/**
 * Сервис регистрации и аутентификации пользователей через Google OAuth 2.0 на PHP 8
 */
class GoogleAuthService {
    private PDO ;
    private string ;
    private string ;
    private string ;

    public function __construct(?PDO  = null) {
        ->db =  ?? Database::getConnection();

         = Database::loadSecrets();
         = ['google_oauth'] ?? [];

        ->clientId = (string)(['client_id'] ?? getenv('GOOGLE_CLIENT_ID') ?: '');
        ->clientSecret = (string)(['client_secret'] ?? getenv('GOOGLE_CLIENT_SECRET') ?: '');
        ->redirectUri = (string)(['redirect_uri'] ?? getenv('GOOGLE_REDIRECT_URI') ?: 'https://davidka.net/helpdesk/oauth_callback.php');
    }

    /**
     * Генерация ссылки для перехода пользователя на Google OAuth 2.0 Consent Screen
     *
     * @return string
     */
    public function getAuthUrl(): string {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

         = bin2hex(random_bytes(16));
        ['oauth_state'] = ;

         = [
            'client_id'     => ->clientId,
            'redirect_uri'  => ->redirectUri,
            'response_type' => 'code',
            'scope'         => 'openid email profile',
            'access_type'   => 'offline',
            'state'         => ,
            'prompt'        => 'select_account'
        ];

        return 'https://accounts.google.com/o/oauth2/v2/auth?' . http_build_query();
    }

    /**
     * Обработка ответа OAuth (Exchange authorization_code -> tokens -> userinfo -> DB registration)
     *
     * @param string 
     * @param string 
     * @return array<string, mixed>
     * @throws RuntimeException
     */
    public function handleCallback(string , string ): array {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        if (empty(['oauth_state']) || !hash_equals(['oauth_state'], )) {
            throw new RuntimeException('Недействительный параметр CSRF state.');
        }
        unset(['oauth_state']);

        // 1. Обмен кода авторизации на Access и Refresh токены
         = ->exchangeCodeForToken();
         = ['access_token'] ?? null;
         = ['refresh_token'] ?? null;
         = (int)(['expires_in'] ?? 3600);

        if (!) {
            throw new RuntimeException('Не удалось получить Access Token от Google.');
        }

        // 2. Получение профиля пользователя от Google UserInfo API
         = ->fetchGoogleUserInfo();
         = (string)(['sub'] ?? '');
         = (string)(['email'] ?? '');
         = (string)(['name'] ?? (['given_name'] ?? 'Google User'));
         = isset(['picture']) ? (string)['picture'] : null;

        if ( === '' ||  === '') {
            throw new RuntimeException('Не удалось извлечь идентификатор или email из профиля Google.');
        }

        // 3. Регистрация или авторизация пользователя в базе данных (в транзакции)
        ->db->beginTransaction();
        try {
            // Проверяем наличие привязанного Google-аккаунта
             = ->db->prepare('SELECT user_id FROM user_oauth_providers WHERE provider = \'google\' AND provider_user_id = ?');
            ->execute([]);
             = ->fetch();

             = null;
            if () {
                 = (int)['user_id'];
                
                // Обновляем аватар и токены
                 = ->db->prepare('UPDATE users SET avatar_url = ?, updated_at = NOW() WHERE id = ?');
                ->execute([, ]);

                 = date('Y-m-d H:i:s', time() + );
                 = ->db->prepare(
                    'UPDATE user_oauth_providers 
                     SET access_token = ?, 
                         refresh_token = COALESCE(?, refresh_token), 
                         token_expires_at = ?, 
                         raw_profile_data = ?, 
                         updated_at = NOW() 
                     WHERE provider = \'google\' AND provider_user_id = ?'
                );
                ->execute([
                    ,
                    ,
                    ,
                    json_encode(, JSON_UNESCAPED_UNICODE),
                    
                ]);
            } else {
                // Проверяем, существует ли уже пользователь с таким email
                 = ->db->prepare('SELECT id FROM users WHERE email = ?');
                ->execute([]);
                 = ->fetch();

                if () {
                     = (int)['id'];
                     = ->db->prepare('UPDATE users SET avatar_url = COALESCE(avatar_url, ?), updated_at = NOW() WHERE id = ?');
                    ->execute([, ]);
                } else {
                    // Создаем нового пользователя
                     = ->db->prepare('INSERT INTO users (email, name, avatar_url, role, status) VALUES (?, ?, ?, \'user\', \'active\')');
                    ->execute([, , ]);
                     = (int)->db->lastInsertId();
                }

                // Привязываем запись провайдера OAuth
                 = date('Y-m-d H:i:s', time() + );
                 = ->db->prepare(
                    'INSERT INTO user_oauth_providers (user_id, provider, provider_user_id, access_token, refresh_token, token_expires_at, raw_profile_data) 
                     VALUES (?, \'google\', ?, ?, ?, ?, ?)'
                );
                ->execute([
                    ,
                    ,
                    ,
                    ,
                    ,
                    json_encode(, JSON_UNESCAPED_UNICODE)
                ]);
            }

            // Создаем пользовательскую сессию
             = bin2hex(random_bytes(32));
             = date('Y-m-d H:i:s', time() + (86400 * 14)); // 14 дней
             = ->db->prepare('INSERT INTO user_sessions (id, user_id, ip_address, user_agent, expires_at) VALUES (?, ?, ?, ?, ?)');
            ->execute([
                ,
                ,
                ['REMOTE_ADDR'] ?? '127.0.0.1',
                ['HTTP_USER_AGENT'] ?? 'Unknown',
                
            ]);

            ->db->commit();

            ['helpdesk_user_id'] = ;
            ['helpdesk_session_id'] = ;

            return [
                'status'     => 'success',
                'user_id'    => ,
                'email'      => ,
                'name'       => ,
                'avatar_url' => ,
                'session_id' => 
            ];
        } catch (Exception ) {
            ->db->rollBack();
            throw ;
        }
    }

    /**
     * Обмен кода на токен через cURL
     *
     * @param string 
     * @return array<string, mixed>
     */
    private function exchangeCodeForToken(string ): array {
         = curl_init('https://oauth2.googleapis.com/token');
        curl_setopt_array(, [
            CURLOPT_POST           => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POSTFIELDS     => http_build_query([
                'code'          => ,
                'client_id'     => ->clientId,
                'client_secret' => ->clientSecret,
                'redirect_uri'  => ->redirectUri,
                'grant_type'    => 'authorization_code',
            ]),
            CURLOPT_HTTPHEADER     => ['Content-Type: application/x-www-form-urlencoded'],
            CURLOPT_TIMEOUT        => 10,
        ]);

         = curl_exec();
         = curl_getinfo(, CURLINFO_HTTP_CODE);
        curl_close();

        if ( !== 200 || !is_string()) {
            throw new RuntimeException('Ошибка запроса токена Google: ' . ( ?: 'Empty response'));
        }

         = json_decode(, true);
        return is_array() ?  : [];
    }

    /**
     * Получение данных пользователя через Google UserInfo API
     *
     * @param string 
     * @return array<string, mixed>
     */
    private function fetchGoogleUserInfo(string ): array {
         = curl_init('https://www.googleapis.com/oauth2/v3/userinfo');
        curl_setopt_array(, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => ["Authorization: Bearer {}"],
            CURLOPT_TIMEOUT        => 10,
        ]);

         = curl_exec();
         = curl_getinfo(, CURLINFO_HTTP_CODE);
        curl_close();

        if ( !== 200 || !is_string()) {
            throw new RuntimeException('Ошибка получения профиля из Google UserInfo API: ' . ( ?: 'Empty response'));
        }

         = json_decode(, true);
        return is_array() ?  : [];
    }
}
