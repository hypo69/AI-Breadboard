# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Security & Persistence Audit Collector
# =============================================================================
# Description:
#   Аудит состояния безопасности Windows: Microsoft Defender, брандмауэр,
#   UAC, Secure Boot, TPM, изоляция ядра (HVCI) и механизмы персистентности (WMI/IFEO).
#
# Examples:
#   >>> from apps.windows.core.modules.security_collector import SecurityCollector
#   >>> collector = SecurityCollector()
#   >>> result = collector.collect()
#
# File: security_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита безопасности и механизмов персистентности Windows."""

from __future__ import annotations

import json
import subprocess
import time
import winreg
from typing import Any, Dict, List

from src.logger import logger
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


class SecurityCollector:
    """Коллектор фактов о конфигурации безопасности и персистентности."""

    def collect(self) -> DomainAuditResult:
        """Сбор данных о безопасности Windows.

        Returns:
            DomainAuditResult: Результат аудита безопасности.
        """
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        metrics: Dict[str, Any] = {}

        # 1. Проверка UAC (User Account Control)
        uac_enabled = self._check_uac()
        metrics["uac_enabled"] = uac_enabled
        if not uac_enabled:
            findings.append(
                AuditFinding(
                    domain="security",
                    category="uac",
                    title="Контроль учетных записей (UAC) отключен",
                    description="Отключение UAC снижает уровень защиты от несанкционированного повышения привилегий.",
                    severity=RiskLevel.CRITICAL,
                    actions=[
                        RemediationAction(
                            action_id="enable_uac",
                            action_type=ActionType.APPLY_CONFIG,
                            title="Включить UAC",
                            description="Установка параметра EnableLUA в 1 в реестре",
                            target="HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System",
                            risk=RiskLevel.CAUTION,
                            requires_reboot=True,
                            execution_command="Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'EnableLUA' -Value 1",
                        )
                    ]
                )
            )

        # 2. Комплексный аудит Microsoft Defender Antivirus
        from apps.windows.core.defender_manager import DefenderManager
        defender_mgr = DefenderManager()
        defender_status = defender_mgr.get_detailed_status()
        defender_prefs = defender_mgr.get_preferences()
        metrics["defender"] = {**defender_status, **defender_prefs}

        # Проверка: Real-Time Protection
        if not defender_status.get("realtime_protection", False):
            findings.append(
                AuditFinding(
                    domain="security",
                    category="antivirus",
                    title="Защита в реальном времени Defender отключена",
                    description="Real-Time Protection выключена, что подвергает систему риску заражения вредоносным ПО.",
                    severity=RiskLevel.CRITICAL,
                    evidence=defender_status,
                    actions=[
                        RemediationAction(
                            action_id="enable_defender_realtime",
                            action_type=ActionType.APPLY_CONFIG,
                            title="Включить Real-Time Protection Defender",
                            description="Включение защиты файловой системы и процессов в реальном времени",
                            target="Microsoft Defender",
                            risk=RiskLevel.SAFE,
                            execution_command="Set-MpPreference -DisableRealtimeMonitoring $false",
                        )
                    ],
                )
            )

        # Проверка: Cloud Protection
        if not defender_status.get("cloud_protection_enabled", False):
            findings.append(
                AuditFinding(
                    domain="security",
                    category="cloud_protection",
                    title="Облачная защита Defender (MAPS) отключена",
                    description="Cloud-delivered protection отключена. Система не получает оперативную информацию о новейших угрозах от Microsoft Threat Intelligence.",
                    severity=RiskLevel.CAUTION,
                    actions=[
                        RemediationAction(
                            action_id="enable_defender_cloud",
                            action_type=ActionType.APPLY_CONFIG,
                            title="Включить Cloud Protection (MAPS Advanced)",
                            description="Включение расширенной облачной защиты Microsoft Defender",
                            target="Microsoft Defender",
                            risk=RiskLevel.SAFE,
                            execution_command="Set-MpPreference -MAPSReporting Advanced",
                        )
                    ],
                )
            )

        # Проверка: Потенциально опасные исключения
        suspicious_ex = defender_prefs.get("exclusions", {}).get("suspicious_paths", [])
        if suspicious_ex:
            findings.append(
                AuditFinding(
                    domain="security",
                    category="exclusions_risk",
                    title=f"Обнаружены рискованные исключения Defender ({len(suspicious_ex)})",
                    description=f"В исключения добавлены критические или глобальные пути: {', '.join(suspicious_ex[:3])}. Вредоносный код в этих каталогах не проверяется.",
                    severity=RiskLevel.CRITICAL if any("C:" in p for p in suspicious_ex) else RiskLevel.CAUTION,
                    evidence={"suspicious_exclusions": suspicious_ex},
                )
            )

        # Проверка: Защита от программ-вымогателей (Controlled Folder Access)
        if defender_status.get("controlled_folder_access") == "disabled":
            findings.append(
                AuditFinding(
                    domain="security",
                    category="ransomware_protection",
                    title="Controlled Folder Access (Защита от Ransomware) отключена",
                    description="Защита пользовательских папок (Документы, Рабочий стол) от шифровальщиков и несанкционированного изменения выключена.",
                    severity=RiskLevel.INFO,
                    actions=[
                        RemediationAction(
                            action_id="enable_defender_cfa_audit",
                            action_type=ActionType.APPLY_CONFIG,
                            title="Включить Controlled Folder Access в режиме аудита",
                            description="Включение CFA в режиме AuditMode для безопасной оценки без блокировок",
                            target="Microsoft Defender",
                            risk=RiskLevel.SAFE,
                            execution_command="Set-MpPreference -EnableControlledFolderAccess AuditMode",
                        )
                    ],
                )
            )

        # Проверка: PUA Protection
        if defender_prefs.get("pua_protection") == "disabled":
            findings.append(
                AuditFinding(
                    domain="security",
                    category="pua_protection",
                    title="Защита от нежелательного ПО (PUA) отключена",
                    description="Defender не блокирует установку сомнительных рекламных модулей, трекеров и bundle-приложений.",
                    severity=RiskLevel.INFO,
                    actions=[
                        RemediationAction(
                            action_id="enable_defender_pua",
                            action_type=ActionType.APPLY_CONFIG,
                            title="Включить защиту от PUA",
                            description="Включение блокировки Potentially Unwanted Applications",
                            target="Microsoft Defender",
                            risk=RiskLevel.SAFE,
                            execution_command="Set-MpPreference -PUAProtection Enabled",
                        )
                    ],
                )
            )

        # 3. Проверка механизмов персистентности (WMI Event Subscriptions, Image File Execution Options, AppInit DLLs)
        persistence_mechanisms = self._check_persistence_mechanisms()
        metrics["persistence_mechanisms"] = persistence_mechanisms
        
        for mech_type, items in persistence_mechanisms.items():
            if items:
                findings.append(
                    AuditFinding(
                        domain="security",
                        category="persistence_risk",
                        title=f"Обнаружены потенциальные механизмы персистентности: {mech_type}",
                        description=f"Найдено {len(items)} записей в {mech_type}, требующих проверки на безопасность.",
                        severity=RiskLevel.CAUTION if len(items) <= 3 else RiskLevel.CRITICAL,
                        evidence={"items": items[:5]},
                    )
                )

        duration_ms = (time.perf_counter() - start_t) * 1000
        status = "ok"
        if any(f.severity == RiskLevel.CRITICAL for f in findings):
            status = "critical"
        elif any(f.severity == RiskLevel.CAUTION for f in findings):
            status = "warning"

        return DomainAuditResult(
            domain_name="security",
            title_ru="Безопасность и персистентность",
            status=status,
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )

    def _check_uac(self) -> bool:
        """Проверка статуса UAC (EnableLUA)."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            ) as key:
                val, _ = winreg.QueryValueEx(key, "EnableLUA")
                return bool(val)
        except OSError:
            return True

    def _get_defender_status(self) -> Dict[str, Any]:
        """Получение статуса Defender через PowerShell Get-MpComputerStatus."""
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, AntivirusEnabled, AntispywareEnabled, AMServiceEnabled, IoavProtectionEnabled | ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                return {
                    "realtime_protection": data.get("RealTimeProtectionEnabled", True),
                    "antivirus_enabled": data.get("AntivirusEnabled", True),
                    "service_enabled": data.get("AMServiceEnabled", True),
                }
        except Exception as e:
            logger.debug(f"Ошибка при вызове Get-MpComputerStatus: {e}")
        return {"realtime_protection": True, "antivirus_enabled": True}

    def _check_persistence_mechanisms(self) -> Dict[str, List[str]]:
        """Проверка механизмов персистентности (WMI, IFEO, AppInit)."""
        mechanisms: Dict[str, List[str]] = {
            "WMI_Event_Subscriptions": [],
            "Image_File_Execution_Options": [],
            "AppInit_DLLs": [],
            "Run_Registry_Keys": [],
        }
        
        # 1. Проверка Image File Execution Options (IFEO)
        try:
            ifeo_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ifeo_path) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        mechanisms["Image_File_Execution_Options"].append(subkey_name)
                        i += 1
                    except OSError:
                        break
        except (OSError, PermissionError):
            pass
        
        # 2. Проверка AppInit DLLs
        try:
            appinit_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, appinit_path) as key:
                try:
                    appinit_dlls, _ = winreg.QueryValueEx(key, "AppInit_DLLs")
                    if appinit_dlls:
                        mechanisms["AppInit_DLLs"] = appinit_dlls.split(";")
                except OSError:
                    pass
        except (OSError, PermissionError):
            pass
        
        # 3. Проверка WMI Event Subscriptions через PowerShell
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-WmiObject -Class __EventFilter | Select-Object -ExpandProperty Name | ConvertTo-Json -Compress",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, list):
                    mechanisms["WMI_Event_Subscriptions"] = data[:10]  # Только первые 10
                elif isinstance(data, str):
                    mechanisms["WMI_Event_Subscriptions"] = [data]
        except Exception as e:
            logger.debug(f"Ошибка при проверке WMI: {e}")
        
        return mechanisms
