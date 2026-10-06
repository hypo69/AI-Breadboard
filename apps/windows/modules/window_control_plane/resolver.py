# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Window Control Plane Backend Resolver
# =============================================================================
# Description:
#   Исполняющий движок Backend Resolver для чтения и применения параметров Windows.
#   Взаимодействует с SystemParametersInfoW, DWM API, Win32 User32, Winreg и GPO.
#   Обеспечивает безопасный Dry-Run (preview), валидацию типов и обработку ошибок.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.window_control_plane.resolver import WindowBackendResolver
#     from apps.windows.modules.window_control_plane.catalog import get_window_catalog
#
#     resolver = WindowBackendResolver()
#     catalog = get_window_catalog()
#     setting = catalog.get_by_id("window.focus.foreground_lock_timeout")
#     res = resolver.read_value(setting)
#
# File: resolver.py
# Project: ai-breadboard
# Package: apps.windows.modules.window_control_plane
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:00:00
# =============================================================================

from __future__ import annotations
"""Исполняющий движок Backend Resolver для взаимодействия с Win32 API, DWM и реестром."""

import ctypes
import os
import platform
import struct
import sys
from typing import Any, Dict, Optional, Tuple
from logger import logger
from apps.windows.modules.window_control_plane import constants as win_const
from apps.windows.modules.window_control_plane.models import (
    BackendType,
    RiskLevel,
    SettingPreviewResponse,
    SettingValueResponse,
    SettingValueType,
    WindowSettingDefinition,
)

if sys.platform == "win32":
    import winreg
else:
    winreg = None  # type: ignore


class ANIMATIONINFO(ctypes.Structure):
    """Win32 структура параметров анимации."""
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("iMinAnimate", ctypes.c_int),
    ]


class WindowBackendResolver:
    """Унифицированный резолвер низкоуровневых параметров Windows."""

    def __init__(self) -> None:
        """Инициализация Win32 DLL библиотек."""
        self._is_windows = sys.platform == "win32"
        self._user32 = None
        self._dwmapi = None
        self._gdi32 = None

        if self._is_windows:
            try:
                self._user32 = ctypes.windll.user32
            except Exception as e:
                logger.debug(f"[WindowBackendResolver] Не удалось загрузить user32.dll: {e}")
            try:
                self._dwmapi = ctypes.windll.dwmapi
            except Exception as e:
                logger.debug(f"[WindowBackendResolver] Не удалось загрузить dwmapi.dll: {e}")
            try:
                self._gdi32 = ctypes.windll.gdi32
            except Exception as e:
                logger.debug(f"[WindowBackendResolver] Не удалось загрузить gdi32.dll: {e}")

    # =========================================================================
    # Чтение параметров
    # =========================================================================
    def read_value(self, setting: WindowSettingDefinition) -> SettingValueResponse:
        """Читает текущее живое значение параметра из системы."""
        if not setting.read_spec:
            return SettingValueResponse(
                setting_id=setting.id,
                name=setting.name,
                name_ru=setting.name_ru,
                category=setting.category.value,
                value=setting.default_value,
                value_type=setting.value_type.value,
                unit=setting.unit,
                is_live=False,
                backend_used="None",
            )

        spec = setting.read_spec
        backend = spec.backend

        if not self._is_windows:
            # Эмуляция в не-Windows окружении
            return SettingValueResponse(
                setting_id=setting.id,
                name=setting.name,
                name_ru=setting.name_ru,
                category=setting.category.value,
                value=setting.default_value,
                value_type=setting.value_type.value,
                unit=setting.unit,
                is_live=False,
                backend_used=f"Mock:{backend.value}",
            )

        try:
            # 1. SystemParametersInfoW
            if backend == BackendType.SYSTEM_PARAMETERS_INFO and spec.api_getter:
                val, err = self._read_spi(spec.api_getter, setting.value_type)
                if err is None and val is not None:
                    return SettingValueResponse(
                        setting_id=setting.id,
                        name=setting.name,
                        name_ru=setting.name_ru,
                        category=setting.category.value,
                        value=val,
                        raw_value=val,
                        value_type=setting.value_type.value,
                        unit=setting.unit,
                        is_live=True,
                        backend_used=backend.value,
                    )
                # Fallback to Registry if specified in spec
                if spec.registry_path and spec.registry_value is not None:
                    reg_val, reg_err = self._read_registry(spec.registry_hive or "HKCU", spec.registry_path, spec.registry_value)
                    if reg_err is None and reg_val is not None:
                        return SettingValueResponse(
                            setting_id=setting.id,
                            name=setting.name,
                            name_ru=setting.name_ru,
                            category=setting.category.value,
                            value=self._cast_type(reg_val, setting.value_type),
                            raw_value=reg_val,
                            value_type=setting.value_type.value,
                            unit=setting.unit,
                            is_live=True,
                            backend_used=f"RegistryFallback:{spec.registry_hive}\\{spec.registry_path}",
                        )

            # 2. Registry / GPO Policy / Policy CSP
            elif backend in (BackendType.REGISTRY, BackendType.POLICY_GPO, BackendType.POLICY_CSP) and spec.registry_path:
                hive = spec.registry_hive or ("HKLM" if backend in (BackendType.POLICY_GPO, BackendType.POLICY_CSP) else "HKCU")
                val_name = spec.registry_value if spec.registry_value is not None else (spec.gpo_name or "")
                reg_val, reg_err = self._read_registry(hive, spec.registry_path, val_name)
                if reg_err is None and reg_val is not None:
                    parsed_val = self._cast_type(reg_val, setting.value_type)
                    return SettingValueResponse(
                        setting_id=setting.id,
                        name=setting.name,
                        name_ru=setting.name_ru,
                        category=setting.category.value,
                        value=parsed_val,
                        raw_value=reg_val,
                        value_type=setting.value_type.value,
                        unit=setting.unit,
                        is_live=True,
                        backend_used=f"{backend.value}:{hive}\\{spec.registry_path}",
                    )

            # 3. DWM API
            elif backend == BackendType.DWM_API:
                val, err = self._read_dwm(spec.api_getter or "")
                if err is None and val is not None:
                    return SettingValueResponse(
                        setting_id=setting.id,
                        name=setting.name,
                        name_ru=setting.name_ru,
                        category=setting.category.value,
                        value=val,
                        value_type=setting.value_type.value,
                        unit=setting.unit,
                        is_live=True,
                        backend_used=backend.value,
                    )

            # 4. Win32 API (SysColors, Caret, DPI)
            elif backend in (BackendType.WIN32_API, BackendType.DISPLAY_CONFIG):
                val, err = self._read_win32(spec.api_getter or "", setting.value_type)
                if err is None and val is not None:
                    return SettingValueResponse(
                        setting_id=setting.id,
                        name=setting.name,
                        name_ru=setting.name_ru,
                        category=setting.category.value,
                        value=val,
                        value_type=setting.value_type.value,
                        unit=setting.unit,
                        is_live=True,
                        backend_used=backend.value,
                    )

        except Exception as ex:
            logger.debug(f"[WindowBackendResolver] Ошибка чтения {setting.id}: {ex}")

        # Fallback to default
        return SettingValueResponse(
            setting_id=setting.id,
            name=setting.name,
            name_ru=setting.name_ru,
            category=setting.category.value,
            value=setting.default_value,
            value_type=setting.value_type.value,
            unit=setting.unit,
            is_live=False,
            backend_used="DefaultFallback",
        )

    # =========================================================================
    # Симуляция (Dry-Run Preview)
    # =========================================================================
    def preview_change(self, setting: WindowSettingDefinition, new_value: Any) -> SettingPreviewResponse:
        """Выполняет сухой прогон (Dry-Run) и валидацию перед записью параметра."""
        current = self.read_value(setting)
        valid, casted_val, err_msg = self._validate_and_cast(setting, new_value)

        planned_be = setting.write_spec.backend.value if setting.write_spec else "None"
        will_rp = (
            setting.risk in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)
            or setting.requires_elevation
            or setting.requires_restart
        )

        safety_summary = (
            f"Параметр: '{setting.name_ru}' ({setting.id})\n"
            f"Текущее значение: {current.value} -> Планируемое: {casted_val}\n"
            f"Исполняющий бэкенд: {planned_be}\n"
            f"Требует перезапуска: {'ДА' if setting.requires_restart else 'НЕТ'}\n"
            f"Требует прав администратора: {'ДА' if setting.requires_elevation else 'НЕТ'}\n"
            f"Точка восстановления: {'Будет создана автоматически' if will_rp else 'Не требуется'}"
        )

        return SettingPreviewResponse(
            setting_id=setting.id,
            name_ru=setting.name_ru,
            current_value=current.value,
            new_value=casted_val if valid else new_value,
            is_valid=valid,
            validation_error=err_msg,
            risk=setting.risk.value,
            requires_elevation=setting.requires_elevation,
            requires_restart=setting.requires_restart,
            will_create_restore_point=will_rp,
            planned_backend=planned_be,
            safety_summary=safety_summary,
        )

    # =========================================================================
    # Запись параметров
    # =========================================================================
    def apply_value(self, setting: WindowSettingDefinition, new_value: Any) -> Tuple[bool, Optional[str]]:
        """Применяет изменение значения параметра в операционной системе."""
        valid, casted_val, err_msg = self._validate_and_cast(setting, new_value)
        if not valid:
            return False, f"Ошибка валидации: {err_msg}"

        if not setting.write_spec:
            return False, "У параметра отсутствует спецификация записи (Read-Only)."

        if not self._is_windows:
            logger.info(f"[WindowBackendResolver] [Mock] Запись {setting.id} = {casted_val}")
            return True, None

        spec = setting.write_spec
        backend = spec.backend

        try:
            # 1. SystemParametersInfoW
            if backend == BackendType.SYSTEM_PARAMETERS_INFO and spec.api_setter:
                ok, err = self._write_spi(spec.api_setter, casted_val, setting.value_type)
                if ok:
                    return True, None
                logger.warning(f"[WindowBackendResolver] SPI write error for {setting.id}: {err}")

            # 2. Registry / GPO Policy
            if (backend in (BackendType.REGISTRY, BackendType.POLICY_GPO, BackendType.POLICY_CSP)
                    or spec.registry_path is not None):
                hive = spec.registry_hive or ("HKLM" if backend in (BackendType.POLICY_GPO, BackendType.POLICY_CSP) else "HKCU")
                val_name = spec.registry_value if spec.registry_value is not None else (spec.gpo_name or "")
                reg_type = spec.registry_type or ("REG_DWORD" if setting.value_type in (SettingValueType.BOOLEAN, SettingValueType.INTEGER) else "REG_SZ")
                ok, err = self._write_registry(hive, spec.registry_path or "", val_name, casted_val, reg_type)
                if ok:
                    return True, None
                return False, f"Ошибка записи реестра: {err}"

            # 3. Win32 API (SysColors, Caret)
            if backend in (BackendType.WIN32_API, BackendType.DISPLAY_CONFIG):
                ok, err = self._write_win32(spec.api_setter or "", casted_val, setting.value_type)
                if ok:
                    return True, None
                return False, f"Ошибка Win32 API: {err}"

            # 4. Action triggers
            if setting.value_type == SettingValueType.ACTION:
                return True, None

            return False, f"Неподдерживаемый исполняющий бэкенд: {backend.value}"

        except Exception as ex:
            logger.error(f"[WindowBackendResolver] Исключение при применении {setting.id}: {ex}", exc_info=True)
            return False, str(ex)

    # =========================================================================
    # Внутренние методы Win32
    # =========================================================================
    def _read_spi(self, getter_name: str, val_type: SettingValueType) -> Tuple[Optional[Any], Optional[str]]:
        """Чтение через SystemParametersInfoW."""
        if not self._user32:
            return None, "user32 not available"

        action_code = getattr(win_const, getter_name, None)
        if action_code is None:
            return None, f"Неизвестная SPI константа {getter_name}"

        try:
            if getter_name == "SPI_GETANIMATION":
                anim = ANIMATIONINFO()
                anim.cbSize = ctypes.sizeof(ANIMATIONINFO)
                res = self._user32.SystemParametersInfoW(action_code, anim.cbSize, ctypes.byref(anim), 0)
                if res != 0:
                    return bool(anim.iMinAnimate), None

            elif val_type == SettingValueType.BOOLEAN:
                pv = ctypes.c_bool()
                res = self._user32.SystemParametersInfoW(action_code, 0, ctypes.byref(pv), 0)
                if res != 0:
                    return bool(pv.value), None
                # Alternate: check uiParam return
                ui = ctypes.c_uint()
                res2 = self._user32.SystemParametersInfoW(action_code, 0, ctypes.byref(ui), 0)
                if res2 != 0:
                    return bool(ui.value), None

            elif val_type in (SettingValueType.INTEGER, SettingValueType.DURATION_MS):
                pv = ctypes.c_uint()
                res = self._user32.SystemParametersInfoW(action_code, 0, ctypes.byref(pv), 0)
                if res != 0:
                    return int(pv.value), None

            elif val_type == SettingValueType.STRING:
                buf = ctypes.create_unicode_buffer(512)
                res = self._user32.SystemParametersInfoW(action_code, 512, buf, 0)
                if res != 0:
                    return buf.value, None

        except Exception as ex:
            return None, str(ex)

        return None, "SPI call returned 0"

    def _write_spi(self, setter_name: str, value: Any, val_type: SettingValueType) -> Tuple[bool, Optional[str]]:
        """Запись через SystemParametersInfoW."""
        if not self._user32:
            return False, "user32 not available"

        action_code = getattr(win_const, setter_name, None)
        if action_code is None:
            return False, f"Неизвестная SPI константа {setter_name}"

        flags = win_const.SPIF_UPDATEINIFILE | win_const.SPIF_SENDCHANGE

        try:
            if setter_name == "SPI_SETANIMATION":
                anim = ANIMATIONINFO()
                anim.cbSize = ctypes.sizeof(ANIMATIONINFO)
                anim.iMinAnimate = 1 if value else 0
                res = self._user32.SystemParametersInfoW(action_code, anim.cbSize, ctypes.byref(anim), flags)
                return (res != 0), None

            elif val_type == SettingValueType.BOOLEAN:
                int_bool = 1 if value else 0
                # Try passing as uiParam
                res = self._user32.SystemParametersInfoW(action_code, int_bool, None, flags)
                if res != 0:
                    return True, None
                # Alternate: pvParam as pointer / int
                res2 = self._user32.SystemParametersInfoW(action_code, 0, ctypes.c_void_p(int_bool), flags)
                return (res2 != 0), None

            elif val_type in (SettingValueType.INTEGER, SettingValueType.DURATION_MS):
                int_val = int(value)
                res = self._user32.SystemParametersInfoW(action_code, int_val, ctypes.c_void_p(int_val), flags)
                if res != 0:
                    return True, None
                res2 = self._user32.SystemParametersInfoW(action_code, 0, ctypes.c_void_p(int_val), flags)
                return (res2 != 0), None

            elif val_type == SettingValueType.STRING:
                str_buf = ctypes.c_wchar_p(str(value))
                res = self._user32.SystemParametersInfoW(action_code, 0, str_buf, flags)
                return (res != 0), None

        except Exception as ex:
            return False, str(ex)

        return False, "SPI setter failed"

    def _read_dwm(self, getter_name: str) -> Tuple[Optional[Any], Optional[str]]:
        """Чтение состояния DWM."""
        if not self._dwmapi:
            return None, "dwmapi not available"

        try:
            if getter_name == "DwmIsCompositionEnabled":
                enabled = ctypes.c_bool()
                res = self._dwmapi.DwmIsCompositionEnabled(ctypes.byref(enabled))
                if res == 0:
                    return bool(enabled.value), None
        except Exception as ex:
            return None, str(ex)

        return None, "DWM getter not matched"

    def _read_win32(self, getter_name: str, val_type: SettingValueType) -> Tuple[Optional[Any], Optional[str]]:
        """Чтение Win32 API функций (GetSysColor, Caret, DPI)."""
        if not self._user32:
            return None, "user32 not available"

        try:
            if "GetSysColor" in getter_name:
                color_name = getter_name.replace("GetSysColor", "").strip()
                color_idx = getattr(win_const, color_name, None)
                if color_idx is not None:
                    rgb = self._user32.GetSysColor(color_idx)
                    r = rgb & 0xFF
                    g = (rgb >> 8) & 0xFF
                    b = (rgb >> 16) & 0xFF
                    return f"#{r:02X}{g:02X}{b:02X}", None

            elif getter_name == "GetCaretBlinkTime":
                ms = self._user32.GetCaretBlinkTime()
                return int(ms), None

            elif getter_name == "GetDpiForSystem":
                if hasattr(self._user32, "GetDpiForSystem"):
                    dpi = self._user32.GetDpiForSystem()
                    return int(dpi), None
                return 96, None

        except Exception as ex:
            return None, str(ex)

        return None, "Win32 getter not matched"

    def _write_win32(self, setter_name: str, value: Any, val_type: SettingValueType) -> Tuple[bool, Optional[str]]:
        """Запись параметров через Win32 API."""
        if not self._user32:
            return False, "user32 not available"

        try:
            if "SetSysColors" in setter_name:
                color_name = setter_name.replace("SetSysColors", "").strip()
                color_idx = getattr(win_const, color_name, None)
                if color_idx is not None and isinstance(value, str) and value.startswith("#"):
                    hex_clean = value.lstrip("#")
                    r = int(hex_clean[0:2], 16)
                    g = int(hex_clean[2:4], 16)
                    b = int(hex_clean[4:6], 16)
                    rgb_int = r | (g << 8) | (b << 16)
                    elements = (ctypes.c_int * 1)(color_idx)
                    colors = (ctypes.c_uint * 1)(rgb_int)
                    res = self._user32.SetSysColors(1, elements, colors)
                    return (res != 0), None

            elif setter_name == "SetCaretBlinkTime":
                res = self._user32.SetCaretBlinkTime(int(value))
                return (res != 0), None

        except Exception as ex:
            return False, str(ex)

        return False, "Win32 setter not matched"

    def _read_registry(self, hive_str: str, subkey: str, val_name: str) -> Tuple[Optional[Any], Optional[str]]:
        """Чтение ключа реестра Windows."""
        if not winreg:
            return None, "winreg not available"

        root = winreg.HKEY_LOCAL_MACHINE if hive_str == "HKLM" else winreg.HKEY_CURRENT_USER
        try:
            with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as k:
                val, reg_type = winreg.QueryValueEx(k, val_name)
                return val, None
        except FileNotFoundError:
            return None, "Key or value not found"
        except Exception as ex:
            return None, str(ex)

    def _write_registry(self, hive_str: str, subkey: str, val_name: str, value: Any, reg_type_str: str) -> Tuple[bool, Optional[str]]:
        """Запись значения в реестр Windows."""
        if not winreg:
            return False, "winreg not available"

        root = winreg.HKEY_LOCAL_MACHINE if hive_str == "HKLM" else winreg.HKEY_CURRENT_USER
        type_map = {
            "REG_DWORD": winreg.REG_DWORD,
            "REG_SZ": winreg.REG_SZ,
            "REG_BINARY": winreg.REG_BINARY,
            "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
        }
        target_type = type_map.get(reg_type_str, winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ)

        try:
            with winreg.CreateKeyEx(root, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WRITE) as k:
                if target_type == winreg.REG_DWORD:
                    val_to_write = int(value)
                elif target_type == winreg.REG_BINARY and isinstance(value, bytes):
                    val_to_write = value
                else:
                    val_to_write = str(value)
                winreg.SetValueEx(k, val_name, 0, target_type, val_to_write)
                return True, None
        except Exception as ex:
            return False, str(ex)

    def _cast_type(self, raw: Any, target_type: SettingValueType) -> Any:
        """Приведение сырого значения реестра к типу параметра."""
        if target_type == SettingValueType.BOOLEAN:
            if isinstance(raw, str):
                return raw.strip().lower() in ("1", "true", "yes", "on")
            return bool(raw)
        elif target_type in (SettingValueType.INTEGER, SettingValueType.DURATION_MS):
            try:
                return int(raw)
            except Exception:
                return raw
        return raw

    def _validate_and_cast(self, setting: WindowSettingDefinition, value: Any) -> Tuple[bool, Any, Optional[str]]:
        """Валидация нового значения по ограничениям типа, диапазону и списку допустимых."""
        v_type = setting.value_type

        # 1. Boolean
        if v_type == SettingValueType.BOOLEAN:
            if isinstance(value, bool):
                return True, value, None
            if isinstance(value, (int, str)):
                s = str(value).strip().lower()
                if s in ("1", "true", "yes", "on"):
                    return True, True, None
                if s in ("0", "false", "no", "off"):
                    return True, False, None
            return False, value, "Значение должно быть логическим (True/False)."

        # 2. Integer / Duration
        elif v_type in (SettingValueType.INTEGER, SettingValueType.DURATION_MS):
            try:
                iv = int(value)
            except (ValueError, TypeError):
                return False, value, "Значение должно быть целым числом."

            if setting.min_val is not None and iv < setting.min_val:
                return False, iv, f"Значение ниже допустимого минимума ({setting.min_val})."
            if setting.max_val is not None and iv > setting.max_val:
                return False, iv, f"Значение превышает допустимый максимум ({setting.max_val})."
            if setting.allowed_values and iv not in setting.allowed_values:
                return False, iv, f"Значение {iv} не входит в список допустимых: {setting.allowed_values}."
            return True, iv, None

        # 3. Enum
        elif v_type == SettingValueType.ENUM:
            str_val = str(value)
            if setting.allowed_values and str_val not in setting.allowed_values:
                # Попробуем без учета регистра
                matched = [x for x in setting.allowed_values if str(x).lower() == str_val.lower()]
                if matched:
                    return True, matched[0], None
                return False, str_val, f"Значение '{str_val}' недопустимо. Варианты: {setting.allowed_values}."
            return True, str_val, None

        # 4. Color Hex
        elif v_type == SettingValueType.COLOR_HEX:
            s = str(value).strip()
            if not s.startswith("#") or len(s) not in (7, 9):
                return False, value, "Цвет должен быть в формате HEX (например: #0078D7 или #0078D7FF)."
            return True, s, None

        return True, value, None
