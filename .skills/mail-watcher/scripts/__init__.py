# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Watcher Skill Package Init
# =============================================================================
# Description:
#   Инициализация пакета навыка mail-watcher.
#
# File: __init__.py
# Package: .agents.skills.mail-watcher.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Пакет навыка отслеживания входящей почты от заданного отправителя."""

from .mail_watcher import (
    MailWatcher,
    MailWatcherConfig,
    WatchedMessage,
    decode_mime_header,
    load_mail_watcher_config,
    send_windows_notification,
)

__all__ = [
    "MailWatcher",
    "MailWatcherConfig",
    "WatchedMessage",
    "decode_mime_header",
    "load_mail_watcher_config",
    "send_windows_notification",
]
