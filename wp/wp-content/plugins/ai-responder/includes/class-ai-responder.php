<?php
/**
 * Main AI Responder core coordinator.
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

class AI_Responder {
    /**
     * @var Breadboard_Client
     */
    protected $client;

    /**
     * @var Comment_Handler
     */
    protected $comment_handler;

    /**
     * Constructor.
     */
    public function __construct() {
        $this->client = new Breadboard_Client();
        $this->comment_handler = new Comment_Handler($this->client);
    }

    /**
     * Run and bootstrap the plugin.
     *
     * @return void
     */
    public function run(): void {
        $this->comment_handler->register_hooks();

        if (is_admin()) {
            $admin_settings = new \AIResponder\Admin\Admin_Settings($this->client);
            $admin_settings->register_hooks();

            $ajax_handlers = new \AIResponder\Admin\Ajax_Handlers($this->client);
            $ajax_handlers->register_hooks();
        }
    }

    /**
     * Get the API client instance.
     *
     * @return Breadboard_Client
     */
    public function get_client(): Breadboard_Client {
        return $this->client;
    }

    /**
     * Get the comment handler instance.
     *
     * @return Comment_Handler
     */
    public function get_comment_handler(): Comment_Handler {
        return $this->comment_handler;
    }
}
