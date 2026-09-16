# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SMTP Mail Agent Package
# =============================================================================
# Description:
#   Пакет скриптов и ядра для работы агента с SMTP почтой.
#
# File: __init__.py
# Package: .agents.skills.smtp-mail-agent.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Пакет скриптов и ядра для работы агента с SMTP почтой."""

from .smtp_core import SmtpClient, SmtpConfig, load_smtp_config

__all__ = ["SmtpClient", "SmtpConfig", "load_smtp_config"]
