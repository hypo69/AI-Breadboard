# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Microsoft Defender Antivirus Manager & CLI Interface
# =============================================================================
# Description:
#   Служба взаимодействия с Microsoft Defender Antivirus через утилиту MpCmdRun.exe
#   и командлеты PowerShell Defender. Позволяет запускать сканирования (Quick/Full/Custom),
#   обновлять сигнатуры, управлять Controlled Folder Access (CFA), PUA и ASR правилами.
#
# Examples:
#   >>> from apps.windows.core.defender_manager import DefenderManager
#   >>> mgr = DefenderManager()
#   >>> status = mgr.get_detailed_status()
#   >>> threats = mgr.get_threat_detections()
#
# File: defender_manager.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер управления и телеметрии Microsoft Defender Antivirus."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

from logger import logger


class DefenderManager:
    """Интерфейс управления проверками, обновлением и настройками Defender."""

    # Известные ASR правила Microsoft (Attack Surface Reduction)
    ASR_RULES_MAP = {
        "56a863a9-875e-4185-98a7-b882c60b5ce5": "Блокировка создания дочерних процессов из Office",
        "756e358e-7973-4037-9730-ff7373792b66": "Блокировка создания исполняемого контента в Office",
        "3b576479-a461-4c6c-b714-2d4e02202b7f": "Блокировка запуска скриптов из исполняемых файлов Office",
        "d4f940ab-401b-4efc-aadc-ad5f3c50688a": "Блокировка выполнения подозрительных скриптов (obfuscated)",
        "92e588db-1e6f-432e-a60d-98517fb36cb7": "Блокировка вызовов Win32 API из макросов Office",
        "b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4": "Блокировка инъекции кода в другие процессы",
        "01443614-cd74-433a-b99e-2ecdc07bfc25": "Блокировка кражи учетных данных из подсистемы LSASS",
        "c1db55ab-c21a-4637-bb3f-a12568109d35": "Блокировка создания процессов через WMI/PSExec",
        "d3e037e1-3eb8-44c8-a917-57927947596d": "Блокировка запуска неподписанных исполняемых файлов на USB",
    }

    def __init__(self) -> None:
        """Инициализация менеджера и поиск MpCmdRun.exe."""
        self.mpcmdrun_path = self._find_mpcmdrun()

    def _find_mpcmdrun(self) -> str:
        """Поиск пути к утилите MpCmdRun.exe."""
        # 1. Проверяем каталог платформы Defender
        program_data_platform = r"C:\ProgramData\Microsoft\Windows Defender\Platform"
        if os.path.exists(program_data_platform):
            try:
                subdirs = sorted(os.listdir(program_data_platform), reverse=True)
                for sub in subdirs:
                    candidate = os.path.join(program_data_platform, sub, "MpCmdRun.exe")
                    if os.path.isfile(candidate):
                        return candidate
            except Exception as e:
                logger.debug(f"Ошибка при поиске MpCmdRun в Platform: {e}")

        # 2. Проверяем Program Files
        std_path = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
        if os.path.isfile(std_path):
            return std_path

        # 3. Проверяем PATH
        which_path = shutil.which("MpCmdRun.exe")
        if which_path:
            return which_path

        return "MpCmdRun.exe"

    def get_detailed_status(self) -> Dict[str, Any]:
        """Получение детального статуса Microsoft Defender через PowerShell Get-MpComputerStatus.

        Returns:
            Dict[str, Any]: Словарь параметров защиты и версий движка/сигнатур.
        """
        ps_cmd = (
            "Get-MpComputerStatus | Select-Object "
            "RealTimeProtectionEnabled, AntivirusEnabled, AntispywareEnabled, "
            "AMServiceEnabled, IoavProtectionEnabled, BehaviorMonitorEnabled, "
            "OnAccessProtectionEnabled, MAPSReporting, FullScanRequired, "
            "RebootRequired, QuickScanSignatureVersion, AntivirusSignatureVersion, "
            "AntivirusSignatureLastUpdated, EngineVersion, AntispywareSignatureVersion, "
            "ControlledFolderAccessEnabled, TamperProtectionSource "
            "| ConvertTo-Json -Compress"
        )
        data = self._run_powershell_json(ps_cmd)
        if not data:
            return {
                "realtime_protection": False,
                "antivirus_enabled": False,
                "cloud_protection_enabled": False,
                "tamper_protection": False,
                "engine_version": "N/A",
                "signature_version": "N/A",
            }

        maps_val = data.get("MAPSReporting", 0)
        cloud_active = maps_val in (1, 2)  # 1 = Basic MAPS, 2 = Advanced MAPS

        cfa_raw = data.get("ControlledFolderAccessEnabled", 0)
        cfa_mode = "disabled"
        if cfa_raw == 1:
            cfa_mode = "enabled"
        elif cfa_raw == 2:
            cfa_mode = "audit"

        return {
            "realtime_protection": bool(data.get("RealTimeProtectionEnabled", False)),
            "antivirus_enabled": bool(data.get("AntivirusEnabled", False)),
            "antispyware_enabled": bool(data.get("AntispywareEnabled", False)),
            "service_enabled": bool(data.get("AMServiceEnabled", False)),
            "ioav_protection": bool(data.get("IoavProtectionEnabled", False)),
            "behavior_monitor": bool(data.get("BehaviorMonitorEnabled", False)),
            "on_access_protection": bool(data.get("OnAccessProtectionEnabled", False)),
            "cloud_protection_enabled": cloud_active,
            "maps_reporting_level": maps_val,
            "controlled_folder_access": cfa_mode,
            "tamper_protection_source": data.get("TamperProtectionSource", "Default"),
            "full_scan_required": bool(data.get("FullScanRequired", False)),
            "reboot_required": bool(data.get("RebootRequired", False)),
            "engine_version": str(data.get("EngineVersion", "Unknown")),
            "signature_version": str(data.get("AntivirusSignatureVersion", "Unknown")),
            "signature_last_updated": str(data.get("AntivirusSignatureLastUpdated", "Unknown")),
        }

    def get_preferences(self) -> Dict[str, Any]:
        """Получение конфигурации исключений, PUA и ASR правил через Get-MpPreference.

        Returns:
            Dict[str, Any]: Исключения, PUA-режим и состояние правил снижения поверхности атаки.
        """
        ps_cmd = (
            "Get-MpPreference | Select-Object "
            "ExclusionPath, ExclusionExtension, ExclusionProcess, "
            "PUAProtection, AttackSurfaceReductionRules_Ids, "
            "AttackSurfaceReductionRules_Actions, ControlledFolderAccessProtectedFolders "
            "| ConvertTo-Json -Compress"
        )
        data = self._run_powershell_json(ps_cmd)
        if not data:
            return {
                "exclusions": {"paths": [], "extensions": [], "processes": []},
                "pua_protection": "disabled",
                "asr_rules": [],
                "cfa_protected_folders": [],
            }

        # PUA
        pua_raw = data.get("PUAProtection", 0)
        pua_status = "disabled"
        if pua_raw == 1:
            pua_status = "enabled"
        elif pua_raw == 2:
            pua_status = "audit"

        # Исключения
        ex_paths = self._normalize_list(data.get("ExclusionPath"))
        ex_exts = self._normalize_list(data.get("ExclusionExtension"))
        ex_procs = self._normalize_list(data.get("ExclusionProcess"))

        # Анализ подозрительных/опасных исключений
        suspicious_exclusions: List[str] = []
        for path in ex_paths:
            p_upper = path.upper().rstrip("\\")
            if p_upper in ("C:", "C:\\", "D:", "D:\\") or any(
                p_upper.endswith(wild) for wild in ("\\*", "\\TEMP", "\\TEMP\\*", "\\APPDATA", "\\APPDATA\\*")
            ):
                suspicious_exclusions.append(path)

        # ASR Rules
        asr_ids = self._normalize_list(data.get("AttackSurfaceReductionRules_Ids"))
        asr_actions = self._normalize_list(data.get("AttackSurfaceReductionRules_Actions"))
        asr_rules: List[Dict[str, Any]] = []
        for idx, rule_id in enumerate(asr_ids):
            action_code = asr_actions[idx] if idx < len(asr_actions) else 0
            action_str = "Disabled"
            if action_code == 1:
                action_str = "Block"
            elif action_code == 2:
                action_str = "Audit"
            elif action_code == 6:
                action_str = "Warn"
            
            asr_rules.append({
                "rule_id": rule_id,
                "name": self.ASR_RULES_MAP.get(rule_id.lower(), "Кастомное ASR правило"),
                "action": action_str,
                "action_code": action_code,
            })

        cfa_folders = self._normalize_list(data.get("ControlledFolderAccessProtectedFolders"))

        return {
            "exclusions": {
                "paths": ex_paths,
                "extensions": ex_exts,
                "processes": ex_procs,
                "suspicious_paths": suspicious_exclusions,
            },
            "pua_protection": pua_status,
            "asr_rules": asr_rules,
            "cfa_protected_folders": cfa_folders,
        }

    def get_threat_detections(self) -> List[Dict[str, Any]]:
        """Получение последних зафиксированных угроз через Get-MpThreatDetection.

        Returns:
            List[Dict[str, Any]]: Список инцидентов обнаружения вредоносного ПО.
        """
        ps_cmd = (
            "Get-MpThreatDetection | Select-Object -First 20 "
            "ThreatID, ThreatName, InitialDetectionTime, Resources, "
            "ActionSuccess, CleaningActionID, CurrentThreatExecutionStatusID "
            "| ConvertTo-Json -Compress"
        )
        data = self._run_powershell_json(ps_cmd)
        if not data:
            return []

        threats_raw = data if isinstance(data, list) else [data]
        results: List[Dict[str, Any]] = []
        for t in threats_raw:
            results.append({
                "threat_id": str(t.get("ThreatID", "")),
                "threat_name": t.get("ThreatName", "Unknown"),
                "detected_at": str(t.get("InitialDetectionTime", "")),
                "resources": self._normalize_list(t.get("Resources")),
                "action_success": bool(t.get("ActionSuccess", True)),
            })
        return results

    def start_scan(self, scan_type: str = "quick", custom_path: Optional[str] = None) -> Dict[str, Any]:
        """Запуск сканирования через MpCmdRun.exe.

        Args:
            scan_type: Тип сканирования ('quick', 'full', 'custom').
            custom_path: Путь к файлу или папке (для scan_type='custom').

        Returns:
            Dict[str, Any]: Результат запуска и код возврата.
        """
        st = scan_type.lower()
        args = [self.mpcmdrun_path, "-Scan"]

        if st == "quick":
            args.extend(["-ScanType", "1"])
        elif st == "full":
            args.extend(["-ScanType", "2"])
        elif st == "custom":
            if not custom_path or not os.path.exists(custom_path):
                return {"success": False, "error": f"Путь не найден: {custom_path}"}
            args.extend(["-ScanType", "3", "-File", custom_path])
        else:
            return {"success": False, "error": f"Неизвестный тип сканирования: {scan_type}"}

        try:
            logger.info(f"Запуск Defender Scan: {' '.join(args)}")
            res = subprocess.run(args, capture_output=True, text=True, timeout=120)
            success = res.returncode in (0, 2)  # 0 = No threats, 2 = Threats found and resolved
            return {
                "success": success,
                "return_code": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "scan_type": scan_type,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": True,
                "message": "Сканирование выполняется в фоновом режиме",
                "scan_type": scan_type,
            }
        except Exception as e:
            logger.error(f"Ошибка при вызове MpCmdRun: {e}")
            return {"success": False, "error": str(e)}

    def update_signatures(self) -> Dict[str, Any]:
        """Принудительное обновление баз сигнатур через MpCmdRun.exe -SignatureUpdate.

        Returns:
            Dict[str, Any]: Статус обновления.
        """
        try:
            cmd = [self.mpcmdrun_path, "-SignatureUpdate"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "success": res.returncode == 0,
                "return_code": res.returncode,
                "output": res.stdout.strip() or res.stderr.strip(),
            }
        except Exception as e:
            logger.error(f"Ошибка обновления сигнатур: {e}")
            return {"success": False, "error": str(e)}

    def set_pua_protection(self, mode: str) -> Dict[str, Any]:
        """Управление защитой от нежелательного ПО (PUA).

        Args:
            mode: 'enabled' (1), 'audit' (2), или 'disabled' (0).
        """
        val_map = {"enabled": 1, "audit": 2, "disabled": 0}
        val = val_map.get(mode.lower(), 1)
        ps_cmd = f"Set-MpPreference -PUAProtection {val}"
        return self._run_powershell_admin(ps_cmd)

    def set_controlled_folder_access(self, mode: str) -> Dict[str, Any]:
        """Управление защитой от вымогателей Controlled Folder Access (CFA).

        Args:
            mode: 'enabled' (1), 'audit' (2), или 'disabled' (0).
        """
        val_map = {"enabled": 1, "audit": 2, "disabled": 0}
        val = val_map.get(mode.lower(), 1)
        ps_cmd = f"Set-MpPreference -EnableControlledFolderAccess {val}"
        return self._run_powershell_admin(ps_cmd)

    def _run_powershell_json(self, command: str) -> Optional[Any]:
        """Выполнение PowerShell команды с возвратом распарсенного JSON."""
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout.strip())
        except Exception as e:
            logger.debug(f"Ошибка PowerShell JSON '{command[:40]}...': {e}")
        return None

    def _run_powershell_admin(self, command: str) -> Dict[str, Any]:
        """Выполнение административной команды PowerShell."""
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _normalize_list(self, val: Any) -> List[str]:
        """Нормализация результата в список строк."""
        if not val:
            return []
        if isinstance(val, list):
            return [str(item) for item in val if item]
        return [str(val)]


__all__ = ["DefenderManager"]