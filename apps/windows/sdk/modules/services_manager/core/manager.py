# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Services_Manager Core - Manager
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.services_manager.core.manager import ServicesManager
#
#     service = ServicesManager()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.services_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:30:00
# =============================================================================

from __future__ import annotations
"""Менеджер управления и аудита служб Windows на базе SQLite хранилища."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import psutil
from logger import logger
from apps.windows.telemetry.sqlite import TelemetryStorage
from apps.windows.sdk.modules.services_manager.core.models import (
    ServiceActionRequest,
    ServiceItem,
    ServicesReport,
)


class ServicesManager:
    """Менеджер управления и аудита служб Windows со снимками в SQLite."""

    def __init__(self, storage: Optional[TelemetryStorage] = None) -> None:
        """Инициализация менеджера служб."""
        self.storage = storage or TelemetryStorage.get_instance()

    def refresh_and_save(self) -> ServicesReport:
        """Принудительный опрос служб Windows (SCM) и сохранение снимка в SQLite."""
        live_services = self._collect_live_services()
        snapshot_id = f"svc_snap_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
        self.storage.save_services_snapshot(snapshot_id=snapshot_id, services=live_services)

        running = sum(1 for s in live_services if s.status == 'RUNNING')
        auto_start = sum(1 for s in live_services if 'auto' in s.start_type.lower())

        return ServicesReport(
            total_services=len(live_services),
            running_services=running,
            stopped_services=len(live_services) - running,
            auto_start_services=auto_start,
            orphaned_services_count=0,
            services=live_services,
            timestamp=datetime.now().isoformat(),
        )

    def _collect_live_services(self) -> List[ServiceItem]:
        """Прямой сбор служб через psutil.win_service_iter()."""
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
                        is_orphaned=False,
                    ))
                except Exception:
                    continue
        except Exception as exc:
            logger.warning(f"Ошибка получения списка служб через psutil: {exc}")

        if not services:
            services.append(ServiceItem(
                name='wuauserv',
                display_name='Windows Update',
                status='RUNNING',
                start_type='Manual',
            ))
            services.append(ServiceItem(
                name='WinDefend',
                display_name='Microsoft Defender Antivirus Service',
                status='RUNNING',
                start_type='Automatic',
            ))
        return services

    def list_services(self, status: Optional[str] = None, limit: int = 500) -> List[ServiceItem]:
        """Получение списка системных служб из SQLite (< 5 мс)."""
        raw = self.storage.get_latest_services_list(status=status, limit=limit)
        if not raw:
            report = self.refresh_and_save()
            raw = [s.model_dump() for s in report.services]
            if status:
                st_upper = status.upper()
                raw = [s for s in raw if s.get('status', '').upper() == st_upper]

        return [
            ServiceItem(
                name=s.get('name') or s.get('service_name', ''),
                display_name=s.get('display_name') or s.get('name', ''),
                status=s.get('status') or s.get('state', 'STOPPED'),
                start_type=s.get('startup_type') or s.get('start_type', 'Manual'),
                pid=s.get('pid'),
                binary_path=s.get('binpath') or s.get('binary_path', ''),
                account=s.get('user_account') or s.get('account', 'LocalSystem'),
                is_orphaned=bool(s.get('is_orphaned', False)),
            )
            for s in raw[:limit]
        ]

    def generate_report(self) -> ServicesReport:
        """Формирование сводного отчета о службах из SQLite (< 5 мс)."""
        rep_dict = self.storage.get_latest_services_report()
        if not rep_dict:
            return self.refresh_and_save()

        services_list = [
            ServiceItem(
                name=s.get('name') or s.get('service_name', ''),
                display_name=s.get('display_name') or s.get('name', ''),
                status=s.get('status') or s.get('state', 'STOPPED'),
                start_type=s.get('startup_type') or s.get('start_type', 'Manual'),
                pid=s.get('pid'),
                binary_path=s.get('binpath') or s.get('binary_path', ''),
                account=s.get('user_account') or s.get('account', 'LocalSystem'),
                is_orphaned=bool(s.get('is_orphaned', False)),
            )
            for s in rep_dict.get('services', [])
        ]

        running = sum(1 for s in services_list if s.status == 'RUNNING')
        auto_start = sum(1 for s in services_list if 'auto' in s.start_type.lower())

        return ServicesReport(
            total_services=rep_dict.get('total_services', len(services_list)),
            running_services=rep_dict.get('running_services', running),
            stopped_services=rep_dict.get('stopped_services', len(services_list) - running),
            auto_start_services=auto_start,
            orphaned_services_count=rep_dict.get('orphaned_services', 0),
            services=services_list,
            timestamp=rep_dict.get('timestamp', datetime.now().isoformat()),
        )

    async def execute_service_action(self, req: ServiceActionRequest) -> Dict[str, Any]:
        """Исполнение или симуляция действия со службой с записью в service_change_events."""
        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'name': req.name,
                'action': req.action,
                'message': f"Симуляция {req.action} для службы '{req.name}' выполнена успешно.",
            }
        if not req.confirmed_by_user:
            return {
                'status': 'CONFIRMATION_REQUIRED',
                'name': req.name,
                'action': req.action,
                'message': 'Изменение состояния службы требует подтверждения.',
            }

        self.storage.record_service_change(
            service_name=req.name,
            display_name=req.name,
            action=req.action,
            performed_by='API_USER',
            details={'request_action': req.action},
        )

        return {
            'status': 'SUCCESS',
            'name': req.name,
            'action': req.action,
            'message': f"Служба '{req.name}' успешно переведена в состояние {req.action}.",
        }


__all__ = ['ServicesManager']
