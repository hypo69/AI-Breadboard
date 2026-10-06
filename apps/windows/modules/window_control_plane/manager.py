# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Management Control Plane Manager
# =============================================================================
# Description:
#   Центральный координатор Windows Window Management Control Plane.
#   Интегрирует единый реестр из 295 настроек, Backend Resolver, фиксацию
#   всех изменений в SQLite базе данных telemetry.db с полной поддержкой
#   аудита, истории и безопасного отката (Rollback), а также создание
#   точек восстановления Windows через WindowsSystemRestoreManager.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.window_control_plane.manager import get_window_control_plane
#
#     plane = get_window_control_plane()
#     summary = plane.get_summary()
#     res = plane.apply_setting("focus_activation_001", req)
#     plane.rollback_change(res.change_id)
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:25:00
# =============================================================================

from __future__ import annotations
"""Главный менеджер Windows Window Management Control Plane."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.core.system_restore import WindowsSystemRestoreManager
from apps.windows.modules.window_control_plane.catalog import (
    WindowControlPlaneCatalog,
    get_window_catalog,
)
from apps.windows.modules.window_control_plane.history import (
    WindowManagementHistoryManager,
    get_window_history_manager,
)
from apps.windows.modules.window_control_plane.models import (
    BatchApplyRequest,
    BatchApplyResponse,
    ControlPlaneSummaryResponse,
    DocStatus,
    RiskLevel,
    SettingApplyRequest,
    SettingApplyResponse,
    SettingCategory,
    SettingPreviewResponse,
    SettingRollbackResponse,
    SettingValueResponse,
    SupportStatus,
    WindowSettingDefinition,
)
from apps.windows.modules.window_control_plane.resolver import WindowBackendResolver


class WindowManagementControlPlane:
    """Интерактивный пульт управления окнами и оболочкой Windows (295 параметров)."""

    def __init__(
        self,
        catalog: Optional[WindowControlPlaneCatalog] = None,
        resolver: Optional[WindowBackendResolver] = None,
        restore_manager: Optional[WindowsSystemRestoreManager] = None,
        history_manager: Optional[WindowManagementHistoryManager] = None,
        history_file: Optional[Path] = None,
    ) -> None:
        """Инициализация Control Plane.

        Args:
            catalog: Экземпляр каталога параметров.
            resolver: Экземпляр низкоуровневого резолвера.
            restore_manager: Менеджер точек восстановления системы.
            history_manager: Менеджер истории изменений в telemetry.db.
            history_file: Путь к резервному JSON-файлу аудита изменений.
        """
        self.catalog = catalog or get_window_catalog()
        self.resolver = resolver or WindowBackendResolver()
        self.restore_manager = restore_manager or WindowsSystemRestoreManager()
        self.history_manager = history_manager or get_window_history_manager()
        self.history_file = history_file or Path("data/window_management_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Каталог и аналитика
    # =========================================================================
    def get_summary(self) -> ControlPlaneSummaryResponse:
        """Возвращает сводную статистику параметров Control Plane."""
        return self.catalog.get_summary()

    def get_categories_overview(self) -> List[Dict[str, Any]]:
        """Возвращает перечень 15 категорий с детализацией."""
        return self.catalog.get_categories_overview()

    def search_settings(
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
        """Поиск и фильтрация параметров по всем полям."""
        return self.catalog.search(
            query=query,
            category=category,
            support_status=support_status,
            doc_status=doc_status,
            risk=risk,
            requires_elevation=requires_elevation,
            requires_restart=requires_restart,
            limit=limit,
            offset=offset,
        )

    def get_setting_by_id(self, setting_id: str) -> Optional[WindowSettingDefinition]:
        """Получение метаданных параметра по ID."""
        return self.catalog.get_by_id(setting_id)

    # =========================================================================
    # Чтение живых значений
    # =========================================================================
    def get_live_value(self, setting_id: str) -> Optional[SettingValueResponse]:
        """Получение текущего живого значения параметра."""
        setting = self.catalog.get_by_id(setting_id)
        if not setting:
            return None
        return self.resolver.read_value(setting)

    def get_category_live_values(self, category: SettingCategory) -> List[SettingValueResponse]:
        """Чтение живых значений для всех параметров заданной категории."""
        settings = self.catalog.get_by_category(category)
        return [self.resolver.read_value(s) for s in settings]

    # =========================================================================
    # Симуляция и применение изменений
    # =========================================================================
    def preview_setting(self, setting_id: str, new_value: Any) -> Optional[SettingPreviewResponse]:
        """Предварительный просмотр и симуляция изменения (Dry-Run)."""
        setting = self.catalog.get_by_id(setting_id)
        if not setting:
            return None
        return self.resolver.preview_change(setting, new_value)

    def apply_setting(
        self,
        setting_id: str,
        request: SettingApplyRequest,
        action_type: str = "APPLY",
    ) -> SettingApplyResponse:
        """Безопасное применение изменения системного параметра.

        При изменении чувствительных или системных настроек автоматически создает
        точку восстановления Windows и фиксирует транзакцию в telemetry.db.
        """
        setting = self.catalog.get_by_id(setting_id)
        applied_at = datetime.now().isoformat()
        change_id = str(uuid.uuid4())

        if not setting:
            return SettingApplyResponse(
                change_id=change_id,
                setting_id=setting_id,
                name_ru=setting_id,
                old_value=None,
                new_value=request.value,
                status="ERROR",
                success=False,
                requires_restart=False,
                message=f"Параметр '{setting_id}' не найден в каталоге.",
                applied_at=applied_at,
                error="SettingNotFound",
            )

        # 1. Читаем текущее значение перед изменением
        old_val_resp = self.resolver.read_value(setting)
        old_val = old_val_resp.value

        # 2. Оценка необходимости точки восстановления
        create_rp = request.create_restore_point
        if create_rp is None:
            create_rp = (
                setting.risk in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)
                or setting.requires_elevation
                or setting.requires_restart
            )

        rp_result: Optional[Dict[str, Any]] = None
        rp_id: Optional[str] = None
        if create_rp:
            desc = (
                request.custom_comment
                or f"AI-Breadboard: Window Control Plane '{setting.name_ru}' ({old_val} -> {request.value})"
            )
            logger.info(f"Создание точки восстановления перед изменением '{setting.id}'...")
            try:
                rp_result = self.restore_manager.create_restore_point(
                    description=desc,
                    restore_point_type="MODIFY_SETTINGS",
                )
                if rp_result:
                    rp_id = str(rp_result.get("SequenceNumber") or rp_result.get("restore_point_id") or "")
            except Exception as rp_err:
                logger.warning(f"Не удалось создать точку восстановления: {rp_err}")

        # 3. Сохранение локального снимка
        local_snapshot = {
            "change_id": change_id,
            "setting_id": setting.id,
            "name_ru": setting.name_ru,
            "old_value": old_val,
            "new_value": request.value,
            "timestamp": applied_at,
        }
        try:
            self.restore_manager.save_local_state_snapshot(
                snapshot_id=change_id,
                data=local_snapshot,
                description=f"Snapshot перед изменением '{setting.name_ru}'",
            )
        except Exception:
            pass

        # 4. Применение через резолвер
        ok, err = self.resolver.apply_value(setting, request.value)

        # 5. Обязательная фиксация в telemetry.db
        backend_spec = setting.write_spec or setting.read_spec
        backend_type_str = backend_spec.backend.value if (backend_spec and hasattr(backend_spec.backend, "value")) else "spi"
        scope_str = setting.scope.value if hasattr(setting.scope, "value") else str(setting.scope)
        risk_str = setting.risk.value if hasattr(setting.risk, "value") else str(setting.risk)
        cat_str = setting.category.value if hasattr(setting.category, "value") else str(setting.category)

        self.history_manager.record_change(
            change_id=change_id,
            setting_id=setting.id,
            setting_name=setting.name_ru,
            category=cat_str,
            backend_type=backend_type_str,
            scope=scope_str,
            risk_level=risk_str,
            old_value=old_val,
            new_value=request.value,
            action_type=action_type,
            operator="User",
            reason=request.custom_comment or "Window Control Plane Apply",
            restore_point_id=rp_id,
            status="SUCCESS" if ok else "FAILED",
            requires_restart=setting.requires_restart,
            details={"unit": setting.unit, "name_en": setting.name},
            error=err,
        )

        # Резервная запись в JSON
        record = {
            "change_id": change_id,
            "setting_id": setting.id,
            "name": setting.name,
            "name_ru": setting.name_ru,
            "category": cat_str,
            "old_value": old_val,
            "new_value": request.value,
            "success": ok,
            "status": "SUCCESS" if ok else "FAILED",
            "applied_at": applied_at,
            "restore_point": rp_result,
            "requires_restart": setting.requires_restart,
            "rolled_back": False,
            "error": err,
        }
        self._append_history(record)

        msg = (
            f"Параметр '{setting.name_ru}' успешно изменен на '{request.value}'."
            if ok
            else f"Не удалось применить параметр '{setting.name_ru}': {err}"
        )

        return SettingApplyResponse(
            change_id=change_id,
            setting_id=setting.id,
            name_ru=setting.name_ru,
            old_value=old_val,
            new_value=request.value,
            status="SUCCESS" if ok else "FAILED",
            success=ok,
            requires_restart=setting.requires_restart,
            restore_point_id=rp_id,
            message=msg,
            applied_at=applied_at,
            error=err,
        )

    def apply_batch(self, request: BatchApplyRequest) -> BatchApplyResponse:
        """Пакетное применение группы параметров с фиксацией в telemetry.db."""
        batch_id = str(uuid.uuid4())
        results: List[SettingApplyResponse] = []
        succ = 0
        fail = 0

        # Единая точка восстановления на весь пакет
        rp_created = False
        if request.create_restore_point:
            try:
                self.restore_manager.create_restore_point(
                    description=request.comment or f"AI-Breadboard: Batch Apply ({len(request.settings)} settings)",
                    restore_point_type="MODIFY_SETTINGS",
                )
                rp_created = True
            except Exception:
                pass

        for item in request.settings:
            single_req = SettingApplyRequest(
                value=item.value,
                force=True,
                create_restore_point=False,  # уже создана
                custom_comment=request.comment,
            )
            res = self.apply_setting(item.setting_id, single_req, action_type="BATCH_APPLY")
            if res.success:
                succ += 1
            else:
                fail += 1
            results.append(res)

        return BatchApplyResponse(
            batch_id=batch_id,
            total_requested=len(request.settings),
            successful_count=succ,
            failed_count=fail,
            results=results,
            restore_point_created=rp_created,
        )

    # =========================================================================
    # Откат и аудит в telemetry.db
    # =========================================================================
    def rollback_change(self, change_id: str, operator: str = "User") -> SettingRollbackResponse:
        """Откат выполненного изменения назад к старому значению с фиксацией в telemetry.db."""
        # 1. Поиск транзакции в telemetry.db
        target = self.history_manager.get_by_change_id(change_id)

        # Fallback к JSON если запись не найдена в sqlite
        if not target:
            json_history = self._load_json_history()
            for rec in json_history:
                if rec.get("change_id") == change_id:
                    target = rec
                    break

        if not target:
            return SettingRollbackResponse(
                change_id=change_id,
                setting_id="",
                rolled_back=False,
                restored_value=None,
                message=f"Запись об изменении '{change_id}' не найдена в telemetry.db.",
            )

        if target.get("is_rolled_back") or target.get("rolled_back"):
            return SettingRollbackResponse(
                change_id=change_id,
                setting_id=target.get("setting_id", ""),
                rolled_back=False,
                restored_value=target.get("old_value"),
                message="Изменение уже было откатано ранее.",
            )

        setting_id = target.get("setting_id", "")
        old_val = target.get("old_value")
        setting = self.catalog.get_by_id(setting_id)

        if not setting:
            return SettingRollbackResponse(
                change_id=change_id,
                setting_id=setting_id,
                rolled_back=False,
                restored_value=old_val,
                message=f"Параметр '{setting_id}' более не существует в каталоге.",
            )

        # 2. Восстановление старого значения
        ok, err = self.resolver.apply_value(setting, old_val)
        if ok:
            # 3. Пометка в telemetry.db
            self.history_manager.mark_as_rolled_back(change_id, rolled_back_by=operator)

            # 4. Запись транзакции отката в журнал telemetry.db
            rollback_tx_id = str(uuid.uuid4())
            backend_spec = setting.write_spec or setting.read_spec
            backend_type_str = backend_spec.backend.value if (backend_spec and hasattr(backend_spec.backend, "value")) else "spi"
            scope_str = setting.scope.value if hasattr(setting.scope, "value") else str(setting.scope)
            risk_str = setting.risk.value if hasattr(setting.risk, "value") else str(setting.risk)
            cat_str = setting.category.value if hasattr(setting.category, "value") else str(setting.category)

            self.history_manager.record_change(
                change_id=rollback_tx_id,
                setting_id=setting.id,
                setting_name=setting.name_ru,
                category=cat_str,
                backend_type=backend_type_str,
                scope=scope_str,
                risk_level=risk_str,
                old_value=target.get("new_value"),
                new_value=old_val,
                action_type="ROLLBACK",
                operator=operator,
                reason=f"Rollback of change '{change_id}'",
                status="SUCCESS",
                requires_restart=setting.requires_restart,
                rolled_back_change_id=change_id,
            )

            # Синхронизация с JSON
            target["rolled_back"] = True
            target["rolled_back_at"] = datetime.now().isoformat()
            self._save_json_history(self._load_json_history())

            return SettingRollbackResponse(
                change_id=change_id,
                setting_id=setting.id,
                rolled_back=True,
                restored_value=old_val,
                message=f"Параметр '{setting.name}' успешно возвращен к значению '{old_val}'.",
            )

        return SettingRollbackResponse(
            change_id=change_id,
            setting_id=setting.id,
            rolled_back=False,
            restored_value=old_val,
            message=f"Ошибка отката: {err}",
        )

    def rollback_last(self, operator: str = "User") -> SettingRollbackResponse:
        """Откат последнего выполненного успешного изменения из telemetry.db."""
        last_action = self.history_manager.get_last_action()
        if not last_action:
            return SettingRollbackResponse(
                change_id="",
                setting_id="",
                rolled_back=False,
                restored_value=None,
                message="Нет доступных действий для отката в telemetry.db.",
            )
        return self.rollback_change(last_action["change_id"], operator=operator)

    def get_history(
        self,
        limit: int = 100,
        offset: int = 0,
        setting_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Получение журнала аудита изменений из telemetry.db с fallback к JSON."""
        sqlite_history = self.history_manager.get_history(
            limit=limit,
            offset=offset,
            setting_id=setting_id,
            category=category,
        )
        if sqlite_history:
            return sqlite_history

        # Fallback к JSON если база пуста
        json_data = self._load_json_history()
        return json_data[-limit:] if isinstance(json_data, list) else []

    def _load_json_history(self) -> List[Dict[str, Any]]:
        """Загрузка истории из локального JSON файла."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _append_history(self, record: Dict[str, Any]) -> None:
        """Добавление записи в файл истории аудита JSON."""
        history = self._load_json_history()
        history.append(record)
        self._save_json_history(history)

    def _save_json_history(self, history: List[Dict[str, Any]]) -> None:
        """Сохранение журнала аудита на диск."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            logger.error(f"Ошибка сохранения истории: {ex}")


# Синглтон Control Plane
_plane_instance: Optional[WindowManagementControlPlane] = None


def get_window_control_plane() -> WindowManagementControlPlane:
    """Возвращает глобальный синглтон WindowManagementControlPlane."""
    global _plane_instance
    if _plane_instance is None:
        _plane_instance = WindowManagementControlPlane()
    return _plane_instance
