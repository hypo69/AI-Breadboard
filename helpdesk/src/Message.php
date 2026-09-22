<?php
/**
 * Helpdesk Message Manager
 * CRUD operations for ticket messages
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/Auth.php';

class Message {
    private PDO $db;
    private Auth $auth;
    
    public function __construct() {
        $this->db = Database::getConnection();
        $this->auth = Auth::getInstance();
    }
    
    public function getForTicket(string $ticketId): array {
        $ticket = $this->db->executeOne(
            "SELECT * FROM helpdesk_tickets WHERE id = ?",
            [$ticketId]
        );
        
        if (!$ticket) {
            return [];
        }
        
        // Check access
        $user = $this->auth->getUser();
        if ($user && $user['role'] !== 'admin' && $user['role'] !== 'operator' && $ticket['user_id'] !== $user['id']) {
            return [];
        }
        
        return $this->db->execute(
            "SELECT * FROM helpdesk_messages 
             WHERE ticket_id = ? 
             ORDER BY created_at ASC",
            [$ticketId]
        );
    }
    
    public function create(string $ticketId, array $data): array {
        $ticket = $this->db->executeOne(
            "SELECT * FROM helpdesk_tickets WHERE id = ?",
            [$ticketId]
        );
        
        if (!$ticket) {
            return ['success' => false, 'message' => 'Ticket not found'];
        }
        
        $user = $this->auth->getUser();
        if (!$user) {
            return ['success' => false, 'message' => 'Not authenticated'];
        }
        
        // Determine sender type
        $senderType = $data['sender_type'] ?? 'user';
        if ($user['role'] === 'admin' || $user['role'] === 'operator') {
            $senderType = 'operator';
        }
        
        $msgId = 'msg_' . substr(uniqid(), -12);
        $now = date('Y-m-d H:i:s');
        
        // Insert message
        $this->db->insert('helpdesk_messages', [
            'id' => $msgId,
            'ticket_id' => $ticketId,
            'sender_id' => $user['id'],
            'sender_name' => $user['name'],
            'sender_type' => $senderType,
            'message_type' => 'text',
            'content' => $data['content'],
            'is_internal_note' => $data['is_internal_note'] ?? 0,
            'created_at' => $now
        ]);
        
        // Update ticket status if operator responds
        if ($senderType === 'operator' && $ticket['status'] === 'open') {
            $this->db->execute(
                "UPDATE helpdesk_tickets SET status = 'in_progress', updated_at = ? WHERE id = ?",
                [$now, $ticketId]
            );
        }
        
        // Update ticket updated_at
        $this->db->execute(
            "UPDATE helpdesk_tickets SET updated_at = ? WHERE id = ?",
            [$now, $ticketId]
        );
        
        return [
            'success' => true,
            'message' => [
                'id' => $msgId,
                'ticket_id' => $ticketId,
                'sender_id' => $user['id'],
                'sender_name' => $user['name'],
                'sender_type' => $senderType,
                'content' => $data['content'],
                'is_internal_note' => $data['is_internal_note'] ?? 0,
                'created_at' => $now
            ]
        ];
    }
    
    public function delete(string $messageId): array {
        $message = $this->db->executeOne(
            "SELECT * FROM helpdesk_messages WHERE id = ?",
            [$messageId]
        );
        
        if (!$message) {
            return ['success' => false, 'message' => 'Message not found'];
        }
        
        $user = $this->auth->getUser();
        if (!$user) {
            return ['success' => false, 'message' => 'Not authenticated'];
        }
        
        // Only owner or admin/operator can delete
        if ($user['role'] !== 'admin' && $user['role'] !== 'operator' && $message['sender_id'] !== $user['id']) {
            return ['success' => false, 'message' => 'Permission denied'];
        }
        
        $this->db->delete('helpdesk_messages', 'id = ?', [$messageId]);
        
        return ['success' => true, 'message' => 'Message deleted'];
    }
}
