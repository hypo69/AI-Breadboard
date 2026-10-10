# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Personalization Manager
# =============================================================================
# Description:
#   Менеджер персонализации Windows (Personalization & Appearance Control Plane).
#   Управляет темами Windows, размером и цветом указателя мыши, обоями рабочего
#   стола, экраном блокировки, Windows Spotlight и интеллектуальным AI Spotlight.
#   Все изменения автоматически фиксируются в SQLite базе данных telemetry.db.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.personalization.manager import get_personalization_manager
#
#     pm = get_personalization_manager()
#     overview = pm.get_overview()
#     pm.update_cursor(CursorUpdateRequest(size=48, custom_color_hex="#FFCC00"))
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.personalization
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:20:00
# =============================================================================

from __future__ import annotations
"""Менеджер персонализации, тем, курсора, обоев и Spotlight для Windows."""

import ctypes
from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union
import uuid
import winreg

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("personalization_manager")

from apps.windows.sdk.modules.personalization.ai_spotlight import (
    AISpotlightEngine,
    get_ai_spotlight_engine,
)
from apps.windows.sdk.modules.personalization.store import PersonalizationStore
from apps.windows.sdk.modules.personalization.models import (
    AISpotlightImageInfo,
    CursorColorScheme,
    CursorSettings,
    CursorUpdateRequest,
    PersonalizationOverviewResponse,
    SpotlightUpdateRequest,
    ThemeApplyRequest,
    WallpaperFitMode,
    WallpaperSettings,
    WallpaperSourceMode,
    WallpaperUpdateRequest,
    WindowsSpotlightSettings,
    WindowsThemeInfo,
)
from apps.windows.sdk.modules.window_control_plane.history import (
    WindowManagementHistoryManager,
    get_window_history_manager,
)

# Win32 константы
SPI_SETDESKWALLPAPER = 0x0014
SPI_GETDESKWALLPAPER = 0x0073
SPI_SETCURSORS = 0x0057
SPI_GETMOUSESPEED = 0x0070
SPI_SETMOUSESPEED = 0x0071
SPI_GETMOUSETRAILS = 0x005E
SPI_SETMOUSETRAILS = 0x005F
SPIF_UPDATEINIFILE = 0x0001
SPIF_SENDCHANGE = 0x0002


class PersonalizationManager:
    """Центральный координатор тем, указателя мыши, обоев и AI Spotlight."""

    def __init__(
        self,
        history_manager: Optional[WindowManagementHistoryManager] = None,
        ai_spotlight: Optional[AISpotlightEngine] = None,
        store: Optional[PersonalizationStore] = None,
    ) -> None:
        """Инициализация менеджера персонализации."""
        self.history = history_manager or get_window_history_manager()
        self.history_manager = self.history
        self.history_mgr = self.history
        self.ai_spotlight = ai_spotlight or get_ai_spotlight_engine()
        self.store = store or PersonalizationStore(self.history.db_path)
        self.backup_dir = self.store.db_path.parent / "personalization_backups"

    # =========================================================================
    # SQLite: снимки, аудит, Data-First состояние, SafeOps
    # =========================================================================
    def _read_taskbar_alignment(self) -> str:
        """Выравнивание значков панели задач Windows 11 (TaskbarAl: 0 — слева, 1 — по центру)."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                0,
                winreg.KEY_READ,
            ) as key:
                return "left" if winreg.QueryValueEx(key, "TaskbarAl")[0] == 0 else "center"
        except OSError:
            return "center"

    def _live_snapshot(self) -> Dict[str, Any]:
        """Собирает текущие значения из системы в формат personalization_snapshots."""
        cursor = self.get_cursor_settings()
        wall = self.get_wallpaper_settings()
        dark = self.is_dark_mode_active()
        return {
            "cursor_size": cursor.size,
            "cursor_type": cursor.color_scheme.value,
            "cursor_color_hex": cursor.custom_color_hex,
            "cursor_shadow_enabled": int(cursor.shadow),
            "cursor_trails_length": cursor.trail_length,
            "cursor_speed": cursor.pointer_speed,
            "apps_use_light_theme": int(not dark),
            "system_use_light_theme": int(not dark),
            "dwm_accent_color_hex": self.get_accent_color_hex(),
            "wallpaper_path": wall.current_wallpaper_path,
            "wallpaper_fit_mode": wall.fit_mode.value.capitalize(),
            "taskbar_alignment": self._read_taskbar_alignment(),
        }

    def _audit(self, group: str, old: Dict[str, Any], new: Dict[str, Any], operator: str, prefix: str = "") -> None:
        """Пишет по записи на каждый изменившийся параметр и фиксирует новый снимок."""
        changed_by = "USER_UI" if operator == "User" else operator
        for key in new:
            if old.get(key) != new[key]:
                self.store.record_change(group, f"{prefix}{key}", old.get(key), new[key], changed_by, True)
        self.store.add_snapshot(self._live_snapshot())

    def _backup_registry(self, *keys: str) -> None:
        """Экспортирует ветки реестра в каталог бэкапов перед изменением (сбой не блокирует операцию)."""
        if sys.platform != "win32":
            return
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for key in keys:
            target = self.backup_dir / f"{stamp}_{key.replace(chr(92), '_')}.reg"
            try:
                subprocess.run(["reg", "export", f"HKCU\\{key}", str(target), "/y"], capture_output=True, timeout=10)
            except Exception as ex:
                logger.warning(f"[PersonalizationManager] Бэкап ветки {key} не создан: {ex}")

    @staticmethod
    def broadcast_setting_change() -> None:
        """Уведомляет окна о смене темы (WM_SETTINGCHANGE с таймаутом, чтобы не подвесить Explorer)."""
        if sys.platform != "win32":
            return
        try:
            result = ctypes.c_ulong()
            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF, 0x001A, 0, "ImmersiveColorSet", 0x0002, 5000, ctypes.byref(result)
            )
        except Exception as ex:
            logger.warning(f"[PersonalizationManager] Ошибка broadcast WM_SETTINGCHANGE: {ex}")

    def get_state(self) -> Dict[str, Any]:
        """Data-First срез персонализации из SQLite; при отсутствии снимков фиксирует первый."""
        snap = self.store.latest_snapshot()
        if snap is None:
            self.store.add_snapshot(self._live_snapshot())
            snap = self.store.latest_snapshot()
        return {
            "cursor": {
                "size": snap["cursor_size"],
                "type": snap["cursor_type"],
                "color_hex": snap["cursor_color_hex"],
                "shadow_enabled": bool(snap["cursor_shadow_enabled"]),
                "trails_length": snap["cursor_trails_length"],
                "speed": snap["cursor_speed"],
            },
            "theme": {
                "apps_use_light_theme": bool(snap["apps_use_light_theme"]),
                "system_use_light_theme": bool(snap["system_use_light_theme"]),
                "accent_color_hex": snap["dwm_accent_color_hex"],
            },
            "wallpaper": {"current_path": snap["wallpaper_path"], "fit_mode": snap["wallpaper_fit_mode"]},
            "taskbar": {"alignment": snap["taskbar_alignment"]},
            "last_updated": snap["captured_at"],
        }

    # =========================================================================
    # Сводный обзор (Overview)
    # =========================================================================
    def get_overview(self) -> PersonalizationOverviewResponse:
        """Возвращает сводный статус тем, курсора, обоев и Spotlight."""
        themes = self.get_theme_list()
        current_theme_info = next((t for t in themes if t.is_current), None)
        current_theme_name = current_theme_info.display_name if current_theme_info else "Windows По умолчанию"
        is_dark = self.is_dark_mode_active()
        accent_hex = self.get_accent_color_hex()

        cursor = self.get_cursor_settings()
        wallpaper = self.get_wallpaper_settings()
        spotlight = self.get_spotlight_settings()
        ai_spotlight_info = self.get_current_ai_spotlight()
        saved_ai_count = len(self.ai_spotlight.get_all_saved_images())

        return PersonalizationOverviewResponse(
            current_theme=current_theme_name,
            is_dark_mode=is_dark,
            accent_color_hex=accent_hex,
            cursor=cursor,
            wallpaper=wallpaper,
            spotlight=spotlight,
            ai_spotlight_current=ai_spotlight_info,
            available_themes_count=len(themes),
            saved_ai_spotlight_count=saved_ai_count,
        )

    # =========================================================================
    # 1. Темы Windows
    # =========================================================================
    def get_theme_list(self) -> List[WindowsThemeInfo]:
        """Сканирует установленные темы Windows (.theme)."""
        themes: List[WindowsThemeInfo] = []
        is_dark = self.is_dark_mode_active()
        accent = self.get_accent_color_hex()
        curr_wall = self._read_current_wallpaper_path()

        # Пути сканирования системных и пользовательских тем
        theme_dirs = [
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Resources" / "Themes",
        ]
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            theme_dirs.append(Path(localappdata) / "Microsoft" / "Windows" / "Themes")

        found_names = set()
        for d in theme_dirs:
            if not d.exists():
                continue
            try:
                for theme_file in d.glob("*.theme"):
                    stem = theme_file.stem
                    if stem.lower() in found_names:
                        continue
                    found_names.add(stem.lower())
                    display_name = self._parse_theme_display_name(theme_file)
                    is_cur = "custom" in stem.lower() or stem.lower() == "aero"

                    themes.append(
                        WindowsThemeInfo(
                            name=stem,
                            display_name=display_name,
                            theme_path=str(theme_file),
                            is_current=is_cur,
                            is_dark_mode=is_dark if is_cur else ("dark" in stem.lower()),
                            accent_color_hex=accent,
                            wallpaper_path=curr_wall if is_cur else None,
                        )
                    )
            except Exception as ex:
                logger.warning(f"[PersonalizationManager] Ошибка чтения тем из {d}: {ex}")

        if not themes:
            # Fallback тема
            themes.append(
                WindowsThemeInfo(
                    name="Default",
                    display_name="Windows (По умолчанию)",
                    is_current=True,
                    is_dark_mode=is_dark,
                    accent_color_hex=accent,
                    wallpaper_path=curr_wall,
                )
            )

        return themes

    def is_dark_mode_active(self) -> bool:
        """Проверяет, включена ли тёмная тема интерфейса Windows."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0,
                winreg.KEY_READ,
            ) as key:
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return val == 0
        except Exception:
            return False

    def get_accent_color_hex(self) -> str:
        """Получает текущий системный акцентный цвет."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\DWM",
                0,
                winreg.KEY_READ,
            ) as key:
                val, _ = winreg.QueryValueEx(key, "AccentColor")
                # Цвет представлен как ABGR (DWORD)
                b = (val >> 16) & 0xFF
                g = (val >> 8) & 0xFF
                r = val & 0xFF
                return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return "#0078D7"

    def apply_theme(self, request: ThemeApplyRequest, operator: str = "User") -> Dict[str, Any]:
        """Применяет тему оформления, переключая режим Dark/Light и акцентный цвет."""
        change_id = str(uuid.uuid4())
        old_dark = self.is_dark_mode_active()
        self._backup_registry(r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        old_accent = self.get_accent_color_hex()

        # 1. Изменение темного/светлого режима если запрошено
        if request.force_dark_mode is not None:
            new_light_val = 0 if request.force_dark_mode else 1
            try:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                ) as key:
                    winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new_light_val)
                    winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_light_val)
            except Exception as ex:
                logger.error(f"[PersonalizationManager] Ошибка изменения темы Dark/Light: {ex}")

        new_dark = self.is_dark_mode_active()
        if request.force_dark_mode is not None:
            self.broadcast_setting_change()
        self._audit("THEME", {"apps_use_light_theme": not old_dark, "system_use_light_theme": not old_dark}, {"apps_use_light_theme": not new_dark, "system_use_light_theme": not new_dark}, operator)

        # 2. Фиксация в telemetry.db
        self.history.record_change(
            change_id=change_id,
            setting_id="personalization.theme.apply",
            setting_name="Применение темы оформления",
            category="window_metrics_theme",
            backend_type="winreg",
            scope="user",
            risk_level="safe",
            old_value={"dark_mode": old_dark, "accent": old_accent},
            new_value={"theme": request.theme_name_or_path, "dark_mode": request.force_dark_mode, "accent": request.accent_color_hex},
            action_type="APPLY",
            operator=operator,
            reason=f"Apply theme {request.theme_name_or_path}",
            status="SUCCESS",
        )

        return {
            "success": True,
            "change_id": change_id,
            "theme_applied": request.theme_name_or_path,
            "is_dark_mode": self.is_dark_mode_active(),
            "accent_color": self.get_accent_color_hex(),
        }

    # =========================================================================
    # 2. Указатель мыши и Курсор
    # =========================================================================
    def get_cursor_settings(self) -> CursorSettings:
        """Чтение текущих настроек курсора из реестра и Win32 SPI."""
        size = 32
        color_scheme = CursorColorScheme.WHITE
        custom_hex = None
        shadow = True
        trails = False
        trail_len = 0
        hide_typing = True
        show_ctrl = False
        speed = 10

        # Чтение размера и цвета из Accessibility и Control Panel\Cursors
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Cursors",
                0,
                winreg.KEY_READ,
            ) as key:
                try:
                    c_base_size, _ = winreg.QueryValueEx(key, "CursorBaseSize")
                    size = max(1, min(128, int(c_base_size)))
                except OSError:
                    pass
        except Exception:
            pass

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Accessibility",
                0,
                winreg.KEY_READ,
            ) as key:
                try:
                    if size == 32:
                        c_size, _ = winreg.QueryValueEx(key, "CursorSize")
                        size = max(1, min(128, int(c_size * 32)))
                except OSError:
                    pass
                try:
                    c_type, _ = winreg.QueryValueEx(key, "CursorType")
                    if c_type == 0:
                        color_scheme = CursorColorScheme.WHITE
                    elif c_type == 1:
                        color_scheme = CursorColorScheme.BLACK
                    elif c_type == 2:
                        color_scheme = CursorColorScheme.INVERTED
                    elif c_type == 3:
                        color_scheme = CursorColorScheme.CUSTOM
                except OSError:
                    pass
                try:
                    c_color, _ = winreg.QueryValueEx(key, "CursorColor")
                    custom_hex = f"#{c_color:06X}"
                    if color_scheme == CursorColorScheme.WHITE and custom_hex != "#000000":
                        color_scheme = CursorColorScheme.CUSTOM
                except OSError:
                    pass
        except Exception:
            pass

        # Чтение скорости указателя Win32
        if sys.platform == "win32":
            try:
                speed_val = ctypes.c_int()
                if ctypes.windll.user32.SystemParametersInfoW(SPI_GETMOUSESPEED, 0, ctypes.byref(speed_val), 0):
                    speed = max(1, min(20, speed_val.value))
            except Exception:
                pass

            try:
                trails_val = ctypes.c_int()
                if ctypes.windll.user32.SystemParametersInfoW(SPI_GETMOUSETRAILS, 0, ctypes.byref(trails_val), 0):
                    trails = trails_val.value > 0
                    trail_len = max(0, min(7, trails_val.value))
            except Exception:
                pass

        # Чтение флагов реестра Desktop
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Desktop",
                0,
                winreg.KEY_READ,
            ) as key:
                try:
                    usr_mask, _ = winreg.QueryValueEx(key, "UserPreferencesMask")
                    if isinstance(usr_mask, (bytes, bytearray)) and len(usr_mask) >= 1:
                        shadow = bool(usr_mask[0] & 0x04)
                except OSError:
                    pass
        except Exception:
            pass

        return CursorSettings(
            size=size,
            color_scheme=color_scheme,
            custom_color_hex=custom_hex,
            shadow=shadow,
            trails=trails,
            trail_length=trail_len,
            hide_while_typing=hide_typing,
            show_location_on_ctrl=show_ctrl,
            pointer_speed=speed,
        )

    def update_cursor(self, request: CursorUpdateRequest, operator: str = "User") -> CursorSettings:
        """Обновление размера, цвета и эффектов курсора мыши."""
        old_settings = self.get_cursor_settings()
        self._backup_registry(r"Software\Microsoft\Accessibility", r"Control Panel\Cursors")
        change_id = str(uuid.uuid4())

        # 1. Запись размера курсора
        if request.size is not None:
            normalized_size = max(1, min(128, request.size))
            scale_factor = max(1, round(normalized_size / 32))
            try:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Accessibility",
                ) as key:
                    winreg.SetValueEx(key, "CursorSize", 0, winreg.REG_DWORD, scale_factor)
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Control Panel\Cursors",
                ) as key:
                    winreg.SetValueEx(key, "CursorBaseSize", 0, winreg.REG_DWORD, normalized_size)
            except Exception as ex:
                logger.error(f"[PersonalizationManager] Ошибка записи размера курсора: {ex}")

        # 1.1. Запись цветовой схемы курсора
        if request.color_scheme is not None:
            type_map = {
                CursorColorScheme.WHITE: 0,
                CursorColorScheme.BLACK: 1,
                CursorColorScheme.INVERTED: 2,
                CursorColorScheme.CUSTOM: 3,
            }
            c_type_val = type_map.get(request.color_scheme, 0)
            try:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Accessibility",
                ) as key:
                    winreg.SetValueEx(key, "CursorType", 0, winreg.REG_DWORD, c_type_val)
                    if request.custom_color_hex:
                        hex_clean = request.custom_color_hex.lstrip("#")
                        if len(hex_clean) == 6:
                            winreg.SetValueEx(key, "CursorColor", 0, winreg.REG_DWORD, int(hex_clean, 16))
            except Exception as ex:
                logger.error(f"[PersonalizationManager] Ошибка записи цвета курсора: {ex}")

        # 2. Запись скорости указателя
        if request.pointer_speed is not None and sys.platform == "win32":
            try:
                spd = max(1, min(20, request.pointer_speed))
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETMOUSESPEED,
                    0,
                    ctypes.c_void_p(spd),
                    SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
                )
            except Exception as ex:
                logger.warning(f"[PersonalizationManager] Ошибка установки скорости мыши: {ex}")

        # 3. Шлейф курсора
        if request.trails is not None and sys.platform == "win32":
            try:
                trail_val = 7 if request.trails else 0
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETMOUSETRAILS,
                    trail_val,
                    0,
                    SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
                )
            except Exception as ex:
                logger.warning(f"[PersonalizationManager] Ошибка шлейфа курсора: {ex}")

        # Обновление схем курсоров в User32
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETCURSORS,
                    0,
                    None,
                    SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
                )
            except Exception:
                pass

        new_settings = self.get_cursor_settings()

        # Фиксация в telemetry.db
        self.history.record_change(
            change_id=change_id,
            setting_id="personalization.cursor.update",
            setting_name="Настройки указателя мыши и доступности",
            category="mouse_behaviour",
            backend_type="spi",
            scope="user",
            risk_level="safe",
            old_value=old_settings.model_dump(),
            new_value=new_settings.model_dump(),
            action_type="APPLY",
            operator=operator,
            reason="Update cursor settings via Control Plane",
            status="SUCCESS",
        )

        self._audit("CURSOR", old_settings.model_dump(mode="json"), new_settings.model_dump(mode="json"), operator, "cursor_")
        return new_settings

    # =========================================================================
    # 3. Обои рабочего стола
    # =========================================================================
    def get_wallpaper_settings(self) -> WallpaperSettings:
        """Получение текущих настроек обоев и режима подгонки."""
        curr_path = self._read_current_wallpaper_path()
        fit_mode = WallpaperFitMode.FILL
        source_mode = WallpaperSourceMode.PICTURE
        bg_hex = "#000000"

        # 1. Чтение типа источника обоев
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers",
                0,
                winreg.KEY_READ,
            ) as key:
                try:
                    bg_type, _ = winreg.QueryValueEx(key, "BackgroundType")
                    if bg_type == 1:
                        source_mode = WallpaperSourceMode.SOLID_COLOR
                    elif bg_type == 2:
                        source_mode = WallpaperSourceMode.SLIDESHOW
                    elif bg_type == 3:
                        source_mode = WallpaperSourceMode.SPOTLIGHT
                    else:
                        source_mode = WallpaperSourceMode.PICTURE
                except OSError:
                    pass
        except Exception:
            pass

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Desktop",
                0,
                winreg.KEY_READ,
            ) as key:
                try:
                    style, _ = winreg.QueryValueEx(key, "WallpaperStyle")
                    tile, _ = winreg.QueryValueEx(key, "TileWallpaper")
                    fit_mode = self._decode_wallpaper_fit(str(style), str(tile))
                except OSError:
                    pass
        except Exception:
            pass

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Colors",
                0,
                winreg.KEY_READ,
            ) as key:
                bg_raw, _ = winreg.QueryValueEx(key, "Background")
                parts = [int(p) for p in str(bg_raw).split() if p.isdigit()]
                if len(parts) >= 3:
                    bg_hex = f"#{parts[0]:02X}{parts[1]:02X}{parts[2]:02X}"
        except Exception:
            pass

        return WallpaperSettings(
            mode=source_mode,
            current_wallpaper_path=curr_path,
            fit_mode=fit_mode,
            background_color_hex=bg_hex,
        )

    def update_wallpaper(self, request: WallpaperUpdateRequest, operator: str = "User") -> WallpaperSettings:
        """Установка новых обоев рабочего стола с масштабированием."""
        old_settings = self.get_wallpaper_settings()
        self._backup_registry(r"Control Panel\Desktop")
        change_id = str(uuid.uuid4())

        # 1. Запись BackgroundType
        if request.mode is not None:
            type_val = 0
            if request.mode == WallpaperSourceMode.SOLID_COLOR:
                type_val = 1
            elif request.mode == WallpaperSourceMode.SLIDESHOW:
                type_val = 2
            elif request.mode == WallpaperSourceMode.SPOTLIGHT:
                type_val = 3
            try:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers",
                ) as key:
                    winreg.SetValueEx(key, "BackgroundType", 0, winreg.REG_DWORD, type_val)
            except Exception as ex:
                logger.warning(f"[PersonalizationManager] Ошибка записи BackgroundType: {ex}")

        # 2. Установка стиля масштабирования
        if request.fit_mode is not None:
            style_val, tile_val = self._encode_wallpaper_fit(request.fit_mode)
            try:
                with winreg.CreateKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Control Panel\Desktop",
                ) as key:
                    winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style_val)
                    winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, tile_val)
            except Exception as ex:
                logger.error(f"[PersonalizationManager] Ошибка записи стиля обоев: {ex}")

        # 3. Установка фонового цвета
        if request.background_color_hex:
            try:
                hex_c = request.background_color_hex.lstrip("#")
                if len(hex_c) == 6:
                    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
                    with winreg.CreateKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Control Panel\Colors",
                    ) as key:
                        winreg.SetValueEx(key, "Background", 0, winreg.REG_SZ, f"{r} {g} {b}")
            except Exception as ex:
                logger.warning(f"[PersonalizationManager] Ошибка записи цвета фона: {ex}")

        # 4. Установка изображения через SystemParametersInfoW
        if request.image_path and Path(request.image_path).exists() and sys.platform == "win32":
            abs_path = str(Path(request.image_path).resolve())
            try:
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETDESKWALLPAPER,
                    0,
                    abs_path,
                    SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
                )
            except Exception as ex:
                logger.error(f"[PersonalizationManager] Ошибка применения обоев Win32: {ex}")

        new_settings = self.get_wallpaper_settings()

        # Фиксация в telemetry.db
        self.history.record_change(
            change_id=change_id,
            setting_id="personalization.wallpaper.update",
            setting_name="Установка обоев рабочего стола",
            category="desktop_explorer",
            backend_type="spi",
            scope="user",
            risk_level="safe",
            old_value=old_settings.model_dump(),
            new_value=new_settings.model_dump(),
            action_type="APPLY",
            operator=operator,
            reason=f"Update wallpaper to {request.image_path or 'new style'}",
            status="SUCCESS",
        )

        self._audit("WALLPAPER", old_settings.model_dump(mode="json"), new_settings.model_dump(mode="json"), operator, "wallpaper_")
        return new_settings

    # =========================================================================
    # 4. Windows Spotlight
    # =========================================================================
    def get_spotlight_settings(self) -> WindowsSpotlightSettings:
        """Получение состояния Windows Spotlight."""
        lock_enabled = True
        desktop_enabled = False

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                0,
                winreg.KEY_READ,
            ) as key:
                try:
                    val, _ = winreg.QueryValueEx(key, "RotatingLockScreenEnabled")
                    lock_enabled = bool(val)
                except OSError:
                    pass
                try:
                    val, _ = winreg.QueryValueEx(key, "RotatingImageOverlayEnabled")
                    desktop_enabled = bool(val)
                except OSError:
                    pass
        except Exception:
            pass

        return WindowsSpotlightSettings(
            enabled_desktop=desktop_enabled,
            enabled_lock_screen=lock_enabled,
            allow_fun_facts=True,
            current_image_title="Интересное от Windows (Spotlight)",
            current_image_description="Ежедневные фотографии пейзажей и памятников природы со всего мира.",
            learn_about_url="https://www.bing.com/search?q=windows+spotlight+wallpaper",
        )

    def update_spotlight(self, request: SpotlightUpdateRequest, operator: str = "User") -> WindowsSpotlightSettings:
        """Настройка параметров Windows Spotlight."""
        old_settings = self.get_spotlight_settings()
        change_id = str(uuid.uuid4())

        try:
            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
            ) as key:
                if request.enabled_lock_screen is not None:
                    winreg.SetValueEx(key, "RotatingLockScreenEnabled", 0, winreg.REG_DWORD, 1 if request.enabled_lock_screen else 0)
                if request.enabled_desktop is not None:
                    winreg.SetValueEx(key, "RotatingImageOverlayEnabled", 0, winreg.REG_DWORD, 1 if request.enabled_desktop else 0)
        except Exception as ex:
            logger.error(f"[PersonalizationManager] Ошибка изменения Spotlight: {ex}")

        new_settings = self.get_spotlight_settings()

        # Фиксация в telemetry.db
        self.history.record_change(
            change_id=change_id,
            setting_id="personalization.spotlight.update",
            setting_name="Настройка службы Windows Spotlight",
            category="desktop_explorer",
            backend_type="winreg",
            scope="user",
            risk_level="safe",
            old_value=old_settings.model_dump(),
            new_value=new_settings.model_dump(),
            action_type="APPLY",
            operator=operator,
            reason="Configure Windows Spotlight via Control Plane",
            status="SUCCESS",
        )

        return new_settings

    # =========================================================================
    # 5. AI Spotlight (Медиа-интеллект и познавательные карточки)
    # =========================================================================
    def get_current_ai_spotlight(self) -> Optional[AISpotlightImageInfo]:
        """Анализирует текущее изображение рабочего стола через AI Spotlight."""
        curr_wall = self._read_current_wallpaper_path()
        if not curr_wall or not Path(curr_wall).exists():
            # Если обои не заданы файлом, проверяем Spotlight кэш
            assets = self.ai_spotlight.find_windows_spotlight_assets()
            if assets:
                curr_wall = str(assets[0])
            else:
                curr_wall = r"C:\Windows\Web\Wallpaper\Windows\img0.jpg"

        return self.ai_spotlight.analyze_image(curr_wall, is_current_wallpaper=True)

    # =========================================================================
    # Вспомогательные методы
    # =========================================================================
    def _read_current_wallpaper_path(self) -> Optional[str]:
        """Чтение пути к текущему файлу обоев."""
        if sys.platform == "win32":
            buf = ctypes.create_unicode_buffer(512)
            try:
                if ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, len(buf), buf, 0):
                    val = buf.value
                    if val and Path(val).exists():
                        return val
            except Exception:
                pass

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Desktop",
                0,
                winreg.KEY_READ,
            ) as key:
                val, _ = winreg.QueryValueEx(key, "Wallpaper")
                return str(val) if val else None
        except Exception:
            return None

    def _parse_theme_display_name(self, theme_file: Path) -> str:
        """Извлечение отображаемого имени из файла .theme."""
        try:
            with open(theme_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().lower().startswith("displayname="):
                        return line.strip().split("=", 1)[1].strip()
        except Exception:
            pass
        return theme_file.stem.replace("_", " ").title()

    def _decode_wallpaper_fit(self, style: str, tile: str) -> WallpaperFitMode:
        """Декодирование значений реестра в WallpaperFitMode."""
        if tile == "1":
            return WallpaperFitMode.TILE
        if style == "10":
            return WallpaperFitMode.FILL
        if style == "6":
            return WallpaperFitMode.FIT
        if style == "2":
            return WallpaperFitMode.STRETCH
        if style == "22":
            return WallpaperFitMode.SPAN
        return WallpaperFitMode.CENTER

    def _encode_wallpaper_fit(self, mode: WallpaperFitMode) -> tuple[str, str]:
        """Кодирование WallpaperFitMode в значения WallpaperStyle и TileWallpaper."""
        if mode == WallpaperFitMode.FILL:
            return "10", "0"
        if mode == WallpaperFitMode.FIT:
            return "6", "0"
        if mode == WallpaperFitMode.STRETCH:
            return "2", "0"
        if mode == WallpaperFitMode.TILE:
            return "0", "1"
        if mode == WallpaperFitMode.SPAN:
            return "22", "0"
        return "0", "0"


_personalization_manager_instance: Optional[PersonalizationManager] = None


def get_personalization_manager() -> PersonalizationManager:
    """Синглтон фабрика менеджера персонализации."""
    global _personalization_manager_instance
    if _personalization_manager_instance is None:
        _personalization_manager_instance = PersonalizationManager()
    return _personalization_manager_instance
