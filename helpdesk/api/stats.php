<?php
/**
 * Helpdesk API - Statistics
 * Returns aggregate helpdesk statistics
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../src/Ticket.php';

$ticket = new Ticket();
$stats = $ticket->getStats();

echo json_encode([
    'status' => 'success',
    'stats' => $stats
]);
