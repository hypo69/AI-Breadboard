"""Пакет скриптов и ядра для работы агента с SMTP почтой."""
from .smtp_core import SmtpClient, SmtpConfig, load_smtp_config
__all__ = ['SmtpClient', 'SmtpConfig', 'load_smtp_config']