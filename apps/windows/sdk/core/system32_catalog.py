# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - System32 Catalog
# =============================================================================
# Description:
#   Автоматический каталог системных инструментов Windows (%SystemRoot%\System32),
#   их возможностей, эквивалентов Win32/PowerShell/WMI/COM, Telemetry Tiers и Control Planes.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.core.system32_catalog import System32Catalog
#
#     catalog = System32Catalog.get_instance()
#     tool = catalog.get_tool("diskpart.exe")
#     monitoring_tools = catalog.get_monitoring_tools()
#
# File: system32_catalog.py
# Project: ai-breadboard
# Package: apps.windows.sdk.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 15:15:00
# =============================================================================

from __future__ import annotations
"""Автоматический каталог системных инструментов Windows (%SystemRoot%\\System32)."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.sdk.core.system32_models import (
    AccessType,
    ControlPlaneType,
    System32CatalogSummary,
    System32QueryFilter,
    System32Tool,
    SystemToolCategory,
    TelemetryTier,
    ToolDangerLevel,
    ToolPrivilegeLevel,
)

_DATA_FILE = Path(__file__).resolve().parent / 'data' / 'windows_command_registry.json'


class System32Catalog:
    """Синглтон каталога системных инструментов Windows (%SystemRoot%\\System32)."""

    _instance: Optional[System32Catalog] = None

    def __init__(self) -> None:
        self._tools: Dict[str, System32Tool] = {}
        self._system32_dir: Path = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'System32'
        self._load_from_json()

    @classmethod
    def get_instance(cls) -> System32Catalog:
        """Получение синглтона каталога."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _reg(self, tool: System32Tool) -> None:
        """Регистрация инструмента в памяти."""
        key = tool.executable.lower().strip()
        self._tools[key] = tool

    def _load_from_json(self) -> None:
        """Загрузка полного каталога из JSON базы данных."""
        if not _DATA_FILE.is_file():
            logger.warning(f'[System32Catalog] Файл данных {_DATA_FILE} не найден.')
            return

        try:
            with open(_DATA_FILE, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            catalog_list = payload.get('catalog', [])
            for item in catalog_list:
                try:
                    tool = System32Tool(
                        executable=item['executable'],
                        category=SystemToolCategory(item['category']),
                        category_code=item.get('category_code', ''),
                        purpose=item['purpose'],
                        access_type=AccessType(item['access_type']),
                        required_privileges=ToolPrivilegeLevel(item['required_privileges']),
                        danger_level=ToolDangerLevel(item['danger_level']),
                        telemetry_tier=TelemetryTier(item.get('telemetry_tier', 'OBSERVE')),
                        primary_control_plane=ControlPlaneType(item.get('primary_control_plane', 'CLI')),
                        native_api_equivalent=item.get('native_api_equivalent'),
                        native_nt_api_equivalent=item.get('native_nt_api_equivalent'),
                        powershell_equivalent=item.get('powershell_equivalent'),
                        wmi_cim_equivalent=item.get('wmi_cim_equivalent'),
                        com_equivalent=item.get('com_equivalent'),
                        etw_provider_equivalent=item.get('etw_provider_equivalent'),
                        event_log_channel_equivalent=item.get('event_log_channel_equivalent'),
                        can_run_unattended=item.get('can_run_unattended', True),
                        can_monitor=item.get('can_monitor', False),
                        can_modify_system=item.get('can_modify_system', False),
                        is_gui=item.get('is_gui', False),
                        is_msc_console=item.get('is_msc_console', False),
                        is_cpl_applet=item.get('is_cpl_applet', False),
                        is_cmd_builtin=item.get('is_cmd_builtin', False),
                        etw_pipeline_enabled=item.get('etw_pipeline_enabled', False),
                        usn_journal_enabled=item.get('usn_journal_enabled', False),
                        command_templates=item.get('command_templates', []),
                        subcommands_info=item.get('subcommands_info', []),
                        subcommands_tree=item.get('subcommands_tree', {}),
                        rest_endpoint=item.get('rest_endpoint'),
                        tags=item.get('tags', []),
                    )
                    self._reg(tool)
                except Exception as ex:
                    logger.debug(f"[System32Catalog] Ошибка парсинга записи {item.get('executable')}: {ex}")
            logger.info(f'[System32Catalog] Успешно загружено {len(self._tools)} инструментов из JSON базы.')
        except Exception as exc:
            logger.error(f'[System32Catalog] Сбой чтения базы данных {_DATA_FILE}: {exc}')

    def get_tool(self, executable: str) -> Optional[System32Tool]:
        """Получение карточки инструмента по имени файла или оснастки."""
        if not executable:
            return None
        return self._tools.get(executable.lower().strip())

    def get_all_tools(self) -> List[System32Tool]:
        """Возвращает полный список зарегистрированных инструментов."""
        return list(self._tools.values())

    def get_tools_by_category(self, category: SystemToolCategory) -> List[System32Tool]:
        """Фильтрация инструментов по системной категории."""
        return [t for t in self._tools.values() if t.category == category]

    def get_tools_by_tier(self, tier: TelemetryTier) -> List[System32Tool]:
        """Фильтрация инструментов по градации AITelemetry Tier."""
        return [t for t in self._tools.values() if t.telemetry_tier == tier]

    def get_tools_by_control_plane(self, plane: ControlPlaneType) -> List[System32Tool]:
        """Фильтрация инструментов по слою Control Plane."""
        return [t for t in self._tools.values() if t.primary_control_plane == plane]

    def get_monitoring_tools(self) -> List[System32Tool]:
        """Возвращает список инструментов, пригодных для мониторинга и телеметрии."""
        return [t for t in self._tools.values() if t.can_monitor]

    def get_etw_tools(self) -> List[System32Tool]:
        """Возвращает список инструментов конвейера ETW."""
        return [t for t in self._tools.values() if t.etw_pipeline_enabled]

    def get_usn_tools(self) -> List[System32Tool]:
        """Возвращает инструменты для работы с NTFS USN журналом."""
        return [t for t in self._tools.values() if t.usn_journal_enabled]

    def filter_tools(self, q_filter: System32QueryFilter) -> List[System32Tool]:
        """Комплексная фильтрация и поиск инструментов."""
        res = list(self._tools.values())
        if q_filter.category is not None:
            res = [t for t in res if t.category == q_filter.category]
        if q_filter.access_type is not None:
            res = [t for t in res if t.access_type == q_filter.access_type]
        if q_filter.required_privileges is not None:
            res = [t for t in res if t.required_privileges == q_filter.required_privileges]
        if q_filter.danger_level is not None:
            res = [t for t in res if t.danger_level == q_filter.danger_level]
        if q_filter.telemetry_tier is not None:
            res = [t for t in res if t.telemetry_tier == q_filter.telemetry_tier]
        if q_filter.primary_control_plane is not None:
            res = [t for t in res if t.primary_control_plane == q_filter.primary_control_plane]
        if q_filter.can_run_unattended is not None:
            res = [t for t in res if t.can_run_unattended == q_filter.can_run_unattended]
        if q_filter.can_monitor is not None:
            res = [t for t in res if t.can_monitor == q_filter.can_monitor]
        if q_filter.can_modify_system is not None:
            res = [t for t in res if t.can_modify_system == q_filter.can_modify_system]
        if q_filter.etw_pipeline_enabled is not None:
            res = [t for t in res if t.etw_pipeline_enabled == q_filter.etw_pipeline_enabled]
        if q_filter.usn_journal_enabled is not None:
            res = [t for t in res if t.usn_journal_enabled == q_filter.usn_journal_enabled]
        if q_filter.is_cmd_builtin is not None:
            res = [t for t in res if t.is_cmd_builtin == q_filter.is_cmd_builtin]
        if q_filter.search_query:
            q = q_filter.search_query.lower().strip()
            res = [
                t for t in res
                if q in t.executable.lower()
                or q in t.purpose.lower()
                or q in t.category_code.lower()
                or any(q in k.lower() for k in t.subcommands_info.keys())
                or any(q in tag.lower() for tag in t.tags)
            ]
        return res

    def check_availability(self, executable: str) -> Dict[str, Any]:
        """Проверка физического наличия инструмента на локальном хосте."""
        clean = executable.strip()
        if clean.startswith('ms-settings:'):
            return {'available': True, 'path': clean, 'source': 'URI Protocol'}

        tool = self.get_tool(clean)
        if tool and tool.is_cmd_builtin:
            return {'available': True, 'path': 'cmd.exe built-in', 'source': 'CMD Internal'}

        sys32_path = self._system32_dir / clean
        if sys32_path.exists():
            return {'available': True, 'path': str(sys32_path), 'source': 'System32'}

        which_path = shutil.which(clean)
        if which_path:
            return {'available': True, 'path': which_path, 'source': 'PATH'}

        return {'available': False, 'path': None, 'source': 'Not Found'}

    def get_system_inventory(self) -> Dict[str, Any]:
        """Сверка каталога с файловой системой хоста."""
        installed = []
        missing = []
        for tool in self._tools.values():
            stat = self.check_availability(tool.executable)
            rec = {
                'executable': tool.executable,
                'category': tool.category.value,
                'category_code': tool.category_code,
                'tier': tool.telemetry_tier.value,
                'available': stat['available'],
                'path': stat['path'],
                'source': stat['source'],
            }
            if stat['available']:
                installed.append(rec)
            else:
                missing.append(rec)

        return {
            'system32_path': str(self._system32_dir),
            'total_registered': len(self._tools),
            'total_installed': len(installed),
            'total_missing': len(missing),
            'installed': installed,
            'missing': missing,
        }

    def get_hierarchy_tree(self) -> Dict[str, Any]:
        """Иерархическое дерево каталога по 66 системным категориям."""
        tree: Dict[str, List[Dict[str, Any]]] = {}
        for cat in SystemToolCategory:
            tools = self.get_tools_by_category(cat)
            if tools:
                tree[cat.value] = [t.to_dict() for t in tools]
        return {'tree': tree, 'total_categories': len(tree)}

    def get_tiers_tree(self) -> Dict[str, Any]:
        """Иерархическое дерево по AITelemetry Tiers (OBSERVE, DIAGNOSE, etc.)."""
        tree: Dict[str, List[Dict[str, Any]]] = {}
        for tier in TelemetryTier:
            tools = self.get_tools_by_tier(tier)
            tree[tier.value] = [t.to_dict() for t in tools]
        return {'tiers': tree, 'total_tiers': len(tree)}

    def get_control_planes_tree(self) -> Dict[str, Any]:
        """Дерево инструментов по слоям Windows Control Plane."""
        tree: Dict[str, List[Dict[str, Any]]] = {}
        for plane in ControlPlaneType:
            tools = self.get_tools_by_control_plane(plane)
            tree[plane.value] = [t.to_dict() for t in tools]
        return {'control_planes': tree, 'total_planes': len(tree)}

    def get_summary(self) -> System32CatalogSummary:
        """Сводная статистика каталога инструментов System32."""
        tools = list(self._tools.values())
        by_cat: Dict[str, int] = {}
        by_danger: Dict[str, int] = {}
        by_priv: Dict[str, int] = {}
        by_tier: Dict[str, int] = {}
        by_plane: Dict[str, int] = {}

        for t in tools:
            by_cat[t.category.value] = by_cat.get(t.category.value, 0) + 1
            by_danger[t.danger_level.value] = by_danger.get(t.danger_level.value, 0) + 1
            by_priv[t.required_privileges.value] = by_priv.get(t.required_privileges.value, 0) + 1
            by_tier[t.telemetry_tier.value] = by_tier.get(t.telemetry_tier.value, 0) + 1
            by_plane[t.primary_control_plane.value] = by_plane.get(t.primary_control_plane.value, 0) + 1

        return System32CatalogSummary(
            total_tools=len(tools),
            categories_count=len(by_cat),
            control_planes_count=len(by_plane),
            read_tools_count=len([t for t in tools if t.access_type == AccessType.READ]),
            write_tools_count=len([t for t in tools if t.access_type == AccessType.WRITE]),
            read_write_tools_count=len([t for t in tools if t.access_type == AccessType.READ_WRITE]),
            monitoring_tools_count=len([t for t in tools if t.can_monitor]),
            etw_tools_count=len([t for t in tools if t.etw_pipeline_enabled]),
            usn_journal_tools_count=len([t for t in tools if t.usn_journal_enabled]),
            gui_tools_count=len([t for t in tools if t.is_gui]),
            msc_consoles_count=len([t for t in tools if t.is_msc_console]),
            cpl_applets_count=len([t for t in tools if t.is_cpl_applet]),
            cmd_builtins_count=len([t for t in tools if t.is_cmd_builtin]),
            by_category=by_cat,
            by_danger_level=by_danger,
            by_privileges=by_priv,
            by_telemetry_tier=by_tier,
            by_control_plane=by_plane,
        )


__all__ = ['System32Catalog']
