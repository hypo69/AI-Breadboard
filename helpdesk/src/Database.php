<?php
/**
 * Helpdesk Database Manager
 * PDO wrapper with connection pooling and error handling
 */

require_once __DIR__ . '/../config.php';

class Database {
    private static ?PDO $instance = null;
    
    public static function getConnection(): PDO {
        if (self::$instance === null) {
            try {
                $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
                $options = [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                    PDO::ATTR_PERSISTENT => false,
                ];
                
                self::$instance = new PDO($dsn, DB_USER, DB_PASS, $options);
                
                // Set timezone
                self::$instance->exec("SET time_zone = '" . date('P') . "'");
                
            } catch (PDOException $e) {
                self::handleError('Database connection failed: ' . $e->getMessage());
            }
        }
        
        return self::$instance;
    }
    
    public static function execute(string $sql, array $params = []): array {
        $stmt = self::getConnection()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }
    
    public static function executeOne(string $sql, array $params = []): ?array {
        $stmt = self::getConnection()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetch();
    }
    
    public static function insert(string $table, array $data): int {
        $columns = implode(', ', array_keys($data));
        $placeholders = ':' . implode(', :', array_keys($data));
        
        $sql = "INSERT INTO $table ($columns) VALUES ($placeholders)";
        $stmt = self::getConnection()->prepare($sql);
        $stmt->execute($data);
        
        return (int)self::getConnection()->lastInsertId();
    }
    
    public static function update(string $table, array $data, string $where, array $params = []): int {
        $set = [];
        foreach (array_keys($data) as $key) {
            $set[] = "$key = :$key";
        }
        $set = implode(', ', $set);
        
        $sql = "UPDATE $table SET $set WHERE $where";
        $stmt = self::getConnection()->prepare($sql);
        $stmt->execute(array_merge($data, $params));
        
        return $stmt->rowCount();
    }
    
    public static function delete(string $table, string $where, array $params = []): int {
        $sql = "DELETE FROM $table WHERE $where";
        $stmt = self::getConnection()->prepare($sql);
        $stmt->execute($params);
        return $stmt->rowCount();
    }
    
    private static function handleError(string $message): void {
        if (DEBUG_MODE) {
            die(json_encode([
                'status' => 'error',
                'message' => $message
            ]));
        }
        
        error_log($message);
        http_response_code(500);
        die(json_encode([
            'status' => 'error',
            'message' => 'Internal server error'
        ]));
    }
}
