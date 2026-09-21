# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Services Matrix Audit Collector
# =============================================================================
# Description:
#   Аудит системных служб Windows, инвентаризация типов запуска, аккаунтов
#   и выявление осиротевших служб (ссылающихся на удаленные исполняемые файлы).
#   Использует нативный Service Control Manager API (advapi32.dll) и реестр.
#
# Examples:
#   >>> from apps.windows.core.modules.services_collector import ServicesCollector
#   >>> collector = ServicesCollector()
#   >>> result = collector.collect()
#
# File: services_collector.py
# Project: ai-breadboard
# Package: apps.windows.core.modules
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Коллектор аудита служб Windows с поддержкой нативного SCM API."""

from __future__ import annotations

import os
import time
import winreg
from typing import Any, Dict, List

import psutil

from src.logger import logger
from apps.windows.api.scm import ServiceControlManager
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel


PROTECTED_SYSTEM_SERVICES = {
    "appxsvc", "bfe", "rpcss", "dcomlaunch", "plugplay", "lanmanworkstation",
    "lanmanserver", "dnscache", "dhcp", "mpssvc", "windefend", "wuauserv",
    "cryptsvc", "eventlog", "nsi", "schedule", "samss", "lsass", "gpsvc",
    "bits", "wsearch", "trustedinstaller", "spooler", "sens", "profsvc",
}


def _resolve_service_binary(image_path: str) -> str:
    """Разрешает реальный путь к исполняемому файлу службы с отсечением параметров.

    Args:
        image_path: Исходная строка ImagePath из реестра.

    Returns:
        str: Абсолютный путь к бинарному файлу или пустая строка.
    """
    if not image_path:
        return ""

    raw = os.path.expandvars(image_path.strip())
    if raw.startswith(r"\??\\"):
        raw = raw[4:]

    # 1. Если путь заключен в кавычки: "C:\Path\To\File.exe" -arg
    if raw.startswith('"'):
        end_idx = raw.find('"', 1)
        if end_idx != -1:
            candidate = raw[1:end_idx].strip()
            if os.path.exists(candidate):
                return candidate
            raw = candidate

    # 2. Если расширение .exe/.sys/.dll присутствует в строке
    for ext in (".exe", ".sys", ".dll"):
        pos = raw.lower().find(ext)
        if pos != -1:
            candidate = raw[: pos + len(ext)].strip().strip('"')
            if os.path.exists(candidate):
                return candidate
            # Проверка в стандартных системных директориях, если путь относительный
            if not os.path.isabs(candidate) or not os.path.dirname(candidate):
                sys_root = os.environ.get("SystemRoot", r"C:\Windows")
                for folder in (
                    os.path.join(sys_root, "System32"),
                    os.path.join(sys_root, "System32", "drivers"),
                    os.path.join(sys_root, "SysWOW64"),
                    sys_root,
                ):
                    full_p = os.path.join(folder, os.path.basename(candidate))
                    if os.path.exists(full_p):
                        return full_p
            # Если кандидат был абсолютным, но с пробелами
            break

    # 3. Базовый split по первому пробелу
    first_token = raw.split()[0].strip().strip('"')
    if os.path.exists(first_token):
        return first_token

    # 4. Проверка системных папок для первого токена
    if not os.path.isabs(first_token) or not os.path.dirname(first_token):
        sys_root = os.environ.get("SystemRoot", r"C:\Windows")
        for folder in (
            os.path.join(sys_root, "System32"),
            os.path.join(sys_root, "System32", "drivers"),
            os.path.join(sys_root, "SysWOW64"),
            sys_root,
        ):
            full_p = os.path.join(folder, os.path.basename(first_token))
            if os.path.exists(full_p):
                return full_p

    return raw


from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider
from apps.windows.core.models import ActionType, AuditFinding, DomainAuditResult, RemediationAction, RiskLevel

class ServicesCollector(TelemetryProvider):
    """Коллектор фактов о службах Windows с использованием нативного SCM API."""

    def __init__(self) -> None:
        """Инициализация коллектора с нативным SCM клиентом."""
        self._scm = ServiceControlManager()
        self._last_result: Optional[DomainAuditResult] = None

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает показатели служб как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_result and self._last_result.metrics:
            metrics = self._last_result.metrics
            sensors.append(HardwareSensor(
                sensor_id="services_total",
                name="Всего системных служб",
                category="services",
                value=float(metrics.get("total_services_count", 0)),
                unit="count"
            ))
            sensors.append(HardwareSensor(
                sensor_id="services_running",
                name="Запущенных служб",
                category="services",
                value=float(metrics.get("running_services_count", 0)),
                unit="count"
            ))
        return sensors

    def collect(self) -> DomainAuditResult:
        """Сбор данных о службах и выявление осиротевших записей."""
        start_t = time.perf_counter()
        findings: List[AuditFinding] = []
        services = []
        running_count = 0
        orphaned_count = 0

        # 1. Попытка нативного сбора через EnumServicesStatusExW (Tier 1 Native Win32)
        native_services = []
        try:
            native_services = self._scm.enum_services()
        except Exception as ex:
            logger.debug(f"Нативный сбор SCM завершился с ошибкой: {ex}")

        if native_services:
            running_count = sum(1 for s in native_services if s.state == "RUNNING")

        # 2. Инвентаризация автозапуска и проверка на осиротевшие службы через реестр
        reg_path = r"SYSTEM\CurrentControlSet\Services"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as root_key:
                num_subkeys, _, _ = winreg.QueryInfoKey(root_key)
                for i in range(min(num_subkeys, 350)):
                    try:
                        svc_name = winreg.EnumKey(root_key, i)
                        with winreg.OpenKey(root_key, svc_name) as svc_key:
                            image_path = self._get_reg_val(svc_key, "ImagePath")
                            display_name = self._get_reg_val(svc_key, "DisplayName") or svc_name
                            start_type = self._get_reg_val(svc_key, "Start")

                            resolved_path = _resolve_service_binary(image_path) if image_path else ""
                            is_protected = svc_name.lower() in PROTECTED_SYSTEM_SERVICES

                            # Проверка на отсутствующий исполняемый файл для автозапускаемых служб (Start == 2)
                            if (
                                image_path
                                and start_type in ("2", 2)
                                and not is_protected
                                and resolved_path
                                and not os.path.exists(resolved_path)
                            ):
                                orphaned_count += 1
                                action = RemediationAction(
                                    action_id=f"disable_orphaned_svc_{svc_name}",
                                    action_type=ActionType.DISABLE_SERVICE,
                                    title=f"Отключить несуществующую службу {svc_name}",
                                    description=f"Служба ссылается на отсутствующий файл: {resolved_path}",
                                    target=svc_name,
                                    risk=RiskLevel.CAUTION,
                                    execution_command=f"Set-Service -Name '{svc_name}' -StartupType Disabled",
                                )
                                findings.append(
                                    AuditFinding(
                                        domain="services",
                                        category="orphaned_service",
                                        title=f"Осиротевшая служба: {display_name}",
                                        description=f"Служба '{svc_name}' настроена на автозапуск, но исполняемый файл отсутствует ({resolved_path}).",
                                        severity=RiskLevel.CAUTION,
                                        evidence={"service": svc_name, "path": resolved_path},
                                        actions=[action],
                                    )
                                )

                            services.append({
                                "name": svc_name,
                                "display_name": display_name,
                                "image_path": image_path,
                            })
                    except (OSError, PermissionError):
                        continue
        except Exception as e:
            logger.debug(f"Ошибка при инвентаризации реестра служб: {e}")

        # Fallback подсчета запущенных служб через psutil если нативный вызов вернул 0
        if running_count == 0:
            try:
                for s in psutil.win_service_iter():
                    if s.status() == psutil.STATUS_RUNNING:
                        running_count += 1
            except Exception:
                pass

        metrics: Dict[str, Any] = {
            "total_services_count": len(services) or len(native_services),
            "running_services_count": running_count,
            "orphaned_services_count": orphaned_count,
            "engine": "Native SCM API (advapi32.dll) + WinReg",
        }

        duration_ms = (time.perf_counter() - start_t) * 1000
        result = DomainAuditResult(
            domain_name="services",
            title_ru="Службы Windows",
            status="warning" if findings else "ok",
            findings=findings,
            metrics=metrics,
            scan_duration_ms=round(duration_ms, 2),
        )
        self._last_result = result
        return result


    def _get_reg_val(self, key: Any, val_name: str) -> Any:
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return val
        except OSError:
            return ""
