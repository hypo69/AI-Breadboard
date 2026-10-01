# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Firewall_Manager - Router
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.firewall_manager.router import init_router
#
#     res = init_router()
#
# File: router.py
# Project: ai-breadboard
# Package: apps.windows.modules.firewall_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from logger import logger
from apps.windows.modules.firewall_manager.core.manager import FirewallManager
from apps.windows.modules.firewall_manager.core.models import (
    FirewallProfile,
    FirewallReport,
    FirewallRule,
    FirewallRuleActionRequest,
)

router = APIRouter(prefix='/api/firewall-manager', tags=['Firewall Manager'])
_manager = FirewallManager()


@router.get('/summary', response_model=FirewallReport)
@router.get('/report', response_model=FirewallReport)
async def get_firewall_report() -> FirewallReport:
    """Сводный отчет о профилях и правилах брандмауэра."""
    return await asyncio.to_thread(_manager.generate_report)


@router.get('/profiles', response_model=List[FirewallProfile])
async def list_profiles() -> List[FirewallProfile]:
    """Статус профилей (Domain, Private, Public)."""
    return await asyncio.to_thread(_manager.get_profiles)


@router.get('/rules', response_model=List[FirewallRule])
async def list_rules(direction: Optional[str] = Query(None, description='In или Out')) -> List[FirewallRule]:
    """Список правил брандмауэра."""
    rules = await asyncio.to_thread(_manager.list_rules)
    if direction:
        d_lower = direction.lower()
        rules = [r for r in rules if r.direction.lower() == d_lower]
    return rules


@router.post('/action')
@router.post('/actions')
async def execute_rule_action(payload: FirewallRuleActionRequest) -> Dict[str, Any]:
    """Добавление, удаление или изменение правила брандмауэра."""
    return await _manager.execute_rule_action(payload)


def init_router() -> APIRouter:
    """Возвращает инициализированный FastAPI роутер."""
    return router


__all__ = ['router', 'init_router']
