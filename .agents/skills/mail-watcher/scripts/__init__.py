"""Пакет навыка отслеживания входящей почты от заданного отправителя."""
from .mail_watcher import MailWatcher, MailWatcherConfig, WatchedMessage, decode_mime_header, load_mail_watcher_config, send_windows_notification
__all__ = ['MailWatcher', 'MailWatcherConfig', 'WatchedMessage', 'decode_mime_header', 'load_mail_watcher_config', 'send_windows_notification']