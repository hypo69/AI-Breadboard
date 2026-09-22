<?php
/**
 * Helpdesk Authentication Manager
 * JWT-based authentication with password hashing
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/Database.php';

class Auth {
    private static ?Auth $instance = null;
    private PDO $db;
    private array $user = null;
    
    private function __construct() {
        $this->db = Database::getConnection();
        $this->startSession();
        $this->loadCurrentUser();
    }
    
    public static function getInstance(): Auth {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function startSession(): void {
        if (session_status() === PHP_SESSION_NONE) {
            session_name(SESSION_NAME);
            session_set_cookie_params([
                'lifetime' => SESSION_LIFETIME,
                'path' => '/',
                'secure' => isset($_SERVER['HTTPS']),
                'httponly' => true,
                'samesite' => 'Strict'
            ]);
            session_start();
        }
    }
    
    private function loadCurrentUser(): void {
        if (isset($_SESSION['user_id'])) {
            $this->user = $this->db->executeOne(
                "SELECT * FROM users WHERE id = ? AND is_active = 1",
                [$_SESSION['user_id']]
            );
        }
    }
    
    public function getUser(): ?array {
        return $this->user;
    }
    
    public function isLoggedIn(): bool {
        return $this->user !== null;
    }
    
    public function hasRole(string $role): bool {
        return $this->user && in_array($this->user['role'], [$role, 'admin']);
    }
    
    public function login(string $email, string $password): array {
        $user = $this->db->executeOne(
            "SELECT * FROM users WHERE email = ?",
            [$email]
        );
        
        if (!$user || !password_verify($password, $user['password_hash'])) {
            return ['success' => false, 'message' => 'Invalid credentials'];
        }
        
        if (!$user['is_active']) {
            return ['success' => false, 'message' => 'Account is deactivated'];
        }
        
        // Update last login
        $this->db->execute(
            "UPDATE users SET last_login = NOW() WHERE id = ?",
            [$user['id']]
        );
        
        // Create session
        $_SESSION['user_id'] = $user['id'];
        $this->user = $user;
        
        // Create JWT token
        $token = $this->createToken($user['id']);
        
        return [
            'success' => true,
            'token' => $token,
            'user' => [
                'id' => $user['id'],
                'email' => $user['email'],
                'name' => $user['name'],
                'role' => $user['role']
            ]
        ];
    }
    
    public function register(string $email, string $password, string $name): array {
        // Check if email exists
        $existing = $this->db->executeOne(
            "SELECT id FROM users WHERE email = ?",
            [$email]
        );
        
        if ($existing) {
            return ['success' => false, 'message' => 'Email already registered'];
        }
        
        // Create user
        $passwordHash = password_hash($password, PASSWORD_BCRYPT);
        $userId = $this->db->insert('users', [
            'email' => $email,
            'password_hash' => $passwordHash,
            'name' => $name,
            'role' => 'user',
            'is_active' => 1,
            'created_at' => date('Y-m-d H:i:s')
        ]);
        
        if (!$userId) {
            return ['success' => false, 'message' => 'Registration failed'];
        }
        
        // Auto-login
        return $this->login($email, $password);
    }
    
    public function logout(): void {
        $_SESSION = [];
        if (ini_get('session.use_cookies')) {
            $params = session_get_cookie_params();
            setcookie(
                SESSION_NAME,
                '',
                time() - 42000,
                $params['path'],
                $params['domain'],
                $params['secure'],
                $params['httponly']
            );
        }
        session_destroy();
        $this->user = null;
    }
    
    public function createToken(int $userId): string {
        $payload = [
            'sub' => $userId,
            'iat' => time(),
            'exp' => time() + JWT_EXPIRY
        ];
        
        return JWT::encode($payload, JWT_SECRET, JWT_ALGO);
    }
    
    public function verifyToken(string $token): ?array {
        try {
            $payload = JWT::decode($token, new Key(JWT_SECRET, JWT_ALGO));
            return (array)$payload;
        } catch (Exception $e) {
            return null;
        }
    }
    
    public function validateRequest(): array {
        $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        
        if (preg_match('/Bearer\s+(\S+)/', $authHeader, $matches)) {
            $token = $matches[1];
            $payload = $this->verifyToken($token);
            
            if ($payload && isset($payload['sub'])) {
                $user = $this->db->executeOne(
                    "SELECT * FROM users WHERE id = ? AND is_active = 1",
                    [(int)$payload['sub']]
                );
                
                if ($user) {
                    $this->user = $user;
                    return ['success' => true, 'user' => $user];
                }
            }
            
            return ['success' => false, 'message' => 'Invalid token'];
        }
        
        if (isset($_SESSION['user_id'])) {
            $this->loadCurrentUser();
            if ($this->user) {
                return ['success' => true, 'user' => $this->user];
            }
        }
        
        return ['success' => false, 'message' => 'Not authenticated'];
    }
}

// JWT class (minimal implementation)
class JWT {
    public static function encode(array $payload, string $key, string $algo = 'HS256'): string {
        $header = ['alg' => $algo, 'typ' => 'JWT'];
        $segments = [
            self::urlSafeB64Encode(json_encode($header)),
            self::urlSafeB64Encode(json_encode($payload))
        ];
        
        $signature = self::sign(implode('.', $segments), $key, $algo);
        $segments[] = self::urlSafeB64Encode($signature);
        
        return implode('.', $segments);
    }
    
    public static function decode(string $jwt, Key $key): stdClass {
        $parts = explode('.', $jwt);
        
        if (count($parts) !== 3) {
            throw new Exception('Invalid JWT format');
        }
        
        [$headerB64, $payloadB64, $signatureB64] = $parts;
        
        if (($header = self::urlSafeB64Decode($headerB64)) === false) {
            throw new Exception('Invalid JWT header');
        }
        
        if (($payload = self::urlSafeB64Decode($payloadB64)) === false) {
            throw new Exception('Invalid JWT payload');
        }
        
        if (self::verify(implode('.', [$headerB64, $payloadB64]), $signatureB64, $key->key, $key->algo) === false) {
            throw new Exception('Invalid JWT signature');
        }
        
        return json_decode($payload);
    }
    
    private static function sign(string $input, string $key, string $algo): string {
        switch ($algo) {
            case 'HS256':
                return hash_hmac('sha256', $input, $key, true);
            case 'HS384':
                return hash_hmac('sha384', $input, $key, true);
            case 'HS512':
                return hash_hmac('sha512', $input, $key, true);
            default:
                throw new Exception('Unsupported algorithm');
        }
    }
    
    private static function verify(string $input, string $signature, string $key, string $algo): bool {
        $expected = self::sign($input, $key, $algo);
        return hash_equals($expected, self::urlSafeB64Decode($signature));
    }
    
    private static function urlSafeB64Encode(string $data): string {
        return str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($data));
    }
    
    private static function urlSafeB64Decode(string $data): ?string {
        $mod4 = strlen($data) % 4;
        if ($mod4) {
            $data .= str_repeat('=', 4 - $mod4);
        }
        return base64_decode(str_replace(['-', '_'], ['+', '/'], $data));
    }
}

class Key {
    public function __construct(
        public string $key,
        public string $algo
    ) {}
}

// Initialize auth
$auth = Auth::getInstance();
