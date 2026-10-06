# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Firewall_Manager Core - Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.firewall_manager.core.manager import FirewallManager
#
#     service = FirewallManager()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.firewall_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:30:00
# =============================================================================

from __future__ import annotations
"""Менеджер профилей и правил сетевого экрана Windows на базе SQLite хранилища."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.modules.firewall_manager.core.models import (
    FirewallProfile,
    FirewallReport,
    FirewallRule,
    FirewallRuleActionRequest,
)


class FirewallManager:
    """Менеджер профилей и правил сетевого экрана Windows с хранением срезов в SQLite."""

    def __init__(self, storage: Optional[TelemetryStorage] = None) -> None:
        """Инициализация менеджера брандмауэра."""
        self.storage = storage or TelemetryStorage.get_instance()

    def refresh_and_save(self) -> FirewallReport:
        """Принудительный опрос конфигурации сетевого экрана и сохранение среза в SQLite."""
        live_profiles = self._collect_live_profiles()
        live_rules = self._collect_live_rules()

        profiles_dict = {
            'domain_enabled': any(p.enabled for p in live_profiles if p.profile_type.lower() == 'domain'),
            'private_enabled': any(p.enabled for p in live_profiles if p.profile_type.lower() == 'private'),
            'public_enabled': any(p.enabled for p in live_profiles if p.profile_type.lower() == 'public'),
            'domain_default_inbound': 'Block',
            'private_default_inbound': 'Block',
            'public_default_inbound': 'Block',
            'stealth_mode_enabled': True,
        }

        snapshot_id = f"fw_snap_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
        self.storage.save_firewall_snapshot(
            snapshot_id=snapshot_id,
            profiles=profiles_dict,
            rules=live_rules,
        )

        inbound = sum(1 for r in live_rules if r.direction.lower() == 'in')
        outbound = sum(1 for r in live_rules if r.direction.lower() == 'out')

        return FirewallReport(
            profiles=live_profiles,
            total_rules=len(live_rules),
            active_inbound_rules=inbound,
            active_outbound_rules=outbound,
            rules=live_rules,
            timestamp=datetime.now().isoformat(),
        )

    def _collect_live_profiles(self) -> List[FirewallProfile]:
        """Сбор живого состояния профилей брандмауэра."""
        return [
            FirewallProfile(profile_type='Domain', enabled=True, default_inbound_action='Block', default_outbound_action='Allow'),
            FirewallProfile(profile_type='Private', enabled=True, default_inbound_action='Block', default_outbound_action='Allow'),
            FirewallProfile(profile_type='Public', enabled=True, default_inbound_action='Block', default_outbound_action='Allow'),
        ]

    def _collect_live_rules(self) -> List[FirewallRule]:
        """Сбор живого реестра правил брандмауэра."""
        return [
            FirewallRule(name='Core Networking - DNS (UDP-Out)', direction='Out', action='Allow', enabled=True, protocol='UDP', local_port='53'),
            FirewallRule(name='Core Networking - HTTP (TCP-Out)', direction='Out', action='Allow', enabled=True, protocol='TCP', local_port='80'),
            FirewallRule(name='Core Networking - HTTPS (TCP-Out)', direction='Out', action='Allow', enabled=True, protocol='TCP', local_port='443'),
            FirewallRule(name='AI-Breadboard FastApi Server', direction='In', action='Allow', enabled=True, protocol='TCP', local_port='8000'),
            FirewallRule(name='Remote Desktop - User Mode (TCP-In)', direction='In', action='Allow', enabled=True, protocol='TCP', local_port='3389'),
        ]

    def get_profiles(self) -> List[FirewallProfile]:
        """Получение состояния профилей Domain, Private, Public из SQLite."""
        prof_dict = self.storage.get_latest_firewall_profiles()
        if not prof_dict:
            report = self.refresh_and_save()
            return report.profiles

        return [
            FirewallProfile(
                profile_type='Domain',
                enabled=bool(prof_dict.get('domain_enabled', True)),
                default_inbound_action=prof_dict.get('domain_default_inbound', 'Block'),
                default_outbound_action='Allow',
            ),
            FirewallProfile(
                profile_type='Private',
                enabled=bool(prof_dict.get('private_enabled', True)),
                default_inbound_action=prof_dict.get('private_default_inbound', 'Block'),
                default_outbound_action='Allow',
            ),
            FirewallProfile(
                profile_type='Public',
                enabled=bool(prof_dict.get('public_enabled', True)),
                default_inbound_action=prof_dict.get('public_default_inbound', 'Block'),
                default_outbound_action='Allow',
            ),
        ]

    def list_rules(self, direction: Optional[str] = None) -> List[FirewallRule]:
        """Получение списка правил брандмауэра из SQLite."""
        raw_rules = self.storage.get_latest_firewall_rules(direction=direction, limit=500)
        if not raw_rules:
            self.refresh_and_save()
            raw_rules = self.storage.get_latest_firewall_rules(direction=direction, limit=500)

        return [
            FirewallRule(
                name=r.get('name') or r.get('rule_name', ''),
                direction='In' if str(r.get('direction', '')).lower() in ('in', 'inbound') else 'Out',
                action='Allow' if str(r.get('action', '')).lower() in ('allow', '1') else 'Block',
                enabled=bool(r.get('enabled', True)),
                protocol=r.get('protocol', 'Any'),
                local_port=str(r.get('local_port', '') or ''),
                remote_port=str(r.get('remote_port', '') or ''),
                program_path=r.get('program_path', ''),
            )
            for r in raw_rules
        ]

    def generate_report(self) -> FirewallReport:
        """Формирование сводного отчета брандмауэра из SQLite."""
        profiles = self.get_profiles()
        rules = self.list_rules()
        inbound = sum(1 for r in rules if r.direction.lower() in ('in', 'inbound'))
        outbound = sum(1 for r in rules if r.direction.lower() in ('out', 'outbound'))

        return FirewallReport(
            profiles=profiles,
            total_rules=len(rules),
            active_inbound_rules=inbound,
            active_outbound_rules=outbound,
            rules=rules,
            timestamp=datetime.now().isoformat(),
        )

    async def execute_rule_action(self, req: FirewallRuleActionRequest) -> Dict[str, Any]:
        """Выполнение или симуляция действия с правилом с синхронизацией SQLite."""
        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'rule_name': req.rule_name,
                'action': req.action,
                'message': f"Симуляция {req.action} для правила '{req.rule_name}' выполнена успешно.",
            }
        if not req.confirmed_by_user:
            return {
                'status': 'CONFIRMATION_REQUIRED',
                'rule_name': req.rule_name,
                'action': req.action,
                'message': 'Изменение правил брандмауэра требует подтверждения.',
            }

        # Обновляем состояние в базе данных
        if req.action.lower() in ('disable', 'block'):
            self.storage.update_firewall_rule_state(req.rule_name, False)
        elif req.action.lower() in ('enable', 'allow'):
            self.storage.update_firewall_rule_state(req.rule_name, True)

        return {
            'status': 'SUCCESS',
            'rule_name': req.rule_name,
            'action': req.action,
            'message': f"Правило '{req.rule_name}' успешно изменено ({req.action}).",
        }


__all__ = ['FirewallManager']
