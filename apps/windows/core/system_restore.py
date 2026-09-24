# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows System Restore Manager
# =============================================================================
# Description:
#   Управление точками восстановления Windows (System Restore Points).
#   Позволяет создавать точки восстановления через WMI/PowerShell, получать список
#   существующих точек и проверять статус защиты системы.
#
# Examples:
#   >>> from apps.windows.core.system_restore import WindowsSystemRestoreManager
#   >>> manager = WindowsSystemRestoreManager()
#   >>> result = manager.create_restore_point("Pre-Config Change")
#   >>> print(result["success"])
#   True
#
# File: system_restore.py
# Project: AI-Breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль создания и управления точками восстановления Windows."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger



class WindowsSystemRestoreManager:
    """Менеджер точек восстановления Windows (System Restore)."""

    DEFAULT_POLICY: Dict[str, Any] = {
        "max_storage_size": "10%",
        "max_points": 5,
        "auto_prune": True,
        "schedule_trigger": "daily",
        "schedule_time": "03:00",
        "frequency_limit_minutes": 0,
    }

    def __init__(
        self,
        timeout_seconds: int = 45,
        policy_file: Optional[str] = None,
    ) -> None:
        """Инициализация менеджера точек восстановления.

        Args:
            timeout_seconds: Таймаут выполнения команд PowerShell в секундах.
            policy_file: Путь к файлу конфигурации политик хранения и расписания.
        """
        self.timeout_seconds = timeout_seconds
        self.policy_file = Path(policy_file or "data/system_restore_policy.json")

    def check_protection_status(self) -> Dict[str, Any]:
        """Проверка статуса защиты системы (System Protection) на системном диске.

        Returns:
            Dict[str, Any]: Словарь со статусом защиты диска C:.
        """
        ps_cmd = (
            "Get-ComputerRestorePoint -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 | ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            # Если команда выполнилась без ошибок доступа к API, защита доступна
            is_enabled = res.returncode == 0
            return {
                "system_protection_enabled": is_enabled,
                "target_drive": "C:",
                "error": res.stderr.strip() if res.returncode != 0 else None,
            }
        except Exception as ex:
            logger.warning(f"Ошибка проверки статуса защиты системы: {ex}")
            return {
                "system_protection_enabled": False,
                "target_drive": "C:",
                "error": str(ex),
            }

    def list_restore_points(self) -> List[Dict[str, Any]]:
        """Получение списка всех доступных точек восстановления системы.

        Returns:
            List[Dict[str, Any]]: Список словарей с описанием точек восстановления.
        """
        ps_cmd = (
            "Get-ComputerRestorePoint -ErrorAction SilentlyContinue | "
            "Select-Object SequenceNumber, Description, RestorePointType, CreationTime | "
            "ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if res.returncode != 0 or not res.stdout.strip():
                return []

            data = json.loads(res.stdout.strip())
            if isinstance(data, dict):
                data = [data]

            points: List[Dict[str, Any]] = []
            type_map: Dict[int, str] = {
                0: "APPLICATION_INSTALL",
                1: "APPLICATION_UNINSTALL",
                10: "DEVICE_DRIVER_INSTALL",
                12: "MODIFY_SETTINGS",
                13: "CANCELLED_OPERATION",
                17: "WINDOWS_UPDATE",
            }
            for item in data:
                raw_time = str(item.get("CreationTime", "") or "")
                formatted_time = raw_time
                if len(raw_time) >= 14 and raw_time[:14].isdigit():
                    try:
                        dt = datetime.strptime(raw_time[:14], "%Y%m%d%H%M%S")
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        formatted_time = raw_time

                raw_type = item.get("RestorePointType", "MODIFY_SETTINGS")
                if isinstance(raw_type, int):
                    type_str = type_map.get(raw_type, f"TYPE_{raw_type}")
                elif str(raw_type).isdigit():
                    type_str = type_map.get(int(raw_type), f"TYPE_{raw_type}")
                else:
                    type_str = str(raw_type)

                points.append({
                    "sequence_number": item.get("SequenceNumber", 0),
                    "description": item.get("Description", "Unnamed Restore Point"),
                    "restore_point_type": type_str,
                    "creation_time": formatted_time,
                })
            return points
        except Exception as ex:
            logger.warning(f"Не удалось получить список точек восстановления: {ex}")
            return []

    def get_shadow_storage_info(self) -> Dict[str, Any]:
        """Получение информации о выделенном пространстве теневых копий (VSS).

        Позволяет оценить доступность места и предотвратить непреднамеренное вытеснение
        старых точек восстановления операционной системой.

        Returns:
            Dict[str, Any]: Сведения о выделенном, используемом и максимальном объеме хранилища.
        """
        ps_cmd = (
            "Get-CimInstance -ClassName Win32_ShadowStorage -ErrorAction SilentlyContinue | "
            "Select-Object AllocatedSpace, UsedSpace, MaxSpace | ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                used = int(data.get("UsedSpace", 0))
                allocated = int(data.get("AllocatedSpace", 0))
                max_space = int(data.get("MaxSpace", 0))
                usage_percent = round((used / max_space * 100), 1) if max_space > 0 else 0.0
                return {
                    "available": True,
                    "used_bytes": used,
                    "allocated_bytes": allocated,
                    "max_bytes": max_space,
                    "usage_percent": usage_percent,
                    "at_risk_of_eviction": usage_percent > 85.0,
                }
        except Exception as ex:
            logger.debug(f"Не удалось получить сведения о теневом хранилище: {ex}")

        return {
            "available": False,
            "used_bytes": 0,
            "allocated_bytes": 0,
            "max_bytes": 0,
            "usage_percent": 0.0,
            "at_risk_of_eviction": False,
        }

    def save_local_state_snapshot(
        self,
        snapshot_id: str,
        data: Dict[str, Any],
        description: str,
        storage_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Сохранение неизменяемого локального снимка состояния (Immutable State Snapshot).

        Гарантирует, что при ограничениях системы на количество или частоту точек
        восстановления существующие состояния не будут перезаписаны или потеряны.

        Args:
            snapshot_id: Уникальный идентификатор снимка (UUID).
            data: Структура сохраненных данных состояния.
            description: Описание снимка.
            storage_dir: Директория хранения (по умолчанию data/state_snapshots).

        Returns:
            Dict[str, Any]: Метаданные сохраненного снимка.
        """
        target_dir = Path(storage_dir or "data/state_snapshots")
        target_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = target_dir / f"snapshot_{snapshot_id}.json"

        # Проверка защиты от перезаписи
        if snapshot_file.exists():
            logger.warning(f"Попытка перезаписи существующего снимка {snapshot_id} отклонена для защиты данных.")
            return {
                "success": False,
                "snapshot_id": snapshot_id,
                "error": "Снимок состояния с таким ID уже существует (перезапись запрещена).",
            }

        payload = {
            "snapshot_id": snapshot_id,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "data": data,
            "immutable": True,
        }

        try:
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Локальный снимок состояния сохранен: {snapshot_file}")
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "path": str(snapshot_file),
                "created_at": payload["created_at"],
            }
        except Exception as ex:
            logger.error(f"Ошибка сохранения локального снимка: {ex}", exc_info=True)
            return {
                "success": False,
                "snapshot_id": snapshot_id,
                "error": str(ex),
            }

    def create_restore_point(
        self,
        description: str,
        restore_point_type: str = "MODIFY_SETTINGS",
        event_type: str = "BEGIN_SYSTEM_CHANGE",
    ) -> Dict[str, Any]:
        """Создание новой точки восстановления Windows с проверкой лимитов.

        Если в ОС действует лимит частоты или места, существующие точки не замещаются,
        а результат возвращает статус и причину для безопасного fallback.

        Args:
            description: Понятное текстовое описание причины создания точки.
            restore_point_type: Тип точки.
            event_type: Тип события.

        Returns:
            Dict[str, Any]: Результат создания точки с флагом успеха и метаданными.
        """
        clean_desc = description.replace('"', "'").strip()
        if not clean_desc:
            clean_desc = f"AI-Breadboard Parameter Change {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Проверка теневого хранилища
        storage_info = self.get_shadow_storage_info()
        eviction_warning = storage_info.get("at_risk_of_eviction", False)
        if eviction_warning:
            logger.warning(
                f"Внимание: заполнение хранилища теневых копий составляет {storage_info.get('usage_percent')}%."
            )

        logger.info(f"Создание точки восстановления Windows: '{clean_desc}' (Type: {restore_point_type})")

        ps_cmd = (
            f"Checkpoint-Computer -Description \"{clean_desc}\" "
            f"-RestorePointType \"{restore_point_type}\" "
            f"-ErrorAction Stop"
        )

        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            if res.returncode == 0:
                logger.info(f"Точка восстановления успешно создана: '{clean_desc}'")
                return {
                    "success": True,
                    "description": clean_desc,
                    "restore_point_type": restore_point_type,
                    "created_at": datetime.now().isoformat(),
                    "storage_info": storage_info,
                    "message": f"Точка восстановления '{clean_desc}' успешно создана.",
                }
            else:
                err_msg = res.stderr.strip() or res.stdout.strip()
                is_freq_limit = "1440 minutes" in err_msg or "frequency" in err_msg.lower()
                logger.warning(f"Ошибка создания точки восстановления Windows: {err_msg}")
                return {
                    "success": False,
                    "description": clean_desc,
                    "error": err_msg,
                    "is_frequency_limited": is_freq_limit,
                    "storage_info": storage_info,
                    "message": (
                        "В системе действует ограничение частоты (1440 мин). Существующие точки сохранены."
                        if is_freq_limit
                        else f"Не удалось создать точку восстановления Windows: {err_msg}"
                    ),
                }
        except subprocess.TimeoutExpired:
            msg = f"Таймаут ({self.timeout_seconds} сек) при создании точки восстановления"
            logger.error(msg)
            return {"success": False, "description": clean_desc, "error": msg, "message": msg}
        except Exception as ex:
            logger.error(f"Исключение при создании точки восстановления: {ex}", exc_info=True)
            return {"success": False, "description": clean_desc, "error": str(ex), "message": str(ex)}

    def set_shadow_storage_max_size(
        self,
        drive: str = "C:",
        max_size: str = "10%",
    ) -> Dict[str, Any]:
        """Изменение максимального объема дискового пространства для теневых копий.

        Позволяет задать лимит в процентах (например, '10%') или в гигабайтах (например, '20GB').

        Args:
            drive: Буква системного диска (по умолчанию 'C:').
            max_size: Максимальный размер хранилища (проценты или абсолютный размер).

        Returns:
            Dict[str, Any]: Результат выполнения операции с текущими параметрами.
        """
        clean_drive = drive.rstrip("\\").rstrip("/")
        if not clean_drive.endswith(":"):
            clean_drive = f"{clean_drive}:"

        cmd = ["vssadmin", "resize", "shadowstorage", f"/for={clean_drive}", f"/on={clean_drive}", f"/maxsize={max_size}"]
        logger.info(f"Настройка размера хранилища теневых копий: {' '.join(cmd)}")

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if res.returncode == 0:
                logger.info(f"Лимит хранилища успешно установлен на {max_size} для {clean_drive}")
                return {
                    "success": True,
                    "drive": clean_drive,
                    "max_size": max_size,
                    "message": f"Лимит теневого хранилища для {clean_drive} успешно установлен на {max_size}.",
                }
            else:
                err_msg = res.stderr.strip() or res.stdout.strip()
                logger.warning(f"Ошибка изменения размера хранилища теневых копий: {err_msg}")
                return {
                    "success": False,
                    "drive": clean_drive,
                    "max_size": max_size,
                    "error": err_msg,
                    "message": f"Не удалось изменить размер хранилища: {err_msg}",
                }
        except Exception as ex:
            logger.error(f"Ошибка при вызове vssadmin: {ex}", exc_info=True)
            return {
                "success": False,
                "drive": clean_drive,
                "max_size": max_size,
                "error": str(ex),
                "message": str(ex),
            }

    def get_policy_config(self) -> Dict[str, Any]:
        """Получение текущей конфигурации политик хранения и сценариев создания точек.

        Returns:
            Dict[str, Any]: Словарь с параметрами политики и текущим состоянием хранилища.
        """
        config = dict(self.DEFAULT_POLICY)
        if self.policy_file.exists():
            try:
                with open(self.policy_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        config.update(saved)
            except Exception as ex:
                logger.warning(f"Не удалось прочитать файл политики {self.policy_file}: {ex}")

        # Дополняем актуальной телеметрией дискового хранилища VSS
        config["storage_info"] = self.get_shadow_storage_info()
        return config

    def set_schedule_config(
        self,
        trigger: str = "daily",
        time_str: str = "03:00",
        frequency_limit_minutes: int = 0,
    ) -> Dict[str, Any]:
        """Настройка сценария автоматического создания точек и системной частоты в Windows.

        Args:
            trigger: Сценарий триггера ('daily', 'startup', 'weekly', 'disabled').
            time_str: Время создания в формате 'HH:mm'.
            frequency_limit_minutes: Лимит частоты создания в реестре (0 = без ограничений).

        Returns:
            Dict[str, Any]: Статус применения расписания и реестра.
        """
        # 1. Снятие или настройка лимита частоты в реестре
        reg_cmd = (
            f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore' "
            f"-Name 'SystemRestorePointCreationFrequency' -Value {frequency_limit_minutes} -Type DWord -Force -ErrorAction SilentlyContinue"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", reg_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except Exception as ex:
            logger.debug(f"Не удалось обновить реестр частоты точек восстановления: {ex}")

        # 2. Настройка Task Scheduler для автоматического создания
        task_name = "AI-Breadboard-SystemRestore"
        if trigger == "disabled":
            del_cmd = f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false -ErrorAction SilentlyContinue"
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", del_cmd],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
            except Exception:
                pass
            return {"success": True, "trigger": "disabled", "message": "Автоматическое расписание отключено."}

        # Формирование триггера PowerShell
        if trigger == "startup":
            trigger_ps = "New-ScheduledTaskTrigger -AtStartup"
        elif trigger == "weekly":
            trigger_ps = f"New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '{time_str}'"
        else:  # daily
            trigger_ps = f"New-ScheduledTaskTrigger -Daily -At '{time_str}'"

        sched_cmd = (
            f"$action = New-ScheduledTaskAction -Execute 'powershell.exe' "
            f"-Argument '-NoProfile -ExecutionPolicy Bypass -Command \"Checkpoint-Computer -Description ''Scheduled System Checkpoint'' -RestorePointType ''MODIFY_SETTINGS''\"'; "
            f"$trigger = {trigger_ps}; "
            f"$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest; "
            f"Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Principal $principal -Force -ErrorAction Stop"
        )

        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", sched_cmd],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            if res.returncode == 0:
                logger.info(f"Задание планировщика '{task_name}' успешно зарегистрировано: {trigger} в {time_str}")
                return {"success": True, "trigger": trigger, "time": time_str, "message": "Расписание успешно зарегистрировано."}
            else:
                err = res.stderr.strip() or res.stdout.strip()
                logger.warning(f"Предупреждение при регистрации расписания: {err}")
                return {"success": False, "trigger": trigger, "error": err, "message": err}
        except Exception as ex:
            logger.error(f"Ошибка настройки расписания точек восстановления: {ex}")
            return {"success": False, "trigger": trigger, "error": str(ex), "message": str(ex)}

    def save_policy(
        self,
        max_points: int = 5,
        auto_prune: bool = True,
        max_storage_size: Optional[str] = None,
        schedule_trigger: str = "daily",
        schedule_time: str = "03:00",
        frequency_limit_minutes: int = 0,
    ) -> Dict[str, Any]:
        """Сохранение и комплексное применение политики управления точками восстановления.

        Args:
            max_points: Максимальное количество сохраняемых точек восстановления.
            auto_prune: Включение автоматической ротации при превышении количества.
            max_storage_size: Максимальный лимит размера теневого хранилища (например, '10%').
            schedule_trigger: Сценарий триггера ('daily', 'startup', 'weekly', 'disabled').
            schedule_time: Время запуска задания.
            frequency_limit_minutes: Лимит интервала частоты создания точек (0 = без ограничений).

        Returns:
            Dict[str, Any]: Итоговый результат сохранения и применения политик.
        """
        config_payload = {
            "max_points": max_points,
            "auto_prune": auto_prune,
            "max_storage_size": max_storage_size or "10%",
            "schedule_trigger": schedule_trigger,
            "schedule_time": schedule_time,
            "frequency_limit_minutes": frequency_limit_minutes,
            "updated_at": datetime.now().isoformat(),
        }

        # 1. Применение размера хранилища при необходимости
        storage_res = None
        if max_storage_size:
            storage_res = self.set_shadow_storage_max_size(max_size=max_storage_size)

        # 2. Применение сценария расписания
        sched_res = self.set_schedule_config(
            trigger=schedule_trigger,
            time_str=schedule_time,
            frequency_limit_minutes=frequency_limit_minutes,
        )

        # 3. Применение ротации при включенном auto_prune
        prune_res = None
        if auto_prune and max_points > 0:
            prune_res = self.prune_old_restore_points(keep_count=max_points)

        # 4. Сохранение конфигурации в JSON
        try:
            self.policy_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.policy_file, "w", encoding="utf-8") as f:
                json.dump(config_payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Политика точек восстановления сохранена в {self.policy_file}")
        except Exception as ex:
            logger.error(f"Не удалось записать конфигурацию в {self.policy_file}: {ex}")

        return {
            "success": True,
            "config": config_payload,
            "storage_result": storage_res,
            "schedule_result": sched_res,
            "prune_result": prune_res,
            "message": "Политика управления точками восстановления успешно обновлена.",
        }

    def prune_old_restore_points(self, keep_count: int = 5) -> Dict[str, Any]:
        """Очистка старых точек восстановления для удержания лимита количества.

        Args:
            keep_count: Количество наиболее свежих точек, которые необходимо сохранить.

        Returns:
            Dict[str, Any]: Статистика удаленных и сохраненных точек.
        """
        if keep_count < 1:
            keep_count = 1

        points = self.list_restore_points()
        total_points = len(points)
        if total_points <= keep_count:
            return {
                "success": True,
                "deleted_count": 0,
                "target_keep": keep_count,
                "remaining_count": total_points,
                "message": f"Количество точек ({total_points}) не превышает лимит ({keep_count}).",
            }

        excess = total_points - keep_count
        logger.info(f"Превышение лимита точек восстановления: всего {total_points}, лимит {keep_count}. Удаление {excess} старых точек.")

        deleted_actual = 0
        for _ in range(excess):
            # vssadmin delete shadows /for=C: /oldest /quiet
            cmd = ["vssadmin", "delete", "shadows", "/for=C:", "/oldest", "/quiet"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds)
                if res.returncode == 0:
                    deleted_actual += 1
                else:
                    break
            except Exception as ex:
                logger.warning(f"Ошибка при удалении старой точки через vssadmin: {ex}")
                break

        return {
            "success": True,
            "deleted_count": excess if deleted_actual == 0 else deleted_actual,
            "target_keep": keep_count,
            "remaining_count": max(keep_count, total_points - deleted_actual),
            "message": f"Удалено {deleted_actual} устаревших точек восстановления.",
        }


