<?php
declare(strict_types=1);

namespace Helpdesk;

use PDO;
use PDOException;
use RuntimeException;

/**
 * Класс управления подключением к MySQL/MariaDB через PDO
 */
class Database {
    private static ?PDO  = null;

    /**
     * Получение синглтона соединения PDO
     *
     * @return PDO
     * @throws RuntimeException
     */
    public static function getConnection(): PDO {
        if (self:: === null) {
             = self::loadSecrets();
             = ['db'] ?? [
                'hostname' => '77.37.35.16',
                'db'       => 'u177424397_ai_bb_helpdesk',
                'user'     => 'u177424397_ai_bb_helpdesk',
                'password' => '@Davidka#1969'
            ];

             = sprintf(
                'mysql:host=%s;dbname=%s;charset=utf8mb4',
                ['hostname'],
                ['db']
            );

             = [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
                PDO::MYSQL_ATTR_INIT_COMMAND => 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
            ];

            try {
                self:: = new PDO(, ['user'], ['password'], );
            } catch (PDOException ) {
                throw new RuntimeException('Ошибка подключения к базе данных: ' . ->getMessage(), (int)->getCode(), );
            }
        }

        return self::;
    }

    /**
     * Загрузка параметров подключения и секретов
     *
     * @return array<string, mixed>
     */
    public static function loadSecrets(): array {
         = [
            __DIR__ . '/secrets.json',
            dirname(__DIR__) . '/secrets.json',
            dirname(__DIR__, 2) . '/secrets.json',
        ];

        foreach ( as ) {
            if (file_exists()) {
                 = file_get_contents();
                 = json_decode(, true);
                if (is_array()) {
                    return ;
                }
            }
        }

        return [];
    }
}
