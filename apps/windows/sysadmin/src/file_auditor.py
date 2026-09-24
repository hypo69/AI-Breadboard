# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows File Deletion & System Auditing Engine
# =============================================================================
# Description:
#   Движок аудита файловой системы Windows:
#   1. Извлечение и сопоставление событий Windows Security Event Log:
#      - Event ID 4663 (Попытка доступа к объекту с маской DELETE / 0x10000)
#      - Event ID 4660 (Подтверждение удаления объекта по HandleId)
#      - Event ID 4656 / 4658 (Запрос и закрытие дескриптора)
#   2. Проверка и управление системной политикой аудита (auditpol File System).
#   3. Настройка и проверка списков управления доступом и аудитом (SACL).
#   4. Корреляция событий для определения точного пути, процесса и пользователя.
#
# File: file_auditor.py
# Project: ai-breadboard
# Package: apps.windows.sysadmin.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок аудита файловой системы и регистрации удаления файлов Windows."""

from __future__ import annotations

import json
import platform
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logger import logger


@dataclass
class FileAuditEvent:
    """Модель отдельного события аудита файловой системы."""

    event_id: int
    timestamp: str
    object_name: str
    object_type: str = "File"
    process_name: str = ""
    process_id: Optional[int] = None
    subject_user_name: str = ""
    subject_domain_name: str = ""
    subject_logon_id: str = ""
    access_mask: str = ""
    accesses: List[str] = field(default_factory=list)
    handle_id: str = ""
    is_deletion: bool = False
    status: str = "Success"
    raw_message: str = ""


@dataclass
class AuditPolicyStatus:
    """Статус глобальной политики аудита файловой системы Windows."""

    subcategory: str = "File System"
    success_enabled: bool = False
    failure_enabled: bool = False
    raw_output: str = ""
    is_configured: bool = False


@dataclass
class FolderSaclStatus:
    """Статус правил аудита (SACL) для конкретной папки или файла."""

    path: str
    exists: bool = False
    audit_rules_count: int = 0
    audited_principals: List[str] = field(default_factory=list)
    has_delete_audit: bool = False
    raw_acl: str = ""


class WindowsFileAuditor:
    """Класс для аудита файловой системы, чтения журнала Security и управления SACL."""

    DELETE_MASKS = {"0x10000", "%%1537", "DELETE", "Delete"}

    def __init__(self) -> None:
        """Инициализация аудитора файловой системы."""
        self.is_windows = platform.system() == "Windows"

    def get_audit_policy_status(self) -> AuditPolicyStatus:
        """Получить статус глобальной политики аудита 'File System' через auditpol.

        Returns:
            AuditPolicyStatus: Текущее состояние политики аудита.
        """
        if not self.is_windows:
            return AuditPolicyStatus(raw_output="Non-Windows platform")

        cmd = 'auditpol.exe /get /subcategory:"File System" /r'
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            raw = res.stdout.strip()
            success = False
            failure = False

            if "Success and Failure" in raw:
                success = True
                failure = True
            elif "Success" in raw:
                success = True
            elif "Failure" in raw:
                failure = True

            if not raw:
                res_txt = subprocess.run(
                    'auditpol.exe /get /subcategory:"File System"',
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True,
                )
                raw = res_txt.stdout.strip()
                if "Success and Failure" in raw or "Успех и отказ" in raw:
                    success = True
                    failure = True
                elif "Success" in raw or "Успех" in raw:
                    success = True
                elif "Failure" in raw or "Отказ" in raw:
                    failure = True

            is_configured = success or failure
            return AuditPolicyStatus(
                subcategory="File System",
                success_enabled=success,
                failure_enabled=failure,
                raw_output=raw,
                is_configured=is_configured,
            )
        except Exception as e:
            logger.error(f"Ошибка получения статуса auditpol: {e}")
            return AuditPolicyStatus(raw_output=str(e))

    def set_audit_policy(self, enable_success: bool = True, enable_failure: bool = True) -> Dict[str, Any]:
        """Включить или отключить аудит File System через auditpol.

        Args:
            enable_success: Включить аудит успешных событий.
            enable_failure: Включить аудит неуспешных попыток.

        Returns:
            Dict[str, Any]: Результат выполнения команды.
        """
        if not self.is_windows:
            return {"success": False, "error": "Non-Windows platform"}

        success_val = "enable" if enable_success else "disable"
        failure_val = "enable" if enable_failure else "disable"
        cmd = f'auditpol.exe /set /subcategory:"File System" /success:{success_val} /failure:{failure_val}'

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            success = res.returncode == 0
            return {
                "success": success,
                "command": cmd,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
            }
        except Exception as e:
            logger.error(f"Ошибка изменения политики auditpol: {e}")
            return {"success": False, "error": str(e)}

    def get_folder_sacl(self, folder_path: str) -> FolderSaclStatus:
        """Проверить наличие правил аудита (SACL) для указанной директории или файла.

        Args:
            folder_path: Путь к целевой папке или файлу.

        Returns:
            FolderSaclStatus: Статус правил SACL.
        """
        path_obj = Path(folder_path)
        if not path_obj.exists():
            return FolderSaclStatus(path=folder_path, exists=False)

        if not self.is_windows:
            return FolderSaclStatus(path=folder_path, exists=True, raw_acl="Non-Windows")

        ps_script = f"""
        $path = '{folder_path}'
        try {{
            $acl = Get-Acl -Path $path -Audit -ErrorAction Stop
            $auditRules = $acl.GetAuditRules($true, $true, [System.Security.Principal.NTAccount])
            $result = @{{
                Exists = $true
                RulesCount = $auditRules.Count
                Principals = @($auditRules | ForEach-Object {{ $_.IdentityReference.Value }})
                HasDelete = $false
                Rules = @($auditRules | ForEach-Object {{
                    if ($_.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::Delete -or 
                        $_.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles) {{
                        $result.HasDelete = $true
                    }}
                    @{{
                        Identity = $_.IdentityReference.Value
                        Rights = $_.FileSystemRights.ToString()
                        AuditFlags = $_.AuditFlags.ToString()
                        Inherited = $_.IsInherited
                    }}
                }})
            }}
            $result | ConvertTo-Json -Depth 3 -Compress
        }} catch {{
            @{{
                Exists = $true
                RulesCount = 0
                Principals = @()
                HasDelete = $false
                Error = $_.Exception.Message
            }} | ConvertTo-Json -Compress
        }}
        """

        try:
            res = subprocess.run(
                f"powershell.exe -NoProfile -NonInteractive -Command \"{ps_script}\"",
                capture_output=True,
                text=True,
                timeout=12,
                shell=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                rules_cnt = data.get("RulesCount", 0)
                principals = data.get("Principals", [])
                if isinstance(principals, str):
                    principals = [principals]
                has_delete = bool(data.get("HasDelete", False))
                rules = data.get("Rules", [])
                if isinstance(rules, list):
                    for r in rules:
                        if isinstance(r, dict):
                            rights = str(r.get("Rights", ""))
                            if "Delete" in rights or "FullControl" in rights:
                                has_delete = True

                return FolderSaclStatus(
                    path=folder_path,
                    exists=True,
                    audit_rules_count=rules_cnt,
                    audited_principals=principals,
                    has_delete_audit=has_delete,
                    raw_acl=res.stdout.strip(),
                )
        except Exception as e:
            logger.error(f"Ошибка чтения SACL для {folder_path}: {e}")

        return FolderSaclStatus(path=folder_path, exists=True, raw_acl="Failed to query SACL")

    def configure_folder_sacl(
        self, folder_path: str, principal: str = "Everyone", enable: bool = True
    ) -> Dict[str, Any]:
        """Настроить правило аудита удаления (Delete & DeleteSubdirectoriesAndFiles) для папки.

        Args:
            folder_path: Путь к целевой директории.
            principal: Учетная запись или группа (по умолчанию 'Everyone' / 'Все').
            enable: Включить или удалить правило аудита.

        Returns:
            Dict[str, Any]: Результат настройки SACL.
        """
        if not self.is_windows:
            return {"success": False, "error": "Non-Windows platform"}

        ps_script = f"""
        $path = '{folder_path}'
        $principal = '{principal}'
        $enable = ${str(enable).lower()}

        try {{
            if (-not (Test-Path $path)) {{
                throw "Path does not exist: $path"
            }}

            $acl = Get-Acl -Path $path -Audit
            $account = New-Object System.Security.Principal.NTAccount($principal)
            $rights = [System.Security.AccessControl.FileSystemRights]::Delete -bor [System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles
            $inheritance = [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit"
            $propagation = [System.Security.AccessControl.PropagationFlags]::None
            $auditFlags = [System.Security.AccessControl.AuditFlags]"Success, Failure"

            $rule = New-Object System.Security.AccessControl.FileSystemAuditRule($account, $rights, $inheritance, $propagation, $auditFlags)

            if ($enable) {{
                $acl.AddAuditRule($rule)
            }} else {{
                $acl.RemoveAuditRuleAll($rule)
            }}

            Set-Acl -Path $path -AclObject $acl
            @{{ Success = $true; Message = "SACL configured successfully for $path" }} | ConvertTo-Json -Compress
        }} catch {{
            @{{ Success = $false; Error = $_.Exception.Message }} | ConvertTo-Json -Compress
        }}
        """

        try:
            res = subprocess.run(
                f"powershell.exe -NoProfile -NonInteractive -Command \"{ps_script}\"",
                capture_output=True,
                text=True,
                timeout=15,
                shell=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                return data
            return {"success": False, "error": res.stderr.strip() or "Empty output"}
        except Exception as e:
            logger.error(f"Ошибка настройки SACL для {folder_path}: {e}")
            return {"success": False, "error": str(e)}

    def fetch_deletion_events(self, hours: int = 24, max_events: int = 100) -> List[FileAuditEvent]:
        """Извлечь и сопоставить события аудита файловой системы и удалений из журнала Security.

        Args:
            hours: Глубина выборки в часах.
            max_events: Максимальное число событий для выборки.

        Returns:
            List[FileAuditEvent]: Список распарсенных событий с сопоставлением.
        """
        if not self.is_windows:
            return []

        ps_cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        $events = Get-WinEvent -FilterHashtable @{{
            LogName = 'Security'
            Id = @(4663, 4660, 4656, 4658)
            StartTime = $startTime
        }} -MaxEvents {max_events} -ErrorAction SilentlyContinue

        if (-not $events) {{
            Write-Output "[]"
            exit 0
        }}

        $outputList = @()
        foreach ($e in $events) {{
            $xml = [xml]$e.ToXml()
            $eventData = @{{}}
            foreach ($data in $xml.Event.EventData.Data) {{
                $eventData[$data.Name] = $data.'#text'
            }}

            $outputList += @{{
                Id = $e.Id
                TimeCreated = $e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
                Message = $e.Message
                EventData = $eventData
            }}
        }}

        $outputList | ConvertTo-Json -Depth 4 -Compress
        """

        try:
            res = subprocess.run(
                f"powershell.exe -NoProfile -NonInteractive -Command \"{ps_cmd}\"",
                capture_output=True,
                text=True,
                timeout=25,
                shell=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                raw_list = data if isinstance(data, list) else [data]
                return self._parse_and_correlate_events(raw_list)
        except Exception as e:
            logger.debug(f"Ошибка запроса журнала событий Security: {e}")

        return []

    def _parse_and_correlate_events(self, raw_events: List[Dict[str, Any]]) -> List[FileAuditEvent]:
        """Разобрать и сопоставить сырые события Security Event Log.

        Args:
            raw_events: Список словарей с событиями.

        Returns:
            List[FileAuditEvent]: Нормализованные события с корреляцией 4660 + 4663.
        """
        parsed_events: List[FileAuditEvent] = []
        handle_map: Dict[str, Dict[str, Any]] = {}

        for ev in raw_events:
            if not isinstance(ev, dict):
                continue

            eid = int(ev.get("Id", 0))
            time_created = str(ev.get("TimeCreated", ""))
            msg = str(ev.get("Message", ""))
            edata = ev.get("EventData", {}) or {}

            obj_name = edata.get("ObjectName") or self._extract_field(msg, r"Object Name:\s*(.+)")
            proc_name = edata.get("ProcessName") or self._extract_field(msg, r"Process Name:\s*(.+)")
            user_name = edata.get("SubjectUserName") or self._extract_field(msg, r"Account Name:\s*(.+)")
            domain_name = edata.get("SubjectDomainName") or self._extract_field(msg, r"Account Domain:\s*(.+)")
            logon_id = edata.get("SubjectLogonId") or self._extract_field(msg, r"Logon ID:\s*(.+)")
            handle_id = edata.get("HandleId") or self._extract_field(msg, r"Handle ID:\s*(.+)")
            access_mask = edata.get("AccessMask") or self._extract_field(msg, r"Access Mask:\s*(.+)")
            access_list_str = edata.get("AccessList") or self._extract_field(msg, r"Accesses:\s*(.+)")

            raw_pid = edata.get("ProcessId") or self._extract_field(msg, r"Process ID:\s*(.+)")
            pid_val = None
            if raw_pid:
                try:
                    pid_val = int(raw_pid, 16) if str(raw_pid).startswith("0x") else int(raw_pid)
                except Exception:
                    pass

            accesses = [a.strip() for a in access_list_str.split("\n") if a.strip()] if access_list_str else []
            is_deletion = False

            if eid == 4660:
                is_deletion = True
            elif eid in (4663, 4656):
                if any(m in access_mask.lower() for m in ["0x10000", "delete"]) or any(
                    "delete" in a.lower() for a in accesses
                ):
                    is_deletion = True
                elif "DELETE" in msg:
                    is_deletion = True

            if handle_id and obj_name:
                handle_map[handle_id] = {
                    "object_name": obj_name,
                    "process_name": proc_name,
                    "process_id": pid_val,
                    "user_name": user_name,
                }

            if eid == 4660 and handle_id in handle_map:
                corr = handle_map[handle_id]
                if not obj_name:
                    obj_name = corr.get("object_name", "")
                if not proc_name:
                    proc_name = corr.get("process_name", "")
                if not pid_val:
                    pid_val = corr.get("process_id")
                if not user_name:
                    user_name = corr.get("user_name", "")

            parsed_events.append(
                FileAuditEvent(
                    event_id=eid,
                    timestamp=time_created,
                    object_name=obj_name or "(Unknown / Correlated Object)",
                    object_type=edata.get("ObjectType", "File"),
                    process_name=proc_name,
                    process_id=pid_val,
                    subject_user_name=user_name,
                    subject_domain_name=domain_name,
                    subject_logon_id=logon_id,
                    access_mask=access_mask,
                    accesses=accesses,
                    handle_id=handle_id,
                    is_deletion=is_deletion,
                    status="Success",
                    raw_message=msg,
                )
            )

        return parsed_events

    @staticmethod
    def _extract_field(text: str, pattern: str) -> str:
        """Извлечь значение поля по регулярному выражению.

        Args:
            text: Исходный текст сообщения.
            pattern: Регулярное выражение.

        Returns:
            str: Извлеченное значение или пустая строка.
        """
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""
