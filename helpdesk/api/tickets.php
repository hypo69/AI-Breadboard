<?php
/**
 * Helpdesk API - Tickets
 * Handles ticket CRUD operations
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../src/Auth.php';
require_once __DIR__ . '/../src/Ticket.php';

$method = $_SERVER['REQUEST_METHOD'];
$auth = Auth::getInstance();

// Validate authentication
if ($method !== 'GET') {
    $result = $auth->validateRequest();
    if (!$result['success']) {
        http_response_code(401);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
        exit;
    }
}

switch ($method) {
    case 'GET':
        handleGet();
        break;
    
    case 'POST':
        handlePost();
        break;
    
    case 'PATCH':
    case 'PUT':
        handleUpdate();
        break;
    
    default:
        http_response_code(405);
        echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
}

function handleGet() {
    $ticketId = $_GET['ticket_id'] ?? '';
    $auth = Auth::getInstance();
    
    if ($ticketId) {
        // Get single ticket
        $ticket = new Ticket();
        $result = $ticket->getById($ticketId);
        
        if ($result) {
            echo json_encode([
                'status' => 'success',
                'ticket' => $result
            ]);
        } else {
            http_response_code(404);
            echo json_encode(['status' => 'error', 'message' => 'Ticket not found']);
        }
    } else {
        // List tickets
        $ticket = new Ticket();
        $filters = [
            'status' => $_GET['status'] ?? null,
            'priority' => $_GET['priority'] ?? null,
            'user_id' => $_GET['user_id'] ?? null,
            'search' => $_GET['search'] ?? null
        ];
        
        $tickets = $ticket->getAll($filters);
        
        echo json_encode([
            'status' => 'success',
            'tickets' => $tickets,
            'count' => count($tickets)
        ]);
    }
}

function handlePost() {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($input)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Invalid JSON']);
        return;
    }
    
    $ticket = new Ticket();
    $result = $ticket->create($input);
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'ticket' => $result['ticket'],
            'message_id' => $result['message_id']
        ]);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}

function handleUpdate() {
    $ticketId = $_GET['ticket_id'] ?? '';
    
    if (empty($ticketId)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Ticket ID required']);
        return;
    }
    
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($input)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Invalid JSON']);
        return;
    }
    
    $ticket = new Ticket();
    $result = $ticket->update($ticketId, $input);
    
    if ($result['success']) {
        echo json_encode([
            'status' => 'success',
            'ticket' => $result['ticket']
        ]);
    } else {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => $result['message']]);
    }
}
