<?php
/**
 * Helpdesk API - Messages
 * Handles message CRUD operations
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../src/Auth.php';
require_once __DIR__ . '/../src/Message.php';

$method = $_SERVER['REQUEST_METHOD'];
$auth = Auth::getInstance();

// Validate authentication
$result = $auth->validateRequest();
if (!$result['success']) {
    http_response_code(401);
    echo json_encode(['status' => 'error', 'message' => $result['message']]);
    exit;
}

switch ($method) {
    case 'GET':
        handleGet();
        break;
    
    case 'POST':
        handlePost();
        break;
    
    case 'DELETE':
        handleDelete();
        break;
    
    default:
        http_response_code(405);
        echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
}

function handleGet() {
    $ticketId = $_GET['ticket_id'] ?? '';
    
    if (empty($ticketId)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Ticket ID required']);
        return;
    }
    
    $message = new Message();
    $messages = $message->getForTicket($ticketId);
    
    echo json_encode([
        'status' => 'success',
        'messages' => $messages,
        'count' => count($messages)
    ]);
}

function handlePost() {
    $ticketId = $_GET['ticket_id'] ?? '';
    
    if (empty($ticketId)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Ticket ID required']);
        return;
    }
    
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($input) || empty($input['content'])) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Content required']);
        return;
    }
    
    $message = new Message();
    $result = $message->create($ticketId, $input);
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'message' => $result['message']
        ]);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}

function handleDelete() {
    $messageId = $_GET['message_id'] ?? '';
    
    if (empty($messageId)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Message ID required']);
        return;
    }
    
    $message = new Message();
    $result = $message->delete($messageId);
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'message' => $result['message']
        ]);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}
