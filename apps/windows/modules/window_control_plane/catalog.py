# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Control Plane Catalog Engine
# =============================================================================
# Description:
#   Диспетчер единого машиночитаемого каталога параметров Windows Settings Registry.
#   Объединяет все 295 параметров по 15 системным категориям, индексирует по ID,
#   номеру, бэкенду, уровню риска и предоставляет богатые фильтры поиска.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.window_control_plane.catalog import get_window_catalog
#
#     catalog = get_window_catalog()
#     setting = catalog.get_by_id("window.focus.foreground_lock_timeout")
#
# File: catalog.py
# Project: ai-breadboard
# Package: apps.windows.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:00:00
# =============================================================================

from __future__ import annotations
"""Единый каталог параметров Window Management Control Plane (295 параметров)."""

from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.modules.window_control_plane.catalog_data_1 import GET_CATALOG_PART_1
from apps.windows.modules.window_control_plane.catalog_data_2 import GET_CATALOG_PART_2
from apps.windows.modules.window_control_plane.catalog_data_3 import GET_CATALOG_PART_3
from apps.windows.modules.window_control_plane.models import (
    ControlPlaneSummaryResponse,
    DocStatus,
    RiskLevel,
    SettingCategory,
    SupportStatus,
    WindowSettingDefinition,
)


class WindowControlPlaneCatalog:
    """Реестр и поисковый движок для 295 параметров управления окнами и оболочкой Windows."""

    def __init__(self) -> None:
        """Инициализация каталога и построение поисковых индексов."""
        self._items_list: List[WindowSettingDefinition] = []
        self._by_id: Dict[str, WindowSettingDefinition] = {}
        self._by_index: Dict[int, WindowSettingDefinition] = {}
        self._by_category: Dict[SettingCategory, List[WindowSettingDefinition]] = {}
        self._load_and_index()

    def _load_and_index(self) -> None:
        """Загрузка всех частей каталога и индексация."""
        part1 = GET_CATALOG_PART_1()
        part2 = GET_CATALOG_PART_2()
        part3 = GET_CATALOG_PART_3()

        all_items = part1 + part2 + part3
        self._items_list = all_items

        for item in all_items:
            self._by_id[item.id] = item
            self._by_index[item.index] = item
            if item.category not in self._by_category:
                self._by_category[item.category] = []
            self._by_category[item.category].append(item)

        logger.info(
            f"[WindowControlPlaneCatalog] Загружено {len(self._items_list)} параметров "
            f"по {len(self._by_category)} категориям."
        )

    def get_all(self) -> List[WindowSettingDefinition]:
        """Возвращает полный список всех 295 параметров."""
        return list(self._items_list)

    def get_by_id(self, setting_id: str) -> Optional[WindowSettingDefinition]:
        """Поиск параметра по строковому идентификатору."""
        return self._by_id.get(setting_id)

    def get_by_index(self, index: int) -> Optional[WindowSettingDefinition]:
        """Поиск параметра по порядковому номеру (1..295)."""
        return self._by_index.get(index)

    def get_by_category(self, category: SettingCategory) -> List[WindowSettingDefinition]:
        """Возвращает список параметров указанной категории."""
        return list(self._by_category.get(category, []))

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[SettingCategory] = None,
        support_status: Optional[SupportStatus] = None,
        doc_status: Optional[DocStatus] = None,
        risk: Optional[RiskLevel] = None,
        requires_elevation: Optional[bool] = None,
        requires_restart: Optional[bool] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> List[WindowSettingDefinition]:
        """Фильтрация и полнотекстовый поиск по реестру параметров.

        Args:
            query: Текст поиска в названии или описании (RU/EN).
            category: Фильтр по одной из 15 категорий.
            support_status: Фильтр по статусу надежности (Safe, Admin, Compat, Unsupported).
            doc_status: Фильтр по типу документации (documented_api, policy, registry_compat).
            risk: Фильтр по уровню риска.
            requires_elevation: Фильтр по требованию прав администратора.
            requires_restart: Фильтр по требованию перезапуска Explorer/Windows.
            limit: Максимальное количество записей.
            offset: Смещение выборки.

        Returns:
            Список найденных определений параметров.
        """
        results = self._items_list

        if category is not None:
            results = [x for x in results if x.category == category]

        if support_status is not None:
            results = [x for x in results if x.support_status == support_status]

        if doc_status is not None:
            results = [x for x in results if x.doc_status == doc_status]

        if risk is not None:
            results = [x for x in results if x.risk == risk]

        if requires_elevation is not None:
            results = [x for x in results if x.requires_elevation == requires_elevation]

        if requires_restart is not None:
            results = [x for x in results if x.requires_restart == requires_restart]

        if query:
            q_clean = query.lower().strip()
            results = [
                x for x in results
                if q_clean in x.id.lower()
                or q_clean in x.name.lower()
                or q_clean in x.name_ru.lower()
                or q_clean in x.description.lower()
                or q_clean in x.description_ru.lower()
                or (x.read_spec and x.read_spec.api_getter and q_clean in x.read_spec.api_getter.lower())
                or (x.read_spec and x.read_spec.registry_value and q_clean in x.read_spec.registry_value.lower())
            ]

        return results[offset:offset + limit]

    def get_summary(self) -> ControlPlaneSummaryResponse:
        """Формирует сводный аналитический отчет по каталогу."""
        import platform

        by_cat: Dict[str, int] = {}
        for cat in SettingCategory:
            by_cat[cat.value] = len(self._by_category.get(cat, []))

        by_sup: Dict[str, int] = {}
        for item in self._items_list:
            st = item.support_status.value
            by_sup[st] = by_sup.get(st, 0) + 1

        by_doc: Dict[str, int] = {}
        for item in self._items_list:
            dt = item.doc_status.value
            by_doc[dt] = by_doc.get(dt, 0) + 1

        by_rk: Dict[str, int] = {}
        for item in self._items_list:
            rk = item.risk.value
            by_rk[rk] = by_rk.get(rk, 0) + 1

        by_be: Dict[str, int] = {}
        for item in self._items_list:
            if item.read_spec:
                be = item.read_spec.backend.value
                by_be[be] = by_be.get(be, 0) + 1

        return ControlPlaneSummaryResponse(
            total_settings=len(self._items_list),
            categories_count=len(SettingCategory),
            by_category=by_cat,
            by_support_status=by_sup,
            by_doc_status=by_doc,
            by_risk=by_rk,
            by_backend=by_be,
            system_platform=platform.system(),
            windows_build=platform.version() if platform.system() == "Windows" else "Non-Windows Host",
        )

    def get_categories_overview(self) -> List[Dict[str, Any]]:
        """Возвращает расширенную структуру всех 15 категорий с перечнем параметров."""
        overview: List[Dict[str, Any]] = []
        for cat in SettingCategory:
            items = self._by_category.get(cat, [])
            overview.append({
                "category_id": cat.value,
                "name": cat.name,
                "total_items": len(items),
                "safe_count": sum(1 for x in items if x.support_status == SupportStatus.SAFE),
                "admin_count": sum(1 for x in items if x.requires_elevation),
                "items": [
                    {
                        "id": x.id,
                        "index": x.index,
                        "name": x.name,
                        "name_ru": x.name_ru,
                        "risk": x.risk.value,
                        "support_status": x.support_status.value,
                        "doc_status": x.doc_status.value,
                        "backend": x.read_spec.backend.value if x.read_spec else "None",
                    }
                    for x in items
                ],
            })
        return overview


# Синглтон каталога
_catalog_instance: Optional[WindowControlPlaneCatalog] = None


def get_window_catalog() -> WindowControlPlaneCatalog:
    """Возвращает глобальный экземпляр каталога параметров."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = WindowControlPlaneCatalog()
    return _catalog_instance
