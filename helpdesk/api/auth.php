<?php
/**
 * Helpdesk API - Authentication
 * Handles login, register, logout, and token validation
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../src/Auth.php';

$method = $_SERVER['REQUEST_METHOD'];

switch ($method) {
    case 'POST':
        handlePost();
        break;
    
    case 'GET':
        handleGet();
        break;
    
    case 'DELETE':
        handleDelete();
        break;
    
    default:
        http_response_code(405);
        echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
}

function handlePost() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($input)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Invalid JSON']);
        return;
    }
    
    $action = $input['action'] ?? '';
    
    switch ($action) {
        case 'login':
            handleLogin($input);
            break;
        
        case 'register':
            handleRegister($input);
            break;
        
        case 'validate':
            handleValidate();
            break;
        
        default:
            http_response_code(400);
            echo json_encode(['status' => 'error', 'message' => 'Unknown action']);
    }
}

function handleGet() {
    $auth = Auth::getInstance();
    
    if ($auth->isLoggedIn()) {
        echo json_encode([
            'status' => 'success',
            'user' => [
                'id' => $auth->getUser()['id'],
                'email' => $auth->getUser()['email'],
                'name' => $auth->getUser()['name'],
                'role' => $auth->getUser()['role']
            ]
        ]);
    } else {
        http_response_code(401);
        echo json_encode(['status' => 'error', 'message' => 'Not authenticated']);
    }
}

function handleDelete() {
    $auth = Auth::getInstance();
    $auth->logout();
    
    echo json_encode(['status' => 'success', 'message' => 'Logged out']);
}

function handleLogin(array $data) {
    $auth = Auth::getInstance();
    
    if (empty($data['email']) || empty($data['password'])) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Email and password required']);
        return;
    }
    
    $result = $auth->login($data['email'], $data['password']);
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'token' => $result['token'],
            'user' => $result['user']
        ]);
    } else {
        http_response_code(401);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}

function handleRegister(array $data) {
    $auth = Auth::getInstance();
    
    if (empty($data['email']) || empty($data['password']) || empty($data['name'])) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'All fields required']);
        return;
    }
    
    $result = $auth->register($data['email'], $data['password'], $data['name']);
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'token' => $result['token'],
            'user' => $result['user']
        ]);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}

function handleValidate() {
    $auth = Auth::getInstance();
    $result = $auth->validateRequest();
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'user' => $result['user']
        ]);
    } else {
        http_response_code(401);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}
