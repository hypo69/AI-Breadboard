<?php
/**
 * Structured logger for AI Responder plugin.
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

class Logger {
    const LEVEL_DEBUG = 'DEBUG';
    const LEVEL_INFO  = 'INFO';
    const LEVEL_WARN  = 'WARNING';
    const LEVEL_ERROR = 'ERROR';

    /**
     * Get the log file path.
     *
     * @return string
     */
    public static function get_log_file(): string {
        return AI_RESPONDER_PATH . 'ai-responder-debug.log';
    }

    /**
     * Ensure log directory exists and is writable.
     *
     * @return void
     */
    public static function create_log_directory(): void {
        $log_file = self::get_log_file();
        $dir = dirname($log_file);
        if (!file_exists($dir)) {
            wp_mkdir_p($dir);
        }
        if (!file_exists($log_file)) {
            file_put_contents($log_file, "# AI Responder Log Initialized: " . gmdate('Y-m-d H:i:s') . "\n");
        }
    }

    /**
     * Log a message with a specific severity level.
     *
     * @param string $level Severity level.
     * @param string $message Message to log.
     * @param mixed  $context Optional additional context data.
     * @return void
     */
    public static function log(string $level, string $message, $context = null): void {
        $timestamp = gmdate('Y-m-d H:i:s');
        $context_str = '';

        if ($context !== null) {
            if (is_array($context) || is_object($context)) {
                $context_str = ' | Context: ' . wp_json_encode($context, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            } else {
                $context_str = ' | Context: ' . (string)$context;
            }
        }

        $formatted = sprintf("[%s] [%s] %s%s\n", $timestamp, $level, $message, $context_str);

        // Append to local log file
        $log_file = self::get_log_file();
        @file_put_contents($log_file, $formatted, FILE_APPEND | LOCK_EX);

        // Log errors/warnings to standard WordPress debug.log if WP_DEBUG is enabled
        if (defined('WP_DEBUG') && WP_DEBUG && in_array($level, [self::LEVEL_WARN, self::LEVEL_ERROR], true)) {
            error_log('[AI-Responder] ' . $formatted);
        }
    }

    /**
     * Log debug message.
     */
    public static function debug(string $message, $context = null): void {
        if (Config::is_debug_mode()) {
            self::log(self::LEVEL_DEBUG, $message, $context);
        }
    }

    /**
     * Log info message.
     */
    public static function info(string $message, $context = null): void {
        self::log(self::LEVEL_INFO, $message, $context);
    }

    /**
     * Log warning message.
     */
    public static function warning(string $message, $context = null): void {
        self::log(self::LEVEL_WARN, $message, $context);
    }

    /**
     * Log error message.
     */
    public static function error(string $message, $context = null): void {
        self::log(self::LEVEL_ERROR, $message, $context);
    }

    /**
     * Retrieve recent log lines.
     *
     * @param int $lines Number of lines to return.
     * @return array
     */
    public static function get_recent_logs(int $lines = 100): array {
        $log_file = self::get_log_file();
        if (!file_exists($log_file)) {
            return [];
        }

        $content = file($log_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if ($content === false) {
            return [];
        }

        return array_slice($content, -$lines);
    }

    /**
     * Clear the log file.
     *
     * @return bool
     */
    public static function clear_logs(): bool {
        $log_file = self::get_log_file();
        return (bool)@file_put_contents($log_file, "# AI Responder Log Reset: " . gmdate('Y-m-d H:i:s') . "\n");
    }
}
