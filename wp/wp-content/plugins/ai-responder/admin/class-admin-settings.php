<?php
/**
 * Admin settings page for AI Responder.
 *
 * @package AIResponder
 * @subpackage Admin
 * @author hypo69
 * @copyright © 2026 hypo69
 */

namespace AIResponder\Admin;

use AIResponder\Config;
use AIResponder\Logger;
use AIResponder\Breadboard_Client;

if (!defined('ABSPATH')) {
    exit;
}

class Admin_Settings {
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
     * Register admin hooks.
     *
     * @return void
     */
    public function register_hooks(): void {
        add_action('admin_menu', [$this, 'add_settings_page']);
        add_action('admin_init', [$this, 'handle_save_settings']);
    }

    /**
     * Add settings page to WordPress admin menu.
     *
     * @return void
     */
    public function add_settings_page(): void {
        add_options_page(
            __('AI Responder Settings', 'ai-responder'),
            __('AI Responder', 'ai-responder'),
            'manage_options',
            'ai-responder',
            [$this, 'render_page']
        );
    }

    /**
     * Handle saving settings form submission.
     *
     * @return void
     */
    public function handle_save_settings(): void {
        if (!isset($_POST['ai_responder_save_nonce'])) {
            return;
        }

        if (!wp_verify_nonce($_POST['ai_responder_save_nonce'], 'ai_responder_save_action')) {
            wp_die(__('Security check failed.', 'ai-responder'));
        }

        if (!current_user_can('manage_options')) {
            wp_die(__('You do not have permission to manage options.', 'ai-responder'));
        }

        $new_settings = [
            'enabled'            => isset($_POST['enabled']),
            'api_url'            => sanitize_text_field($_POST['api_url'] ?? ''),
            'api_key'            => sanitize_text_field($_POST['api_key'] ?? ''),
            'model'              => sanitize_text_field($_POST['model'] ?? 'gemini-2.5-flash'),
            'provider'           => sanitize_text_field($_POST['provider'] ?? 'gemini'),
            'bot_user_id'        => absint($_POST['bot_user_id'] ?? 0),
            'auto_approve'       => isset($_POST['auto_approve']),
            'reply_delay'        => absint($_POST['reply_delay'] ?? 10),
            'debug_mode'         => isset($_POST['debug_mode']),
            'system_instruction' => sanitize_textarea_field($_POST['system_instruction'] ?? ''),
            'min_comment_length' => absint($_POST['min_comment_length'] ?? 5),
            'max_thread_depth'   => absint($_POST['max_thread_depth'] ?? 5),
            'timeout'            => absint($_POST['timeout'] ?? 60),
            'exclude_keywords'   => sanitize_text_field($_POST['exclude_keywords'] ?? ''),
        ];

        Config::update_settings($new_settings);

        add_settings_error('ai_responder_messages', 'ai_responder_saved', __('Settings saved successfully.', 'ai-responder'), 'updated');
    }

    /**
     * Render the admin settings page.
     *
     * @return void
     */
    public function render_page(): void {
        if (!current_user_can('manage_options')) {
            return;
        }

        $settings = Config::get_settings();
        $users = get_users(['orderby' => 'display_name', 'order' => 'ASC']);
        $recent_logs = Logger::get_recent_logs(80);
        $exclude_kw_str = is_array($settings['exclude_keywords']) ? implode(', ', $settings['exclude_keywords']) : (string)$settings['exclude_keywords'];

        settings_errors('ai_responder_messages');
        ?>
        <div class="wrap ai-responder-admin">
            <h1><?php echo esc_html(get_admin_page_title()); ?> <span style="font-size: 13px; color: #666;">v<?php echo esc_html(AI_RESPONDER_VERSION); ?></span></h1>
            <p class="description">
                <?php esc_html_e('Automated AI comment responder connected with AI-Breadboard (kino.davidka.net).', 'ai-responder'); ?>
            </p>

            <style>
                .air-card { background: #fff; border: 1px solid #ccd0d4; box-shadow: 0 1px 1px rgba(0,0,0,.04); padding: 20px; margin-bottom: 20px; border-radius: 4px; }
                .air-card h2 { margin-top: 0; padding-bottom: 10px; border-bottom: 1px solid #eee; font-size: 1.2em; }
                .air-log-viewer { background: #1e1e1e; color: #d4d4d4; font-family: Consolas, Monaco, monospace; font-size: 12px; padding: 15px; border-radius: 4px; max-height: 350px; overflow-y: scroll; white-space: pre-wrap; word-break: break-all; }
                .air-status-badge { display: inline-block; padding: 4px 8px; border-radius: 3px; font-weight: bold; font-size: 12px; }
                .air-badge-active { background: #d4edda; color: #155724; }
                .air-badge-inactive { background: #f8d7da; color: #721c24; }
            </style>

            <form method="post" action="">
                <?php wp_nonce_field('ai_responder_save_action', 'ai_responder_save_nonce'); ?>

                <!-- General & Connection Settings -->
                <div class="air-card">
                    <h2><?php esc_html_e('1. AI-Breadboard Connection', 'ai-responder'); ?></h2>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><?php esc_html_e('Status', 'ai-responder'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox" name="enabled" value="1" <?php checked($settings['enabled']); ?>>
                                    <strong><?php esc_html_e('Enable AI Auto-Replies', 'ai-responder'); ?></strong>
                                </label>
                                <p class="description"><?php esc_html_e('Toggle auto-reply processing on or off.', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="api_url"><?php esc_html_e('AI Backend Endpoint', 'ai-responder'); ?></label></th>
                            <td>
                                <input type="url" name="api_url" id="api_url" value="<?php echo esc_attr($settings['api_url']); ?>" class="large-text" required>
                                <p class="description"><?php esc_html_e('Default: https://kino.davidka.net/api/chat/comment-responder', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="api_key"><?php esc_html_e('API Secret Token (Optional)', 'ai-responder'); ?></label></th>
                            <td>
                                <input type="password" name="api_key" id="api_key" value="<?php echo esc_attr($settings['api_key']); ?>" class="regular-text">
                                <p class="description"><?php esc_html_e('Auth token if required by AI-Breadboard server.', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="model"><?php esc_html_e('Model Name', 'ai-responder'); ?></label></th>
                            <td>
                                <input type="text" name="model" id="model" value="<?php echo esc_attr($settings['model']); ?>" class="regular-text">
                                <p class="description"><?php esc_html_e('Examples: gemini-2.5-flash, gemini-2.5-pro, foundry:phi-3.5-mini-instruct, ollama:llama3.1', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="provider"><?php esc_html_e('Provider', 'ai-responder'); ?></label></th>
                            <td>
                                <select name="provider" id="provider">
                                    <option value="gemini" <?php selected($settings['provider'], 'gemini'); ?>>Google Gemini</option>
                                    <option value="foundry" <?php selected($settings['provider'], 'foundry'); ?>>Microsoft Foundry Local</option>
                                    <option value="ollama" <?php selected($settings['provider'], 'ollama'); ?>>Ollama Local</option>
                                    <option value="openai" <?php selected($settings['provider'], 'openai'); ?>>OpenAI / Compatible</option>
                                    <option value="hf" <?php selected($settings['provider'], 'hf'); ?>>HuggingFace Transformers</option>
                                    <option value="onnx" <?php selected($settings['provider'], 'onnx'); ?>>ONNX Runtime / DirectML</option>
                                </select>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- WordPress Bot User Configuration -->
                <div class="air-card">
                    <h2><?php esc_html_e('2. Dedicated WordPress Bot User', 'ai-responder'); ?></h2>
                    <p class="description">
                        <?php esc_html_e('Select a dedicated WordPress user account to author AI replies. Using a dedicated bot user ensures proper display name/avatar and prevents the bot from answering its own replies.', 'ai-responder'); ?>
                    </p>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><label for="bot_user_id"><?php esc_html_e('Bot User Account', 'ai-responder'); ?></label></th>
                            <td>
                                <select name="bot_user_id" id="bot_user_id">
                                    <option value="0"><?php esc_html_e('-- None (Generic AI Assistant) --', 'ai-responder'); ?></option>
                                    <?php foreach ($users as $user): ?>
                                        <option value="<?php echo esc_attr($user->ID); ?>" <?php selected($settings['bot_user_id'], $user->ID); ?>>
                                            <?php echo esc_html($user->display_name . ' (' . $user->user_login . ' - ' . $user->user_email . ')'); ?>
                                        </option>
                                    <?php endforeach; ?>
                                </select>
                                <p class="description">
                                    <?php esc_html_e('Recommended: Create a user named "Davidka AI" or "AI Assistant" and select it here.', 'ai-responder'); ?>
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Comment Moderation & Rules -->
                <div class="air-card">
                    <h2><?php esc_html_e('3. Comment Moderation & Timing', 'ai-responder'); ?></h2>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><?php esc_html_e('Auto-Approve Replies', 'ai-responder'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox" name="auto_approve" value="1" <?php checked($settings['auto_approve']); ?>>
                                    <?php esc_html_e('Publish AI replies immediately without requiring manual moderation', 'ai-responder'); ?>
                                </label>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="reply_delay"><?php esc_html_e('Reply Delay (seconds)', 'ai-responder'); ?></label></th>
                            <td>
                                <input type="number" name="reply_delay" id="reply_delay" value="<?php echo esc_attr($settings['reply_delay']); ?>" min="0" max="3600" class="small-text">
                                <p class="description"><?php esc_html_e('Simulates natural typing/reading delay (e.g. 10-30 seconds). Processed via WP-Cron.', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="min_comment_length"><?php esc_html_e('Min Comment Length', 'ai-responder'); ?></label></th>
                            <td>
                                <input type="number" name="min_comment_length" id="min_comment_length" value="<?php echo esc_attr($settings['min_comment_length']); ?>" min="1" max="500" class="small-text">
                                <p class="description"><?php esc_html_e('Minimum number of characters required for AI to respond.', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><label for="exclude_keywords"><?php esc_html_e('Excluded Keywords (Spam Filter)', 'ai-responder'); ?></label></th>
                            <td>
                                <input type="text" name="exclude_keywords" id="exclude_keywords" value="<?php echo esc_attr($exclude_kw_str); ?>" class="large-text">
                                <p class="description"><?php esc_html_e('Comma-separated list of words that prevent AI generation.', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php esc_html_e('Debug Mode', 'ai-responder'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox" name="debug_mode" value="1" <?php checked($settings['debug_mode']); ?>>
                                    <?php esc_html_e('Enable verbose logging to ai-responder-debug.log', 'ai-responder'); ?>
                                </label>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Custom System Prompt -->
                <div class="air-card">
                    <h2><?php esc_html_e('4. AI Persona & Instructions', 'ai-responder'); ?></h2>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><label for="system_instruction"><?php esc_html_e('System Prompt', 'ai-responder'); ?></label></th>
                            <td>
                                <textarea name="system_instruction" id="system_instruction" rows="5" class="large-text code"><?php echo esc_textarea($settings['system_instruction']); ?></textarea>
                                <p class="description"><?php esc_html_e('Define personality, guidelines, tone, and language behavior.', 'ai-responder'); ?></p>
                            </td>
                        </tr>
                    </table>
                </div>

                <?php submit_button(__('Save Settings', 'ai-responder')); ?>
            </form>

            <!-- Test Connection -->
            <div class="air-card">
                <h2><?php esc_html_e('5. Test Connection to AI-Breadboard', 'ai-responder'); ?></h2>
                <p><?php esc_html_e('Send a synthetic test request to kino.davidka.net to verify connectivity and model responsiveness.', 'ai-responder'); ?></p>
                <button type="button" id="air-test-connection-btn" class="button button-secondary">
                    <?php esc_html_e('▶️ Test Connection', 'ai-responder'); ?>
                </button>
                <span id="air-test-spinner" class="spinner" style="float: none; margin-top: 0;"></span>
                <div id="air-test-result" style="margin-top: 15px; display: none; padding: 10px; border-radius: 4px;"></div>
            </div>

            <!-- Log Viewer -->
            <div class="air-card">
                <h2><?php esc_html_e('6. Activity Logs', 'ai-responder'); ?></h2>
                <p>
                    <button type="button" id="air-refresh-logs-btn" class="button button-secondary"><?php esc_html_e('🔄 Refresh Logs', 'ai-responder'); ?></button>
                    <button type="button" id="air-clear-logs-btn" class="button button-link-delete" style="margin-left: 10px;"><?php esc_html_e('🗑️ Clear Logs', 'ai-responder'); ?></button>
                </p>
                <div id="air-log-box" class="air-log-viewer"><?php echo esc_html(implode("\n", $recent_logs)); ?></div>
            </div>
        </div>

        <script>
        jQuery(document).ready(function($) {
            $('#air-test-connection-btn').on('click', function() {
                var $btn = $(this);
                var $spinner = $('#air-test-spinner');
                var $result = $('#air-test-result');

                $btn.prop('disabled', true);
                $spinner.addClass('is-active');
                $result.hide().removeClass('notice-success notice-error');

                $.ajax({
                    url: ajaxurl,
                    type: 'POST',
                    data: {
                        action: 'ai_responder_test_connection',
                        nonce: '<?php echo wp_create_nonce('ai_responder_ajax_nonce'); ?>'
                    },
                    success: function(res) {
                        $btn.prop('disabled', false);
                        $spinner.removeClass('is-active');
                        $result.show();

                        if (res.success) {
                            $result.css({'background': '#d4edda', 'color': '#155724', 'border': '1px solid #c3e6cb'})
                                   .html('<strong>✅ ' + res.data.message + '</strong> (' + res.data.duration_ms + 'ms)');
                        } else {
                            $result.css({'background': '#f8d7da', 'color': '#721c24', 'border': '1px solid #f5c6cb'})
                                   .html('<strong>❌ ' + (res.data ? res.data.message : 'Error') + '</strong>');
                        }
                    },
                    error: function() {
                        $btn.prop('disabled', false);
                        $spinner.removeClass('is-active');
                        $result.show().css({'background': '#f8d7da', 'color': '#721c24', 'border': '1px solid #f5c6cb'})
                               .html('<strong>❌ Server request failed. Check network or console.</strong>');
                    }
                });
            });

            $('#air-clear-logs-btn').on('click', function() {
                if (!confirm('Are you sure you want to clear the logs?')) return;
                $.post(ajaxurl, {
                    action: 'ai_responder_clear_logs',
                    nonce: '<?php echo wp_create_nonce('ai_responder_ajax_nonce'); ?>'
                }, function(res) {
                    if (res.success) {
                        $('#air-log-box').text(res.data.logs.join('\n'));
                    }
                });
            });

            $('#air-refresh-logs-btn').on('click', function() {
                $.post(ajaxurl, {
                    action: 'ai_responder_get_logs',
                    nonce: '<?php echo wp_create_nonce('ai_responder_ajax_nonce'); ?>'
                }, function(res) {
                    if (res.success) {
                        $('#air-log-box').text(res.data.logs.join('\n'));
                        var box = document.getElementById('air-log-box');
                        box.scrollTop = box.scrollHeight;
                    }
                });
            });
        });
        </script>
        <?php
    }
}
