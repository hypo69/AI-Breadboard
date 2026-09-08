<?php
/**
 * Handles WordPress comment hooks, filtering, and scheduled async AI reply execution.
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

class Comment_Handler {
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
     * Register hooks.
     *
     * @return void
     */
    public function register_hooks(): void {
        // Hook when a new comment is posted
        add_action('comment_post', [$this, 'on_comment_post'], 20, 3);

        // Hook when comment status changes to approved
        add_action('wp_set_comment_status', [$this, 'on_comment_status_changed'], 20, 2);

        // Action hook for scheduled async execution
        add_action('ai_responder_process_comment_event', [$this, 'process_comment_async'], 10, 1);
    }

    /**
     * Handler for new comment post event.
     *
     * @param int        $comment_id
     * @param int|string $comment_approved 1 if approved, 0 if in moderation, 'spam' if spam.
     * @param array      $commentdata
     * @return void
     */
    public function on_comment_post(int $comment_id, $comment_approved, array $commentdata): void {
        Logger::debug("New comment posted ID #$comment_id (status: $comment_approved)");

        if ((string)$comment_approved === '1' || $comment_approved === 1 || $comment_approved === 'approve') {
            $this->schedule_reply($comment_id);
        } else {
            Logger::debug("Comment #$comment_id is not approved immediately. Waiting for moderation.");
        }
    }

    /**
     * Handler when comment moderation status is changed.
     *
     * @param int    $comment_id
     * @param string $comment_status
     * @return void
     */
    public function on_comment_status_changed(int $comment_id, string $comment_status): void {
        if ($comment_status === 'approve' || $comment_status === '1') {
            Logger::debug("Comment #$comment_id status changed to approved. Scheduling AI reply.");
            $this->schedule_reply($comment_id);
        }
    }

    /**
     * Schedule asynchronous reply generation for a comment.
     *
     * @param int $comment_id
     * @return void
     */
    public function schedule_reply(int $comment_id): void {
        if (!Config::get('enabled', false)) {
            Logger::debug("Plugin is disabled in settings. Skipping comment #$comment_id.");
            return;
        }

        $comment = get_comment($comment_id);
        if (!$comment) {
            return;
        }

        // Validate comment eligible for reply
        if (!$this->is_eligible_for_reply($comment)) {
            return;
        }

        // Prevent duplicate scheduling
        if (get_comment_meta($comment_id, '_ai_responder_scheduled', true) || get_comment_meta($comment_id, '_ai_responder_replied', true)) {
            Logger::debug("Comment #$comment_id is already scheduled or replied. Skipping.");
            return;
        }

        update_comment_meta($comment_id, '_ai_responder_scheduled', time());

        $delay = (int)Config::get('reply_delay', 10);
        $timestamp = time() + max(1, $delay);

        wp_schedule_single_event($timestamp, 'ai_responder_process_comment_event', [$comment_id]);

        Logger::info("Scheduled AI reply for comment #$comment_id with $delay seconds delay.");
    }

    /**
     * Validate if a comment should be processed by the AI bot.
     *
     * @param \WP_Comment $comment
     * @return bool
     */
    public function is_eligible_for_reply(\WP_Comment $comment): bool {
        // Skip pingbacks and trackbacks
        if (!empty($comment->comment_type) && !in_array($comment->comment_type, ['comment', ''], true)) {
            Logger::debug("Skipping comment #{$comment->comment_ID}: non-standard comment type '{$comment->comment_type}'");
            return false;
        }

        $bot_user_id = (int)Config::get('bot_user_id', 0);

        // Crucial check: Prevent bot from replying to its own comments
        if ($bot_user_id > 0 && (int)$comment->user_id === $bot_user_id) {
            Logger::debug("Skipping comment #{$comment->comment_ID}: author is the configured AI bot user (user_id #$bot_user_id)");
            return false;
        }

        // Check if author is in excluded list
        $excluded_authors = (array)Config::get('exclude_authors', []);
        if (in_array(trim($comment->comment_author), $excluded_authors, true)) {
            Logger::debug("Skipping comment #{$comment->comment_ID}: author '{$comment->comment_author}' is excluded.");
            return false;
        }

        // Check minimum length
        $content = trim($comment->comment_content);
        $min_length = (int)Config::get('min_comment_length', 5);
        if (mb_strlen($content) < $min_length) {
            Logger::debug("Skipping comment #{$comment->comment_ID}: content too short (" . mb_strlen($content) . " < $min_length)");
            return false;
        }

        // Check excluded spam keywords
        $excluded_keywords = (array)Config::get('exclude_keywords', []);
        $content_lower = mb_strtolower($content);
        foreach ($excluded_keywords as $keyword) {
            $kw = trim(mb_strtolower($keyword));
            if (!empty($kw) && mb_strpos($content_lower, $kw) !== false) {
                Logger::warning("Skipping comment #{$comment->comment_ID}: contains excluded keyword '$kw'");
                return false;
            }
        }

        return true;
    }

    /**
     * Background execution to generate and insert the AI reply comment.
     *
     * @param int $comment_id
     * @return void
     */
    public function process_comment_async(int $comment_id): void {
        Logger::info("Executing background AI reply process for comment #$comment_id");

        $comment = get_comment($comment_id);
        if (!$comment) {
            Logger::error("Comment #$comment_id not found in database.");
            return;
        }

        if (get_comment_meta($comment_id, '_ai_responder_replied', true)) {
            Logger::info("Comment #$comment_id already received an AI reply. Skipping duplicate execution.");
            return;
        }

        $post = get_post($comment->comment_post_ID);
        $post_title = $post ? $post->post_title : '';
        $post_content = $post ? wp_strip_all_tags($post->post_content) : '';

        // Extract parent thread context if applicable
        $parent_context = $this->build_thread_context($comment);

        $payload = [
            'post_title'      => $post_title,
            'post_content'    => $post_content,
            'comment_author'  => $comment->comment_author,
            'comment_content' => $comment->comment_content,
            'parent_context'  => $parent_context,
            'model'           => Config::get('model', 'gemini-2.5-flash'),
            'provider'        => Config::get('provider', 'gemini'),
            'system_instruction' => Config::get('system_instruction', ''),
        ];

        $response = $this->client->generate_reply($payload);

        if (!$response['success'] || empty($response['reply'])) {
            Logger::error("Failed to generate AI response for comment #$comment_id: " . ($response['error'] ?: 'Unknown error'));
            return;
        }

        // Insert AI reply comment into WordPress
        $inserted_id = $this->insert_ai_comment($comment, $response['reply']);

        if ($inserted_id) {
            update_comment_meta($comment_id, '_ai_responder_replied', time());
            update_comment_meta($inserted_id, '_ai_responder_is_bot_reply', 1);
            update_comment_meta($inserted_id, '_ai_responder_model', $response['model'] ?? '');
            Logger::info("Successfully posted AI reply #$inserted_id to parent comment #$comment_id");
        } else {
            Logger::error("Failed to insert AI comment into WordPress database for parent #$comment_id");
        }
    }

    /**
     * Build linear thread context for nested comments.
     *
     * @param \WP_Comment $comment
     * @return string
     */
    protected function build_thread_context(\WP_Comment $comment): string {
        $context_lines = [];
        $current_parent_id = (int)$comment->comment_parent;
        $depth = 0;
        $max_depth = (int)Config::get('max_thread_depth', 5);

        while ($current_parent_id > 0 && $depth < $max_depth) {
            $parent = get_comment($current_parent_id);
            if (!$parent) {
                break;
            }
            $author = $parent->comment_author ?: 'User';
            $content = wp_strip_all_tags($parent->comment_content);
            array_unshift($context_lines, "$author: $content");
            $current_parent_id = (int)$parent->comment_parent;
            $depth++;
        }

        return implode("\n", $context_lines);
    }

    /**
     * Insert reply comment into WordPress DB.
     *
     * @param \WP_Comment $parent_comment
     * @param string      $reply_content
     * @return int|false
     */
    protected function insert_ai_comment(\WP_Comment $parent_comment, string $reply_content) {
        $bot_user_id = (int)Config::get('bot_user_id', 0);
        $author_name = 'AI Assistant';
        $author_email = 'ai@davidka.net';
        $author_url = home_url();

        if ($bot_user_id > 0) {
            $user = get_userdata($bot_user_id);
            if ($user) {
                $author_name  = $user->display_name ?: $user->user_login;
                $author_email = $user->user_email;
                $author_url   = $user->user_url ?: home_url();
            }
        }

        $auto_approve = Config::get('auto_approve', true) ? 1 : 0;

        $commentdata = [
            'comment_post_ID'      => $parent_comment->comment_post_ID,
            'comment_parent'       => $parent_comment->comment_ID,
            'comment_author'       => $author_name,
            'comment_author_email' => $author_email,
            'comment_author_url'   => $author_url,
            'comment_content'      => $reply_content,
            'comment_type'         => 'comment',
            'user_id'              => $bot_user_id > 0 ? $bot_user_id : 0,
            'comment_approved'     => $auto_approve,
            'comment_agent'        => 'AI Responder via kino.davidka.net',
        ];

        return wp_insert_comment($commentdata);
    }
}
