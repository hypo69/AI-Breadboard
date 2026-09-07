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
            self.app.add_handler(CommandHandler("auth", self._cmd_auth))
            self.app.add_handler(CommandHandler("login", self._cmd_auth))
            self.app.add_handler(CommandHandler("register", self._cmd_auth))
            self.app.add_handler(CommandHandler("dialogs", self._cmd_dialogs))
            self.app.add_handler(CommandHandler("link", self._cmd_link))
            self.app.add_handler(CommandHandler("tts", self._cmd_tts))

            # Callback queries
            self.app.add_handler(CallbackQueryHandler(self._handle_callback_query))

            # Media handlers for dialogue audio and transcripts
            self.app.add_handler(MessageHandler(filters.VOICE, self._handle_voice_dialog))
            self.app.add_handler(MessageHandler(filters.AUDIO, self._handle_audio_dialog))
            self.app.add_handler(MessageHandler(filters.Document.ALL, self._handle_document_dialog))

            # Text messages
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

    def _get_oauth_url(self, tg_id: int, tg_username: Optional[str] = "") -> str:
        """Construct Google OAuth registration URL for Telegram user.

        Args:
            tg_id (int): Telegram user ID.
            tg_username (Optional[str]): Telegram username.

        Returns:
            str: Full URL to Google OAuth authorization endpoint.
        """
        import urllib.parse
        api_base = self.config.get("api_base_url", "http://127.0.0.1:8000").rstrip("/")
        params: Dict[str, str] = {"tg_id": str(tg_id)}
        if tg_username:
            params["tg_username"] = str(tg_username)
        return f"{api_base}/auth/google?{urllib.parse.urlencode(params)}"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte count into human-readable string.

        Args:
            size_bytes (int): Size in bytes.

        Returns:
            str: Formatted string (e.g., '2.4 MB').
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    # ── Command Handlers ──────────────────────────────────────────────────────

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command.

        Displays user authentication state, Google OAuth registration link if unauthenticated,
        or personal workspace dashboard if authenticated.
        """
        if not update.effective_chat or not update.effective_user:
            return

        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""
        user_name = update.effective_user.first_name or "User"
        api_base = self.config.get("api_base_url", "http://127.0.0.1:8000").rstrip("/")
        rc_url = f"{api_base}/rc"

        from src.user_manager import user_manager
        user = user_manager.get_user_by_telegram_id(tg_id)

        if user:
            # User is authenticated & linked
            email = user.get("email", "")
            name = user.get("name", user_name)

            keyboard = [
                [InlineKeyboardButton("🎛 Remote Control (Mini App)", web_app=WebAppInfo(url=rc_url))],
                [
                    InlineKeyboardButton("📁 Мои записи диалогов", callback_data="btn_dialogs"),
                    InlineKeyboardButton("📊 Статус", callback_data="btn_status"),
                ],
                [
                    InlineKeyboardButton("❓ Помощь", callback_data="btn_help"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = (
                f"👋 *Здравствуйте, {name}!* Рады видеть вас в *AI Breadboard*.\n\n"
                f"👤 *Аккаунт:* `{email}`\n"
                f"🆔 *Telegram ID:* `{tg_id}`\n\n"
                "🎙 *Отправка записей диалогов:*\n"
                "Вы можете прямо сейчас отправлять сюда с телефона:\n"
                "• Голосовые сообщения\n"
                "• Аудиофайлы (`.mp3`, `.m4a`, `.wav`, `.ogg`)\n"
                "• Документы с расшифровками диалогов (`.txt`, `.json`, `.md`, `.docx`)\n\n"
                "Все файлы автоматически сохраняются в вашу изолированную папку `dialogs/` на сервере.\n\n"
                "• `/dialogs` — Просмотр ваших сохраненных записей\n"
                "• `/tts <текст>` — Озвучивание текста\n"
                "• `/status` — Состояние моделей и сервера\n"
                "• `/help` — Справка по всем командам"
            )
        else:
            # User is not linked yet — provide Google OAuth button
            oauth_url = self._get_oauth_url(tg_id, tg_username)

            keyboard = [
                [InlineKeyboardButton("🔑 Войти через Google OAuth", url=oauth_url)],
                [InlineKeyboardButton("🎛 Remote Control (Mini App)", web_app=WebAppInfo(url=rc_url))],
                [
                    InlineKeyboardButton("📊 Статус", callback_data="btn_status"),
                    InlineKeyboardButton("❓ Помощь", callback_data="btn_help"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = (
                f"👋 *Здравствуйте, {user_name}!* Добро пожаловать в *AI Breadboard*.\n\n"
                "Для привязки аккаунта и синхронизации файлов с вашей личной папкой на сервере, "
                "пожалуйста, авторизуйтесь через Google.\n\n"
                "Нажмите кнопку *«Войти через Google OAuth»* ниже.\n\n"
                "После входа вы сможете отправлять голосовые заметки и файлы записей диалогов, "
                "а они будут поступать в вашу персональную директорию."
            )

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _cmd_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /auth, /login, and /register commands for Google OAuth sign-in."""
        if not update.message or not update.effective_user:
            return

        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""

        from src.user_manager import user_manager
        user = user_manager.get_user_by_telegram_id(tg_id)

        if user:
            await update.message.reply_text(
                f"✅ Вы уже авторизованы как *{user.get('name', 'User')}* (`{user.get('email', '')}`).\n\n"
                "Вы можете сразу отправлять файлы с записями диалогов или воспользоваться `/dialogs`.",
                parse_mode="Markdown",
            )
            return

        oauth_url = self._get_oauth_url(tg_id, tg_username)
        keyboard = [[InlineKeyboardButton("🔑 Авторизоваться через Google", url=oauth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔑 *Авторизация через Google OAuth*\n\n"
            "Нажмите кнопку ниже, чтобы войти в свой Google аккаунт и привязать его к Telegram:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _cmd_dialogs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /dialogs command to list saved dialogue recordings."""
        if not update.message or not update.effective_user:
            return

        tg_id = update.effective_user.id
        from src.user_manager import user_manager
        user = user_manager.get_user_by_telegram_id(tg_id)

        if not user:
            oauth_url = self._get_oauth_url(tg_id, update.effective_user.username or "")
            keyboard = [[InlineKeyboardButton("🔑 Войти через Google OAuth", url=oauth_url)]]
            await update.message.reply_text(
                "⚠️ *Требуется авторизация*\n\n"
                "Авторизуйтесь через Google, чтобы получить доступ к своим файлам диалогов:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return

        dialogs_dir = user_manager.get_user_directory(user["id"], "dialogs", create=True)
        files = sorted(list(dialogs_dir.glob("*")), key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True)
        file_items = [f for f in files if f.is_file()]

        if not file_items:
            await update.message.reply_text(
                f"📁 *Ваша папка диалогов пуста*\n\n"
                f"📂 Директория: `data/users/{user['id']}/dialogs/`\n\n"
                "Отправьте аудиосообщение или файл записи диалога с телефона, и он появится здесь!",
                parse_mode="Markdown",
            )
            return

        total_bytes = sum(f.stat().st_size for f in file_items)
        lines = [
            f"📁 *Ваши файлы записей диалогов ({len(file_items)} шт., {self._format_size(total_bytes)}):*\n"
        ]
        for f in file_items[:10]:
            lines.append(f"• `{f.name}` ({self._format_size(f.stat().st_size)})")

        if len(file_items) > 10:
            lines.append(f"\n_...и еще {len(file_items) - 10} файлов._")

        lines.append(f"\n📂 *Путь на сервере:* `data/users/{user['id']}/dialogs/`")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        if not update.message:
            return

        help_text = (
            "📖 *Команды AI Breadboard Bot:*\n\n"
            "• `/start` — Главное меню и статус подключения\n"
            "• `/auth` или `/login` — Вход через Google OAuth\n"
            "• `/dialogs` — Список ваших записей диалогов в личной папке\n"
            "• `/link <ТОКЕН>` — Ручная привязка по 8-значному токену из профиля\n"
            "• `/status` — Состояние сервисов и активных нейросетей\n"
            "• `/tts <текст>` — Голосовое озвучивание текста\n"
            "• `/help` — Эта справка\n\n"
            "🎙 *Записи диалогов:* Просто отправьте аудиофайл, голосовое сообщение или документ с телефона, и бот сохранит его в вашу персональную директорию!\n\n"
            "💬 *AI Чат:* Отправьте текстовое сообщение, чтобы спросить ассистента."
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
                "⚠️ *Использование:* `/link <8-значный-токен>`\n\n"
                "Токен привязки можно сгенерировать в веб-интерфейсе в профиле пользователя.",
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
                    f"✅ *Аккаунт успешно привязан!*\n\n"
                    f"Ваш Telegram ID (`{tg_id}`) подключен к учетной записи AI Breadboard.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "❌ *Ошибка привязки.* Токен истек или недействителен. Сгенерируйте новый в настройках веб-профиля.",
                    parse_mode="Markdown",
                )
        except Exception as exc:
            logger.error(f"Error executing account linking: {exc}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка привязки аккаунта: {exc}")

    async def _cmd_tts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tts <text> voice synthesis command."""
        if not update.message:
            return

        text = " ".join(context.args or []).strip()
        if not text:
            await update.message.reply_text("⚠️ *Использование:* `/tts <текст для озвучки>`", parse_mode="Markdown")
            return

        api_base = self.config.get("api_base_url", "http://127.0.0.1:8000")
        await handle_telegram_voiceover_request(update, context, text=text, api_base_url=api_base)

    # ── Dialogue Media File Handlers ──────────────────────────────────────────

    async def _save_dialog_attachment(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        attachment: Any,
        default_filename: str,
    ) -> None:
        """Authenticate user and save received media or document into their dialogue directory."""
        if not update.message or not update.effective_user:
            return

        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""

        from src.user_manager import user_manager
        user = user_manager.get_user_by_telegram_id(tg_id)

        if not user:
            oauth_url = self._get_oauth_url(tg_id, tg_username)
            keyboard = [[InlineKeyboardButton("🔑 Войти через Google OAuth", url=oauth_url)]]
            await update.message.reply_text(
                "⚠️ *Требуется авторизация*\n\n"
                "Чтобы отправлять файлы диалогов в вашу персональную директорию на сервере, "
                "пожалуйста, авторизуйтесь через Google:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
            return

        try:
            await update.message.chat.send_action("upload_document")
            tg_file = await context.bot.get_file(attachment.file_id)
            data_bytes = bytes(await tg_file.download_as_bytearray())

            meta = user_manager.save_user_dialog_file(
                user_id=user["id"],
                filename=default_filename,
                content=data_bytes,
                subfolder="dialogs",
            )

            file_size_str = self._format_size(meta["size_bytes"])
            user_display = user.get("name") or user.get("email") or f"User #{user['id']}"

            response_text = (
                "✅ *Файл диалога успешно сохранён!*\n\n"
                f"📁 *Файл:* `{meta['filename']}`\n"
                f"📦 *Размер:* `{file_size_str}`\n"
                f"📂 *Директория:* `{meta['relative_path']}`\n"
                f"👤 *Пользователь:* {user_display}\n\n"
                "Файл доступен в вашей рабочей области AI Breadboard."
            )
            await update.message.reply_text(response_text, parse_mode="Markdown")

        except Exception as exc:
            logger.error(f"Error saving dialogue attachment: {exc}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка сохранения файла диалога: {exc}")

    async def _handle_voice_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming voice messages from user's phone."""
        if not update.message or not update.message.voice:
            return
        voice = update.message.voice
        unique_id = getattr(voice, "file_unique_id", "voice")
        default_name = f"voice_{unique_id}.ogg"
        await self._save_dialog_attachment(update, context, voice, default_name)

    async def _handle_audio_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming audio files from user's phone."""
        if not update.message or not update.message.audio:
            return
        audio = update.message.audio
        name = audio.file_name or f"audio_{getattr(audio, 'file_unique_id', 'clip')}.mp3"
        await self._save_dialog_attachment(update, context, audio, name)

    async def _handle_document_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming document files (transcripts, dialogue logs, audio files as docs)."""
        if not update.message or not update.message.document:
            return
        doc = update.message.document
        name = doc.file_name or f"doc_{getattr(doc, 'file_unique_id', 'file')}.dat"
        await self._save_dialog_attachment(update, context, doc, name)

    # ── Text & Callback Query Handlers ────────────────────────────────────────

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
                "📖 *Команды:* /start, /auth, /dialogs, /status, /link <токен>, /tts <текст>.\n\n"
                "Отправляйте голосовые сообщения и файлы с телефона для сохранения в личную папку диалогов.",
                parse_mode="Markdown",
            )
        elif data == "btn_dialogs":
            if update.effective_user:
                from src.user_manager import user_manager
                user = user_manager.get_user_by_telegram_id(update.effective_user.id)
                if user:
                    dialogs_dir = user_manager.get_user_directory(user["id"], "dialogs", create=True)
                    files = [f for f in dialogs_dir.glob("*") if f.is_file()]
                    total_bytes = sum(f.stat().st_size for f in files)
                    text = f"📁 *Ваши записи диалогов:* {len(files)} шт. ({self._format_size(total_bytes)})\n📂 `data/users/{user['id']}/dialogs/`"
                else:
                    text = "⚠️ Авторизуйтесь через Google с помощью команды /auth."
                await query.edit_message_text(text, parse_mode="Markdown")

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
            await update.message.reply_text(f"⚠️ Ошибка генерации ответа: {exc}")

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
