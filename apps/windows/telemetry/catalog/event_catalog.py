# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Event Catalog
# =============================================================================
# Description:
#   Иерархический каталог провайдеров и каналов Windows Event Log,
#   классификация по 7 доменам телеметрии (Security, Process, Storage, Network,
#   Update, Hardware, Power) и Sysmon, движки построения графов происхождения
#   (Process Provenance) и реконструкции жизненного цикла (Power Lifecycle).
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.event_catalog import WindowsEventCatalogEngine
#
#     engine = WindowsEventCatalogEngine()
#     catalog = engine.get_full_catalog()
#     domains = engine.get_domains_summary()
#
# File: event_catalog.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:35:00
# =============================================================================

from __future__ import annotations
"""Иерархический каталог провайдеров и каналов Windows Event Log по 7 доменам телеметрии."""

import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.telemetry.win32_ffi.wevtapi import WevtAPI
from apps.windows.telemetry.sqlite import TelemetryStorage


class TelemetryDomain(str, Enum):
    """7 доменов классификации Windows Event Logs."""
    SECURITY_IDENTITY = 'security_identity'       # 1. 🛡️ Security / Identity
    PROCESS_SERVICES_TASKS = 'process_tasks'      # 2. ⚙️ Process / Services / Tasks
    STORAGE_FILESYSTEM = 'storage_io'             # 3. 💾 Storage & Filesystem
    NETWORK_COMMUNICATIONS = 'network_comms'      # 4. 🌐 Network & Sockets
    WINDOWS_UPDATE = 'windows_update'             # 5. 🔄 Windows Update
    HARDWARE_PNP_DRIVERS = 'hardware_pnp'         # 6. 🔌 Hardware / Drivers / PnP
    POWER_BOOT_SHUTDOWN = 'power_lifecycle'       # 7. 🔋 Power / Boot / Shutdown
    SYSMON_OBSERVABILITY = 'sysmon_deep'          # 🧩 Sysmon Observability Layer


@dataclass
class EventProviderCatalogEntry:
    """Запись каталога провайдеров и каналов Windows Event Log."""
    id: str
    provider: str
    channel: str
    domain: TelemetryDomain
    domain_title: str
    key_events: Dict[int, str]
    levels: List[str]
    realtime_supported: bool
    historical_supported: bool
    privilege_required: str
    volume_rating: str  # Low, Medium, High, Extreme
    useful_fields: List[str]
    recommended_collector: str
    storage_class: str
    correlation_targets: List[str]
    description: str = ''
    is_present_on_host: bool = True
    record_count: int = 0
    size_mb: float = 0.0


# Полный реестр провайдеров по 7 доменам телеметрии
EVENT_PROVIDERS_REGISTRY: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. 🛡️ Security / Identity
    # -------------------------------------------------------------------------
    {
        'id': 'sec_auditing',
        'provider': 'Microsoft-Windows-Security-Auditing',
        'channel': 'Security',
        'domain': TelemetryDomain.SECURITY_IDENTITY,
        'domain_title': '1. Security / Identity',
        'key_events': {
            4624: 'Успешный вход (Logon)',
            4625: 'Неудачная попытка входа (Failed Logon)',
            4634: 'Завершение сеанса пользователя (Logoff)',
            4647: 'Пользователь инициировал выход',
            4672: 'Назначение специальных привилегий (Admin/UAC)',
            4720: 'Создание пользователя',
            4726: 'Удаление пользователя',
            4732: 'Добавление пользователя в локальную группу',
            4738: 'Изменение атрибутов учетной записи',
            4740: 'Блокировка учетной записи (Account Lockout)',
            1102: 'Очистка журнала аудита безопасности',
        },
        'levels': ['Information', 'Audit Success', 'Audit Failure'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'SeSecurityPrivilege (Admin)',
        'volume_rating': 'High',
        'useful_fields': ['SubjectUserName', 'TargetUserName', 'LogonType', 'IpAddress', 'TargetSid'],
        'recommended_collector': 'WevtAPI Incremental Bookmark',
        'storage_class': 'security_events',
        'correlation_targets': ['processes', 'user_sessions', 'network_sockets'],
        'description': 'Основной журнал аудита безопасности Windows: авторизация, аккаунты, группы и права.',
    },
    {
        'id': 'sec_kerberos',
        'provider': 'Microsoft-Windows-Kerberos-Key-Distribution-Center',
        'channel': 'Security',
        'domain': TelemetryDomain.SECURITY_IDENTITY,
        'domain_title': '1. Security / Identity',
        'key_events': {
            4768: 'Выдача Kerberos TGT билета',
            4769: 'Выдача Kerberos Service Ticket (TGS)',
            4771: 'Сбой преаутентификации Kerberos (Неверный пароль)',
            4776: 'NTLM валидация учетных данных',
        },
        'levels': ['Information', 'Audit Failure'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Medium',
        'useful_fields': ['TargetUserName', 'ServiceName', 'TicketOptions', 'FailureCode', 'IpAddress'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'security_events',
        'correlation_targets': ['domain_auth', 'failed_logons', 'lateral_movement'],
        'description': 'Аудит протоколов Kerberos и NTLM аутентификации в корпоративной сети и локальном хосте.',
    },
    {
        'id': 'sec_grouppolicy',
        'provider': 'Microsoft-Windows-GroupPolicy',
        'channel': 'Microsoft-Windows-GroupPolicy/Operational',
        'domain': TelemetryDomain.SECURITY_IDENTITY,
        'domain_title': '1. Security / Identity',
        'key_events': {
            5312: 'Список примененных политик Group Policy Objects (GPO)',
            5314: 'Начало обработки групповой политики',
            7004: 'Ошибка применения политики пользователя/компьютера',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Low',
        'useful_fields': ['GPOList', 'PrincipalSamName', 'ElapsedTimeInMilliseconds', 'ErrorCode'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'security_events',
        'correlation_targets': ['policy_drift', 'system_baseline'],
        'description': 'Телеметрия применения групповых политик Windows и изменений конфигурации безопасности.',
    },

    # -------------------------------------------------------------------------
    # 2. ⚙️ Process / Services / Tasks
    # -------------------------------------------------------------------------
    {
        'id': 'proc_creation_4688',
        'provider': 'Microsoft-Windows-Security-Auditing',
        'channel': 'Security',
        'domain': TelemetryDomain.PROCESS_SERVICES_TASKS,
        'domain_title': '2. Process / Services / Tasks',
        'key_events': {
            4688: 'Создание нового процесса (с CommandLine и Parent PID)',
            4689: 'Завершение работы процесса (Process Exit)',
        },
        'levels': ['Information', 'Audit Success'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Extreme',
        'useful_fields': ['NewProcessName', 'CommandLine', 'ProcessId', 'CreatorProcessId', 'ParentProcessName', 'SubjectUserName'],
        'recommended_collector': 'WevtAPI Incremental Tail',
        'storage_class': 'security_events',
        'correlation_targets': ['process_provenance_tree', 'cpu_spikes', 'file_access'],
        'description': 'Глубокий аудит жизненного цикла процессов: полный путь, аргументы запуска, родительский PID.',
    },
    {
        'id': 'proc_scm_services',
        'provider': 'Service Control Manager',
        'channel': 'System',
        'domain': TelemetryDomain.PROCESS_SERVICES_TASKS,
        'domain_title': '2. Process / Services / Tasks',
        'key_events': {
            7036: 'Изменение состояния службы (Запущена / Остановлена)',
            7045: 'Установка новой системной службы (Service Install)',
            7031: 'Аварийное завершение службы (Service Crash)',
            7034: 'Неожиданная остановка службы',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'Medium',
        'useful_fields': ['ServiceName', 'ImagePath', 'ServiceType', 'StartType', 'AccountName'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'security_events',
        'correlation_targets': ['process_provenance', 'service_matrix', 'boot_time'],
        'description': 'Диспетчер служб Windows (SCM): запуск, остановка, установка новых сервисов и сбои.',
    },
    {
        'id': 'proc_taskscheduler',
        'provider': 'Microsoft-Windows-TaskScheduler',
        'channel': 'Microsoft-Windows-TaskScheduler/Operational',
        'domain': TelemetryDomain.PROCESS_SERVICES_TASKS,
        'domain_title': '2. Process / Services / Tasks',
        'key_events': {
            106: 'Регистрация новой задачи в планировщике',
            107: 'Запуск задачи по расписанию или триггеру',
            102: 'Успешное завершение задачи',
            103: 'Сбой или ошибка выполнения задачи',
            140: 'Изменение конфигурации задачи',
            141: 'Удаление задачи из планировщика',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'High',
        'useful_fields': ['TaskName', 'ActionName', 'ResultCode', 'UserName', 'TaskInstanceId'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'security_events',
        'correlation_targets': ['process_provenance', 'persistence_audit', 'scheduled_jobs'],
        'description': 'Планировщик заданий: создание, триггеры, запуск задач и фоновая персистентность.',
    },
    {
        'id': 'proc_wmi_activity',
        'provider': 'Microsoft-Windows-WMI-Activity',
        'channel': 'Microsoft-Windows-WMI-Activity/Operational',
        'domain': TelemetryDomain.PROCESS_SERVICES_TASKS,
        'domain_title': '2. Process / Services / Tasks',
        'key_events': {
            5857: 'Инициализация WMI провайдера',
            5858: 'Ошибка выполнения WMI запроса (Query Failure)',
            5861: 'Регистрация постоянного WMI Event Consumer (Персистентность)',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Medium',
        'useful_fields': ['Query', 'Namespace', 'ClientProcessId', 'User', 'ResultCode'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'security_events',
        'correlation_targets': ['process_provenance', 'wmi_persistence'],
        'description': 'Инфраструктура WMI: запросы процессов, сбои провайдеров и механизмы постоянной подписки.',
    },
    {
        'id': 'proc_powershell',
        'provider': 'Microsoft-Windows-PowerShell',
        'channel': 'Microsoft-Windows-PowerShell/Operational',
        'domain': TelemetryDomain.PROCESS_SERVICES_TASKS,
        'domain_title': '2. Process / Services / Tasks',
        'key_events': {
            4103: 'Выполнение командного блока (Pipeline Execution)',
            4104: 'Логирование содержимого скрипта (Script Block Logging)',
            40961: 'Запуск консоли PowerShell хоста',
        },
        'levels': ['Information', 'Warning'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'High',
        'useful_fields': ['ScriptBlockText', 'Path', 'UserId', 'ProcessId', 'HostName'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'security_events',
        'correlation_targets': ['script_provenance', 'admin_audit'],
        'description': 'Среда PowerShell: выполнение сценариев автоматизации, командлетов и расширенный ScriptBlock аудит.',
    },

    # -------------------------------------------------------------------------
    # 3. 💾 Storage & Filesystem
    # -------------------------------------------------------------------------
    {
        'id': 'stor_ntfs',
        'provider': 'Microsoft-Windows-Ntfs',
        'channel': 'Microsoft-Windows-Ntfs/Operational',
        'domain': TelemetryDomain.STORAGE_FILESYSTEM,
        'domain_title': '3. Storage & Filesystem',
        'key_events': {
            140: 'Сброс буфера файловой системы на диск',
            141: 'Внимание: ошибка метаданных тома NTFS',
            142: 'Активация подсистемы самовосстановления NTFS (Self-Healing)',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Medium',
        'useful_fields': ['VolumeId', 'VolumeName', 'NtfsStatus', 'CorruptOffset'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['disk_io_spikes', 'file_corruption', 'smart_metrics'],
        'description': 'Файловая система NTFS: целостность томов, ошибки записи метаданных и самовосстановление.',
    },
    {
        'id': 'stor_disk_diag',
        'provider': 'Microsoft-Windows-DiskDiagnostic',
        'channel': 'Microsoft-Windows-DiskDiagnostic/Operational',
        'domain': TelemetryDomain.STORAGE_FILESYSTEM,
        'domain_title': '3. Storage & Filesystem',
        'key_events': {
            1: 'Диагностика накопителя: предупреждение о скором выходе из строя (SMART Alert)',
            2: 'Результаты автоматической самодиагностики диска',
        },
        'levels': ['Warning', 'Error', 'Critical'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Low',
        'useful_fields': ['DeviceName', 'Model', 'SerialNumber', 'SmartAttribute', 'RawValue'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['smart_sensors', 'hardware_health'],
        'description': 'Диагностика накопителей: ранние аппаратные предупреждения S.M.A.R.T. о деградации диска.',
    },
    {
        'id': 'stor_spaces',
        'provider': 'Microsoft-Windows-StorageSpaces-Driver',
        'channel': 'Microsoft-Windows-StorageSpaces-Driver/Operational',
        'domain': TelemetryDomain.STORAGE_FILESYSTEM,
        'domain_title': '3. Storage & Filesystem',
        'key_events': {
            100: 'Инициализация пула Storage Spaces',
            200: 'Отказ физического диска в дисковом пространстве',
            201: 'Автоматическое восстановление зеркалирования (Repair/Resync)',
        },
        'levels': ['Information', 'Warning', 'Error', 'Critical'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Low',
        'useful_fields': ['PoolId', 'SpaceId', 'PhysicalDiskId', 'ErrorStatus'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['disk_arrays', 'raid_health'],
        'description': 'Драйвер дисковых пространств Storage Spaces: пулы дисков, сбои зеркал и ресинхронизация.',
    },

    # -------------------------------------------------------------------------
    # 4. 🌐 Network & Sockets
    # -------------------------------------------------------------------------
    {
        'id': 'net_dns_client',
        'provider': 'Microsoft-Windows-DNS-Client',
        'channel': 'Microsoft-Windows-DNS-Client/Operational',
        'domain': TelemetryDomain.NETWORK_COMMUNICATIONS,
        'domain_title': '4. Network & Sockets',
        'key_events': {
            3008: 'Разрешение DNS запроса (Query Completed)',
            3018: 'Таймаут обращения к DNS серверу',
            3020: 'Сбой разрешения доменного имени (NXDOMAIN / Server Failure)',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'High',
        'useful_fields': ['QueryName', 'QueryType', 'QueryStatus', 'ServerList'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'network_metrics',
        'correlation_targets': ['process_sockets', 'latency_spikes', 'web_activity'],
        'description': 'Клиент DNS Windows: история запросов, задержки DNS-серверов и сбои резолвинга.',
    },
    {
        'id': 'net_firewall',
        'provider': 'Microsoft-Windows-Windows Firewall With Advanced Security',
        'channel': 'Microsoft-Windows-Windows Firewall With Advanced Security/Firewall',
        'domain': TelemetryDomain.NETWORK_COMMUNICATIONS,
        'domain_title': '4. Network & Sockets',
        'key_events': {
            2004: 'Брандмауэр разрешил входящее/исходящее соединение',
            2005: 'Брандмауэр заблокировал пакет (Packet Dropped)',
            2006: 'Изменение правила брандмауэра',
        },
        'levels': ['Information', 'Warning'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'High',
        'useful_fields': ['RuleId', 'ApplicationPath', 'LocalPort', 'RemotePort', 'Protocol', 'Direction'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'network_metrics',
        'correlation_targets': ['process_provenance', 'blocked_ports', 'security_events'],
        'description': 'Сетевой экран Windows Defender Firewall: блокировки пакетов, порты и изменение правил.',
    },
    {
        'id': 'net_smb_client',
        'provider': 'Microsoft-Windows-SMBClient',
        'channel': 'Microsoft-Windows-SMBClient/Security',
        'domain': TelemetryDomain.NETWORK_COMMUNICATIONS,
        'domain_title': '4. Network & Sockets',
        'key_events': {
            31001: 'Подключение к сетевой папке SMB',
            31017: 'Сбой авторизации на SMB сервере',
            31020: 'Сброс сессии сетевого ресурса из-за сетевого таймаута',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Low',
        'useful_fields': ['ServerName', 'ShareName', 'UserName', 'Status'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'network_metrics',
        'correlation_targets': ['network_shares', 'storage_io'],
        'description': 'Сетевой клиент SMB: обращения к общим сетевым папкам и сбои передачи файлов.',
    },

    # -------------------------------------------------------------------------
    # 5. 🔄 Windows Update
    # -------------------------------------------------------------------------
    {
        'id': 'upd_client',
        'provider': 'Microsoft-Windows-WindowsUpdateClient',
        'channel': 'Microsoft-Windows-WindowsUpdateClient/Operational',
        'domain': TelemetryDomain.WINDOWS_UPDATE,
        'domain_title': '5. Windows Update',
        'key_events': {
            19: 'Успешная установка обновления Windows Update (KB)',
            20: 'Ошибка при установке накопительного обновления',
            21: 'Установка пакета завершена, требуется перезапуск ОС',
            24: 'Начало скачивания компонентов обновления',
            25: 'Начало установки пакета обновления',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'Low',
        'useful_fields': ['UpdateTitle', 'KBNumber', 'ErrorCode', 'SupportUrl', 'ClientApplicationID'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['reboots', 'servicing_integrity', 'disk_usage'],
        'description': 'Клиент обновлений Windows Update: история загрузки, установки KB-пакетов и связанные перезагрузки.',
    },
    {
        'id': 'upd_orchestrator',
        'provider': 'Microsoft-Windows-UpdateOrchestrator',
        'channel': 'Microsoft-Windows-UpdateOrchestrator/Operational',
        'domain': TelemetryDomain.WINDOWS_UPDATE,
        'domain_title': '5. Windows Update',
        'key_events': {
            101: 'Update Orchestrator запустил проверку обновлений',
            102: 'Обнаружены доступные обновления',
            201: 'Запланирована принудительная перезагрузка системы для завершения обновления',
        },
        'levels': ['Information', 'Warning'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Low',
        'useful_fields': ['ActionName', 'RebootDeadline', 'ScheduledTime'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['planned_reboots', 'update_cycle'],
        'description': 'Диспетчер Update Orchestrator: планирование обслуживания и дедлайны перезагрузок.',
    },

    # -------------------------------------------------------------------------
    # 6. 🔌 Hardware / Drivers / Plug-and-Play
    # -------------------------------------------------------------------------
    {
        'id': 'hw_kernel_pnp',
        'provider': 'Microsoft-Windows-Kernel-PnP',
        'channel': 'Microsoft-Windows-Kernel-PnP/Configuration',
        'domain': TelemetryDomain.HARDWARE_PNP_DRIVERS,
        'domain_title': '6. Hardware / Drivers / PnP',
        'key_events': {
            400: 'Устройство настроено (Device Configured)',
            410: 'Устройство запущено (Device Started)',
            411: 'Сбой запуска устройства (Device Start Failed, Code 10 / 43)',
            420: 'Удаление устройства (Device Removed / Unplugged)',
            430: 'Требуется перезагрузка после установки драйвера',
        },
        'levels': ['Information', 'Warning', 'Error', 'Critical'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Medium',
        'useful_fields': ['DeviceInstanceId', 'DriverName', 'DriverVersion', 'ProblemStatus', 'HardwareIds'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['hardware_monitor', 'usb_peripherals', 'pnp_errors'],
        'description': 'Диспетчер оборудования Plug and Play: подключение USB/PCIe устройств, загрузка драйверов и ошибки Code 10/43.',
    },
    {
        'id': 'hw_device_setup',
        'provider': 'Microsoft-Windows-DeviceSetupManager',
        'channel': 'Microsoft-Windows-DeviceSetupManager/Admin',
        'domain': TelemetryDomain.HARDWARE_PNP_DRIVERS,
        'domain_title': '6. Hardware / Drivers / PnP',
        'key_events': {
            112: 'Успешная загрузка драйвера из Windows Update Driver Store',
            131: 'Ошибка сопоставления метаданных устройства',
        },
        'levels': ['Information', 'Warning', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin',
        'volume_rating': 'Low',
        'useful_fields': ['DeviceInstanceId', 'DriverPackage', 'Status'],
        'recommended_collector': 'WevtAPI Query',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['driver_store', 'peripherals'],
        'description': 'Диспетчер установки драйверов DeviceSetupManager: автоматический поиск пакетов в DriverStore.',
    },

    # -------------------------------------------------------------------------
    # 7. 🔋 Power / Boot / Shutdown Lifecycle
    # -------------------------------------------------------------------------
    {
        'id': 'pwr_kernel_power',
        'provider': 'Microsoft-Windows-Kernel-Power',
        'channel': 'Microsoft-Windows-Kernel-Power/Operational',
        'domain': TelemetryDomain.POWER_BOOT_SHUTDOWN,
        'domain_title': '7. Power / Boot / Shutdown',
        'key_events': {
            41: 'КРИТИЧЕСКИЙ СБОЙ: Перезагрузка без предварительного чистого выключения (BSOD / Power Cut)',
            42: 'Переход системы в спящий режим (Sleep / Modern Standby)',
            107: 'Выход системы из спящего режима (Resume from Sleep)',
            109: 'Переход ядра в режим гибернации (Fast Startup / Hibernate)',
            172: 'Изменение состояния подключения к электросети (AC / Battery)',
        },
        'levels': ['Information', 'Warning', 'Critical'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'Low',
        'useful_fields': ['BugcheckCode', 'BugcheckParameter1', 'SleepTime', 'WakeTime', 'TargetState'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['reboot_analyzer', 'bsod_crashes', 'uptime_timeline'],
        'description': 'Управление питанием ядра: переходы в сон/гибернацию, сбои питания (Event 41) и тайминги ACPI.',
    },
    {
        'id': 'pwr_user32_shutdown',
        'provider': 'User32',
        'channel': 'System',
        'domain': TelemetryDomain.POWER_BOOT_SHUTDOWN,
        'domain_title': '7. Power / Boot / Shutdown',
        'key_events': {
            1074: 'Плановое выключение / перезагрузка инициирована пользователем или процессом',
        },
        'levels': ['Information'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'Low',
        'useful_fields': ['InitiatingProcess', 'CallingUser', 'ShutdownReason', 'ReasonCode'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['user_actions', 'reboot_provenance'],
        'description': 'Инициация планового выключения/перезагрузки: кто, из какого процесса и по какой причине.',
    },
    {
        'id': 'pwr_eventlog_lifecycle',
        'provider': 'EventLog',
        'channel': 'System',
        'domain': TelemetryDomain.POWER_BOOT_SHUTDOWN,
        'domain_title': '7. Power / Boot / Shutdown',
        'key_events': {
            6005: 'Служба журнала событий запущена (Система успешно загрузилась)',
            6006: 'Служба журнала событий остановлена (Штатное выключение ОС)',
            6008: 'Предыдущее выключение системы было неожиданным (Unexpected Shutdown)',
        },
        'levels': ['Information', 'Error'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'User / Admin',
        'volume_rating': 'Low',
        'useful_fields': ['TimeOfLastKnownGoodState', 'EventLogStatus'],
        'recommended_collector': 'WevtAPI Incremental',
        'storage_class': 'system_snapshots',
        'correlation_targets': ['uptime_graph', 'crash_frequency'],
        'description': 'Метки времени загрузки и завершения работы операционной системы для расчета надежности.',
    },

    # -------------------------------------------------------------------------
    # 8. 🧩 Sysmon Observability Layer
    # -------------------------------------------------------------------------
    {
        'id': 'sysmon_deep_core',
        'provider': 'Microsoft-Windows-Sysmon',
        'channel': 'Microsoft-Windows-Sysmon/Operational',
        'domain': TelemetryDomain.SYSMON_OBSERVABILITY,
        'domain_title': 'Sysmon Observability Layer',
        'key_events': {
            1: 'Создание процесса с хэшами (SHA256, MD5, ParentCommandLine)',
            3: 'Сетевое соединение процесса (Source/Dest IP, Port, Process)',
            6: 'Загрузка драйвера ядра (Driver Loaded, Hashes)',
            7: 'Загрузка DLL модуля в процесс (Image Loaded)',
            10: 'Доступ одного процесса к памяти другого (Process Access / Injection)',
            11: 'Создание файла на диске (File Created)',
            12: 'Создание/удаление ключа реестра',
            13: 'Изменение значения реестра (Registry Value Set)',
            22: 'DNS запрос процесса (DNS Query with Process ID)',
        },
        'levels': ['Information'],
        'realtime_supported': True,
        'historical_supported': True,
        'privilege_required': 'Admin / System',
        'volume_rating': 'Extreme',
        'useful_fields': ['UtcTime', 'ProcessGuid', 'ProcessId', 'Image', 'CommandLine', 'Hashes', 'ParentProcessId', 'DestinationIp', 'DestinationPort'],
        'recommended_collector': 'Sysmon Collector / WevtAPI',
        'storage_class': 'security_events',
        'correlation_targets': ['process_provenance_deep', 'network_sockets', 'driver_hashes'],
        'description': 'Microsoft System Monitor: непрерывная телеметрия процессов, сетевых сокетов, файловых операций и хэшей драйверов.',
    },
]


class WindowsEventCatalogEngine:
    """Движок иерархического каталога каналов Windows Event Log и корреляционных графов."""

    def __init__(self) -> None:
        """Инициализация движка каталога."""
        self._wevtapi = WevtAPI()
        self._storage = TelemetryStorage()
        self._catalog_cache: Optional[List[EventProviderCatalogEntry]] = None
        self._cache_timestamp: float = 0.0

    def get_full_catalog(self, force_refresh: bool = False) -> List[EventProviderCatalogEntry]:
        """Возвращает полный структурированный каталог провайдеров и каналов."""
        now = time.time()
        if not force_refresh and self._catalog_cache and (now - self._cache_timestamp < 30.0):
            return self._catalog_cache

        entries: List[EventProviderCatalogEntry] = []
        for reg in EVENT_PROVIDERS_REGISTRY:
            cname = reg['channel']
            rec_cnt = self._wevtapi.get_channel_record_count(cname)
            
            # Проверка доступности
            is_present = True
            size_mb = 0.0
            try:
                # Оценка размера через wevtutil gli (быстро)
                info = self._wevtapi.check_channel_access(cname)
                is_present = info.get('accessible', True)
            except Exception:
                is_present = False

            entry = EventProviderCatalogEntry(
                id=reg['id'],
                provider=reg['provider'],
                channel=reg['channel'],
                domain=reg['domain'],
                domain_title=reg['domain_title'],
                key_events=reg['key_events'],
                levels=reg['levels'],
                realtime_supported=reg['realtime_supported'],
                historical_supported=reg['historical_supported'],
                privilege_required=reg['privilege_required'],
                volume_rating=reg['volume_rating'],
                useful_fields=reg['useful_fields'],
                recommended_collector=reg['recommended_collector'],
                storage_class=reg['storage_class'],
                correlation_targets=reg['correlation_targets'],
                description=reg.get('description', ''),
                is_present_on_host=is_present,
                record_count=rec_cnt,
                size_mb=round(rec_cnt * 0.0006, 2),  # примерная оценка в МБ если нет прямого размера
            )
            entries.append(entry)

        self._catalog_cache = entries
        self._cache_timestamp = now
        return entries

    def get_domains_summary(self) -> Dict[str, Any]:
        """Формирует сводную аналитику по 7 доменам телеметрии."""
        catalog = self.get_full_catalog()
        domains_map: Dict[str, Dict[str, Any]] = {
            TelemetryDomain.SECURITY_IDENTITY.value: {
                'id': TelemetryDomain.SECURITY_IDENTITY.value,
                'title': '1. 🛡️ Security / Identity',
                'description': 'Кто вошел, кто вышел, права доступа, UAC и аудит учетных записей.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [4624, 4625, 4672, 4720, 1102],
                'status': 'Active',
            },
            TelemetryDomain.PROCESS_SERVICES_TASKS.value: {
                'id': TelemetryDomain.PROCESS_SERVICES_TASKS.value,
                'title': '2. ⚙️ Process / Services / Tasks',
                'description': 'Жизненный цикл процессов, аргументы CommandLine, службы SCM, задачи и скрипты.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [4688, 4689, 7036, 7045, 106, 4104],
                'status': 'Active',
            },
            TelemetryDomain.STORAGE_FILESYSTEM.value: {
                'id': TelemetryDomain.STORAGE_FILESYSTEM.value,
                'title': '3. 💾 Storage & Filesystem',
                'description': 'Ошибки томов NTFS, S.M.A.R.T. предупреждения и целостность накопителей.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [140, 142, 1, 2, 200],
                'status': 'Active',
            },
            TelemetryDomain.NETWORK_COMMUNICATIONS.value: {
                'id': TelemetryDomain.NETWORK_COMMUNICATIONS.value,
                'title': '4. 🌐 Network & Sockets',
                'description': 'DNS-запросы, блокировки брандмауэра и соединения по протоколам SMB/TCP.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [3008, 3018, 2004, 2005, 31001],
                'status': 'Active',
            },
            TelemetryDomain.WINDOWS_UPDATE.value: {
                'id': TelemetryDomain.WINDOWS_UPDATE.value,
                'title': '5. 🔄 Windows Update',
                'description': 'Установка накопительных пакетов KB, ошибки патчей и дедлайны обслуживания.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [19, 20, 21, 25, 201],
                'status': 'Active',
            },
            TelemetryDomain.HARDWARE_PNP_DRIVERS.value: {
                'id': TelemetryDomain.HARDWARE_PNP_DRIVERS.value,
                'title': '6. 🔌 Hardware / Drivers / PnP',
                'description': 'Подключение USB/PCIe оборудования, ошибки драйверов Code 10/43 и DriverStore.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [400, 410, 411, 420, 112],
                'status': 'Active',
            },
            TelemetryDomain.POWER_BOOT_SHUTDOWN.value: {
                'id': TelemetryDomain.POWER_BOOT_SHUTDOWN.value,
                'title': '7. 🔋 Power / Boot / Shutdown',
                'description': 'Цепочка жизненного цикла: Boot -> Login -> Sleep -> Wake -> Shutdown/Crash.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [41, 42, 107, 1074, 6005, 6008],
                'status': 'Active',
            },
            TelemetryDomain.SYSMON_OBSERVABILITY.value: {
                'id': TelemetryDomain.SYSMON_OBSERVABILITY.value,
                'title': '🧩 Sysmon Observability Layer',
                'description': 'Глубокая сквозная телеметрия создания процессов с хэшами, сокетов и файлов.',
                'channels_count': 0,
                'total_records': 0,
                'key_events': [1, 3, 6, 7, 10, 11, 22],
                'status': 'Optional',
            },
        }

        for item in catalog:
            dom_key = item.domain.value if hasattr(item.domain, 'value') else str(item.domain)
            if dom_key in domains_map:
                domains_map[dom_key]['channels_count'] += 1
                domains_map[dom_key]['total_records'] += item.record_count

        sysmon_info = self.check_sysmon_status()
        if not sysmon_info['installed']:
            domains_map[TelemetryDomain.SYSMON_OBSERVABILITY.value]['status'] = 'Не установлен'
        else:
            domains_map[TelemetryDomain.SYSMON_OBSERVABILITY.value]['status'] = 'Активен'

        return {
            'domains': list(domains_map.values()),
            'total_registered_providers': len(catalog),
            'sysmon_installed': sysmon_info['installed'],
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }

    def reconstruct_process_provenance(
        self,
        process_name: Optional[str] = None,
        pid: Optional[int] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Строит дерево происхождения процессов (Process Provenance Graph).

        Цепочка: User -> Parent Process -> Process -> Child Processes -> Service / Task.
        """
        # Считываем события 4688 и 4689 из Security
        events_4688 = self._storage.get_security_events(event_id=4688, process_name=process_name, pid=pid, limit=100)
        
        # Считываем события служб SCM (System)
        scm_events = self._wevtapi.read_events(channel='System', limit=100, event_id=7045, hours=hours)
        # Считываем события TaskScheduler
        task_events = self._wevtapi.read_events(channel='Microsoft-Windows-TaskScheduler/Operational', limit=100, event_id=107, hours=hours)

        nodes: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []
        seen_pids: Set[int] = set()

        for ev in events_4688:
            curr_pid = ev.get('process_id') or 0
            parent_pid = ev.get('parent_process_id') or 0
            pname = ev.get('process_name') or 'unknown.exe'
            parent_name = ev.get('parent_process_name') or (f"PID {parent_pid}" if parent_pid else 'explorer.exe')
            user = ev.get('subject_user') or 'SYSTEM'
            cmd = ev.get('command_line') or ''
            ts = ev.get('timestamp') or ''

            node_id = f"proc_{curr_pid}_{pname}"
            parent_node_id = f"proc_{parent_pid}_{parent_name}"

            if curr_pid not in seen_pids:
                nodes.append({
                    'id': node_id,
                    'type': 'process',
                    'name': pname.split('\\')[-1],
                    'full_path': pname,
                    'pid': curr_pid,
                    'user': user,
                    'command_line': cmd,
                    'timestamp': ts,
                    'role': 'Target Process',
                })
                seen_pids.add(curr_pid)

            if parent_pid and parent_pid not in seen_pids:
                nodes.append({
                    'id': parent_node_id,
                    'type': 'parent_process',
                    'name': parent_name.split('\\')[-1],
                    'full_path': parent_name,
                    'pid': parent_pid,
                    'user': user,
                    'command_line': '',
                    'timestamp': ts,
                    'role': 'Parent Creator',
                })
                seen_pids.add(parent_pid)

            if parent_pid:
                links.append({
                    'source': parent_node_id,
                    'target': node_id,
                    'relationship': 'spawns',
                    'label': f"Fork ({ts.split(' ')[-1] if ' ' in ts else ts})",
                })

        # Связываем со службами
        for scm in scm_events[:10]:
            srv_name = scm.get('message', '').split(' ')[0] or 'System Service'
            srv_id = f"srv_{scm.get('event_id')}_{srv_name}"
            nodes.append({
                'id': srv_id,
                'type': 'service',
                'name': srv_name,
                'timestamp': scm.get('timestamp', ''),
                'role': 'Windows Service',
            })

        return {
            'target_filter': {'process_name': process_name, 'pid': pid},
            'nodes': nodes,
            'links': links,
            'total_nodes': len(nodes),
            'total_links': len(links),
        }

    def reconstruct_power_lifecycle(self, hours: int = 72) -> List[Dict[str, Any]]:
        """Реконструирует хронологию жизненного цикла ОС: Boot -> Login -> Sleep -> Wake -> Shutdown/Crash."""
        # Используем WevtAPI для чтения Kernel-Power, User32, EventLog
        pwr_events = self._wevtapi.read_events(
            channel='System',
            limit=200,
            hours=hours,
            event_id=[41, 1074, 6005, 6006, 6008, 12, 13, 42, 107],
        )

        timeline: List[Dict[str, Any]] = []
        for ev in pwr_events:
            eid = ev.get('event_id', 0)
            msg = ev.get('message', '')
            ts = ev.get('timestamp', '')
            provider = ev.get('provider', '')

            phase = 'WORK'
            icon = '⚙️'
            severity = 'info'

            if eid in (6005, 12):
                phase = 'BOOT'
                icon = '🚀'
                msg = 'Запуск операционной системы и служб ядра'
            elif eid == 42:
                phase = 'SLEEP'
                icon = '🌙'
                msg = 'Переход системы в спящий режим (Sleep)'
            elif eid == 107:
                phase = 'WAKE'
                icon = '☀️'
                msg = 'Пробуждение системы из спящего режима'
            elif eid == 1074:
                phase = 'SHUTDOWN_PLANNED'
                icon = '🛑'
                severity = 'warning'
            elif eid in (6006, 13):
                phase = 'SHUTDOWN_CLEAN'
                icon = '⏹️'
                msg = 'Штатное завершение работы Windows'
            elif eid in (41, 6008):
                phase = 'CRASH_UNEXPECTED'
                icon = '🚨'
                severity = 'critical'
                msg = 'Критический сбой питания / BSOD (Внезапная перезагрузка)'

            timeline.append({
                'timestamp': ts,
                'phase': phase,
                'icon': icon,
                'event_id': eid,
                'provider': provider,
                'severity': severity,
                'message': msg,
                'raw_data': ev.get('raw_data', ''),
            })

        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        return timeline

    def reconstruct_hardware_pnp_chain(self, hours: int = 72) -> List[Dict[str, Any]]:
        """Реконструирует цепочку событий оборудования и драйверов Plug and Play."""
        pnp_events = self._wevtapi.read_events(
            channel='Microsoft-Windows-Kernel-PnP/Configuration',
            limit=100,
            hours=hours,
        )

        chain: List[Dict[str, Any]] = []
        for ev in pnp_events:
            eid = ev.get('event_id', 0)
            msg = ev.get('message', '')
            ts = ev.get('timestamp', '')

            status = 'Configured'
            if eid == 411:
                status = 'Failed (Code 10/43)'
            elif eid == 420:
                status = 'Unplugged / Removed'
            elif eid == 410:
                status = 'Started'

            chain.append({
                'timestamp': ts,
                'event_id': eid,
                'status': status,
                'message': msg,
                'level': ev.get('level', 'Information'),
            })

        return chain

    def check_sysmon_status(self) -> Dict[str, Any]:
        """Проверяет статус службы и журнала Sysmon в системе."""
        rec_cnt = self._wevtapi.get_channel_record_count('Microsoft-Windows-Sysmon/Operational')
        has_channel = rec_cnt > 0

        # Проверка службы
        service_running = False
        try:
            res = subprocess.run(['sc', 'query', 'Sysmon64'], capture_output=True, text=True, timeout=3)
            if 'RUNNING' in res.stdout:
                service_running = True
            else:
                res2 = subprocess.run(['sc', 'query', 'Sysmon'], capture_output=True, text=True, timeout=3)
                if 'RUNNING' in res2.stdout:
                    service_running = True
        except Exception:
            service_running = False

        return {
            'installed': has_channel or service_running,
            'service_running': service_running,
            'channel_name': 'Microsoft-Windows-Sysmon/Operational',
            'record_count': rec_cnt,
            'capabilities': [
                'Process Creation with Hashes (SHA256, MD5, IMPHASH)',
                'Network Connection Telemetry (Process -> IP:Port)',
                'File Creation & Modification Tracking',
                'Driver & Kernel Module Signature Verification',
                'Process Memory Access / Injection Detection',
                'DNS Queries per Process ID',
            ] if (has_channel or service_running) else [],
        }


WindowsEventCatalog = WindowsEventCatalogEngine

__all__ = [
    'TelemetryDomain',
    'EventProviderCatalogEntry',
    'WindowsEventCatalogEngine',
    'WindowsEventCatalog',
    'EVENT_PROVIDERS_REGISTRY',
]

