# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Command & Telemetry Indexer
# =============================================================================
# Description:
#   Индексатор системных команд Windows, атомарных операций, коллекторов телеметрии,
#   утилит System32, параметров SafeOps и зондов для базы знаний WikiLLM.
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.command_indexer import CommandKnowledgeIndexer
#     from apps.windows.wikillm.storage import WikiStorage
#
#     storage = WikiStorage("data/windows_wikillm/telemetry_commands.db")
#     indexer = CommandKnowledgeIndexer(storage)
#     count = indexer.index_all()
#
# File: command_indexer.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 07:54:00
# =============================================================================

from __future__ import annotations
"""Индексатор системных команд Windows, коллекторов телеметрии и зондов для WikiLLM."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from .models import (
    ArtifactType,
    Claim,
    DiagnosticKnowledge,
    Evidence,
    KnowledgeEntity,
    KnowledgeSource,
    ResolutionAction,
    utc_now_iso,
)
from .storage import WikiStorage


class CommandKnowledgeIndexer:
    """Индексатор системных команд, скриптов и телеметрии в базу знаний WikiLLM."""

    def __init__(self, storage: WikiStorage) -> None:
        """Инициализирует индексатор команд.

        Args:
            storage: Экземпляр хранилища WikiStorage.
        """
        self.storage = storage

    def index_atomic_capabilities(self) -> int:
        """Индексирует полный реестр атомарных операций Windows (atomic_capabilities.py).

        Returns:
            Количество проиндексированных команд.
        """
        try:
            from apps.windows.sdk.core.atomic_capabilities import WindowsAtomicCapabilitiesRegistry
            registry = WindowsAtomicCapabilitiesRegistry.get_instance()
            count = 0

            for op_id, op in registry._operations.items():
                canonical_key = f"cmd:{op.id.lower()}"
                risk_str = getattr(op.risk_level, "value", str(op.risk_level)).lower()
                priv_str = getattr(op.required_privilege, "value", str(op.required_privilege))
                cat_str = getattr(op.category, "value", str(op.category))

                action = ResolutionAction(
                    title=op.name_ru,
                    description=op.description,
                    command=op.cli_template or op.powershell_equivalent,
                    risk_level=risk_str,
                    is_automated=(risk_str in ("read_only", "safe")),
                )

                diag_info = DiagnosticKnowledge(
                    symptoms=[f"Требуется операция: {op.name_ru}"],
                    possible_causes=[f"Категория возможностей: {cat_str}"],
                    diagnostic_actions=[action] if risk_str in ("read_only", "safe") else [],
                    remediation_steps=[action],
                    related_components=[op.utility] if op.utility else [],
                )

                claims = [
                    Claim(
                        statement=f"Утилита: {op.utility or 'PowerShell/WinAPI'}, уровень привилегий: {priv_str}, риск: {risk_str}.",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    )
                ]

                if op.native_api_equivalent:
                    claims.append(Claim(
                        statement=f"Нативный C-FFI эквивалент: {op.native_api_equivalent}",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    ))

                tags = [
                    "command",
                    "atomic",
                    "windows",
                    cat_str,
                    risk_str,
                ]
                if op.utility:
                    tags.append(op.utility.lower().replace(".exe", ""))

                entity = KnowledgeEntity(
                    canonical_key=canonical_key,
                    entity_type=ArtifactType.COMMAND,
                    name=op.name_ru,
                    summary=op.description[:250],
                    category=cat_str,
                    severity="warning" if risk_str in ("high", "critical") else "info",
                    confidence=1.0,
                    provenance_source=KnowledgeSource.DOCUMENTED,
                    diagnostic_info=diag_info,
                    claims=claims,
                    tags=tags,
                )

                self.storage.save_entity(entity)
                count += 1

            logger.info(f"[CommandKnowledgeIndexer] Успешно проиндексировано {count} атомарных операций Windows.")
            return count
        except Exception as exc:
            logger.error(f"[CommandKnowledgeIndexer] Ошибка при индексации atomic_capabilities: {exc}", exc_info=True)
            return 0

    def index_telemetry_collectors(self) -> int:
        """Индексирует 15 специализированных коллекторов аудита телеметрии.

        Returns:
            Количество проиндексированных коллекторов.
        """
        collectors_info = [
            ("driver", "Коллектор драйверов и устройств PnP", "Сбор сведений об установленных драйверах, PnP-устройствах, кодах ошибок оборудования и GPU.", "driver"),
            ("storage", "Коллектор дисковых накопителей и томов", "Инспекция физических дисков, структуры разделов, параметров файловой системы и SMART.", "storage"),
            ("network", "Коллектор сетевых адаптеров и сокетов", "Аудит сетевых интерфейсов, открытых портов, активных TCP/UDP соединений и DNS.", "network"),
            ("process", "Коллектор процессов и ресурсов", "Снимок активных процессов Windows, потребления CPU/RAM, дескрипторов и потоков.", "process"),
            ("services", "Коллектор системных служб Windows", "Аудит запущенных и остановленных служб Windows, типов автозапуска и зависимостей.", "services"),
            ("tasks", "Коллектор планировщика Task Scheduler", "Инспекция запланированных заданий Windows, триггеров и истории выполнения.", "tasks"),
            ("security", "Коллектор безопасности и антивируса", "Мониторинг статуса Windows Defender, параметров UAC, брандмауэра и автозагрузки.", "security"),
            ("eventlog", "Коллектор системных журналов Event Log", "Сканирование журналов System, Application, Security на наличие ошибок и сбоев.", "eventlog"),
            ("performance", "Коллектор производительности и узких мест", "Анализ счетчиков производительности PDH, нагрузки на процессор и очередей дисков.", "performance"),
            ("software", "Коллектор установленного ПО и активности", "Инвентаризация установленных программ, анализ UserAssist (ROT13) и Prefetch.", "software"),
            ("clean", "Коллектор временных файлов и кэша", "Аудит временных каталогов Temp, кэша обновлений Windows Update и дампов памяти.", "clean"),
            ("update", "Коллектор обновлений Windows", "Проверка установленных KB-пакетов, истории обновлений и готовности к обновлениям ОС.", "update"),
            ("integrity", "Коллектор целостности файлов и компонентов", "Проверка системных файлов (SFC/DISM) и анализ журналов CBS.", "integrity"),
            ("file_activity", "Коллектор файловой активности", "Мониторинг изменений системных каталогов в реальном времени.", "file_activity"),
            ("postinstall", "Коллектор артефактов постобслуживания", "Проверка остаточных файлов после установки и настройки окружения.", "postinstall"),
        ]

        count = 0
        for name, title, desc, domain in collectors_info:
            canonical_key = f"collector:{name}"
            action = ResolutionAction(
                title=f"Запустить коллектор {name}",
                description=desc,
                command=f"apps.windows.sdk.core.audits.{name}_collector.collect()",
                risk_level="safe",
                is_automated=True,
            )

            diag_info = DiagnosticKnowledge(
                symptoms=[f"Требуется сбор телеметрии по домену: {domain}"],
                possible_causes=[f"Диагностический аудит домена: {domain}"],
                diagnostic_actions=[action],
                remediation_steps=[action],
                related_components=[f"{name}_collector"],
            )

            claims = [
                Claim(
                    statement=f"Коллектор аудита подсистемы Windows SDK ({name}). Домен: {domain}.",
                    confidence=1.0,
                    source=KnowledgeSource.DOCUMENTED,
                    verified=True,
                )
            ]

            entity = KnowledgeEntity(
                canonical_key=canonical_key,
                entity_type=ArtifactType.COMMAND,
                name=title,
                summary=desc[:250],
                category="telemetry",
                severity="info",
                confidence=1.0,
                provenance_source=KnowledgeSource.DOCUMENTED,
                diagnostic_info=diag_info,
                claims=claims,
                tags=["collector", "telemetry", "audit", name, domain],
            )

            self.storage.save_entity(entity)
            count += 1

        logger.info(f"[CommandKnowledgeIndexer] Успешно проиндексировано {count} коллекторов телеметрии.")
        return count

    def index_system_params(self) -> int:
        """Индексирует параметры SafeOps из каталога SafeSystemParamManager.

        Returns:
            Количество проиндексированных параметров.
        """
        try:
            from apps.windows.sdk.core.system_param_manager import SafeSystemParamManager
            manager = SafeSystemParamManager()
            catalog = getattr(manager, "_catalog", {})
            count = 0

            for param_id, param in catalog.items():
                canonical_key = f"sys_param:{param_id.lower()}"
                risk_str = getattr(param.risk, "value", str(param.risk)).lower()
                cat_str = getattr(param.category, "value", str(param.category))

                action = ResolutionAction(
                    title=f"Управление параметром: {param.name}",
                    description=param.description,
                    command=f"py manage_tools.py sys-param set {param_id} <значение>",
                    risk_level=risk_str,
                    is_automated=False,
                )

                diag_info = DiagnosticKnowledge(
                    symptoms=[f"Настройка параметра: {param.name}"],
                    possible_causes=[f"Целевой реестр/служба: {param.target}"],
                    remediation_steps=[action],
                    related_components=[param.target],
                )

                claims = [
                    Claim(
                        statement=f"Параметр {param.name} (ID: {param_id}), чувствительный: {param.is_sensitive}, риск: {risk_str}.",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    )
                ]

                entity = KnowledgeEntity(
                    canonical_key=canonical_key,
                    entity_type=ArtifactType.COMMAND,
                    name=param.name,
                    summary=param.description[:250],
                    category=cat_str,
                    severity="warning" if risk_str in ("high", "critical") else "info",
                    confidence=1.0,
                    provenance_source=KnowledgeSource.DOCUMENTED,
                    diagnostic_info=diag_info,
                    claims=claims,
                    tags=["sys_param", "safeops", "registry", cat_str, risk_str],
                )

                self.storage.save_entity(entity)
                count += 1

            logger.info(f"[CommandKnowledgeIndexer] Успешно проиндексировано {count} системных параметров SafeOps.")
            return count
        except Exception as exc:
            logger.warning(f"[CommandKnowledgeIndexer] Ошибка индексации system_param: {exc}")
            return 0

    def index_system32_catalog(self) -> int:
        """Индексирует каталог системных утилит System32 (system32_catalog.py).

        Returns:
            Количество проиндексированных утилит.
        """
        try:
            from apps.windows.sdk.core.system32_catalog import System32Catalog
            catalog = System32Catalog.get_instance()
            count = 0

            for tool_name, tool in catalog._tools.items():
                tool_key = tool_name.lower().replace('.exe', '')
                canonical_key = f"sys32:{tool_key}"
                danger_str = getattr(tool.danger_level, "value", str(tool.danger_level)).lower()
                cat_str = getattr(tool.category, "value", str(tool.category)).lower()
                tier_str = getattr(tool.telemetry_tier, "value", str(tool.telemetry_tier)).lower()

                cmd_example = tool.command_templates[0] if tool.command_templates else tool.executable

                action = ResolutionAction(
                    title=f"Утилита Windows: {tool.executable}",
                    description=tool.purpose,
                    command=cmd_example,
                    risk_level=danger_str,
                    is_automated=(danger_str in ("none", "low", "safe")),
                )

                diag_info = DiagnosticKnowledge(
                    symptoms=[f"Требуется системный инструмент: {tool.executable}"],
                    possible_causes=[f"Категория: {cat_str}", f"Control Plane: {getattr(tool.primary_control_plane, 'value', str(tool.primary_control_plane))}"],
                    diagnostic_actions=[action] if danger_str in ("none", "low", "safe") else [],
                    remediation_steps=[action],
                    related_components=[tool.executable],
                )

                claims = [
                    Claim(
                        statement=f"Системный инструмент Windows System32 ({tool.executable}). Назначение: {tool.purpose}. Риск: {danger_str}, Tier: {tier_str}.",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    )
                ]

                if tool.powershell_equivalent:
                    claims.append(Claim(
                        statement=f"PowerShell эквивалент: {tool.powershell_equivalent}",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    ))
                if tool.wmi_cim_equivalent:
                    claims.append(Claim(
                        statement=f"WMI/CIM эквивалент: {tool.wmi_cim_equivalent}",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    ))
                if tool.native_api_equivalent:
                    claims.append(Claim(
                        statement=f"Win32 C-FFI эквивалент: {tool.native_api_equivalent}",
                        confidence=1.0,
                        source=KnowledgeSource.DOCUMENTED,
                        verified=True,
                    ))

                entity = KnowledgeEntity(
                    canonical_key=canonical_key,
                    entity_type=ArtifactType.COMMAND,
                    name=tool.executable,
                    summary=tool.purpose[:250],
                    category=cat_str,
                    severity="warning" if danger_str in ("high", "critical") else "info",
                    confidence=1.0,
                    provenance_source=KnowledgeSource.DOCUMENTED,
                    diagnostic_info=diag_info,
                    claims=claims,
                    tags=["sys32", "utility", "windows", cat_str, danger_str] + list(tool.tags or []),
                )

                self.storage.save_entity(entity)
                count += 1

            logger.info(f"[CommandKnowledgeIndexer] Успешно проиндексировано {count} утилит System32.")
            return count
        except Exception as exc:
            logger.warning(f"[CommandKnowledgeIndexer] Ошибка индексации System32 catalog: {exc}")
            return 0

    def index_all(self) -> Dict[str, int]:
        """Запускает полную индексацию всех команд, коллекторов, System32 утилит и параметров.

        Returns:
            Словарь с количеством проиндексированных сущностей по категориям.
        """
        atomic_cnt = self.index_atomic_capabilities()
        collector_cnt = self.index_telemetry_collectors()
        param_cnt = self.index_system_params()
        sys32_cnt = self.index_system32_catalog()
        total = atomic_cnt + collector_cnt + param_cnt + sys32_cnt

        return {
            "atomic_capabilities": atomic_cnt,
            "telemetry_collectors": collector_cnt,
            "system_params": param_cnt,
            "system32_tools": sys32_cnt,
            "total_commands_indexed": total,
        }
