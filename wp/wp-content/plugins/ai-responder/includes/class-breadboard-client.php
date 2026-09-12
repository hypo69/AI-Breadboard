<?php
/**
 * AI-Breadboard API client for WordPress AI Responder.
 *
 * @package AIResponder
 * @subpackage Includes
 * @author hypo69
 * @copyright © 2026 hypo69
 */

namespace AIResponder;

if (!defined('ABSPATH')) {
    exit;
}

class Breadboard_Client {
    /**
     * Send comment data to AI-Breadboard backend to generate a response.
     *
     * @param array $payload Comment and context payload.
     * @return array [ 'success' => bool, 'reply' => string, 'error' => string, 'duration_ms' => float ]
     */
    public function generate_reply(array $payload): array {
        $api_url = Config::get('api_url', 'https://kino.davidka.net/api/chat/comment-responder');
        $api_key = Config::get('api_key', '');
        $timeout = (int)Config::get('timeout', 60);

        if (empty($api_url)) {
            Logger::error('API URL is not configured in settings.');
            return [
                'success' => false,
                'reply'   => '',
                'error'   => 'API URL is not configured',
                'duration_ms' => 0.0,
            ];
        }

        // Add model and prompt defaults if not set in payload
        if (empty($payload['model'])) {
            $payload['model'] = Config::get('model', 'gemini-2.5-flash');
        }
        if (empty($payload['provider'])) {
            $payload['provider'] = Config::get('provider', 'gemini');
        }
        if (empty($payload['system_instruction'])) {
            $payload['system_instruction'] = Config::get('system_instruction', '');
        }

        $headers = [
            'Content-Type' => 'application/json',
            'Accept'       => 'application/json',
            'User-Agent'   => 'WordPress-AI-Responder/' . AI_RESPONDER_VERSION . ' (davidka.net)',
        ];

        if (!empty($api_key)) {
            $headers['Authorization'] = 'Bearer ' . $api_key;
            $headers['X-API-Key']     = $api_key;
        }

        Logger::info('Dispatching comment reply request to Breadboard', [
            'url'    => $api_url,
            'model'  => $payload['model'],
            'author' => $payload['comment_author'] ?? 'unknown',
        ]);

        $start_time = microtime(true);
        $response = wp_remote_post($api_url, [
            'method'      => 'POST',
            'timeout'     => $timeout,
            'redirection' => 5,
            'httpversion' => '1.1',
            'blocking'    => true,
            'headers'     => $headers,
            'body'        => wp_json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE),
            'sslverify'   => false, // Allow self-signed or internal SSL certificates
        ]);

        $duration_ms = round((microtime(true) - $start_time) * 1000, 1);

        if (is_wp_error($response)) {
            $error_message = $response->get_error_message();
            Logger::error('Breadboard API request failed: ' . $error_message, ['duration_ms' => $duration_ms]);
            return [
                'success'     => false,
                'reply'       => '',
                'error'       => $error_message,
                'duration_ms' => $duration_ms,
            ];
        }

        $status_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        if ($status_code < 200 || $status_code >= 300) {
            $err = !empty($data['detail']) ? $data['detail'] : (!empty($data['message']) ? $data['message'] : "HTTP Status $status_code");
            Logger::error("Breadboard API returned HTTP $status_code", ['error' => $err, 'body' => $body]);
            return [
                'success'     => false,
                'reply'       => '',
                'error'       => (string)$err,
                'duration_ms' => $duration_ms,
            ];
        }

        if (isset($data['status']) && $data['status'] === 'error') {
            $err = $data['message'] ?? 'Unknown error from AI model';
            Logger::error('Breadboard returned status error: ' . $err);
            return [
                'success'     => false,
                'reply'       => '',
                'error'       => $err,
                'duration_ms' => $duration_ms,
            ];
        }

        $reply = '';
        if (!empty($data['reply'])) {
            $reply = trim($data['reply']);
        } elseif (!empty($data['response'])) {
            $reply = trim($data['response']);
        }

        if (empty($reply)) {
            Logger::warning('Received empty reply from AI Breadboard', ['response' => $data]);
            return [
                'success'     => false,
                'reply'       => '',
                'error'       => 'Received empty response from AI model',
                'duration_ms' => $duration_ms,
            ];
        }

        Logger::info('Received successful response from Breadboard', [
            'duration_ms'  => $duration_ms,
            'reply_length' => mb_strlen($reply),
        ]);

        return [
            'success'     => true,
            'reply'       => $reply,
            'error'       => '',
            'duration_ms' => $duration_ms,
            'model'       => $data['model'] ?? $payload['model'],
        ];
    }

    /**
     * Test connectivity to the AI-Breadboard API endpoint.
     *
     * @return array [ 'success' => bool, 'message' => string, 'duration_ms' => float ]
     */
    public function test_connection(): array {
        $result = $this->generate_reply([
            'post_title'      => 'Test Connection Post',
            'post_content'    => 'This is a test request from WordPress admin to verify connection to AI-Breadboard.',
            'comment_author'  => 'Admin Tester',
            'comment_content' => 'Hello AI Assistant! Please confirm that the integration with davidka.net is working properly.',
            'parent_context'  => '',
        ]);

        if ($result['success']) {
            return [
                'success'     => true,
                'message'     => 'Connection successful! Response: ' . $result['reply'],
                'duration_ms' => $result['duration_ms'],
            ];
        }

        return [
            'success'     => false,
            'message'     => 'Connection failed: ' . ($result['error'] ?: 'Unknown error'),
            'duration_ms' => $result['duration_ms'],
        ];
    }
}
