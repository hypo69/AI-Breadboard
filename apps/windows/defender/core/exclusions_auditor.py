# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Defender Exclusions Security Auditor
# =============================================================================
# Description:
#   Аудит исключений из антивирусной проверки (пути, расширения, процессы).
#   Эвристический анализ рисков для выявления опасных конфигураций
#   (например, исключение системных папок C:\, Temp, общих путей или системных процессов).
#
# File: exclusions_auditor.py
# Project: ai-breadboard
# Package: apps.windows.defender.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль аудита исключений безопасности Microsoft Defender."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from logger import logger
from apps.windows.defender.core.defender_service import DefenderService
from apps.windows.defender.core.models import (
    ExclusionItem,
    ExclusionRiskLevel,
    ExclusionsAuditReport,
)


class ExclusionsAuditor:
    """Анализатор и аудитор исключений Defender."""

    # Опасные расширения файлов
    CRITICAL_EXTENSIONS = {".exe", ".dll", ".sys", ".scr", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".hta"}
    
    # Опасные имена процессов
    CRITICAL_PROCESSES = {
        "powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe", "cscript.exe",
        "rundll32.exe", "mshta.exe", "regsvr32.exe", "svchost.exe", "explorer.exe",
        "certutil.exe", "bitsadmin.exe", "curl.exe", "bash.exe", "wsl.exe"
    }

    def __init__(self, defender_service: Optional[DefenderService] = None) -> None:
        """Инициализация аудитора исключений."""
        self._service = defender_service or DefenderService()

    def _analyze_path_risk(self, path: str) -> Tuple[ExclusionRiskLevel, str]:
        """Оценка уровня риска для исключенного пути.

        Args:
            path: Путь к файлу или каталогу.

        Returns:
            Tuple[ExclusionRiskLevel, str]: Уровень риска и текстовое обоснование.
        """
        p_lower = path.strip().lower()

        # 1. Корневые диски и маски корней
        if re.match(r"^[a-z]:\\?\*?$", p_lower) or p_lower in ("c:", "c:\\", "c:\\*", "d:\\*"):
            return (
                ExclusionRiskLevel.CRITICAL,
                "Исключение всего диска целиком полностью ослепляет защиту на данном накопителе.",
            )

        # 2. Системные директории Windows и System32
        if "c:\\windows" in p_lower or "system32" in p_lower or "syswow64" in p_lower:
            return (
                ExclusionRiskLevel.CRITICAL,
                "Исключение системной директории Windows позволяет вредоносному ПО скрываться без обнаружения.",
            )

        # 3. Временные папки (Temp, %TEMP%, AppData\Local\Temp)
        if "\\temp" in p_lower or "%temp%" in p_lower or "\\tmp" in p_lower:
            return (
                ExclusionRiskLevel.HIGH,
                "Временные папки — основное место выгрузки дропперов и первичных стадий вредоносного ПО.",
            )

        # 4. Общие пользовательские папки (C:\Users\*, C:\Users\Public)
        if re.match(r"^c:\\users\\\*?", p_lower) or "c:\\users\\public" in p_lower:
            return (
                ExclusionRiskLevel.HIGH,
                "Широкое исключение каталогов пользователей создает уязвимость для скачиваемых из сети файлов.",
            )

        # 5. Каталоги инструментов разработки или утилит (C:\Tools, D:\Dev)
        if any(token in p_lower for token in ["c:\\tools", "c:\\dev", "d:\\dev", "c:\\bin"]):
            return (
                ExclusionRiskLevel.MEDIUM,
                "Каталог инструментов разработки часто используется для вспомогательного ПО; убедитесь в чистоте содержимого.",
            )

        return (ExclusionRiskLevel.SAFE, "Легитимный специфический путь.")

    def _analyze_extension_risk(self, ext: str) -> Tuple[ExclusionRiskLevel, str]:
        """Оценка риска исключенного расширения файла.

        Args:
            ext: Расширение файла (например, .exe).

        Returns:
            Tuple[ExclusionRiskLevel, str]: Уровень риска и обоснование.
        """
        clean_ext = ext.strip().lower()
        if not clean_ext.startswith("."):
            clean_ext = "." + clean_ext

        if clean_ext in self.CRITICAL_EXTENSIONS:
            return (
                ExclusionRiskLevel.CRITICAL,
                f"Исключение исполняемого расширения '{clean_ext}' позволяет вредоносному коду выполняться без проверки.",
            )

        if clean_ext in {".zip", ".rar", ".7z", ".iso", ".tar", ".gz"}:
            return (
                ExclusionRiskLevel.HIGH,
                f"Исключение архивов '{clean_ext}' препятствует проверке упакованных угроз при распаковке.",
            )

        return (ExclusionRiskLevel.LOW, f"Исключение расширения '{clean_ext}'.")

    def _analyze_process_risk(self, proc: str) -> Tuple[ExclusionRiskLevel, str]:
        """Оценка риска исключенного процесса.

        Args:
            proc: Имя исполняемого файла процесса или путь к нему.

        Returns:
            Tuple[ExclusionRiskLevel, str]: Уровень риска и обоснование.
        """
        p_base = proc.strip().lower().replace("/", "\\").split("\\")[-1]

        if p_base in self.CRITICAL_PROCESSES:
            return (
                ExclusionRiskLevel.CRITICAL,
                f"Исключение системного интерпретатора '{p_base}' полностью открывает систему для Fileless и скриптовых атак.",
            )

        return (ExclusionRiskLevel.MEDIUM, f"Исключение процесса '{p_base}'. Требуется проверка источника запуска.")

    def audit_exclusions(self) -> ExclusionsAuditReport:
        """Сбор и эвристический аудит всех исключений Defender.

        Returns:
            ExclusionsAuditReport: Детальный отчет с оценками рисков.
        """
        pref_data = self._service._run_powershell_json("Get-MpPreference")
        path_items: List[ExclusionItem] = []
        ext_items: List[ExclusionItem] = []
        proc_items: List[ExclusionItem] = []

        if pref_data:
            # 1. Пути
            raw_paths = pref_data.get("ExclusionPath") or []
            if isinstance(raw_paths, str):
                raw_paths = [raw_paths]
            for p in raw_paths:
                risk, reason = self._analyze_path_risk(p)
                path_items.append(
                    ExclusionItem(
                        type="path",
                        value=p,
                        risk_level=risk,
                        risk_reason=reason,
                    )
                )

            # 2. Расширения
            raw_exts = pref_data.get("ExclusionExtension") or []
            if isinstance(raw_exts, str):
                raw_exts = [raw_exts]
            for ext in raw_exts:
                risk, reason = self._analyze_extension_risk(ext)
                ext_items.append(
                    ExclusionItem(
                        type="extension",
                        value=ext,
                        risk_level=risk,
                        risk_reason=reason,
                    )
                )

            # 3. Процессы
            raw_procs = pref_data.get("ExclusionProcess") or []
            if isinstance(raw_procs, str):
                raw_procs = [raw_procs]
            for proc in raw_procs:
                risk, reason = self._analyze_process_risk(proc)
                proc_items.append(
                    ExclusionItem(
                        type="process",
                        value=proc,
                        risk_level=risk,
                        risk_reason=reason,
                    )
                )

        all_items = path_items + ext_items + proc_items
        suspicious = [i for i in all_items if i.risk_level in (ExclusionRiskLevel.HIGH, ExclusionRiskLevel.CRITICAL)]

        if suspicious:
            rec = f"Обнаружено {len(suspicious)} подозрительных/критических исключений! Настоятельно рекомендуется удалить широкие маски путей и системные интерпретаторы из исключений."
        elif all_items:
            rec = f"Сконфигурировано {len(all_items)} исключений с низким уровнем риска."
        else:
            rec = "Исключения отсутствуют. Антивирусная защита работает в полном объеме."

        return ExclusionsAuditReport(
            total_exclusions=len(all_items),
            suspicious_count=len(suspicious),
            path_exclusions=path_items,
            extension_exclusions=ext_items,
            process_exclusions=proc_items,
            summary_recommendation=rec,
        )
