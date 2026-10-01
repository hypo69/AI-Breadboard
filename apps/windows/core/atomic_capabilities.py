# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Atomic Capabilities
# =============================================================================
# Description:
#   Реестр атомарных возможностей и операций утилит Windows.
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.atomic_capabilities import WindowsAtomicCapabilitiesRegistry
#
#     instance = WindowsAtomicCapabilitiesRegistry.get_instance()
#
# File: atomic_capabilities.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Реестр атомарных возможностей и операций утилит Windows."""

import asyncio
import ctypes
import platform
import subprocess
import time
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.core.atomic_models import (
    AtomicOperation,
    AtomicOperationExecutionRequest,
    AtomicOperationExecutionResult,
    CapabilityCategory,
    ExecutionMethod,
    HttpMethod,
    PrivilegeLevel,
    RiskLevel,
)


class WindowsAtomicCapabilitiesRegistry:
    """Реестр атомарных возможностей и операций утилит Windows."""

    _instance: Optional[WindowsAtomicCapabilitiesRegistry] = None

    def __init__(self) -> None:
        self._operations: Dict[str, AtomicOperation] = {}
        self._load_catalog()

    @classmethod
    def get_instance(cls) -> WindowsAtomicCapabilitiesRegistry:
        """Получение синглтона реестра."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register(self, op: AtomicOperation) -> None:
        """Регистрация операции в каталоге."""
        self._operations[op.id] = op

    def _load_catalog(self) -> None:
        """Загрузка полного каталога всех 17 категорий и утилит."""
        # 1. Диски и файловые системы (Storage & Filesystems)
        self._register(AtomicOperation(
            id='diskpart.disk.list', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Перечисление физических дисков', description='Получить список всех физических дисков, их номеров, статуса и размера.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/storage/disks', cli_template='diskpart /s list_disks.txt',
            native_api_equivalent='DeviceIoControl(IOCTL_DISK_GET_DRIVE_LAYOUT_EX)'
        ))
        self._register(AtomicOperation(
            id='diskpart.disk.clean', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Очистка структуры диска', description='Удаление разметки разделов и скрытых секторов выбранного диска.',
            risk_level=RiskLevel.CRITICAL, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/storage/disks/{disk_id}/clean', cli_template='diskpart /s clean_disk.txt',
            parameters={'disk_id': {'type': 'int', 'required': True, 'description': 'Номер диска'}}
        ))
        self._register(AtomicOperation(
            id='diskpart.partition.list', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Перечисление разделов диска', description='Получить список всех разделов на указанном физическом диске.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/storage/disks/{disk_id}/partitions', cli_template='diskpart /s list_parts.txt',
            parameters={'disk_id': {'type': 'int', 'required': True, 'description': 'Номер диска'}}
        ))
        self._register(AtomicOperation(
            id='diskpart.partition.create', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Создание раздела на диске', description='Создать primary или efi раздел заданного размера на диске.',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/storage/disks/{disk_id}/partitions', cli_template='diskpart /s create_part.txt',
            parameters={'disk_id': {'type': 'int', 'required': True}, 'part_type': {'type': 'str', 'default': 'primary'}, 'size_mb': {'type': 'int'}}
        ))
        self._register(AtomicOperation(
            id='diskpart.partition.delete', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Удаление раздела', description='Удалить выбранный раздел диска с потерей данных в нем.',
            risk_level=RiskLevel.CRITICAL, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.DELETE, api_route='/api/v1/storage/disks/{disk_id}/partitions/{partition_id}', cli_template='diskpart /s del_part.txt',
            parameters={'disk_id': {'type': 'int', 'required': True}, 'partition_id': {'type': 'int', 'required': True}}
        ))
        self._register(AtomicOperation(
            id='diskpart.volume.format', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Форматирование тома', description='Форматирование тома в NTFS/FAT32/exFAT с назначением метки.',
            risk_level=RiskLevel.CRITICAL, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/storage/volumes/{volume_id}/format', cli_template='format {drive_letter}: /FS:{fs} /Q /Y',
            parameters={'drive_letter': {'type': 'str', 'required': True}, 'fs': {'type': 'str', 'default': 'NTFS'}, 'quick': {'type': 'bool', 'default': True}}
        ))
        self._register(AtomicOperation(
            id='diskpart.volume.assign_letter', utility='diskpart.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Назначение буквы диска', description='Привязать свободную букву диска к указанному тому.',
            risk_level=RiskLevel.MEDIUM, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/storage/volumes/{volume_id}/assign-letter', cli_template='diskpart /s assign_letter.txt',
            parameters={'volume_id': {'type': 'int', 'required': True}, 'letter': {'type': 'str', 'required': True}}
        ))
        self._register(AtomicOperation(
            id='fsutil.fs.info', utility='fsutil.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Информация о файловой системе', description='Получить тип ФС, размер кластера, статистику секторов и метаданные тома.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/storage/fs/info', cli_template='fsutil fsinfo volumeinfo {drive_letter}:',
            parameters={'drive_letter': {'type': 'str', 'default': 'C'}}
        ))
        self._register(AtomicOperation(
            id='fsutil.fs.trim_query', utility='fsutil.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Проверка состояния TRIM для SSD', description='Запрос глобального статуса TRIM (DisableDeleteNotify).',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/storage/fs/trim', cli_template='fsutil behavior query DisableDeleteNotify'
        ))
        self._register(AtomicOperation(
            id='fsutil.fs.trim_set', utility='fsutil.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Включение/отключение TRIM для SSD', description='Установка режима TRIM для твердотельных накопителей.',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/storage/fs/trim', cli_template='fsutil behavior set DisableDeleteNotify {value}',
            parameters={'value': {'type': 'int', 'default': 0, 'description': '0 = Включен (рекомендуется), 1 = Отключен'}}
        ))
        self._register(AtomicOperation(
            id='mountvol.mountpoint.list', utility='mountvol.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Перечисление точек монтирования и GUID томов', description='Список всех подключенных томов и их GUID.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/storage/mountpoints', cli_template='mountvol.exe'
        ))
        self._register(AtomicOperation(
            id='chkdsk.volume.check', utility='chkdsk.exe', category=CapabilityCategory.STORAGE_FS,
            name_ru='Проверка целостности файловой системы', description='Анализ ошибок тома без блокировки или с исправлением (/F).',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/storage/volumes/{volume_id}/chkdsk', cli_template='chkdsk.exe {drive_letter}: /scan',
            parameters={'drive_letter': {'type': 'str', 'default': 'C'}, 'fix': {'type': 'bool', 'default': False}}
        ))

        # 2. Загрузка и восстановление (Boot & Recovery)
        self._register(AtomicOperation(
            id='bcdedit.boot.list', utility='bcdedit.exe', category=CapabilityCategory.BOOT_RECOVERY,
            name_ru='Чтение конфигурации BCD', description='Список всех записей диспетчера загрузки Windows и параметров загрузчика.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/boot/entries', cli_template='bcdedit.exe /enum all'
        ))
        self._register(AtomicOperation(
            id='bcdedit.boot.set_timeout', utility='bcdedit.exe', category=CapabilityCategory.BOOT_RECOVERY,
            name_ru='Настройка таймаута меню загрузки', description='Изменение времени ожидания выбора операционной системы в секундах.',
            risk_level=RiskLevel.MEDIUM, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/boot/timeout', cli_template='bcdedit.exe /timeout {seconds}',
            parameters={'seconds': {'type': 'int', 'default': 5}}
        ))
        self._register(AtomicOperation(
            id='bcdboot.boot.repair', utility='bcdboot.exe', category=CapabilityCategory.BOOT_RECOVERY,
            name_ru='Восстановление системных файлов загрузки', description='Копирование критических файлов загрузчика из Windows на системный раздел EFI.',
            risk_level=RiskLevel.CRITICAL, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/boot/repair-environment', cli_template='bcdboot.exe {source_dir} /s {efi_drive}: /f ALL',
            parameters={'source_dir': {'type': 'str', 'default': 'C:\\Windows'}, 'efi_drive': {'type': 'str', 'default': 'S'}}
        ))
        self._register(AtomicOperation(
            id='reagentc.winre.info', utility='reagentc.exe', category=CapabilityCategory.BOOT_RECOVERY,
            name_ru='Проверка состояния среды WinRE', description='Получение статуса, местоположения образа и BCD идентификатора среды восстановления.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/recovery/winre/info', cli_template='reagentc.exe /info'
        ))
        self._register(AtomicOperation(
            id='reagentc.winre.enable', utility='reagentc.exe', category=CapabilityCategory.BOOT_RECOVERY,
            name_ru='Включение среды восстановления WinRE', description='Активация встроенной среды аварийного восстановления Windows.',
            risk_level=RiskLevel.MEDIUM, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/recovery/winre/enable', cli_template='reagentc.exe /enable'
        ))

        # 3. Системные файлы и компоненты (Servicing & Integrity)
        self._register(AtomicOperation(
            id='sfc.scannow', utility='sfc.exe', category=CapabilityCategory.SERVICING_INTEGRITY,
            name_ru='Проверка и восстановление системных файлов WRP', description='Сканирование защищенных файлов Windows и замена поврежденных копий из кэша.',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/servicing/sfc/scannow', cli_template='sfc.exe /scannow'
        ))
        self._register(AtomicOperation(
            id='dism.check_health', utility='DISM.exe', category=CapabilityCategory.SERVICING_INTEGRITY,
            name_ru='Проверка повреждений хранилища компонентов DISM', description='Быстрая проверка флага повреждения в Component Store.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/servicing/dism/check-health', cli_template='dism.exe /Online /Cleanup-Image /CheckHealth'
        ))
        self._register(AtomicOperation(
            id='dism.restore_health', utility='DISM.exe', category=CapabilityCategory.SERVICING_INTEGRITY,
            name_ru='Восстановление хранилища компонентов DISM', description='Глубокое сканирование и восстановление образа Windows عبر Windows Update / WIM.',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/servicing/dism/restore-health', cli_template='dism.exe /Online /Cleanup-Image /RestoreHealth'
        ))
        self._register(AtomicOperation(
            id='dism.features.list', utility='DISM.exe', category=CapabilityCategory.SERVICING_INTEGRITY,
            name_ru='Перечисление компонентов Windows', description='Список доступных и активированных дополнительных компонентов ОС.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/servicing/features', cli_template='dism.exe /Online /Get-Features /Format:Table'
        ))

        # 4. Драйверы и устройства (Drivers & Hardware)
        self._register(AtomicOperation(
            id='pnputil.device.list', utility='pnputil.exe', category=CapabilityCategory.DRIVERS_HARDWARE,
            name_ru='Перечисление устройств PnP', description='Получить список подключенных аппаратных устройств и их ID экземпляров.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/hardware/devices', cli_template='pnputil.exe /enum-devices'
        ))
        self._register(AtomicOperation(
            id='pnputil.device.problems', utility='pnputil.exe', category=CapabilityCategory.DRIVERS_HARDWARE,
            name_ru='Поиск проблемных устройств (Code 10/43)', description='Мгновенный список всех устройств с аппаратными ошибками или сбоем драйвера.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/hardware/devices/problems', cli_template='pnputil.exe /enum-devices /problem'
        ))
        self._register(AtomicOperation(
            id='pnputil.driver.packages', utility='pnputil.exe', category=CapabilityCategory.DRIVERS_HARDWARE,
            name_ru='Список пакетов драйверов в DriverStore', description='Список всех OEM .INF пакетов, зарегистрированных в хранилище драйверов.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/hardware/drivers/packages', cli_template='pnputil.exe /enum-drivers'
        ))
        self._register(AtomicOperation(
            id='driverquery.list', utility='driverquery.exe', category=CapabilityCategory.DRIVERS_HARDWARE,
            name_ru='Список загруженных драйверов ядра', description='Таблица установленных драйверов ядра, типов и даты линковки.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/hardware/drivers/installed', cli_template='driverquery.exe /fo csv /v'
        ))

        # 5. Процессы (Processes)
        self._register(AtomicOperation(
            id='tasklist.list', utility='tasklist.exe', category=CapabilityCategory.PROCESSES,
            name_ru='Список активных процессов', description='Перечисление всех запущенных процессов, PID, сессий и потребления ОЗУ.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/processes', cli_template='tasklist.exe /FO CSV',
            native_api_equivalent='EnumProcesses / CreateToolhelp32Snapshot'
        ))
        self._register(AtomicOperation(
            id='taskkill.kill_pid', utility='taskkill.exe', category=CapabilityCategory.PROCESSES,
            name_ru='Завершение процесса по PID', description='Принудительное завершение процесса по его идентификатору.',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/processes/{pid}/kill', cli_template='taskkill.exe /F /PID {pid}',
            parameters={'pid': {'type': 'int', 'required': True}}, native_api_equivalent='TerminateProcess'
        ))

        # 6. Планировщик (Scheduler)
        self._register(AtomicOperation(
            id='schtasks.task.list', utility='schtasks.exe', category=CapabilityCategory.SCHEDULER,
            name_ru='Список запланированных заданий', description='Получить список всех задач Windows Task Scheduler с расписанием и статусом.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.COM,
            http_method=HttpMethod.GET, api_route='/api/v1/scheduler/tasks', cli_template='schtasks.exe /Query /FO CSV /V'
        ))
        self._register(AtomicOperation(
            id='schtasks.task.run', utility='schtasks.exe', category=CapabilityCategory.SCHEDULER,
            name_ru='Запуск задания планировщика', description='Принудительный запуск выполнения задания по его имени/пути.',
            risk_level=RiskLevel.LOW, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/scheduler/tasks/{task_path}/run', cli_template='schtasks.exe /Run /TN "{task_path}"',
            parameters={'task_path': {'type': 'str', 'required': True}}
        ))

        # 7. Производительность и трассировка (Performance & Tracing)
        self._register(AtomicOperation(
            id='logman.collectors.list', utility='logman.exe', category=CapabilityCategory.PERFORMANCE_TRACING,
            name_ru='Список наборов сборщиков данных', description='Просмотр активных и настроенных сборщиков ETW и счетчиков производительности.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/tracing/collectors', cli_template='logman.exe query'
        ))
        self._register(AtomicOperation(
            id='typeperf.counters.sample', utility='typeperf.exe', category=CapabilityCategory.PERFORMANCE_TRACING,
            name_ru='Замер счетчиков производительности', description='Чтение моментальных значений счетчиков CPU, диска, памяти и сети.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/tracing/counters/sample', cli_template='typeperf.exe "\\Processor(_Total)\\% Processor Time" -sc 1'
        ))

        # 8. Службы (Services)
        self._register(AtomicOperation(
            id='sc.service.list', utility='sc.exe', category=CapabilityCategory.SERVICES,
            name_ru='Список системных служб', description='Перечисление служб Windows с текущим состоянием (RUNNING, STOPPED) и типом запуска.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/services', cli_template='sc.exe query type= service state= all',
            native_api_equivalent='EnumServicesStatusExW'
        ))
        self._register(AtomicOperation(
            id='sc.service.start', utility='sc.exe', category=CapabilityCategory.SERVICES,
            name_ru='Запуск службы', description='Запуск службы по ее системному имени.',
            risk_level=RiskLevel.MEDIUM, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.POST, api_route='/api/v1/services/{name}/start', cli_template='net start "{name}"',
            parameters={'name': {'type': 'str', 'required': True}}, native_api_equivalent='StartServiceW'
        ))
        self._register(AtomicOperation(
            id='sc.service.stop', utility='sc.exe', category=CapabilityCategory.SERVICES,
            name_ru='Остановка службы', description='Остановка работающей службы Windows.',
            risk_level=RiskLevel.MEDIUM, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.POST, api_route='/api/v1/services/{name}/stop', cli_template='net stop "{name}"',
            parameters={'name': {'type': 'str', 'required': True}}, native_api_equivalent='ControlService(SERVICE_CONTROL_STOP)'
        ))

        # 9. Журналы событий (Event Logs)
        self._register(AtomicOperation(
            id='wevtutil.log.list', utility='wevtutil.exe', category=CapabilityCategory.EVENT_LOGS,
            name_ru='Перечисление каналов журналов событий', description='Список всех зарегистрированных каналов событий Windows Event Log.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/events/logs', cli_template='wevtutil.exe el',
            native_api_equivalent='EvtOpenChannelEnum / EvtNextChannelPath'
        ))
        self._register(AtomicOperation(
            id='wevtutil.log.clear', utility='wevtutil.exe', category=CapabilityCategory.EVENT_LOGS,
            name_ru='Очистка журнала событий', description='Удаление всех сохраненных событий из указанного канала.',
            risk_level=RiskLevel.HIGH, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/events/logs/{log_name}/clear', cli_template='wevtutil.exe cl "{log_name}"',
            parameters={'log_name': {'type': 'str', 'required': True}}
        ))

        # 10. Сеть (Network)
        self._register(AtomicOperation(
            id='ipconfig.all', utility='ipconfig.exe', category=CapabilityCategory.NETWORK,
            name_ru='Полная IP конфигурация адаптеров', description='Чтение IP, маски, шлюза, DHCP, DNS и физических MAC-адресов.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/network/ip-config', cli_template='ipconfig.exe /all',
            native_api_equivalent='GetAdaptersAddresses'
        ))
        self._register(AtomicOperation(
            id='ipconfig.flushdns', utility='ipconfig.exe', category=CapabilityCategory.NETWORK,
            name_ru='Сброс кэша DNS резолвера', description='Очистка локального кэша DNS записей Windows.',
            risk_level=RiskLevel.LOW, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/network/dns/flush', cli_template='ipconfig.exe /flushdns'
        ))
        self._register(AtomicOperation(
            id='netstat.connections', utility='netstat.exe', category=CapabilityCategory.NETWORK,
            name_ru='Список сетевых соединений и сокетов', description='Таблица всех активных TCP/UDP соединений с привязкой к PID процессов.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/network/connections', cli_template='netstat.exe -ano',
            native_api_equivalent='GetExtendedTcpTable / GetExtendedUdpTable'
        ))
        self._register(AtomicOperation(
            id='route.table', utility='route.exe', category=CapabilityCategory.NETWORK,
            name_ru='Таблица сетевой маршрутизации', description='Просмотр постоянных и активных IPv4/IPv6 маршрутов и метрик шлюзов.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/network/routes', cli_template='route.exe print',
            native_api_equivalent='GetIpForwardTable2'
        ))

        # 11. Firewall
        self._register(AtomicOperation(
            id='advfirewall.status', utility='netsh.exe advfirewall', category=CapabilityCategory.FIREWALL,
            name_ru='Состояние профилей брандмауэра', description='Проверка состояния профилей Domain, Private, Public и глобальных политик.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/firewall/status', cli_template='netsh advfirewall show allprofiles'
        ))
        self._register(AtomicOperation(
            id='advfirewall.rules.list', utility='netsh.exe advfirewall', category=CapabilityCategory.FIREWALL,
            name_ru='Список правил брандмауэра', description='Список входящих и исходящих правил фильтрации трафика.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/firewall/rules', cli_template='netsh advfirewall firewall show rule name=all'
        ))

        # 12. Безопасность и ACL (Security & ACL)
        self._register(AtomicOperation(
            id='icacls.get', utility='icacls.exe', category=CapabilityCategory.SECURITY_ACL,
            name_ru='Чтение списков контроля доступа ACL', description='Просмотр прав доступа пользователей и групп к файлу или папке.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/security/acl', cli_template='icacls.exe "{target_path}"',
            parameters={'target_path': {'type': 'str', 'required': True}}, native_api_equivalent='GetNamedSecurityInfoW'
        ))
        self._register(AtomicOperation(
            id='manage_bde.status', utility='manage-bde.exe', category=CapabilityCategory.SECURITY_ACL,
            name_ru='Статус шифрования BitLocker', description='Проверка статуса защиты дисков BitLocker, типа шифрования и статуса TPM/PIN.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/security/bitlocker/status', cli_template='manage-bde.exe -status'
        ))

        # 13. Реестр и GPO (Registry & Policy)
        self._register(AtomicOperation(
            id='reg.query', utility='reg.exe', category=CapabilityCategory.REGISTRY_GPO,
            name_ru='Чтение ключей и значений системного реестра', description='Безопасный запрос значений параметров из HKLM/HKCU/HKCR.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/registry/values', cli_template='reg.exe query "{key_path}" /v "{value_name}"',
            parameters={'key_path': {'type': 'str', 'required': True}, 'value_name': {'type': 'str'}},
            native_api_equivalent='RegOpenKeyExW / RegQueryValueExW'
        ))
        self._register(AtomicOperation(
            id='gpupdate.force', utility='gpupdate.exe', category=CapabilityCategory.REGISTRY_GPO,
            name_ru='Принудительное обновление групповых политик GPO', description='Синхронизация политик компьютера и пользователя с контроллером домена или локально.',
            risk_level=RiskLevel.MEDIUM, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.POST, api_route='/api/v1/gpo/update', cli_template='gpupdate.exe /force'
        ))
        self._register(AtomicOperation(
            id='gpresult.summary', utility='gpresult.exe', category=CapabilityCategory.REGISTRY_GPO,
            name_ru='Сводка примененных политик RSoP', description='Отчет о действующих групповых политиках для текущего пользователя и хоста.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/gpo/result', cli_template='gpresult.exe /r'
        ))

        # 14. Пользователи и группы (Identity & Users)
        self._register(AtomicOperation(
            id='net_user.list', utility='net.exe user', category=CapabilityCategory.IDENTITY_USERS,
            name_ru='Список локальных учетных записей', description='Перечисление всех локальных пользователей Windows.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/users', cli_template='net.exe user',
            native_api_equivalent='NetUserEnum'
        ))
        self._register(AtomicOperation(
            id='whoami.all', utility='whoami.exe', category=CapabilityCategory.IDENTITY_USERS,
            name_ru='Идентификация текущей сессии и привилегий', description='Получение текущего SID, имени пользователя, списка групп и назначенных Se-привилегий.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.NATIVE_API,
            http_method=HttpMethod.GET, api_route='/api/v1/users/whoami', cli_template='whoami.exe /all',
            native_api_equivalent='OpenProcessToken / GetTokenInformation'
        ))

        # 15. VSS и резервное копирование (VSS & Backup)
        self._register(AtomicOperation(
            id='vssadmin.shadows.list', utility='vssadmin.exe', category=CapabilityCategory.VSS_BACKUP,
            name_ru='Список теневых копий томов (VSS)', description='Перечисление созданных снимков томов Volume Snapshot Service.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/vss/shadows', cli_template='vssadmin.exe list shadows'
        ))
        self._register(AtomicOperation(
            id='vssadmin.storage.list', utility='vssadmin.exe', category=CapabilityCategory.VSS_BACKUP,
            name_ru='Хранилище теневых копий VSS', description='Размер выделенного и используемого пространства под теневые копии на томах.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.ADMINISTRATOR, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/vss/storage', cli_template='vssadmin.exe list shadowstorage'
        ))

        # 16. Power & Lifecycle
        self._register(AtomicOperation(
            id='powercfg.schemes.list', utility='powercfg.exe', category=CapabilityCategory.POWER_LIFECYCLE,
            name_ru='Список схем электропитания', description='Список доступных профилей управления питанием и активной схемы.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/power/schemes', cli_template='powercfg.exe /list'
        ))
        self._register(AtomicOperation(
            id='powercfg.requests', utility='powercfg.exe', category=CapabilityCategory.POWER_LIFECYCLE,
            name_ru='Запросы блокировки сна (Sleep Troubleshooter)', description='Мгновенный список процессов, драйверов и аудиопотоков, препятствующих уходу в спящий режим.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/power/requests', cli_template='powercfg.exe /requests'
        ))
        self._register(AtomicOperation(
            id='systeminfo.get', utility='systeminfo.exe', category=CapabilityCategory.POWER_LIFECYCLE,
            name_ru='Полная системная информация о хосте', description='Сведения о сборке Windows, процессоре, BIOS, времени загрузки и хотфиксах.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/system/info', cli_template='systeminfo.exe /fo csv'
        ))

        # 17. ПО и пакеты (Software & Packages)
        self._register(AtomicOperation(
            id='winget.search', utility='winget.exe', category=CapabilityCategory.SOFTWARE_PACKAGES,
            name_ru='Поиск пакетов в репозиториях WinGet', description='Поиск программ в каталогах Windows Package Manager и MS Store.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/packages/winget/search', cli_template='winget.exe search "{query}"',
            parameters={'query': {'type': 'str', 'required': True}}
        ))
        self._register(AtomicOperation(
            id='winget.list', utility='winget.exe', category=CapabilityCategory.SOFTWARE_PACKAGES,
            name_ru='Список установленных пакетов WinGet', description='Получить список установленного ПО с версиями и доступными обновлениями.',
            risk_level=RiskLevel.READ_ONLY, required_privilege=PrivilegeLevel.STANDARD, execution_method=ExecutionMethod.CLI,
            http_method=HttpMethod.GET, api_route='/api/v1/packages/winget/installed', cli_template='winget.exe list'
        ))

    def get_all_operations(self) -> List[AtomicOperation]:
        """Получение полного плоского списка всех зарегистрированных операций."""
        return list(self._operations.values())

    def get_operation(self, operation_id: str) -> Optional[AtomicOperation]:
        """Поиск операции по уникальному идентификатору."""
        return self._operations.get(operation_id)

    def get_operations_by_utility(self, utility_name: str) -> List[AtomicOperation]:
        """Поиск операций для конкретной утилиты (например diskpart или fsutil)."""
        u_clean = utility_name.lower().replace('.exe', '').replace('.com', '')
        return [
            op for op in self._operations.values()
            if u_clean in op.utility.lower().replace('.exe', '').replace('.com', '')
        ]

    def get_operations_by_category(self, category: CapabilityCategory) -> List[AtomicOperation]:
        """Поиск операций по заданной категории."""
        return [op for op in self._operations.values() if op.category == category]

    def get_tree(self) -> Dict[str, Any]:
        """Построение иерархического дерева: утилита -> список атомарных операций."""
        tree: Dict[str, List[Dict[str, Any]]] = {}
        for op in self._operations.values():
            util_key = op.utility
            if util_key not in tree:
                tree[util_key] = []
            tree[util_key].append(op.to_dict())
        return tree

    def get_categories_tree(self) -> Dict[str, Any]:
        """Построение иерархического дерева: категория -> утилита -> список операций."""
        cat_tree: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for op in self._operations.values():
            cat_name = op.category.value
            if cat_name not in cat_tree:
                cat_tree[cat_name] = {}
            if op.utility not in cat_tree[cat_name]:
                cat_tree[cat_name][op.utility] = []
            cat_tree[cat_name][op.utility].append(op.to_dict())
        return cat_tree

    async def execute_operation(self, request: AtomicOperationExecutionRequest) -> AtomicOperationExecutionResult:
        """Исполнение или симуляция атомарной операции с проверкой SafeOps.

        Args:
            request: Запрос с идентификатором операции, параметрами и флагом dry_run.

        Returns:
            AtomicOperationExecutionResult с результатом вызова.
        """
        start_t = time.perf_counter()
        op = self.get_operation(request.operation_id)
        if not op:
            return AtomicOperationExecutionResult(
                operation_id=request.operation_id,
                utility='unknown',
                status='ERROR',
                is_dry_run=request.dry_run,
                risk_level=RiskLevel.CRITICAL.value,
                required_privilege=PrivilegeLevel.ADMINISTRATOR.value,
                command_executed='',
                message=f"Операция '{request.operation_id}' не найдена в реестре возможностей.",
                execution_time_ms=0.0
            )

        cmd = op.cli_template
        for k, v in request.parameters.items():
            cmd = cmd.replace(f"{{{k}}}", str(v))

        # Режим Dry-Run / Симуляция
        if request.dry_run:
            duration_ms = (time.perf_counter() - start_t) * 1000
            return AtomicOperationExecutionResult(
                operation_id=op.id,
                utility=op.utility,
                status='DRY_RUN_SIMULATED',
                is_dry_run=True,
                risk_level=op.risk_level.value,
                required_privilege=op.required_privilege.value,
                command_executed=cmd,
                message=f"Симуляция операции '{op.name_ru}' выполнена успешно (команда не запускалась).",
                data={'operation': op.to_dict(), 'resolved_command': cmd, 'parameters': request.parameters},
                execution_time_ms=round(duration_ms, 2)
            )

        # Проверка подтверждения для опасных операций
        if op.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not request.confirmed_by_user:
            return AtomicOperationExecutionResult(
                operation_id=op.id,
                utility=op.utility,
                status='CONFIRMATION_REQUIRED',
                is_dry_run=False,
                risk_level=op.risk_level.value,
                required_privilege=op.required_privilege.value,
                command_executed=cmd,
                message=f"Операция с уровнем риска {op.risk_level.value} требует явного подтверждения пользователя (confirmed_by_user=True).",
                execution_time_ms=0.0
            )

        if platform.system() != 'Windows':
            duration_ms = (time.perf_counter() - start_t) * 1000
            return AtomicOperationExecutionResult(
                operation_id=op.id,
                utility=op.utility,
                status='MOCK_SUCCESS',
                is_dry_run=False,
                risk_level=op.risk_level.value,
                required_privilege=op.required_privilege.value,
                command_executed=cmd,
                message='Исполнение симулировано (хост не Windows).',
                execution_time_ms=round(duration_ms, 2)
            )

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            duration_ms = (time.perf_counter() - start_t) * 1000
            output = proc.stdout.strip() or proc.stderr.strip()
            status = 'SUCCESS' if proc.returncode == 0 else 'CLI_ERROR'
            return AtomicOperationExecutionResult(
                operation_id=op.id,
                utility=op.utility,
                status=status,
                is_dry_run=False,
                risk_level=op.risk_level.value,
                required_privilege=op.required_privilege.value,
                command_executed=cmd,
                message=f"Команда завершилась с кодом {proc.returncode}.",
                data={'stdout': proc.stdout, 'stderr': proc.stderr, 'returncode': proc.returncode},
                execution_time_ms=round(duration_ms, 2)
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_t) * 1000
            logger.error(f"[WindowsAtomicCapabilitiesRegistry] Сбой выполнения '{op.id}': {exc}")
            return AtomicOperationExecutionResult(
                operation_id=op.id,
                utility=op.utility,
                status='EXECUTION_EXCEPTION',
                is_dry_run=False,
                risk_level=op.risk_level.value,
                required_privilege=op.required_privilege.value,
                command_executed=cmd,
                message=str(exc),
                execution_time_ms=round(duration_ms, 2)
            )


def get_atomic_registry() -> WindowsAtomicCapabilitiesRegistry:
    """Хелпер доступа к экземпляру реестра возможностей."""
    return WindowsAtomicCapabilitiesRegistry.get_instance()


__all__ = [
    'WindowsAtomicCapabilitiesRegistry',
    'get_atomic_registry',
]
