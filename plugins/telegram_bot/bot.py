# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Bot Service and Command Dispatcher
# =============================================================================
# Description:
#   Implements the core Telegram bot lifecycle using python-telegram-bot, routing
#   commands (/start, /help, /link, /status, /tts), Mini App web app integration,
#   and AI assistant chat responses.
#
# File: bot.py
# Project: ai-breadboard
# Package: plugins.telegram_bot
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram bot engine and command router.

Manages the python-telegram-bot Application lifecycle, polling loop,
user authentication, account linking, remote control web app, and AI chat.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.logger import logger
from plugins.telegram_bot.tts import handle_telegram_voiceover_request


class TelegramBotEngine:
    """Manages Telegram bot application lifecycle, commands, and messaging.

    Attributes:
        token (str): Bot API token.
        admin_ids (List[int]): List of administrator Telegram user IDs.
        ai_model (Any): Optional AI model instance for conversational responses.
        config (Dict[str, Any]): Bot runtime configuration.
        app (Optional[Application]): python-telegram-bot Application instance.
        is_running (bool): Running status of the polling engine.
    """

    def __init__(
        self,
        token: str,
        admin_ids: Optional[List[int]] = None,
        ai_model: Any = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the Telegram bot engine.

        Args:
            token (str): Telegram Bot token from BotFather.
            admin_ids (Optional[List[int]]): List of authorized admin Telegram user IDs.
            ai_model (Any): Optional AI model instance.
            config (Optional[Dict[str, Any]]): Configuration dictionary.
        """
        self.token: str = token.strip() if token else ""
        self.admin_ids: List[int] = admin_ids or []
        self.ai_model: Any = ai_model
        self.config: Dict[str, Any] = config or {}
        self.app: Optional[Application] = None
        self.is_running: bool = False
        self._bot_info: Dict[str, Any] = {}

    def is_configured(self) -> bool:
        """Check if bot has a valid non-empty token configured.

        Returns:
            bool: True if token is present and valid string format.
        """
        return bool(self.token and len(self.token) > 10 and ":" in self.token)

    async def initialize(self) -> bool:
        """Build and configure the python-telegram-bot Application instance.

        Returns:
            bool: True if initialized successfully, False otherwise.
        """
        if not self.is_configured():
            logger.warning("TelegramBotEngine: Token is not configured or invalid.")
            return False

        try:
            self.app = (
                ApplicationBuilder()
                .token(self.token)
                .build()
            )

            # Register standard command handlers
            self.app.add_handler(CommandHandler("start", self._cmd_start))
            self.app.add_handler(CommandHandler("help", self._cmd_help))
            self.app.add_handler(CommandHandler("status", self._cmd_status))
            self.app.add_handler(CommandHandler("link", self._cmd_link))
            self.app.add_handler(CommandHandler("tts", self._cmd_tts))

            # Callback queries and text messages
            self.app.add_handler(CallbackQueryHandler(self._handle_callback_query))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))

            await self.app.initialize()
            logger.info("TelegramBotEngine: Application initialized.")
            return True

        except Exception as exc:
            logger.error(f"TelegramBotEngine initialization failed: {exc}", exc_info=True)
            self.app = None
            return False

    async def start(self) -> None:
        """Start the Telegram bot background updater and polling.

        Exceptions:
            RuntimeError: If initialization fails or token is missing.
        """
        if self.is_running:
            logger.info("TelegramBotEngine is already running.")
            return

        if not self.app:
            ok = await self.initialize()
            if not ok or not self.app:
                raise RuntimeError("Cannot start Telegram bot: Initialization failed.")

        try:
            await self.app.start()
            if self.app.updater:
                await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            self.is_running = True

            bot_user = await self.app.bot.get_me()
            self._bot_info = {
                "id": bot_user.id,
                "username": bot_user.username,
                "first_name": bot_user.first_name,
            }
            logger.info(f"Telegram bot started successfully as @{bot_user.username} (ID: {bot_user.id}).")

        except Exception as exc:
            self.is_running = False
            logger.error(f"Failed to start Telegram bot updater: {exc}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Gracefully stop polling and shutdown Telegram bot application."""
        if not self.is_running or not self.app:
            return

        try:
            logger.info("Stopping Telegram bot...")
            if self.app.updater and self.app.updater.running:
                await self.app.updater.stop()
            if self.app.running:
                await self.app.stop()
            await self.app.shutdown()
            self.is_running = False
            logger.info("Telegram bot stopped cleanly.")
        except Exception as exc:
            logger.error(f"Error while stopping Telegram bot: {exc}", exc_info=True)
            self.is_running = False

    def get_info(self) -> Dict[str, Any]:
        """Return runtime status information of the bot engine.

        Returns:
            Dict[str, Any]: Status metadata dictionary.
        """
        return {
            "configured": self.is_configured(),
            "running": self.is_running,
            "bot_info": self._bot_info,
            "admin_count": len(self.admin_ids),
        }

    # ── Command Handlers ──────────────────────────────────────────────────────

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command.

        Displays welcome message and optional WebApp launch button for Remote Control.
        """
        if not update.effective_chat or not update.effective_user:
            return

        user_name = update.effective_user.first_name or "User"
        api_base = self.config.get("api_base_url", "http://127.0.0.1:8000")
        rc_url = f"{api_base}/rc"

        keyboard = [
            [InlineKeyboardButton("🎛 Remote Control (Mini App)", web_app=WebAppInfo(url=rc_url))],
            [
                InlineKeyboardButton("📊 Status", callback_data="btn_status"),
                InlineKeyboardButton("❓ Help", callback_data="btn_help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            f"👋 *Hello, {user_name}!* Welcome to *AI Breadboard Assistant*.\n\n"
            "I can assist you with your media library, stream AI responses, and provide "
            "remote control for your cosmic player.\n\n"
            "• `/link <token>` — Link your Telegram account to AI Breadboard\n"
            "• `/status` — View system and model status\n"
            "• `/tts <text>` — Synthesize voice message\n"
            "• `/help` — List available commands\n\n"
            "Tap below to launch the Remote Control Mini App!"
        )

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        if not update.message:
            return

        help_text = (
            "📖 *AI Breadboard Bot Commands:*\n\n"
            "• `/start` — Welcome screen and Mini App launcher\n"
            "• `/link <TOKEN>` — Link account with 8-character token from web profile\n"
            "• `/status` — System, server, and active AI model health status\n"
            "• `/tts <text>` — Convert text to adaptive voice note\n"
            "• `/help` — Show this help message\n\n"
            "💬 *Chat:* Simply send any text message to ask the AI assistant!"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        if not update.message:
            return

        status_text = self._build_status_message()
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def _cmd_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /link <token> command to bind user account."""
        if not update.message or not update.effective_user:
            return

        args = context.args or []
        if not args:
            await update.message.reply_text(
                "⚠️ *Usage:* `/link <8-character-token>`\n\n"
                "Get your link token in AI Breadboard Web Interface under *User Profile*.",
                parse_mode="Markdown",
            )
            return

        token = args[0].strip().upper()
        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""

        try:
            from src.user_manager import user_manager

            success = user_manager.link_telegram_account(token, tg_id, tg_username)
            if success:
                await update.message.reply_text(
                    f"✅ *Account linked successfully!*\n\n"
                    f"Your Telegram ID (`{tg_id}`) is now connected to your AI Breadboard account.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "❌ *Linking failed.* The token may be expired or invalid. Please generate a new token in web settings.",
                    parse_mode="Markdown",
                )
        except Exception as exc:
            logger.error(f"Error executing account linking: {exc}", exc_info=True)
            await update.message.reply_text(f"❌ Error linking account: {exc}")

    async def _cmd_tts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tts <text> voice synthesis command."""
        if not update.message:
            return

        text = " ".join(context.args or []).strip()
        if not text:
            await update.message.reply_text("⚠️ *Usage:* `/tts <text to speak>`", parse_mode="Markdown")
            return

        api_base = self.config.get("api_base_url", "http://127.0.0.1:8000")
        await handle_telegram_voiceover_request(update, context, text=text, api_base_url=api_base)

    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        if not query:
            return

        await query.answer()
        data = query.data or ""

        if data == "btn_status":
            await query.edit_message_text(self._build_status_message(), parse_mode="Markdown")
        elif data == "btn_help":
            await query.edit_message_text(
                "📖 *Commands:* /start, /help, /status, /link <token>, /tts <text>.",
                parse_mode="Markdown",
            )

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages and query the AI model."""
        if not update.message or not update.message.text:
            return

        user_text = update.message.text.strip()
        if not user_text:
            return

        # Check if AI model is available
        if not self.ai_model:
            await update.message.reply_text(
                f"🤖 Echo: {user_text}\n\n_(AI model is currently not attached)_",
            )
            return

        try:
            # Send typing action
            await update.message.chat.send_action("typing")

            # Route through chat or generate method
            ai_reply = ""
            if hasattr(self.ai_model, "chat") and callable(self.ai_model.chat):
                res = self.ai_model.chat(user_text)
                ai_reply = await res if asyncio.iscoroutine(res) else str(res)
            elif hasattr(self.ai_model, "generate") and callable(self.ai_model.generate):
                res = self.ai_model.generate(user_text)
                ai_reply = await res if asyncio.iscoroutine(res) else str(res)
            else:
                ai_reply = f"AI model received: {user_text}"

            await update.message.reply_text(ai_reply)

        except Exception as exc:
            logger.error(f"Error generating AI reply for Telegram message: {exc}", exc_info=True)
            await update.message.reply_text(f"⚠️ Error generating response: {exc}")

    def _build_status_message(self) -> str:
        """Construct status report string."""
        model_name = "None"
        if self.ai_model:
            model_name = getattr(self.ai_model, "model_name", type(self.ai_model).__name__)

        return (
            "📊 *AI Breadboard Status:*\n\n"
            f"• *Bot Service:* {'🟢 Online' if self.is_running else '🔴 Offline'}\n"
            f"• *Bot Username:* @{self._bot_info.get('username', 'Unknown')}\n"
            f"• *Active AI Model:* `{model_name}`\n"
            f"• *Configured Admins:* {len(self.admin_ids)}\n"
        )
