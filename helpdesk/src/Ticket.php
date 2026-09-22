<?php
/**
 * Helpdesk Ticket Manager
 * CRUD operations for support tickets
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/Auth.php';

class Ticket {
    private PDO $db;
    private Auth $auth;
    
    public function __construct() {
        $this->db = Database::getConnection();
        $this->auth = Auth::getInstance();
    }
    
    public function getAll(array $filters = []): array {
        $sql = "SELECT t.*, u.name as user_name, u.email as user_email
                FROM helpdesk_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                WHERE 1=1";
        $params = [];
        
        // Filter by status
        if (!empty($filters['status']) && $filters['status'] !== 'all') {
            $sql .= " AND t.status = ?";
            $params[] = $filters['status'];
        }
        
        // Filter by priority
        if (!empty($filters['priority'])) {
            $sql .= " AND t.priority = ?";
            $params[] = $filters['priority'];
        }
        
        // Filter by user (non-admin can only see their own tickets)
        $user = $this->auth->getUser();
        if ($user && $user['role'] !== 'admin' && $user['role'] !== 'operator') {
            $sql .= " AND t.user_id = ?";
            $params[] = $user['id'];
        }
        
        // Filter by user_id parameter
        if (!empty($filters['user_id'])) {
            $sql .= " AND t.user_id = ?";
            $params[] = $filters['user_id'];
        }
        
        // Search
        if (!empty($filters['search'])) {
            $sql .= " AND (t.subject LIKE ? OR t.user_name LIKE ? OR CAST(t.ticket_number AS CHAR) LIKE ?)";
            $searchTerm = '%' . $filters['search'] . '%';
            $params[] = $searchTerm;
            $params[] = $searchTerm;
            $params[] = $searchTerm;
        }
        
        // Order by priority and date
        $sql .= " ORDER BY CASE t.priority 
                    WHEN 'urgent' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'normal' THEN 3 
                    ELSE 4 
                 END, t.updated_at DESC";
        
        $tickets = $this->db->execute($sql, $params);
        
        // Add message count and last message
        foreach ($tickets as &$ticket) {
            $ticket['messages_count'] = (int)$this->db->executeOne(
                "SELECT COUNT(*) as c FROM helpdesk_messages WHERE ticket_id = ?",
                [$ticket['id']]
            )['c'];
            
            $lastMsg = $this->db->executeOne(
                "SELECT * FROM helpdesk_messages WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1",
                [$ticket['id']]
            );
            $ticket['last_message'] = $lastMsg;
        }
        
        return $tickets;
    }
    
    public function getById(string $ticketId): ?array {
        $ticket = $this->db->executeOne(
            "SELECT t.*, u.name as user_name, u.email as user_email
             FROM helpdesk_tickets t
             LEFT JOIN users u ON t.user_id = u.id
             WHERE t.id = ?",
            [$ticketId]
        );
        
        if (!$ticket) {
            return null;
        }
        
        // Check access
        $user = $this->auth->getUser();
        if ($user && $user['role'] !== 'admin' && $user['role'] !== 'operator' && $ticket['user_id'] !== $user['id']) {
            return null;
        }
        
        // Get messages
        $messages = $this->db->execute(
            "SELECT * FROM helpdesk_messages 
             WHERE ticket_id = ? 
             ORDER BY created_at ASC",
            [$ticketId]
        );
        
        $ticket['messages'] = $messages;
        
        return $ticket;
    }
    
    public function create(array $data): array {
        $user = $this->auth->getUser();
        if (!$user) {
            return ['success' => false, 'message' => 'Not authenticated'];
        }
        
        $ticketId = 'ticket_' . substr(uniqid(), -12);
        $ticketNumber = $this->getNextTicketNumber();
        $now = date('Y-m-d H:i:s');
        
        // Insert ticket
        $this->db->insert('helpdesk_tickets', [
            'id' => $ticketId,
            'ticket_number' => $ticketNumber,
            'user_id' => $user['id'],
            'user_name' => $data['user_name'] ?? $user['name'],
            'user_email' => $data['user_email'] ?? $user['email'],
            'subject' => $data['subject'],
            'category' => $data['category'] ?? 'general',
            'status' => 'open',
            'priority' => $data['priority'] ?? 'normal',
            'created_at' => $now,
            'updated_at' => $now
        ]);
        
        // Insert initial message
        $msgId = 'msg_' . substr(uniqid(), -12);
        $this->db->insert('helpdesk_messages', [
            'id' => $msgId,
            'ticket_id' => $ticketId,
            'sender_id' => $user['id'],
            'sender_name' => $data['user_name'] ?? $user['name'],
            'sender_type' => 'user',
            'message_type' => 'text',
            'content' => $data['message'],
            'is_internal_note' => 0,
            'created_at' => $now
        ]);
        
        return [
            'success' => true,
            'ticket' => [
                'id' => $ticketId,
                'ticket_number' => $ticketNumber,
                'user_id' => $user['id'],
                'subject' => $data['subject'],
                'status' => 'open',
                'priority' => $data['priority'] ?? 'normal'
            ],
            'message_id' => $msgId
        ];
    }
    
    public function update(string $ticketId, array $data): array {
        $ticket = $this->getById($ticketId);
        if (!$ticket) {
            return ['success' => false, 'message' => 'Ticket not found'];
        }
        
        $user = $this->auth->getUser();
        if (!$user) {
            return ['success' => false, 'message' => 'Not authenticated'];
        }
        
        // Check permissions
        if ($user['role'] !== 'admin' && $user['role'] !== 'operator' && $ticket['user_id'] !== $user['id']) {
            return ['success' => false, 'message' => 'Permission denied'];
        }
        
        $updates = [];
        $params = [];
        
        if (isset($data['status'])) {
            $updates[] = 'status = ?';
            $params[] = $data['status'];
            
            if (in_array($data['status'], ['resolved', 'closed'])) {
                $updates[] = 'closed_at = ?';
                $params[] = date('Y-m-d H:i:s');
            } else {
                $updates[] = 'closed_at = NULL';
            }
        }
        
        if (isset($data['priority'])) {
            $updates[] = 'priority = ?';
            $params[] = $data['priority'];
        }
        
        if (isset($data['assigned_to'])) {
            $updates[] = 'assigned_to = ?';
            $params[] = $data['assigned_to'];
            
            if (isset($data['assigned_name'])) {
                $updates[] = 'assigned_name = ?';
                $params[] = $data['assigned_name'];
            }
        }
        
        if (!empty($updates)) {
            $params[] = $ticketId;
            $sql = "UPDATE helpdesk_tickets SET " . implode(', ', $updates) . ", updated_at = ? WHERE id = ?";
            array_unshift($params, date('Y-m-d H:i:s'));
            $this->db->execute($sql, $params);
        }
        
        return ['success' => true, 'ticket' => $this->getById($ticketId)];
    }
    
    public function getStats(): array {
        $total = (int)$this->db->executeOne("SELECT COUNT(*) as c FROM helpdesk_tickets")['c'];
        $open = (int)$this->db->executeOne("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'open'")['c'];
        $inProgress = (int)$this->db->executeOne("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'in_progress'")['c'];
        $resolved = (int)$this->db->executeOne("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'resolved'")['c'];
        $closed = (int)$this->db->executeOne("SELECT COUNT(*) as c FROM helpdesk_tickets WHERE status = 'closed'")['c'];
        $urgent = (int)$this->db->executeOne(
            "SELECT COUNT(*) as c FROM helpdesk_tickets WHERE priority = 'urgent' AND status NOT IN ('resolved', 'closed')"
        )['c'];
        
        return [
            'total_tickets' => $total,
            'open_tickets' => $open,
            'in_progress_tickets' => $inProgress,
            'resolved_tickets' => $resolved,
            'closed_tickets' => $closed,
            'urgent_tickets' => $urgent
        ];
    }
    
    private function getNextTicketNumber(): int {
        $result = $this->db->executeOne(
            "SELECT current_value FROM helpdesk_sequences WHERE name = 'ticket_number'"
        );
        
        if (!$result) {
            $this->db->insert('helpdesk_sequences', [
                'name' => 'ticket_number',
                'current_value' => 1000
            ]);
            return 1000;
        }
        
        $this->db->execute(
            "UPDATE helpdesk_sequences SET current_value = current_value + 1 WHERE name = 'ticket_number'"
        );
        
        return (int)$result['current_value'];
    }
}
