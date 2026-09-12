<?php
/**
 * Plugin Name: AI Responder for davidka.net
 * Plugin URI: https://github.com/hypo69/ai-responder
 * Description: Automated context-aware AI comment responder connected with AI-Breadboard (kino.davidka.net).
 * Version: 2.0.0
 * Author: hypo69
 * Author URI: https://github.com/hypo69
 * License: MIT
 * Text Domain: ai-responder
 * Domain Path: /languages
 *
 * @package AIResponder
 */

// Direct access security check
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Plugin Constants
 */
define('AI_RESPONDER_VERSION', '2.0.0');
define('AI_RESPONDER_PATH', plugin_dir_path(__FILE__));
define('AI_RESPONDER_URL', plugin_dir_url(__FILE__));

/**
 * Autoloader for AIResponder classes
 */
spl_autoload_register(function ($class) {
    $prefix = 'AIResponder\\';
    $len = strlen($prefix);

    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }

    $relative_class = substr($class, $len);
    $parts = explode('\\', $relative_class);

    if (count($parts) === 1) {
        $file = AI_RESPONDER_PATH . 'includes/class-' . strtolower(str_replace('_', '-', $parts[0])) . '.php';
    } else {
        $subdir = strtolower($parts[0]);
        $classname = strtolower(str_replace('_', '-', $parts[1]));
        $file = AI_RESPONDER_PATH . $subdir . '/class-' . $classname . '.php';
    }

    if (file_exists($file)) {
        require_once $file;
    }
});

/**
 * Load core classes
 */
require_once AI_RESPONDER_PATH . 'includes/class-logger.php';
require_once AI_RESPONDER_PATH . 'includes/class-config.php';
require_once AI_RESPONDER_PATH . 'includes/class-breadboard-client.php';
require_once AI_RESPONDER_PATH . 'includes/class-comment-handler.php';
require_once AI_RESPONDER_PATH . 'includes/class-ai-responder.php';

if (is_admin()) {
    require_once AI_RESPONDER_PATH . 'admin/class-admin-settings.php';
    require_once AI_RESPONDER_PATH . 'admin/class-ajax-handlers.php';
}

/**
 * Bootstrap plugin instance
 *
 * @return void
 */
function ai_responder_init(): void {
    $plugin = new \AIResponder\AI_Responder();
    $plugin->run();
}
add_action('plugins_loaded', 'ai_responder_init');

/**
 * Plugin activation hook
 *
 * @return void
 */
function ai_responder_activate(): void {
    \AIResponder\Config::create_default_config();
    \AIResponder\Logger::create_log_directory();
    \AIResponder\Logger::info('AI Responder v' . AI_RESPONDER_VERSION . ' activated successfully');
}
register_activation_hook(__FILE__, 'ai_responder_activate');

/**
 * Plugin deactivation hook
 *
 * @return void
 */
function ai_responder_deactivate(): void {
    // Clear scheduled cron events
    wp_clear_scheduled_hook('ai_responder_process_comment_event');
    \AIResponder\Logger::info('AI Responder deactivated');
}
register_deactivation_hook(__FILE__, 'ai_responder_deactivate');

/**
 * Plugin action links in plugins list
 *
 * @param array $links
 * @return array
 */
function ai_responder_plugin_action_links(array $links): array {
    $settings_link = sprintf(
        '<a href="%s">%s</a>',
        admin_url('options-general.php?page=ai-responder'),
        __('Settings', 'ai-responder')
    );
    array_unshift($links, $settings_link);
    return $links;
}
add_filter('plugin_action_links_' . plugin_basename(__FILE__), 'ai_responder_plugin_action_links');