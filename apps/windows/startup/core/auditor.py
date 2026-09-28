"""Движок глубокого аудита безопасности и производительности автозапуска."""
from __future__ import annotations
import os
import platform
import time
from datetime import datetime
from typing import List, Tuple
from logger import logger
from apps.windows.startup.core.models import AuditReport, AuditSummary, ItemCategory, RiskLevel, StartupEntry, StartupLocationType
from apps.windows.startup.core.scanner import StartupScanner

class StartupAuditor:
    """Аудитор безопасности и чистоты автозапуска Windows."""

    def __init__(self, scanner: StartupScanner | None=None) -> None:
        """Инициализация аудитора автозапуска.

        Args:
            scanner: Опциональный экземпляр сканера точек автозапуска.
        """
        self.scanner = scanner or StartupScanner()

    def run_audit(self) -> AuditReport:
        """Запускает полное сканирование и формирует детальный отчет аудита.

        Returns:
            AuditReport: Полный отчет с классификацией, оценками риска и рекомендациями.
        """
        start_time = time.perf_counter()
        raw_entries = self.scanner.scan_all()
        audited_entries: List[StartupEntry] = []
        for entry in raw_entries:
            audited = self._audit_entry(entry)
            audited_entries.append(audited)
        summary = self._build_summary(audited_entries)
        recommendations = self._generate_system_recommendations(audited_entries, summary)
        alerts = [e for e in audited_entries if e.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.CRITICAL)]
        broken = [e for e in audited_entries if not e.file_exists and e.risk_level != RiskLevel.CLEAN]
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return AuditReport(timestamp=datetime.now().isoformat(), hostname=platform.node(), os_name=f'{platform.system()} {platform.release()} ({platform.version()})', scan_duration_ms=round(duration_ms, 2), summary=summary, entries=audited_entries, security_alerts=alerts, broken_items=broken, recommendations=recommendations)

    def _audit_entry(self, entry: StartupEntry) -> StartupEntry:
        """Детальный аудит отдельной записи автозапуска."""
        reasons: List[str] = []
        risk = RiskLevel.CLEAN
        cat = ItemCategory.UNKNOWN
        impact = 'Низкое'
        rec = 'Оставить как есть'
        path_lower = (entry.executable_path or '').lower()
        cmd_lower = (entry.command or '').lower()
        args_lower = (entry.arguments or '').lower()
        name_lower = (entry.name or '').lower()
        if entry.location_type == StartupLocationType.IFEO:
            risk = RiskLevel.CRITICAL
            cat = ItemCategory.SUSPICIOUS_SCRIPT
            reasons.append('Обнаружен отладочный перехватчик запуска (IFEO Debugger). Возможна персистентность вредоносного ПО.')
            rec = 'Удалить отладочный перехватчик из реестра IFEO'
            impact = 'Высокое'
        elif not entry.file_exists and entry.executable_path:
            cat = ItemCategory.BROKEN_ENTRY
            risk = RiskLevel.WARNING
            reasons.append(f'Исполняемый файл не найден на диске: {entry.executable_path}')
            rec = 'Удалить или очистить битую ссылку автозапуска'
            impact = 'Низкое'
        elif any((f in cmd_lower or f in args_lower for f in ('-encodedcommand', '-enc ', '-windowstyle hidden', '-w hidden', 'bypass -c'))):
            risk = RiskLevel.CRITICAL
            cat = ItemCategory.SUSPICIOUS_SCRIPT
            reasons.append('Командная строка содержит скрытые или закодированные параметры выполнения (PowerShell/CMD).')
            rec = 'Отключить немедленно и выполнить проверку безопасности'
            impact = 'Среднее'
        elif any((p in path_lower for p in ('\\appdata\\local\\temp', '\\windows\\temp', '\\users\\public'))):
            risk = RiskLevel.SUSPICIOUS
            cat = ItemCategory.SUSPICIOUS_SCRIPT
            reasons.append('Запуск исполняемого файла из временного или общедоступного каталога (Temp / Public).')
            rec = 'Проверить источник файла и отключить автозапуск'
            impact = 'Среднее'
        elif any((eng in path_lower for eng in ('mshta.exe', 'wscript.exe', 'cscript.exe', 'regsvr32.exe', 'certutil.exe'))):
            risk = RiskLevel.SUSPICIOUS
            cat = ItemCategory.SUSPICIOUS_SCRIPT
            reasons.append(f'Автозапуск скриптового интерпретатора ({Path(entry.executable_path).name}).')
            rec = 'Изучить исполняемый скрипт и отключить при отсутствии необходимости'
            impact = 'Среднее'
        elif 'microsoft' in entry.publisher.lower() or '\\windows\\system32' in path_lower or '\\windows\\winsxs' in path_lower:
            cat = ItemCategory.SYSTEM_CORE
            risk = RiskLevel.CLEAN
            rec = 'Системный доверенный компонент Windows'
            impact = 'Низкое'
        elif any((v in path_lower or v in entry.publisher.lower() for v in ('nvidia', 'realtek', 'intel', 'amd', 'synaptics', 'logitech'))):
            cat = ItemCategory.HARDWARE_DRIVER
            risk = RiskLevel.CLEAN
            rec = 'Драйвер или утилита оборудования'
            impact = 'Среднее'
        elif any((u in name_lower or u in cmd_lower for u in ('update', 'updater', 'autoupdate', 'crashreport'))):
            cat = ItemCategory.BACKGROUND_UPDATER
            risk = RiskLevel.NOTICE
            reasons.append('Фоновый модуль проверки обновлений. Замедляет вход в систему.')
            rec = 'Можно отключить для ускорения загрузки Windows'
            impact = 'Среднее'
        elif any((app in path_lower for app in ('chrome.exe', 'telegram.exe', 'discord.exe', 'steam.exe', 'spotify.exe', 'slack.exe', 'viber.exe'))):
            cat = ItemCategory.KNOWN_APP
            risk = RiskLevel.NOTICE
            reasons.append('Стороннее пользовательское приложение в автозагрузке.')
            rec = 'Отключить, если приложение не требуется сразу при старте ПК'
            impact = 'Высокое'
        else:
            cat = ItemCategory.UNKNOWN
            risk = RiskLevel.NOTICE
            reasons.append('Сторонняя программа автозапуска.')
            rec = 'Проверить необходимость автоматического старта'
            impact = 'Среднее'
        if not entry.is_enabled:
            impact = 'Отключено'
            rec = 'Элемент уже отключен в Диспетчере задач'
        entry.category = cat
        entry.risk_level = risk
        entry.risk_reasons = reasons
        entry.boot_impact = impact
        entry.recommendation = rec
        return entry

    def _build_summary(self, entries: List[StartupEntry]) -> AuditSummary:
        """Подсчет статистики и расчет индекса безопасности."""
        summary = AuditSummary()
        summary.total_entries = len(entries)
        for e in entries:
            if e.is_enabled:
                summary.active_entries += 1
            else:
                summary.disabled_entries += 1
            if not e.file_exists and e.executable_path:
                summary.broken_entries += 1
            if e.risk_level == RiskLevel.CLEAN:
                summary.clean_count += 1
            elif e.risk_level == RiskLevel.NOTICE:
                summary.notice_count += 1
            elif e.risk_level == RiskLevel.WARNING:
                summary.warning_count += 1
            elif e.risk_level == RiskLevel.SUSPICIOUS:
                summary.suspicious_count += 1
            elif e.risk_level == RiskLevel.CRITICAL:
                summary.critical_count += 1
            cat_val = e.category.value if hasattr(e.category, 'value') else str(e.category)
            summary.categories_breakdown[cat_val] = summary.categories_breakdown.get(cat_val, 0) + 1
            loc_val = e.location_type.value if hasattr(e.location_type, 'value') else str(e.location_type)
            summary.locations_breakdown[loc_val] = summary.locations_breakdown.get(loc_val, 0) + 1
        score = 100
        score -= summary.critical_count * 25
        score -= summary.suspicious_count * 15
        score -= summary.warning_count * 5
        if summary.active_entries > 10:
            score -= (summary.active_entries - 10) * 2
        summary.health_score = max(0, min(100, score))
        return summary

    def _generate_system_recommendations(self, entries: List[StartupEntry], summary: AuditSummary) -> List[str]:
        """Генерация сводных рекомендаций по оптимизации автозапуска."""
        recs: List[str] = []
        if summary.critical_count > 0:
            recs.append(f'⚠️ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ УГРОЗЫ ({summary.critical_count} шт.): Немедленно проверьте отладочные перехватчики или скрытые скрипты!')
        if summary.suspicious_count > 0:
            recs.append(f'🔍 Внимание: найдено {summary.suspicious_count} подозрительных записей во временных папках или скриптах. Рекомендуется их отключить.')
        if summary.broken_entries > 0:
            recs.append(f'🧹 Очистка: обнаружено {summary.broken_entries} битых ссылок автозагрузки, ссылающихся на несуществующие файлы.')
        if summary.active_entries > 15:
            recs.append(f'⚡ Оптимизация старта: у вас активно {summary.active_entries} программ автозапуска. Отключение тяжелых фоновых апдейтеров ускорит загрузку Windows.')
        else:
            recs.append('✅ Конфигурация автозапуска находится в хорошем состоянии.')
        return recs