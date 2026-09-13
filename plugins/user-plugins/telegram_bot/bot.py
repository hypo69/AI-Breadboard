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
            self.app.add_handler(CommandHandler("auth", self._cmd_start))
            self.app.add_handler(CommandHandler("login", self._cmd_start))
            self.app.add_handler(CommandHandler("register", self._cmd_start))
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
        """Handle /start command with Deep Linking support (/start <TOKEN>)."""
        if not update.effective_chat or not update.effective_user or not update.message:
            return

        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""
        user_name = update.effective_user.first_name or "User"

        from src.user_manager import user_manager

        # Check for deep-link payload: /start A1B2C3D4
        args = context.args or []
        if args:
            token_candidate = args[0].strip().upper()
            if len(token_candidate) == 8 and re.match(r'^[A-F0-9]{8}$', token_candidate):
                success = user_manager.link_telegram_account(token_candidate, tg_id, tg_username or user_name)
                if success:
                    user = user_manager.get_user_by_telegram_id(tg_id)
                    u_name = user.get("name") or user_name
                    email = user.get("email", "")
                    await update.message.reply_text(
                        f"🎉 *Здравствуйте, {u_name}! Ваш Telegram-аккаунт успешно привязан!*\n\n"
                        f"👤 *Аккаунт:* `{email}`\n"
                        f"🆔 *Telegram ID:* `{tg_id}`\n\n"
                        "🎙 Теперь вы можете отправлять голосовые заметки и аудиофайлы прямо сюда.\n"
                        "Они сохраняются в вашей персональной папке на сервере и обрабатываются инструментами AI Breadboard.",
                        parse_mode="Markdown",
                    )
                    return
                else:
                    await update.message.reply_text(
                        "❌ *Ошибка привязки аккаунта!*\nКод недействителен, истек (10 минут) или уже использован.\n"
                        "Сгенерируйте новый код в веб-профиле.",
                        parse_mode="Markdown",
                    )
                    return

        # Check existing linked user
        user = user_manager.get_user_by_telegram_id(tg_id)

        api_base = self.config.get("api_base_url", "").rstrip("/")
        rc_url = f"{api_base}/rc" if api_base else ""

        if user:
            # Authenticated user
            email = user.get("email", "")
            name = user.get("name", user_name)

            keyboard: List[List[InlineKeyboardButton]] = []
            if rc_url.lower().startswith("https://"):
                keyboard.append([InlineKeyboardButton("🎛 Remote Control (Mini App)", web_app=WebAppInfo(url=rc_url))])

            keyboard.append([
                InlineKeyboardButton("📁 Мои аудиозаписи", callback_data="btn_dialogs"),
                InlineKeyboardButton("📊 Статус", callback_data="btn_status"),
            ])
            keyboard.append([
                InlineKeyboardButton("❓ Помощь", callback_data="btn_help"),
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = (
                f"👋 *Здравствуйте, {name}!* Рады видеть вас в *AI Breadboard*.\n\n"
                f"👤 *Аккаунт:* `{email}`\n"
                f"🆔 *Telegram ID:* `{tg_id}`\n\n"
                "🎙 *Отправка аудиозаписей:*\n"
                "Вы можете отправлять сюда:\n"
                "• Голосовые сообщения\n"
                "• Аудиофайлы (`.mp3`, `.m4a`, `.wav`, `.ogg`)\n"
                "• Документы с аудиозаписями\n\n"
                "Все файлы сохраняются напрямую в вашу персональную папку `audio/` на сервере и обрабатываются нашими инструментами.\n\n"
                "• `/dialogs` — Список сохранённых аудиозаписей\n"
                "• `/status` — Состояние сервисов и нейросетей\n"
                "• `/tts <текст>` — Голосовое озвучивание текста"
            )
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            # Unauthenticated user — require /link <TOKEN>
            keyboard = [
                [
                    InlineKeyboardButton("📊 Статус", callback_data="btn_status"),
                    InlineKeyboardButton("❓ Помощь", callback_data="btn_help"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            welcome_text = (
                f"👋 *Здравствуйте, {user_name}!* Добро пожаловать в *AI Breadboard*.\n\n"
                "🔒 *Требуется привязка аккаунта:*\n"
                "Чтобы бот сохранял файлы в вашу личную изолированную папку и обрабатывал их, "
                "необходимо связать ваш Telegram-аккаунт с профилем в системе.\n\n"
                "📌 *Как привязать:*\n"
                "1. Войдите в веб-интерфейс AI Breadboard\n"
                "2. В профиле пользователя нажмите кнопку *«Привязать Telegram»* (или скопируйте 8-значный код)\n"
                "3. Отправьте код сюда командой `/link <КОД>` (или просто пришлите сам 8-значный код)."
            )
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

    async def _cmd_dialogs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /dialogs command to list user's audio recordings and dialog files."""
        if not update.message or not update.effective_user:
            return

        from src.user_manager import user_manager
        user = user_manager.get_user_by_telegram_id(update.effective_user.id)

        if not user:
            await update.message.reply_text(
                "🔒 *Требуется привязка аккаунта!*\nОтправьте команду `/link <КОД>`, полученный в профиле.",
                parse_mode="Markdown",
            )
            return

        user_id = user["id"]
        audio_dir = user_manager.get_user_directory(user_id, "audio", create=True)
        dialogs_dir = user_manager.get_user_directory(user_id, "dialogs", create=True)

        audio_files = sorted([f for f in audio_dir.glob("*") if f.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
        dialog_files = sorted([f for f in dialogs_dir.glob("*") if f.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)

        total_audio_bytes = sum(f.stat().st_size for f in audio_files)
        
        text = (
            f"📁 *Ваше персональное хранилище:*\n\n"
            f"🎙 *Аудиофайлы:* {len(audio_files)} шт. ({self._format_size(total_audio_bytes)})\n"
            f"📂 `data/users/{user_id}/audio/`\n\n"
            f"📋 *Отчёты и стенограммы:* {len(dialog_files)} шт.\n"
            f"📂 `data/users/{user_id}/dialogs/`\n"
        )

        if audio_files:
            text += "\n*Последние аудиофайлы:*\n"
            for f in audio_files[:5]:
                text += f"• `{f.name}` ({self._format_size(f.stat().st_size)})\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    async def _cmd_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /auth, /login, /register commands as alias to /start."""
        await self._cmd_start(update, context)

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        if not update.message:
            return

        help_text = (
            "📖 *Справка по командам AI Breadboard Bot:*\n\n"
            "• `/start` — Главное меню и статус авторизации\n"
            "• `/link <ТОКЕН>` — Привязать Telegram к веб-профилю по 8-значному коду\n"
            "• `/dialogs` — Список ваших аудиозаписей в персональной папке\n"
            "• `/status` — Состояние сервера и подключенных AI-моделей\n"
            "• `/tts <текст>` — Озвучить текст голосом\n"
            "• `/help` — Эта справка\n\n"
            "🎙 *Обработка аудио:* Отправьте голосовое сообщение или аудиофайл — бот сохранит его в вашу личную директорию, распознает речь и проведет диаризацию."
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
                "⚠️ *Использование:* `/link <8-значный-код>`\n\n"
                "Код привязки можно сгенерировать в веб-интерфейсе в профиле пользователя.",
                parse_mode="Markdown",
            )
            return

        token = args[0].strip().upper()
        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""
        user_name = update.effective_user.first_name or "User"

        try:
            from src.user_manager import user_manager

            success = user_manager.link_telegram_account(token, tg_id, tg_username or user_name)
            if success:
                user = user_manager.get_user_by_telegram_id(tg_id)
                u_name = user.get("name", user_name)
                email = user.get("email", "")
                await update.message.reply_text(
                    f"🎉 *Здравствуйте, {u_name}! Ваш Telegram-аккаунт успешно привязан!*\n\n"
                    f"👤 *Аккаунт:* `{email}`\n"
                    f"🆔 *Telegram ID:* `{tg_id}`\n\n"
                    "Теперь вы можете отправлять аудиофайлы и голосовые сообщения для обработки.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "❌ *Ошибка привязки.* Код истек или недействителен. Сгенерируйте новый в настройках профиля.",
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

    # ── Dialogue Audio Handlers ───────────────────────────────────────────────

    async def _save_and_process_audio(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        attachment: Any,
        default_filename: str,
    ) -> None:
        """Authenticate user, save audio directly into isolated user workspace, and process with audio tools."""
        if not update.message or not update.effective_user:
            return

        tg_id = update.effective_user.id
        from src.user_manager import user_manager
        user = user_manager.get_user_by_telegram_id(tg_id)

        if not user:
            await update.message.reply_text(
                "🔒 *Доступ ограничен!*\n\n"
                "Для сохранения и обработки аудио необходимо привязать ваш аккаунт.\n"
                "Сгенерируйте код в веб-профиле и отправьте команду `/link <КОД>` (или откройте прямую ссылку из профиля).",
                parse_mode="Markdown",
            )
            return

        user_id = user["id"]

        try:
            status_msg = await update.message.reply_text("📥 *Сохраняю аудиофайл в вашу личную папку...*", parse_mode="Markdown")

            # 1. Download file directly into user's audio directory
            user_audio_dir = user_manager.get_user_directory(user_id, subfolder="audio", create=True)

            clean_name = Path(default_filename).name
            clean_name = "".join(c for c in clean_name if c.isalnum() or c in ("-", "_", ".", " ")).strip()
            if not clean_name:
                clean_name = f"audio_{int(time.time())}.ogg"

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp_str}_{clean_name}"
            saved_file_path = user_audio_dir / saved_filename

            await update.message.chat.send_action("upload_document")
            tg_file = await context.bot.get_file(attachment.file_id)
            await tg_file.download_to_drive(saved_file_path)

            file_size_str = self._format_size(saved_file_path.stat().st_size)
            await status_msg.edit_text(
                f"✅ *Файл сохранён:* `{saved_filename}` ({file_size_str})\n"
                "⚙️ *Запускаю распознавание речи и анализ диалога...*",
                parse_mode="Markdown",
            )

            # 2. Run speech recognition
            recognized_text = ""
            try:
                from src.utils.convertors.tts import speech_recognizer
                loop = asyncio.get_event_loop()
                recognized_text = await loop.run_in_executor(
                    None, speech_recognizer, None, saved_file_path, "ru-RU"
                )
            except Exception as sr_err:
                logger.warning(f"Speech recognition notice: {sr_err}")

            # 3. If audio diarization service is available, process dialogue
            diarization_summary = ""
            try:
                from src.ai.audio_diarization import AudioDiarizationService
                diar_service = AudioDiarizationService()
                diar_res = await diar_service.process_audio_file(saved_file_path)
                if diar_res and diar_res.summary:
                    diarization_summary = diar_res.markdown_report or diar_res.summary
            except Exception as diar_err:
                logger.info(f"Diarization status: {diar_err}")

            # 4. Save markdown report to user's dialogs directory
            user_dialogs_dir = user_manager.get_user_directory(user_id, subfolder="dialogs", create=True)
            transcript_md_path = user_dialogs_dir / f"{timestamp_str}_transcript.md"

            md_lines = [
                f"# Аудиозапись: {saved_filename}",
                f"- **Дата загрузки:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **Размер файла:** {file_size_str}",
                f"- **Путь к файлу:** `data/users/{user_id}/audio/{saved_filename}`",
                "",
            ]
            if recognized_text and not recognized_text.startswith("Error") and not recognized_text.startswith("Could not"):
                md_lines.extend(["## Распознанный текст", "", recognized_text, ""])
            if diarization_summary:
                md_lines.extend(["## Анализ и стенограмма диалога", "", diarization_summary, ""])

            transcript_md_path.write_text("\n".join(md_lines), encoding="utf-8")

            # 5. Build user response
            res_parts = [
                "🎙 *Результат обработки аудио:*",
                f"📁 *Файл:* `{saved_filename}` ({file_size_str})",
            ]
            if recognized_text and not recognized_text.startswith("Error") and not recognized_text.startswith("Could not"):
                res_parts.append(f"\n💬 *Распознанный текст:*\n«{recognized_text}»")
            
            if diarization_summary:
                trimmed_summary = diarization_summary[:3000]
                res_parts.append(f"\n📋 *Анализ / Резюме:*\n{trimmed_summary}")

            if (not recognized_text or recognized_text.startswith("Could not")) and not diarization_summary:
                res_parts.append("\nℹ️ Аудио успешно сохранено в вашей личной папке.")

            res_parts.append(f"\n📂 *Личная папка:* `data/users/{user_id}/audio/`")

            await status_msg.edit_text("\n".join(res_parts), parse_mode="Markdown")

        except Exception as exc:
            logger.error(f"Error processing audio attachment: {exc}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка обработки аудио: {exc}")

    async def _handle_voice_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming voice messages."""
        if not update.message or not update.message.voice:
            return
        voice = update.message.voice
        unique_id = getattr(voice, "file_unique_id", "voice")
        default_name = f"voice_{unique_id}.ogg"
        await self._save_and_process_audio(update, context, voice, default_name)

    async def _handle_audio_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming audio files."""
        if not update.message or not update.message.audio:
            return
        audio = update.message.audio
        name = audio.file_name or f"audio_{getattr(audio, 'file_unique_id', 'clip')}.mp3"
        await self._save_and_process_audio(update, context, audio, name)

    async def _handle_document_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming documents (audio documents and transcripts)."""
        if not update.message or not update.message.document:
            return
        doc = update.message.document
        name = doc.file_name or f"doc_{getattr(doc, 'file_unique_id', 'file')}.dat"
        await self._save_and_process_audio(update, context, doc, name)

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
                "📖 *Команды:* /start, /link <код>, /dialogs, /status, /tts <текст>.\n\n"
                "Отправляйте голосовые сообщения и аудиофайлы для автоматического сохранения в личную папку и распознавания.",
                parse_mode="Markdown",
            )
        elif data == "btn_dialogs":
            if update.effective_user:
                from src.user_manager import user_manager
                user = user_manager.get_user_by_telegram_id(update.effective_user.id)
                if user:
                    audio_dir = user_manager.get_user_directory(user["id"], "audio", create=True)
                    files = [f for f in audio_dir.glob("*") if f.is_file()]
                    total_bytes = sum(f.stat().st_size for f in files)
                    text = f"📁 *Ваши аудиозаписи:* {len(files)} шт. ({self._format_size(total_bytes)})\n📂 `data/users/{user['id']}/audio/`"
                else:
                    text = "🔒 Сначала привяжите аккаунт, отправив `/link <КОД>`."
                await query.edit_message_text(text, parse_mode="Markdown")

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages (direct token input or AI chat)."""
        if not update.message or not update.message.text or not update.effective_user:
            return

        user_text = update.message.text.strip()
        if not user_text:
            return

        tg_id = update.effective_user.id
        tg_username = update.effective_user.username or ""
        user_name = update.effective_user.first_name or "User"

        from src.user_manager import user_manager

        # Check if user entered an 8-character linking token directly: "A1B2C3D4", "link A1B2C3D4", "/link A1B2C3D4"
        token_match = re.match(r'^(?:/?link\s+)?/?([A-F0-9]{8})$', user_text, re.IGNORECASE)
        if token_match:
            token = token_match.group(1).upper()
            success = user_manager.link_telegram_account(token, tg_id, tg_username or user_name)
            if success:
                user = user_manager.get_user_by_telegram_id(tg_id)
                u_name = user.get("name", user_name)
                await update.message.reply_text(
                    f"🎉 *Здравствуйте, {u_name}! Ваш Telegram-аккаунт успешно привязан!*\n\n"
                    f"👤 *Аккаунт:* `{user.get('email', '')}`\n"
                    f"🆔 *Telegram ID:* `{tg_id}`\n\n"
                    "Теперь вы можете отправлять голосовые заметки и аудиофайлы прямо сюда.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "❌ *Ошибка привязки аккаунта!*\nКод недействителен, истек (10 минут) или уже использован.\n"
                    "Сгенерируйте новый код в веб-профиле.",
                    parse_mode="Markdown",
                )
            return

        # Check if user is linked
        user = user_manager.get_user_by_telegram_id(tg_id)
        if not user:
            await update.message.reply_text(
                "🔒 *Доступ ограничен!*\n\n"
                "Чтобы пользоваться ботом, привяжите ваш аккаунт: откройте профиль в веб-интерфейсе, "
                "нажмите кнопку *«Привязать Telegram»* или отправьте сюда полученный код командой `/link <КОД>`.",
                parse_mode="Markdown",
            )
            return

        # If AI model is attached, query AI model
        if not self.ai_model:
            await update.message.reply_text(
                f"🤖 Сообщение получено: «{user_text}»\n\n"
                "Отправьте аудиозапись или голосовое сообщение для распознавания и анализа.",
            )
            return

        try:
            await update.message.chat.send_action("typing")

            ai_reply = ""
            if hasattr(self.ai_model, "chat") and callable(self.ai_model.chat):
                res = self.ai_model.chat(user_text)
                ai_reply = await res if asyncio.iscoroutine(res) else str(res)
            elif hasattr(self.ai_model, "generate") and callable(self.ai_model.generate):
                res = self.ai_model.generate(user_text)
                ai_reply = await res if asyncio.iscoroutine(res) else str(res)
            else:
                ai_reply = f"Ответ: {user_text}"

            await update.message.reply_text(ai_reply)

        except Exception as exc:
            logger.error(f"Error generating AI reply for Telegram message: {exc}", exc_info=True)
            await update.message.reply_text(f"⚠️ Ошибка обработки запроса: {exc}")

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
