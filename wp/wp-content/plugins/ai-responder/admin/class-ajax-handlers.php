<?php
/**
 * AJAX handlers for AI Responder admin dashboard.
 *
 * @package AIResponder
 * @subpackage Admin
 * @author hypo69
 * @copyright © 2026 hypo69
 */

namespace AIResponder\Admin;

use AIResponder\Breadboard_Client;
use AIResponder\Logger;

if (!defined('ABSPATH')) {
    exit;
}

class Ajax_Handlers {
    /**
     * @var Breadboard_Client
     */
    protected $client;

    /**
     * Constructor.
     *
     * @param Breadboard_Client $client
     */
    public function __construct(Breadboard_Client $client) {
        $this->client = $client;
    }

    /**
     * Register AJAX actions.
     *
     * @return void
     */
    public function register_hooks(): void {
        add_action('wp_ajax_ai_responder_test_connection', [$this, 'handle_test_connection']);
        add_action('wp_ajax_ai_responder_clear_logs', [$this, 'handle_clear_logs']);
        add_action('wp_ajax_ai_responder_get_logs', [$this, 'handle_get_logs']);
    }

    /**
     * Handle test connection request.
     *
     * @return void
     */
    public function handle_test_connection(): void {
        check_ajax_referer('ai_responder_ajax_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Unauthorized']);
        }

        $res = $this->client->test_connection();

        if ($res['success']) {
            wp_send_json_success($res);
        } else {
            wp_send_json_error($res);
        }
    }

    /**
     * Handle clearing log file.
     *
     * @return void
     */
    public function handle_clear_logs(): void {
        check_ajax_referer('ai_responder_ajax_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Unauthorized']);
        }

        Logger::clear_logs();
        $recent = Logger::get_recent_logs(50);

        wp_send_json_success(['logs' => $recent]);
    }

    /**
     * Handle fetching recent logs.
     *
     * @return void
     */
    public function handle_get_logs(): void {
        check_ajax_referer('ai_responder_ajax_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Unauthorized']);
        }

        $recent = Logger::get_recent_logs(80);

        wp_send_json_success(['logs' => $recent]);
    }
}
