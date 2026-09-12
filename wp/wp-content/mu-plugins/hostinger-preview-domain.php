<?php
/**
 * Plugin Name:       Hostinger Preview Domain
 * Plugin URI:        https://www.hostinger.com
 * Description:       Enable access to the website through a temporary domain while the main domain is not yet configured.
 * Version:           1.4.0
 * Author:            Hostinger
 * Author URI:        https://www.hostinger.com
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       hostinger-preview-domain
 * Domain Path:       /languages
 * Requires at least: 5.0
 * Requires PHP:      7.0
 * MU Plugin:         Yes
 */

if ( ! class_exists( 'Hostinger_Temporary_Domain_Handler' ) ) {
    class Hostinger_Temporary_Domain_Handler {
        const MAX_RECURSION_DEPTH      = 50;
        const MAX_FILTER_CONTENT_BYTES = 5242880;  // 5 MB
        const MAX_FILTER_QUERY_BYTES   = 1048576;  // 1 MB

        private $site_domain;
        private $current_domain;
        private $db_site_url;
        private static $meta_filter_in_progress = array();
        private static $query_filter_in_progress = false;

        public function __construct() {
            $this->initialize_domains();
            $this->setup_hooks();
        }

        /**
         * Initialize the handler if the preview indicator is present.
         *
         * @return self|null Returns a new instance if preview indicator is found, otherwise null.
         */
        public static function init() {
            if ( function_exists( 'getallheaders' ) ) {
                $headers = getallheaders();
                if ( isset( $headers['X-Preview-Indicator'] ) && $headers['X-Preview-Indicator'] ) {
                    return new self();
                }
            }

            if ( isset( $_SERVER['HTTP_X_PREVIEW_INDICATOR'] ) && $_SERVER['HTTP_X_PREVIEW_INDICATOR'] ) {
                return new self();
            }

            return null;
        }

        /**
         * Filter and rewrite the URL if necessary.
         *
         * @param string      $url     The original URL.
         * @param mixed       $path    Optional. Path relative to the URL.
         * @param string|null $scheme  Optional. Scheme to give the URL context.
         * @param int|null    $blog_id Optional. Blog ID.
         *
         * @return string The filtered URL.
         */
        public function filter_url( $url, $path = '', $scheme = null, $blog_id = null ) {
            if ( ! filter_var( $url, FILTER_VALIDATE_URL ) ) {
                return $url;
            }

            $filtered_url = str_replace( [ 'http://' . $this->site_domain, 'https://' . $this->site_domain ], 'https://' . $this->current_domain, $url );

            return filter_var( $filtered_url, FILTER_SANITIZE_URL ) ?: '';
        }

        /**
         * Filter site icon URL to remove www prefix
         *
         * @param string $url The site icon URL
         * @return string The filtered URL
         */
        public function filter_site_icon_url( $url ) {
            if ( empty( $url ) ) {
                return $url;
            }

            $url = $this->filter_url( $url );

            $url = preg_replace( '/https?:\/\/www\./i', 'https://', $url );

            return $url;
        }

        /**
         * Filter and rewrite the content if necessary.
         *
         * @param string $content The original content.
         *
         * @return string The filtered content.
         */
        public function filter_content( $content ) {
            // Bail on huge responses — keeps regex cost / memory blow-up bounded.
            if ( strlen( $content ) > self::MAX_FILTER_CONTENT_BYTES ) {
                return $content;
            }

            // Bail when the response declared a non-HTML content type by now —
            // CSV exports, file downloads, JSON, XML, etc. don't need attribute rewriting.
            if ( ! $this->response_is_html() ) {
                return $content;
            }

            $patterns = [
                '/(href|src|action|srcset|data-img-url)\s*=\s*[\'"]https?:\/\/' . preg_quote( $this->site_domain, '/' ) . '[^\s\'"<>]*/i',
                '/(@import\s+["\']|url\(["\']?)https?:\/\/' . preg_quote( $this->site_domain, '/' ) . '[^\s\'"<>)]*/i',
            ];

            foreach ( $patterns as $pattern ) {
                $rewritten = preg_replace_callback( $pattern, function ( $matches ) {
                    $url = substr( $matches[0], strpos( $matches[0], 'http' ) );

                    return str_replace( $url, $this->filter_url( $url ), $matches[0] );
                }, $content );

                // PCRE error (backtrack limit etc.) — keep the unmodified content
                // for this pattern so we never emit NULL into the response.
                if ( is_string( $rewritten ) ) {
                    $content = $rewritten;
                }
            }

            return $content ?: '';
        }

        /**
         * Whether the current response is (so far) declared as HTML/XHTML.
         * If no Content-Type has been emitted yet, assume HTML — that's WP's
         * default for template responses.
         *
         * @return bool
         */
        private function response_is_html() {
            foreach ( headers_list() as $header ) {
                if ( stripos( $header, 'content-type:' ) !== 0 ) {
                    continue;
                }
                return stripos( $header, 'text/html' ) !== false
                    || stripos( $header, 'application/xhtml' ) !== false;
            }
            return true;
        }

        /**
         * Handle CORS headers.
         *
         * @return void
         */
        public function handle_cors() {
            $allowed_origin = 'https://' . filter_var( $this->current_domain, FILTER_SANITIZE_URL );

            if ( isset( $_SERVER['HTTP_ORIGIN'] ) && $_SERVER['HTTP_ORIGIN'] === $allowed_origin ) {
                header( 'Access-Control-Allow-Origin: ' . $allowed_origin );
                header( 'Access-Control-Allow-Methods: GET, POST, OPTIONS' );
                header( 'Access-Control-Allow-Credentials: true' );
                header( 'Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept' );
                header( 'Access-Control-Max-Age: 86400' );

                if ( $_SERVER['REQUEST_METHOD'] === 'OPTIONS' ) {
                    header( 'HTTP/1.1 204 No Content' );
                    exit();
                }
            }
        }

        /**
         * Start output buffering if URL rewriting is needed.
         *
         * Skips request contexts that cannot produce HTML or could cause
         * unbounded memory growth: AJAX, cron, XML-RPC, sitemap/feed/file URIs.
         * (REST_REQUEST is not yet defined at `init` time, so the second-pass
         * content-type check inside filter_content() catches REST responses.)
         *
         * @return void
         */
        public function start_output_buffer() {
            if ( $this->should_skip_output_buffer() ) {
                return;
            }
            ob_start( [ $this, 'filter_content' ] );
        }

        /**
         * Whether to skip output buffering entirely for this request.
         *
         * @return bool
         */
        private function should_skip_output_buffer() {
            if ( ( defined( 'DOING_AJAX' ) && DOING_AJAX )
                || ( defined( 'DOING_CRON' ) && DOING_CRON )
                || ( defined( 'XMLRPC_REQUEST' ) && XMLRPC_REQUEST ) ) {
                return true;
            }

            $uri  = isset( $_SERVER['REQUEST_URI'] ) ? (string) $_SERVER['REQUEST_URI'] : '';
            $path = $uri === '' ? '' : (string) parse_url( $uri, PHP_URL_PATH );

            if ( $path === '' ) {
                return false;
            }

            if ( strpos( $path, 'wp-sitemap' ) !== false || strpos( $path, '/feed' ) !== false ) {
                return true;
            }

            // Static / binary file extensions that WP or plugins may serve via PHP.
            return (bool) preg_match(
                '/\.(xml|json|csv|pdf|zip|tar|gz|jpe?g|png|gif|webp|svg|ico|woff2?|ttf|mp[34]|webm|wav|ogg|mov|avi)$/i',
                $path
            );
        }

        /**
         * Initialize site and current domains.
         *
         * @return void
         */
        private function initialize_domains() {
            $this->site_domain = $this->sanitize_domain( parse_url( get_site_url(), PHP_URL_HOST ) ?: '' );
            $this->current_domain = $this->sanitize_domain( isset($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'] : '' );
            $this->db_site_url = $this->get_site_url_from_db();
        }

        /**
         * Get site URL from database directly without WordPress functions
         *
         * @return string The site URL without http:// or https://
         */
        private function get_site_url_from_db() {
            global $wpdb;

            $site_url = $wpdb->get_var(
                $wpdb->prepare(
                    "SELECT REPLACE(REPLACE(option_value, 'https://', ''), 'http://', '') 
                    FROM {$wpdb->options} 
                    WHERE option_name = %s 
                    LIMIT 1",
                    'siteurl'
                )
            );

            return $this->sanitize_domain($site_url ?: '');
        }

        /**
         * Setup hooks for URL and content filtering.
         *
         * @return void
         */
        private function setup_hooks() {
            if ( $this->should_skip_hooks() ) {
                return;
            }

            add_filter( 'home_url', [ $this, 'filter_url' ], 10, 4 );
            add_filter( 'site_url', [ $this, 'filter_url' ], 10, 4 );
            add_filter( 'wp_redirect', [ $this, 'filter_url' ], 10 );

            add_filter( 'get_site_icon_url', [ $this, 'filter_site_icon_url' ], 10, 1 );

            $content_filters = [ 'the_content', 'widget_text', 'wp_nav_menu_items' ];
            foreach ( $content_filters as $filter ) {
                add_filter( $filter, [ $this, 'filter_content' ], 999 );
            }

            add_filter( 'wp_get_attachment_url', [ $this, 'filter_url' ] );

            if ( is_admin() ) {
                $this->setup_admin_filters();
            }

            add_action( 'init', [ $this, 'start_output_buffer' ], 0 );
            add_action( 'init', [ $this, 'handle_cors' ], 0 );

            add_filter( 'wp_insert_post_data', [ $this, 'replace_host_in_content' ], 10, 2 );
            add_filter( 'content_save_pre', [ $this, 'replace_host_in_content_simple' ], 10, 1 );
            add_filter( 'pre_update_option', [ $this, 'replace_host_in_option' ], 10, 3 );

            foreach ( array( 'post', 'term', 'user', 'comment' ) as $meta_type ) {
                add_filter(
                    "update_{$meta_type}_metadata",
                    function ( $check, $object_id, $meta_key, $meta_value, $prev_value ) use ( $meta_type ) {
                        return $this->filter_meta_save( $check, $object_id, $meta_key, $meta_value, $prev_value, $meta_type, false );
                    },
                    10,
                    5
                );
                add_filter(
                    "add_{$meta_type}_metadata",
                    function ( $check, $object_id, $meta_key, $meta_value, $unique ) use ( $meta_type ) {
                        return $this->filter_meta_save( $check, $object_id, $meta_key, $meta_value, $unique, $meta_type, true );
                    },
                    10,
                    5
                );
            }

            add_filter( 'preprocess_comment', [ $this, 'replace_host_in_comment' ] );

            if ( is_multisite() ) {
                add_filter( 'pre_update_site_option', [ $this, 'replace_host_in_site_option' ], 10, 1 );
                add_filter( 'pre_add_site_option',    [ $this, 'replace_host_in_site_option' ], 10, 1 );
            }

            add_filter( 'query', [ $this, 'filter_query' ], 999 );
        }

        /**
         * Setup filters for admin URLs.
         *
         * @return void
         */
        private function setup_admin_filters() {
            $admin_filters = [
                'admin_url',
                'plugins_url',
                'theme_file_uri',
                'includes_url',
                'content_url',
                'style_loader_src',
                'script_loader_src',
                'preview_post_link',
            ];

            foreach ( $admin_filters as $filter ) {
                add_filter( $filter, [ $this, 'filter_url' ], 10, 3 );
            }
        }

        /**
         * Sanitize a domain name.
         *
         * @param string $domain The domain name to sanitize.
         *
         * @return string The sanitized domain name.
         */
        private function sanitize_domain( $domain ) {
            return preg_replace( '/[^a-z0-9\-\.]/', '', strtolower( trim( $domain ) ) );
        }

        /**
         * Check if we should skip applying hooks for this request.
         *
         * @return bool True if hooks should be skipped
         */
        private function should_skip_hooks() {
            if ( php_sapi_name() === 'cli' ) {
                if ( $this->is_litespeed_command() ) {
                    return true;
                }
            }

            if ( ! $this->should_rewrite_url() ) {
                return true;
            }

            $script_name = isset( $_SERVER['SCRIPT_FILENAME'] ) ? basename( $_SERVER['SCRIPT_FILENAME'] ) : '';
            if ( strpos( $script_name, 'autologin' ) !== false || isset( $_GET['platform'] ) ) {
                return true;
            }

            return false;
        }

        /**
         * Simple check if current command contains LiteSpeed references
         *
         * @return bool True if litespeed command detected
         */
        private function is_litespeed_command() {
            global $argv;

            if ( ! empty( $argv ) ) {
                $command = implode( ' ', $argv );
                if ( stripos( $command, 'litespeed' ) !== false || stripos( $command, 'lscache' ) !== false ) {
                    return true;
                }
            }

            return false;
        }

        /**
         * Determine if the URL should be rewritten.
         *
         * @return bool True if the URL should be rewritten, false otherwise.
         */
        private function should_rewrite_url() {
            return $this->current_domain !== $this->site_domain;
        }

        /**
         * Replace current host with site URL in post content during save
         *
         * @param array $data    Post data array
         * @param array $postarr Original post array
         *
         * @return array Modified post data
         */
        public function replace_host_in_content( $data, $postarr ) {
            if ( ! $this->current_domain || ! $this->db_site_url || $this->current_domain === $this->db_site_url ) {
                return $data;
            }

            $fields = array( 'post_content', 'post_title', 'post_excerpt', 'guid' );

            foreach ( $fields as $field ) {
                if ( isset( $data[ $field ] ) && is_string( $data[ $field ] ) ) {
                    $data[ $field ] = str_replace( $this->current_domain, $this->db_site_url, $data[ $field ] );
                }
            }

            return $data;
        }

        /**
         * Replace current host with site URL in regular content during save
         *
         * @param string $content The content being saved
         *
         * @return string Modified content
         */
        public function replace_host_in_content_simple( $content ) {
            if ( $this->current_domain && $this->db_site_url && $this->current_domain !== $this->db_site_url ) {
                $content = str_replace( $this->current_domain, $this->db_site_url, $content );
            }

            return $content;
        }

        /**
         * Replace current host with site URL in options
         *
         * @param mixed  $value     The new option value
         * @param string $option    Option name
         * @param mixed  $old_value The old option value
         *
         * @return mixed Modified option value
         */
        public function replace_host_in_option( $value, $option, $old_value ) {
            // Skip siteurl/home — they legitimately store the real domain.
            if ( in_array( $option, array( 'siteurl', 'home' ) ) ) {
                return $value;
            }

            if ( $this->current_domain && $this->db_site_url && $this->current_domain !== $this->db_site_url ) {
                if ( is_string( $value ) ) {
                    $value = str_replace( $this->current_domain, $this->db_site_url, $value );
                } elseif ( is_array( $value ) ) {
                    $value = $this->replace_in_array_recursive( $value, $this->current_domain, $this->db_site_url );
                }
            }

            return $value;
        }

        /**
         * Generic add/update meta filter callback.
         *
         * Re-entry guard is per meta_type so that, while we're processing
         * post-meta, an unrelated user-meta save in the same request still
         * gets cleaned.
         *
         * @param null|bool $check
         * @param int       $object_id
         * @param string    $meta_key
         * @param mixed     $meta_value
         * @param mixed     $extra      $prev_value for update, $unique for add
         * @param string    $meta_type  'post'|'term'|'user'|'comment'
         * @param bool      $is_add     true for add_metadata, false for update_metadata
         *
         * @return null|bool|int
         */
        private function filter_meta_save( $check, $object_id, $meta_key, $meta_value, $extra, $meta_type, $is_add ) {
            if ( ! $this->meta_value_needs_replacement( $meta_value ) ) {
                return $check;
            }

            if ( ! empty( self::$meta_filter_in_progress[ $meta_type ] ) ) {
                return $check;
            }

            $cleaned = $this->replace_in_value( $meta_value, $this->current_domain, $this->db_site_url );

            self::$meta_filter_in_progress[ $meta_type ] = true;
            try {
                if ( $is_add ) {
                    $result = add_metadata( $meta_type, $object_id, $meta_key, $cleaned, (bool) $extra );
                } else {
                    $result = update_metadata( $meta_type, $object_id, $meta_key, $cleaned, $extra );
                }
            } finally {
                self::$meta_filter_in_progress[ $meta_type ] = false;
            }

            return $result;
        }

        /**
         * Replace current host in comment fields before insert.
         *
         * @param array $commentdata
         *
         * @return array
         */
        public function replace_host_in_comment( $commentdata ) {
            if ( ! $this->current_domain || ! $this->db_site_url || $this->current_domain === $this->db_site_url ) {
                return $commentdata;
            }

            if ( ! is_array( $commentdata ) ) {
                return $commentdata;
            }

            $fields = array( 'comment_content', 'comment_author', 'comment_author_url' );

            foreach ( $fields as $field ) {
                if ( isset( $commentdata[ $field ] ) && is_string( $commentdata[ $field ] ) ) {
                    $commentdata[ $field ] = str_replace( $this->current_domain, $this->db_site_url, $commentdata[ $field ] );
                }
            }

            return $commentdata;
        }

        /**
         * Replace current host inside a network (multisite) option value.
         *
         * @param mixed $value
         *
         * @return mixed
         */
        public function replace_host_in_site_option( $value ) {
            if ( ! $this->current_domain || ! $this->db_site_url || $this->current_domain === $this->db_site_url ) {
                return $value;
            }

            if ( is_string( $value ) ) {
                return str_replace( $this->current_domain, $this->db_site_url, $value );
            }

            if ( is_array( $value ) || is_object( $value ) ) {
                return $this->replace_in_array_recursive( $value, $this->current_domain, $this->db_site_url );
            }

            return $value;
        }

        /**
         * Determine whether a meta value contains the preview domain and is
         * worth walking. Fast path for the common no-leak case.
         *
         * @param mixed $value
         *
         * @return bool
         */
        private function meta_value_needs_replacement( $value ) {
            if ( ! $this->current_domain || ! $this->db_site_url || $this->current_domain === $this->db_site_url ) {
                return false;
            }

            if ( is_string( $value ) ) {
                return strpos( $value, $this->current_domain ) !== false;
            }

            if ( is_array( $value ) || is_object( $value ) ) {
                try {
                    return strpos( serialize( $value ), $this->current_domain ) !== false;
                } catch ( \Throwable $e ) {
                    return false;
                }
            }

            return false;
        }

        /**
         * Recursively replace values inside arrays or objects.
         *
         * @param array|object $value   The structure to walk.
         * @param string       $search  The search string.
         * @param string       $replace The replacement string.
         * @param int          $depth   Current recursion depth.
         *
         * @return array|object The processed structure.
         */
        private function replace_in_array_recursive( $value, $search, $replace, $depth = 0 ) {
            if ( is_array( $value ) ) {
                $result = array();
                foreach ( $value as $key => $item ) {
                    $result[ $key ] = $this->replace_in_value( $item, $search, $replace, $depth );
                }
                return $result;
            }

            if ( is_object( $value ) ) {
                foreach ( get_object_vars( $value ) as $key => $item ) {
                    $value->$key = $this->replace_in_value( $item, $search, $replace, $depth );
                }
                return $value;
            }

            return $value;
        }

        /**
         * Replace inside a single value of any supported type.
         *
         * Stops descending after MAX_RECURSION_DEPTH to guard against circular
         * references (e.g. arrays / objects with self-referential pointers)
         * which would otherwise loop until stack/memory exhaustion.
         *
         * @param mixed  $value
         * @param string $search
         * @param string $replace
         * @param int    $depth   Current recursion depth.
         *
         * @return mixed
         */
        private function replace_in_value( $value, $search, $replace, $depth = 0 ) {
            if ( is_string( $value ) ) {
                return str_replace( $search, $replace, $value );
            }
            if ( is_array( $value ) || is_object( $value ) ) {
                if ( $depth >= self::MAX_RECURSION_DEPTH ) {
                    return $value;
                }
                return $this->replace_in_array_recursive( $value, $search, $replace, $depth + 1 );
            }
            return $value;
        }

        /**
         *
         * Last-resort filter applied to every SQL statement before execution.
         *
         * @param string $query
         *
         * @return string
         */
        public function filter_query( $query ) {
            if ( ! $this->current_domain || ! $this->db_site_url || $this->current_domain === $this->db_site_url ) {
                return $query;
            }

            // Fast path: no preview domain anywhere in the query.
            if ( strpos( $query, $this->current_domain ) === false ) {
                return $query;
            }

            if ( self::$query_filter_in_progress ) {
                return $query;
            }

            if ( ! preg_match( '/^\s*(?:INSERT|UPDATE|REPLACE)\s/i', $query ) ) {
                return $query;
            }

            // Never touch siteurl/home option writes — those legitimately store a domain.
            if ( preg_match( "/option_name\s*=\s*'(?:siteurl|home)'/i", $query ) ) {
                return $query;
            }

            self::$query_filter_in_progress = true;
            try {
                $rewritten = $this->rewrite_query_string_literals( $query );
            } catch ( \Throwable $e ) {
                // Failsafe — any parsing error returns the original query so we never break a save.
                $rewritten = $query;
            } finally {
                self::$query_filter_in_progress = false;
            }

            return $rewritten;
        }

        /**
         * Walk every single-quoted string literal in the SQL and clean each one.
         *
         * @param string $query
         *
         * @return string
         */
        private function rewrite_query_string_literals( $query ) {
            // Skip pathological-size queries — keeps PCRE under its backtrack
            // limit and avoids extra memory pressure on huge multi-row INSERTs.
            if ( strlen( $query ) > self::MAX_FILTER_QUERY_BYTES ) {
                return $query;
            }

            $pattern = "/'((?:[^'\\\\]|\\\\.)*)'/s";

            $rewritten = preg_replace_callback(
                $pattern,
                function ( $matches ) {
                    $escaped = $matches[1];

                    if ( strpos( $escaped, $this->current_domain ) === false ) {
                        return $matches[0];
                    }

                    $unescaped = $this->mysql_unescape( $escaped );
                    $cleaned   = $this->clean_query_string_value( $unescaped );

                    if ( $cleaned === $unescaped ) {
                        return $matches[0];
                    }

                    global $wpdb;
                    return "'" . $wpdb->_real_escape( $cleaned ) . "'";
                },
                $query
            );

            // PCRE error (backtrack/recursion limit, bad UTF-8 etc.) returns
            // null — fall back to the original query so we never hand mysqli a
            // NULL and trigger a fatal.
            if ( ! is_string( $rewritten ) ) {
                return $query;
            }

            return $rewritten;
        }

        /**
         *
         * Clean a single decoded SQL string value.
         *
         *
         * @param string $value
         *
         * @return string
         */
        private function clean_query_string_value( $value ) {
            if ( $this->looks_serialized( $value ) ) {
                // Refuse C: (any class) and O: that names anything other than stdClass.
                if ( preg_match( '/(?:C:\d+:"|O:\d+:"(?!stdClass":))/', $value ) ) {
                    return $value;
                }

                $unserialized = @unserialize( $value, array( 'allowed_classes' => array( 'stdClass' ) ) );
                if ( $unserialized !== false || $value === 'b:0;' || $value === 'N;' ) {
                    $cleaned = $this->replace_in_value( $unserialized, $this->current_domain, $this->db_site_url );
                    return serialize( $cleaned );
                }
            }

            // Skip values that aren't valid UTF-8 — likely binary / BLOB content.
            if ( @preg_match( '//u', $value ) !== 1 ) {
                return $value;
            }

            return str_replace( $this->current_domain, $this->db_site_url, $value );
        }

        /**
         * Cheap check whether a string looks like PHP-serialized data.
         *
         * @param string $value
         *
         * @return bool
         */
        private function looks_serialized( $value ) {
            if ( ! is_string( $value ) ) {
                return false;
            }
            if ( $value === 'N;' ) {
                return true;
            }
            if ( strlen( $value ) < 4 || $value[1] !== ':' ) {
                return false;
            }
            return in_array( $value[0], array( 'a', 's', 'b', 'i', 'd', 'O', 'C' ), true );
        }

        /**
         * Inverse of mysqli_real_escape_string for the escape sequences WordPress
         * actually produces (\0, \n, \r, \Z, \\, \', \").
         *
         * @param string $str
         *
         * @return string
         */
        private function mysql_unescape( $str ) {
            $result = '';
            $len    = strlen( $str );

            for ( $i = 0; $i < $len; $i++ ) {
                $c = $str[ $i ];
                if ( $c === '\\' && $i + 1 < $len ) {
                    $next = $str[ $i + 1 ];
                    switch ( $next ) {
                        case '0':  $result .= "\0";   break;
                        case 'n':  $result .= "\n";   break;
                        case 'r':  $result .= "\r";   break;
                        case 'Z':  $result .= "\x1A"; break;
                        case '\\': $result .= '\\';   break;
                        case '\'': $result .= '\'';   break;
                        case '"':  $result .= '"';    break;
                        default:   $result .= $next;  break;
                    }
                    $i++;
                } else {
                    $result .= $c;
                }
            }

            return $result;
        }
    }

    Hostinger_Temporary_Domain_Handler::init();
}
