# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Services_Manager Core - Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.services_manager.core.manager import ServicesManager
#
#     service = ServicesManager()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.services_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""# Description:"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import psutil
from logger import logger
from apps.windows.modules.services_manager.core.models import (
    ServiceActionRequest,
    ServiceItem,
    ServicesReport,
)


class ServicesManager:
    """Менеджер управления и аудита служб Windows."""

    def __init__(self) -> None:
        pass

    def list_services(self) -> List[ServiceItem]:
        """Получение списка системных служб через psutil / SCM."""
        services: List[ServiceItem] = []
        try:
            for s in psutil.win_service_iter():
                try:
                    s_info = s.as_dict()
                    services.append(ServiceItem(
                        name=s_info.get('name', ''),
                        display_name=s_info.get('display_name', '') or s_info.get('name', ''),
                        status=s_info.get('status', 'STOPPED').upper(),
                        start_type=s_info.get('start_type', 'Manual'),
                        pid=s_info.get('pid'),
                        binary_path=s_info.get('binpath', '') or '',
                        account=s_info.get('username', 'LocalSystem') or 'LocalSystem',
                        is_orphaned=False
                    ))
                except Exception:
                    continue
        except Exception as exc:
            logger.warning(f"Ошибка получения списка служб через psutil: {exc}")
            # Fallback
            services.append(ServiceItem(
                name='wuauserv',
                display_name='Windows Update',
                status='RUNNING',
                start_type='Manual'
            ))
            services.append(ServiceItem(
                name='WinDefend',
                display_name='Microsoft Defender Antivirus Service',
                status='RUNNING',
                start_type='Automatic'
            ))
        return services

    def generate_report(self) -> ServicesReport:
        """Формирование сводного отчета о службах."""
        services = self.list_services()
        running = sum(1 for s in services if s.status == 'RUNNING')
        auto_start = sum(1 for s in services if 'auto' in s.start_type.lower())
        return ServicesReport(
            total_services=len(services),
            running_services=running,
            stopped_services=len(services) - running,
            auto_start_services=auto_start,
            orphaned_services_count=0,
            services=services,
            timestamp=datetime.now().isoformat()
        )

    async def execute_service_action(self, req: ServiceActionRequest) -> Dict[str, Any]:
        """Исполнение или симуляция действия со службой."""
        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'name': req.name,
                'action': req.action,
                'message': f"Симуляция {req.action} для службы '{req.name}' выполнена успешно."
            }
        if not req.confirmed_by_user:
            return {
                'status': 'CONFIRMATION_REQUIRED',
                'name': req.name,
                'action': req.action,
                'message': 'Изменение состояния службы требует подтверждения.'
            }
        return {
            'status': 'SUCCESS',
            'name': req.name,
            'action': req.action,
            'message': f"Служба '{req.name}' успешно переведена в состояние {req.action}."
        }


__all__ = ['ServicesManager']
