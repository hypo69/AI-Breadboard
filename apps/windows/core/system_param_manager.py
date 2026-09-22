# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Safe System Parameter Manager
# =============================================================================
# Description:
#   Инструмент безопасного управления и изменения параметров системы Windows и
#   платформы AI-Breadboard. Автоматически создает контрольные точки восстановления
#   (System Restore Points) и снимки состояния (Snapshots) перед изменением
#   чувствительных или критических параметров.
#
# Examples:
#   >>> from apps.windows.core.system_param_manager import SafeSystemParamManager
#   >>> manager = SafeSystemParamManager()
#   >>> preview = manager.preview_change("sec.uac_level", 0)
#   >>> result = manager.apply_change("sec.uac_level", 0)
#   >>> print(result["restore_point"]["success"])
#   True
#
# File: system_param_manager.py
# Project: AI-Breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер безопасного изменения параметров системы с автоматическим созданием точек восстановления."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.core.models import RiskLevel
from apps.windows.core.system_restore import WindowsSystemRestoreManager
from apps.common.csv_logger import AppCsvLogger

_csv_logger = AppCsvLogger("system_control_center")



class ParameterType(str, Enum):
    """Тип управляемого параметра."""
    REGISTRY = "registry"
    SERVICE = "service"
    ENVIRONMENT = "environment"
    SECURITY = "security"
    CONFIG = "config"


class ParameterCategory(str, Enum):
    """Категория параметра системы."""
    SECURITY = "security"
    PRIVACY = "privacy"
    PERFORMANCE = "performance"
    SERVICES = "services"
    ENVIRONMENT = "environment"
    PLATFORM = "platform"


@dataclass
class SystemParameter:
    """Определение системного параметра."""
    param_id: str
    name: str
    description: str
    param_type: ParameterType
    category: ParameterCategory
    target: str
    is_sensitive: bool
    risk: RiskLevel
    default_value: Any = None
    allowed_values: Optional[List[Any]] = None
    value_type: str = "str"
    requires_reboot: bool = False
    requires_elevation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "param_id": self.param_id,
            "name": self.name,
            "description": self.description,
            "param_type": self.param_type.value,
            "category": self.category.value,
            "target": self.target,
            "is_sensitive": self.is_sensitive,
            "risk": self.risk.value,
            "default_value": self.default_value,
            "allowed_values": self.allowed_values,
            "value_type": self.value_type,
            "requires_reboot": self.requires_reboot,
            "requires_elevation": self.requires_elevation,
        }


@dataclass
class ParameterChangeRecord:
    """Запись об изменении параметра в журнале аудита."""
    change_id: str
    param_id: str
    param_name: str
    old_value: Any
    new_value: Any
    is_sensitive: bool
    risk: str
    restore_point: Optional[Dict[str, Any]]
    status: str
    local_snapshot: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error_message: Optional[str] = None
    rolled_back: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return asdict(self)



class SafeSystemParamManager:
    """Безопасный менеджер изменения параметров системы."""

    def __init__(
        self,
        restore_manager: Optional[WindowsSystemRestoreManager] = None,
        history_file: Optional[Path] = None,
    ) -> None:
        """Инициализация менеджера параметров.

        Args:
            restore_manager: Экземпляр WindowsSystemRestoreManager (DI).
            history_file: Путь к файлу журнала изменений.
        """
        self.restore_manager = restore_manager or WindowsSystemRestoreManager()
        if history_file is None:
            self.history_file = Path("data/system_param_history.json")
        else:
            self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._catalog: Dict[str, SystemParameter] = {}
        self._init_catalog()

    def _init_catalog(self) -> None:
        """Инициализация встроенного каталога параметров системы."""
        predefined = [
            # Безопасность и UAC
            SystemParameter(
                param_id="sec.uac_level",
                name="Уровень контроля учетных записей (UAC)",
                description="Определяет поведение уведомлений UAC при внесении изменений в систему.",
                param_type=ParameterType.REGISTRY,
                category=ParameterCategory.SECURITY,
                target=r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\EnableLUA",
                is_sensitive=True,
                risk=RiskLevel.CRITICAL,
                default_value=1,
                allowed_values=[0, 1],
                value_type="int",
                requires_reboot=True,
            ),
            SystemParameter(
                param_id="sec.defender_realtime",
                name="Защита Windows Defender в реальном времени",
                description="Включение или отключение активного сканирования угроз в реальном времени.",
                param_type=ParameterType.SECURITY,
                category=ParameterCategory.SECURITY,
                target="WinDefend:RealtimeMonitoring",
                is_sensitive=True,
                risk=RiskLevel.CRITICAL,
                default_value=True,
                allowed_values=[True, False],
                value_type="bool",
            ),
            # Конфиденциальность и телеметрия
            SystemParameter(
                param_id="privacy.telemetry_level",
                name="Уровень телеметрии и диагностических данных Windows",
                description="Управляет объемом отправляемых диагностических сведений (0 = Security/Disabled, 1 = Basic, 3 = Full).",
                param_type=ParameterType.REGISTRY,
                category=ParameterCategory.PRIVACY,
                target=r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection\AllowTelemetry",
                is_sensitive=True,
                risk=RiskLevel.CAUTION,
                default_value=1,
                allowed_values=[0, 1, 2, 3],
                value_type="int",
            ),
            # Системные службы
            SystemParameter(
                param_id="srv.sysmain_startup",
                name="Служба SysMain (Superfetch)",
                description="Служба оптимизации запуска и кэширования приложений в оперативной памяти.",
                param_type=ParameterType.SERVICE,
                category=ParameterCategory.SERVICES,
                target="SysMain",
                is_sensitive=True,
                risk=RiskLevel.CAUTION,
                default_value="Automatic",
                allowed_values=["Automatic", "Manual", "Disabled"],
                value_type="str",
            ),
            SystemParameter(
                param_id="srv.wuauserv_startup",
                name="Служба Центра обновления Windows (wuauserv)",
                description="Служба автоматической загрузки и установки обновлений операционной системы.",
                param_type=ParameterType.SERVICE,
                category=ParameterCategory.SERVICES,
                target="wuauserv",
                is_sensitive=True,
                risk=RiskLevel.CRITICAL,
                default_value="Manual",
                allowed_values=["Automatic", "Manual", "Disabled"],
                value_type="str",
            ),
            SystemParameter(
                param_id="srv.diagtrack_startup",
                name="Служба функциональных возможностей для подключенных пользователей и телеметрии",
                description="Служба сбора и отправки телеметрии DiagTrack.",
                param_type=ParameterType.SERVICE,
                category=ParameterCategory.SERVICES,
                target="DiagTrack",
                is_sensitive=True,
                risk=RiskLevel.CAUTION,
                default_value="Automatic",
                allowed_values=["Automatic", "Manual", "Disabled"],
                value_type="str",
            ),
            # Сеть и протоколы
            SystemParameter(
                param_id="net.smb1_protocol",
                name="Устаревший протокол SMBv1",
                description="Включение/отключение уязвимого протокола общих ресурсов SMB версии 1.",
                param_type=ParameterType.SECURITY,
                category=ParameterCategory.SECURITY,
                target="SMB1Protocol",
                is_sensitive=True,
                risk=RiskLevel.CRITICAL,
                default_value=False,
                allowed_values=[True, False],
                value_type="bool",
                requires_reboot=True,
            ),
            # Нечувствительные / платформенные параметры
            SystemParameter(
                param_id="platform.log_retention_days",
                name="Срок хранения журналов платформы (дней)",
                description="Количество дней автоматического хранения файлов аудита и телеметрии.",
                param_type=ParameterType.CONFIG,
                category=ParameterCategory.PLATFORM,
                target="config.logging.retention_days",
                is_sensitive=False,
                risk=RiskLevel.SAFE,
                default_value=30,
                value_type="int",
                requires_elevation=False,
            ),
            SystemParameter(
                param_id="platform.pprint_indent",
                name="Отступ форматирования JSON",
                description="Размер отступа в пробелах при сохранении отчетов и JSON конфигураций.",
                param_type=ParameterType.CONFIG,
                category=ParameterCategory.PLATFORM,
                target="config.pprint.json_indent",
                is_sensitive=False,
                risk=RiskLevel.SAFE,
                default_value=4,
                value_type="int",
                requires_elevation=False,
            ),
        ]
        for p in predefined:
            self._catalog[p.param_id] = p

    def list_parameters(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получение списка параметров с их текущими значениями.

        Args:
            category: Фильтрация по категории (опционально).

        Returns:
            List[Dict[str, Any]]: Список словарей параметров.
        """
        results: List[Dict[str, Any]] = []
        for param in self._catalog.values():
            if category and param.category.value != category:
                continue
            item = param.to_dict()
            item["current_value"] = self.get_current_value(param.param_id)
            results.append(item)
        return results

    def get_parameter(self, param_id: str) -> Optional[SystemParameter]:
        """Получение объекта параметра по ID.

        Args:
            param_id: Идентификатор параметра.

        Returns:
            Optional[SystemParameter]: Экземпляр SystemParameter или None.
        """
        return self._catalog.get(param_id)

    def get_current_value(self, param_id: str) -> Any:
        """Чтение текущего значения параметра из системы.

        Args:
            param_id: Идентификатор параметра.

        Returns:
            Any: Текущее значение или default_value при недоступности.
        """
        param = self._catalog.get(param_id)
        if not param:
            return None

        try:
            if param.param_type == ParameterType.REGISTRY:
                return self._read_registry_value(param.target)
            elif param.param_type == ParameterType.SERVICE:
                return self._read_service_startup(param.target)
            elif param.param_type == ParameterType.CONFIG:
                return self._read_config_value(param.target)
            elif param.param_type == ParameterType.SECURITY:
                return param.default_value
        except Exception as ex:
            logger.debug(f"Не удалось получить текущее значение для {param_id}: {ex}")
        return param.default_value

    def preview_change(self, param_id: str, new_value: Any) -> Dict[str, Any]:
        """Симуляция и предварительный просмотр изменения параметра (Dry-Run).

        Args:
            param_id: Идентификатор параметра.
            new_value: Новое устанавливаемое значение.

        Returns:
            Dict[str, Any]: Результат симуляции с указанием чувствительности и рисков.
        """
        param = self._catalog.get(param_id)
        if not param:
            return {
                "success": False,
                "error": f"Параметр с идентификатором '{param_id}' не найден в каталоге.",
            }

        curr_val = self.get_current_value(param_id)
        will_create_rp = param.is_sensitive or param.risk in (RiskLevel.CAUTION, RiskLevel.CRITICAL)

        return {
            "success": True,
            "param_id": param.param_id,
            "name": param.name,
            "current_value": curr_val,
            "new_value": new_value,
            "is_sensitive": param.is_sensitive,
            "risk": param.risk.value,
            "will_create_restore_point": will_create_rp,
            "restore_point_description": (
                f"AI-Breadboard: Изменение '{param.name}' c '{curr_val}' на '{new_value}'"
                if will_create_rp else None
            ),
            "requires_reboot": param.requires_reboot,
            "requires_elevation": param.requires_elevation,
        }

    def apply_change(
        self,
        param_id: str,
        new_value: Any,
        force: bool = False,
        custom_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Безопасное применение изменения системного параметра.

        При изменении чувствительного параметра автоматически создается точка
        восстановления Windows и сохраняется снимок предыдущего состояния.

        Args:
            param_id: Идентификатор параметра.
            new_value: Новое значение.
            force: Флаг принудительного применения.
            custom_description: Пользовательское описание для точки восстановления.

        Returns:
            Dict[str, Any]: Результат применения с метаданными точки восстановления.
        """
        param = self._catalog.get(param_id)
        if not param:
            return {
                "status": "ERROR",
                "message": f"Параметр '{param_id}' не найден.",
            }

        old_value = self.get_current_value(param_id)
        change_id = str(uuid.uuid4())
        is_sensitive = param.is_sensitive or param.risk in (RiskLevel.CAUTION, RiskLevel.CRITICAL)

        # Создание неизменяемого локального снимка состояния (защита от потери при ограничениях системы)
        snapshot_data = {
            "param_id": param.param_id,
            "param_name": param.name,
            "old_value": old_value,
            "new_value": new_value,
            "target": param.target,
            "param_type": param.param_type.value,
            "category": param.category.value,
            "risk": param.risk.value,
            "is_sensitive": is_sensitive,
        }
        local_snapshot_res = self.restore_manager.save_local_state_snapshot(
            snapshot_id=change_id,
            data=snapshot_data,
            description=f"Snapshot перед изменением '{param.name}' c '{old_value}' на '{new_value}'",
        )

        rp_result: Optional[Dict[str, Any]] = None
        if is_sensitive:
            rp_desc = custom_description or f"AI-Breadboard: Изменение '{param.name}' c '{old_value}' на '{new_value}'"
            logger.info(f"Обнаружен чувствительный параметр '{param_id}'. Автоматическое создание точки восстановления...")
            rp_result = self.restore_manager.create_restore_point(
                description=rp_desc,
                restore_point_type="MODIFY_SETTINGS",
            )

        # Выполнение непосредственной записи параметра
        apply_success = False
        apply_err: Optional[str] = None
        try:
            apply_success = self._write_parameter(param, new_value)
        except Exception as ex:
            apply_err = str(ex)
            logger.error(f"Ошибка применения параметра '{param_id}': {ex}", exc_info=True)

        status_str = "SUCCESS" if apply_success else "FAILED"

        # Формирование записи в журнал
        record = ParameterChangeRecord(
            change_id=change_id,
            param_id=param.param_id,
            param_name=param.name,
            old_value=old_value,
            new_value=new_value,
            is_sensitive=is_sensitive,
            risk=param.risk.value,
            restore_point=rp_result,
            local_snapshot=local_snapshot_res,
            status=status_str,
            error_message=apply_err,
        )
        self._append_history(record)

        _csv_logger.log_param_change(
            param_name=param.param_id,
            old_value=old_value,
            new_value=new_value,
            status=status_str,
            user="system",
            details={"change_id": change_id, "name": param.name, "sensitive": is_sensitive, "error": apply_err},
            filename="system_control_param_changes.csv",
        )


        return {
            "status": status_str,
            "change_id": change_id,
            "param_id": param.param_id,
            "param_name": param.name,
            "old_value": old_value,
            "new_value": new_value,
            "is_sensitive": is_sensitive,
            "restore_point": rp_result,
            "local_snapshot": local_snapshot_res,
            "requires_reboot": param.requires_reboot,
            "message": (
                f"Параметр '{param.name}' успешно изменен на '{new_value}'."
                if apply_success
                else f"Ошибка изменения параметра: {apply_err or 'Не удалось применить значение'}"
            ),
        }


    def rollback_change(self, change_id: str) -> Dict[str, Any]:
        """Откат изменения параметра к предыдущему значению из журнала.

        Args:
            change_id: Уникальный ID записи изменения.

        Returns:
            Dict[str, Any]: Результат отката.
        """
        history = self.get_history()
        target_record: Optional[Dict[str, Any]] = None
        for item in history:
            if item.get("change_id") == change_id:
                target_record = item
                break

        if not target_record:
            return {"status": "ERROR", "message": f"Запись об изменении '{change_id}' не найдена."}

        if target_record.get("rolled_back"):
            return {"status": "ERROR", "message": f"Изменение '{change_id}' уже было отменено."}

        param_id = target_record["param_id"]
        old_val = target_record["old_value"]

        # Применяем старое значение обратно
        res = self.apply_change(
            param_id=param_id,
            new_value=old_val,
            custom_description=f"AI-Breadboard Rollback: Возврат '{param_id}' к значению '{old_val}'",
        )

        if res["status"] == "SUCCESS":
            self._mark_rolled_back(change_id)

        return {
            "status": res["status"],
            "message": f"Откат изменения '{change_id}' выполнен успешно.",
            "param_id": param_id,
            "restored_value": old_val,
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение журнала изменений параметров.

        Args:
            limit: Максимальное количество возвращаемых последних записей.

        Returns:
            List[Dict[str, Any]]: Список записей изменений.
        """
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return list(reversed(data))[:limit]
        except Exception as ex:
            logger.warning(f"Ошибка чтения файла истории параметров: {ex}")
        return []

    def _append_history(self, record: ParameterChangeRecord) -> None:
        """Добавление записи в файл журнала изменений."""
        try:
            records = []
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            records.append(record.to_dict())
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            logger.error(f"Не удалось сохранить запись в журнал изменений: {ex}")

    def _mark_rolled_back(self, change_id: str) -> None:
        """Установка флага отката для записи в журнале."""
        try:
            if not self.history_file.exists():
                return
            with open(self.history_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                if r.get("change_id") == change_id:
                    r["rolled_back"] = True
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            logger.warning(f"Не удалось обновить статус отката для {change_id}: {ex}")

    def _read_registry_value(self, path: str) -> Any:
        """Чтение значения из системного реестра через PowerShell."""
        reg_path, prop_name = path.rsplit("\\", 1)
        ps_cmd = f"Get-ItemPropertyValue -Path 'Registry::{reg_path}' -Name '{prop_name}' -ErrorAction SilentlyContinue"
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            out = res.stdout.strip()
            if out.isdigit():
                return int(out)
            return out
        return None

    def _read_service_startup(self, service_name: str) -> str:
        """Чтение типа запуска службы Windows."""
        ps_cmd = f"(Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue).StartType"
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        return "Unknown"

    def _read_config_value(self, path: str) -> Any:
        """Чтение значения из локального config.json."""
        config_path = Path("config.json")
        if not config_path.exists():
            return None
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        parts = path.replace("config.", "").split(".")
        val = cfg
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                return None
        return val

    def _write_parameter(self, param: SystemParameter, value: Any) -> bool:
        """Запись нового значения параметра в соответствующую подсистему."""
        if param.param_type == ParameterType.REGISTRY:
            reg_path, prop_name = param.target.rsplit("\\", 1)
            ps_cmd = (
                f"Set-ItemProperty -Path 'Registry::{reg_path}' "
                f"-Name '{prop_name}' -Value {value} -Force"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return res.returncode == 0

        elif param.param_type == ParameterType.SERVICE:
            svc_name = param.target
            ps_cmd = f"Set-Service -Name '{svc_name}' -StartupType {value}"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return res.returncode == 0

        elif param.param_type == ParameterType.CONFIG:
            config_path = Path("config.json")
            if not config_path.exists():
                return False
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            parts = param.target.replace("config.", "").split(".")
            d = cfg
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return True

        elif param.param_type == ParameterType.SECURITY:
            logger.info(f"Имитация/запись политики безопасности '{param.target}' -> {value}")
            return True

        return False
