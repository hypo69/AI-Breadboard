# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Attack Surface Reduction (ASR) Manager
# =============================================================================
# Description:
#   Аудит и диагностика правил Attack Surface Reduction (ASR) Microsoft Defender.
#   Содержит полный каталог GUID стандартных правил ASR, сопоставление
#   текущих режимов (Disabled, Block, Audit, Warn) и рекомендации по защите.
#
# File: asr_manager.py
# Project: ai-breadboard
# Package: apps.windows.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль аудита и управления правилами Attack Surface Reduction (ASR)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.defender.core.defender_service import DefenderService
from apps.windows.defender.core.models import ASRRuleInfo, ProtectionState


class ASRManager:
    """Менеджер правил Attack Surface Reduction (ASR)."""

    # Официальный каталог правил Attack Surface Reduction от Microsoft
    ASR_RULES_CATALOG: Dict[str, Dict[str, str]] = {
        "d4f940ab-401b-4efc-aadc-ad5f3c50688a": {
            "name": "Блокировка кражи учетных данных из подсистемы LSASS",
            "description": "Блокирует попытки дампа памяти и кражи паролей/хешей из процесса lsass.exe.",
            "category": "Credential Theft",
            "recommendation": "Рекомендуется включить в режим 'Block' на всех рабочих станциях.",
        },
        "3b5764aa-a486-44a2-ba62-52b393774756": {
            "name": "Блокировка создания дочерних процессов приложениями Office",
            "description": "Запрещает Word, Excel, PowerPoint создавать дочерние исполняемые процессы (например, CMD, PowerShell).",
            "category": "Office",
            "recommendation": "Критически важное правило против вредоносных документов и макросов.",
        },
        "756346d7-0a4f-429a-830c-32f9e447f538": {
            "name": "Блокировка создания исполняемого контента приложениями Office",
            "description": "Блокирует запись исполняемых файлов (.exe, .dll) на диск из документов Office.",
            "category": "Office",
            "recommendation": "Предотвращает дропперы вредоносного ПО.",
        },
        "26190899-7702-4414-94bb-6c3763670f98": {
            "name": "Блокировка внедрения кода приложениями Office в другие процессы",
            "description": "Блокирует попытки Process Injection из приложений Microsoft Office.",
            "category": "Office",
            "recommendation": "Защищает от сложных fileless техник закрепления.",
        },
        "d3e037e1-3eb8-44c8-a917-57927947596d": {
            "name": "Блокировка создания дочерних процессов Adobe Reader",
            "description": "Запрещает Acrobat Reader запускать дочерние процессы при открытии PDF файлов.",
            "category": "Adobe Reader",
            "recommendation": "Блокирует эксплойты в PDF-документах.",
        },
        "5beb7efe-b997-4b6e-bba4-52c56e3566cb": {
            "name": "Блокировка запуска обфусцированных скриптов",
            "description": "Выявляет и блокирует запуск запутанных (obfuscated) скриптов PowerShell, VBScript, JScript.",
            "category": "Scripts",
            "recommendation": "Эффективная защита от загрузчиков и скриптовых атак.",
        },
        "92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b": {
            "name": "Блокировка подозрительного поведения скриптов VBScript/JScript",
            "description": "Блокирует загрузку и запуск исполняемых файлов классическими движками скриптов.",
            "category": "Scripts",
            "recommendation": "Рекомендуется режим 'Block'.",
        },
        "01443614-cd74-433a-b99e-2ecdc07bfc25": {
            "name": "Блокировка создания исполняемых файлов через WMI/PSExec",
            "description": "Блокирует создание и удаленный запуск процессов через WMI и утилиты типа PSExec.",
            "category": "Lateral Movement",
            "recommendation": "Защищает от горизонтального перемещения злоумышленников в сети.",
        },
        "c1db55ab-c21a-4637-bb3f-a12568109d35": {
            "name": "Расширенная защита от программ-вымогателей (Ransomware)",
            "description": "Блокирует нетипичные попытки массового шифрования и модификации файлов.",
            "category": "Ransomware",
            "recommendation": "Обязательное правило для противодействия вымогателям.",
        },
        "9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2": {
            "name": "Блокировка кражи учетных данных из веб-браузеров и LSASS через WMI",
            "description": "Блокирует обращение вредоносного ПО к хранилищам паролей.",
            "category": "Credential Theft",
            "recommendation": "Рекомендуется режим 'Block'.",
        },
        "56a863a9-875e-4185-98a7-b882c60b5ce5": {
            "name": "Блокировка запуска неподписанных и недоверенных файлов из USB",
            "description": "Запрещает запуск исполняемых файлов с подключаемых съемных накопителей.",
            "category": "USB & Removable",
            "recommendation": "Защищает от зараженных флешек и переносных носителей.",
        },
        "b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4": {
            "name": "Блокировка запуска недоверенных исполняемых файлов, не соответствующих критерию распространенности",
            "description": "Блокирует запуск редких/новых файлов без достаточной репутации в облаке Microsoft.",
            "category": "Untrusted Binaries",
            "recommendation": "Рекомендуется режим 'Block' или 'Audit'.",
        },
        "e6db77e5-3e12-4247-8177-410e1147ccf3": {
            "name": "Блокировка постоянства (Persistence) через WMI события",
            "description": "Блокирует закрепление вредоносного ПО в системе через постоянные WMI подписки (WMI Event Consumers).",
            "category": "Persistence",
            "recommendation": "Защищает от скрытых способов автозагрузки в обход реестра.",
        },
        "56a863a9-875e-4185-98a7-b882c60b5ce6": {
            "name": "Блокировка использования уязвимых подписанных драйверов (BYOVD)",
            "description": "Блокирует атаки Bring Your Own Vulnerable Driver для обхода ядра Windows.",
            "category": "Drivers",
            "recommendation": "Критично для предотвращения атак на уровне ядра ОС.",
        },
    }

    ACTION_MAP = {
        0: ProtectionState.DISABLED,
        1: ProtectionState.ENABLED,  # Block
        2: ProtectionState.AUDIT,
        6: ProtectionState.WARN,
    }

    def __init__(self, defender_service: Optional[DefenderService] = None) -> None:
        """Инициализация менеджера ASR.

        Args:
            defender_service: Опциональный экземпляр DefenderService.
        """
        self._service = defender_service or DefenderService()

    def get_asr_rules(self) -> List[ASRRuleInfo]:
        """Получение списка всех правил ASR с текущим статусом их конфигурации.

        Returns:
            List[ASRRuleInfo]: Список правил ASR с описанием и статусом.
        """
        pref_data = self._service._run_powershell_json("Get-MpPreference")
        configured_rules: Dict[str, ProtectionState] = {}

        if pref_data:
            rule_ids = pref_data.get("AttackSurfaceReductionRules_Ids") or []
            rule_actions = pref_data.get("AttackSurfaceReductionRules_Actions") or []

            # Приведение к списку, если возвращен единичный элемент
            if isinstance(rule_ids, str):
                rule_ids = [rule_ids]
            if isinstance(rule_actions, int):
                rule_actions = [rule_actions]

            for i, guid in enumerate(rule_ids):
                clean_guid = str(guid).strip().lower()
                action_val = rule_actions[i] if i < len(rule_actions) else 0
                state = self.ACTION_MAP.get(action_val, ProtectionState.UNKNOWN)
                configured_rules[clean_guid] = state

        results: List[ASRRuleInfo] = []
        for guid, meta in self.ASR_RULES_CATALOG.items():
            state = configured_rules.get(guid.lower(), ProtectionState.NOT_CONFIGURED)
            results.append(
                ASRRuleInfo(
                    guid=guid,
                    name=meta["name"],
                    description=meta["description"],
                    category=meta["category"],
                    recommendation=meta["recommendation"],
                    state=state,
                )
            )

        return results
