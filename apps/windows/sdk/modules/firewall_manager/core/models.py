# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Firewall_Manager Core - Models
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.firewall_manager.core.models import FirewallProfile
#
#     service = FirewallProfile()
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.firewall_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FirewallProfile(BaseModel):
    """Статус профиля брандмауэра."""
    profile_type: str  # Domain, Private, Public
    enabled: bool = True
    default_inbound_action: str = 'Block'
    default_outbound_action: str = 'Allow'


class FirewallRule(BaseModel):
    """Правило брандмауэра Windows."""
    name: str
    direction: str = 'In'  # In, Out
    action: str = 'Allow'  # Allow, Block
    enabled: bool = True
    protocol: str = 'TCP'
    local_port: Optional[str] = None
    program: Optional[str] = None


class FirewallReport(BaseModel):
    """Сводный отчет состояния брандмауэра."""
    profiles: List[FirewallProfile] = Field(default_factory=list)
    total_rules: int = 0
    active_inbound_rules: int = 0
    active_outbound_rules: int = 0
    rules: List[FirewallRule] = Field(default_factory=list)
    timestamp: str = ''


class FirewallRuleActionRequest(BaseModel):
    """Запрос на добавление, удаление или изменение правила."""
    rule_name: str
    action: str  # add, delete, enable, disable
    direction: Optional[str] = 'In'
    rule_action: Optional[str] = 'Allow'
    port: Optional[str] = None
    dry_run: bool = True
    confirmed_by_user: bool = False


__all__ = [
    'FirewallProfile',
    'FirewallRule',
    'FirewallReport',
    'FirewallRuleActionRequest',
]
