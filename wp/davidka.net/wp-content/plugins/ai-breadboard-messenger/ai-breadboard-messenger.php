<?php
/**
 * Plugin Name: AI Breadboard Messenger & Meeting Rooms
 * Plugin URI: https://github.com/hypo69/AI-Breadboard
 * Description: Enterprise real-time Telegram/WhatsApp-like Messenger and WebRTC meeting rooms integrated with WordPress users, SSO, and AI Breadboard RAG backends.
 * Version: 1.0.0
 * Author: hypo69
 * Author URI: https://github.com/hypo69
 * License: GPL-2.0+
 * Text Domain: ai-breadboard-messenger
 */

if (!defined('ABSPATH')) {
    exit;
}

class AIBreadboardMessenger {
    private static $instance = null;
    private $api_base_url;
    private $sync_secret;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        $this->api_base_url = get_option('ab_messenger_api_url', 'http://localhost:8000');
        $this->sync_secret = get_option('ab_messenger_sync_secret', 'breadboard_messenger_secret_key_2026');

        // Admin menu
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);

        // Frontend hooks
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_action('wp_footer', [$this, 'render_floating_widget']);
        add_shortcode('breadboard_messenger', [$this, 'render_shortcode']);

        // User sync hooks
        add_action('user_register', [$this, 'sync_user_on_change'], 10, 1);
        add_action('profile_update', [$this, 'sync_user_on_change'], 10, 1);
        add_action('wp_login', [$this, 'sync_user_on_login'], 10, 2);

        // REST API endpoints for WordPress
        add_action('rest_api_init', [$this, 'register_rest_routes']);
    }

    public function add_admin_menu() {
        add_menu_page(
            'AI Messenger',
            'AI Messenger',
            'manage_options',
            'ai-breadboard-messenger',
            [$this, 'render_admin_page'],
            'dashicons-format-chat',
            30
        );
    }

    public function register_settings() {
        register_setting('ab_messenger_options', 'ab_messenger_api_url');
        register_setting('ab_messenger_options', 'ab_messenger_sync_secret');
        register_setting('ab_messenger_options', 'ab_messenger_enable_widget');
    }

    public function render_admin_page() {
        ?>
        <div class="wrap">
            <h1>AI Breadboard Messenger Settings</h1>
            <form method="post" action="options.php">
                <?php settings_fields('ab_messenger_options'); ?>
                <?php do_settings_sections('ab_messenger_options'); ?>
                <table class="form-table">
                    <tr valign="top">
                        <th scope="row">Backend Server URL</th>
                        <td>
                            <input type="url" name="ab_messenger_api_url" value="<?php echo esc_attr(get_option('ab_messenger_api_url', 'http://localhost:8000')); ?>" class="regular-text" />
                            <p class="description">URL of AI-Breadboard FastAPI server or standalone messenger microservice.</p>
                        </td>
                    </tr>
                    <tr valign="top">
                        <th scope="row">Sync Secret Key</th>
                        <td>
                            <input type="password" name="ab_messenger_sync_secret" value="<?php echo esc_attr(get_option('ab_messenger_sync_secret', 'breadboard_messenger_secret_key_2026')); ?>" class="regular-text" />
                            <p class="description">Shared secret key matching MESSENGER_SYNC_SECRET on the Python backend.</p>
                        </td>
                    </tr>
                    <tr valign="top">
                        <th scope="row">Enable Floating Widget</th>
                        <td>
                            <label>
                                <input type="checkbox" name="ab_messenger_enable_widget" value="1" <?php checked(1, get_option('ab_messenger_enable_widget', 1)); ?> />
                                Display floating messenger launcher on public pages for logged-in users.
                            </label>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }

    public function enqueue_assets() {
        if (!is_user_logged_in() && !get_option('ab_messenger_enable_widget', 1)) {
            return;
        }
        $server_url = rtrim($this->api_base_url, '/');
        wp_enqueue_script(
            'ab-messenger-widget',
            $server_url . '/webinterface/messenger/widget.js',
            [],
            '1.0.0',
            true
        );

        $current_user = wp_get_current_user();
        $sso_token = $this->generate_sso_token($current_user);

        wp_localize_script('ab-messenger-widget', 'AB_MESSENGER_CONFIG', [
            'apiUrl' => $server_url,
            'ssoToken' => $sso_token,
            'userId' => (string)$current_user->ID,
            'userName' => $current_user->display_name ?: $current_user->user_login,
            'userAvatar' => get_avatar_url($current_user->ID),
        ]);
    }

    public function render_floating_widget() {
        if (!get_option('ab_messenger_enable_widget', 1)) {
            return;
        }
        echo '<div id="ab-messenger-root"></div>';
    }

    public function render_shortcode($atts) {
        $server_url = rtrim($this->api_base_url, '/');
        $current_user = wp_get_current_user();
        $sso_token = $this->generate_sso_token($current_user);
        
        $iframe_url = $server_url . '/webinterface/messenger/?token=' . urlencode($sso_token);
        return '<div class="ab-messenger-container" style="width:100%; height:750px; border-radius:12px; overflow:hidden; box-shadow:0 8px 30px rgba(0,0,0,0.15);">'
             . '<iframe src="' . esc_url($iframe_url) . '" style="width:100%; height:100%; border:none;" allow="camera; microphone; display-capture; autoplay"></iframe>'
             . '</div>';
    }

    public function sync_user_on_login($user_login, $user) {
        $this->sync_user_to_backend($user);
    }

    public function sync_user_on_change($user_id) {
        $user = get_userdata($user_id);
        if ($user) {
            $this->sync_user_to_backend($user);
        }
    }

    private function sync_user_to_backend($user) {
        $endpoint = rtrim($this->api_base_url, '/') . '/api/messenger/sync/user';
        $payload = json_encode([
            'id' => (string)$user->ID,
            'email' => $user->user_email,
            'username' => $user->user_login,
            'display_name' => $user->display_name,
            'avatar_url' => get_avatar_url($user->ID),
            'roles' => (array)$user->roles,
            'source' => 'wordpress'
        ]);

        $signature = hash_hmac('sha256', $payload, $this->sync_secret);

        wp_remote_post($endpoint, [
            'headers' => [
                'Content-Type' => 'application/json',
                'X-WP-Signature' => $signature,
            ],
            'body' => $payload,
            'timeout' => 5,
        ]);
    }

    private function generate_sso_token($user) {
        if (!$user || !$user->ID) {
            return '';
        }
        // Base64Url JWT encoding
        $header = base64_encode(json_encode(['typ' => 'JWT', 'alg' => 'HS256']));
        $payload = base64_encode(json_encode([
            'sub' => (string)$user->ID,
            'email' => $user->user_email,
            'name' => $user->display_name ?: $user->user_login,
            'iss' => 'ai-breadboard-messenger',
            'exp' => time() + (86400 * 3), // 3 days
            'iat' => time(),
        ]));
        
        $signature = hash_hmac('sha256', "$header.$payload", $this->sync_secret, true);
        $encoded_sig = base64_encode($signature);
        
        return "$header.$payload.$encoded_sig";
    }

    public function register_rest_routes() {
        register_rest_route('aibreadboard/v1', '/status', [
            'methods' => 'GET',
            'callback' => function() {
                return rest_ensure_response(['status' => 'connected', 'version' => '1.0.0']);
            },
            'permission_callback' => '__return_true',
        ]);
    }
}

add_action('plugins_loaded', ['AIBreadboardMessenger', 'get_instance']);
