<?php
/**
 * Configuration and options manager for AI Responder plugin.
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

class Config {
    const OPTION_KEY = 'ai_responder_settings';
    const CONFIG_FILE = 'config.json';

    /**
     * Get default plugin configuration settings.
     *
     * @return array
     */
    public static function get_defaults(): array {
        return [
            'enabled'            => false,
            'api_url'            => 'https://kino.davidka.net/api/chat/comment-responder',
            'api_key'            => '',
            'model'              => 'gemini-2.5-flash',
            'provider'           => 'gemini',
            'bot_user_id'        => 0,
            'auto_approve'       => true,
            'reply_delay'        => 10,
            'debug_mode'         => true,
            'system_instruction' => "You are an intelligent, friendly AI assistant for davidka.net blog. Answer questions constructively, politely, and succinctly in the language of the comment.",
            'min_comment_length' => 5,
            'max_thread_depth'   => 5,
            'timeout'            => 60,
            'exclude_authors'    => [],
            'exclude_keywords'   => ['spam', 'viagra', 'casino', 'free money', 'crypto airdrop'],
        ];
    }

    /**
     * Retrieve merged plugin settings.
     *
     * @return array
     */
    public static function get_settings(): array {
        $defaults = self::get_defaults();
        $stored = get_option(self::OPTION_KEY, []);

        // Fallback to config.json if option is empty
        if (empty($stored)) {
            $json_file = AI_RESPONDER_PATH . self::CONFIG_FILE;
            if (file_exists($json_file)) {
                $raw = file_get_contents($json_file);
                $decoded = json_decode($raw, true);
                if (is_array($decoded)) {
                    $stored = $decoded;
                }
            }
        }

        return wp_parse_args($stored, $defaults);
    }

    /**
     * Get a specific setting value.
     *
     * @param string $key Setting key.
     * @param mixed  $default Default fallback.
     * @return mixed
     */
    public static function get(string $key, $default = null) {
        $settings = self::get_settings();
        return $settings[$key] ?? $default;
    }

    /**
     * Update plugin settings.
     *
     * @param array $new_settings Settings to update.
     * @return bool
     */
    public static function update_settings(array $new_settings): bool {
        $current = self::get_settings();
        $merged = wp_parse_args($new_settings, $current);

        // Sanitize values
        $merged['enabled']            = (bool)($merged['enabled'] ?? false);
        $merged['api_url']            = esc_url_raw($merged['api_url'] ?? '');
        $merged['api_key']            = sanitize_text_field($merged['api_key'] ?? '');
        $merged['model']              = sanitize_text_field($merged['model'] ?? 'gemini-2.5-flash');
        $merged['provider']           = sanitize_text_field($merged['provider'] ?? 'gemini');
        $merged['bot_user_id']        = absint($merged['bot_user_id'] ?? 0);
        $merged['auto_approve']       = (bool)($merged['auto_approve'] ?? true);
        $merged['reply_delay']        = max(0, absint($merged['reply_delay'] ?? 0));
        $merged['debug_mode']         = (bool)($merged['debug_mode'] ?? true);
        $merged['system_instruction'] = sanitize_textarea_field($merged['system_instruction'] ?? '');
        $merged['min_comment_length'] = max(1, absint($merged['min_comment_length'] ?? 5));
        $merged['max_thread_depth']   = max(1, absint($merged['max_thread_depth'] ?? 5));
        $merged['timeout']            = max(5, absint($merged['timeout'] ?? 60));

        if (is_string($merged['exclude_keywords'] ?? '')) {
            $merged['exclude_keywords'] = array_filter(array_map('trim', explode(',', $merged['exclude_keywords'])));
        }

        // Save to DB
        $updated = update_option(self::OPTION_KEY, $merged);

        // Sync to config.json
        $json_file = AI_RESPONDER_PATH . self::CONFIG_FILE;
        @file_put_contents($json_file, wp_json_encode($merged, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));

        return $updated;
    }

    /**
     * Create default configuration file.
     *
     * @return void
     */
    public static function create_default_config(): void {
        $json_file = AI_RESPONDER_PATH . self::CONFIG_FILE;
        if (!file_exists($json_file)) {
            @file_put_contents(
                $json_file,
                wp_json_encode(self::get_defaults(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)
            );
        }
    }

    /**
     * Check if debug mode is active.
     *
     * @return bool
     */
    public static function is_debug_mode(): bool {
        return (bool)self::get('debug_mode', true);
    }
}
