# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps User_Assistant Src -   Init  
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`__init__`).
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.user_assistant.src
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`__init__`)."""

from apps.user_assistant.src.mail_service import MailService
from apps.user_assistant.src.calendar_service import CalendarService
from apps.user_assistant.src.docs_service import DocsService
__all__ = ['MailService', 'CalendarService', 'DocsService']