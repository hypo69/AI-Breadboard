# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Client Resource Analyzer
# =============================================================================
# Description:
#   Анализ ресурсов программ, запущенных клиентом (память, процессор, диск),
#   и экспертная оценка аномальных/неизвестных ресурсоемких процессов через модель Gemini.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.client_resource_analyzer import ClientResourceAnalyzer
#
#     analyzer = ClientResourceAnalyzer()
#     summary = await analyzer.analyze_client_resources()
#
# File: client_resource_analyzer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:47:00
# =============================================================================

from __future__ import annotations
"""Анализ ресурсов программ, запущенных клиентом, и оценка неизвестных процессов через Gemini."""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import ClientProgramResource, ClientResourceSummary, UnknownProgramEvaluation
from .query_engine import TelemetryQueryEngine

try:
    from src.ai.orchestration.unified_chat import UnifiedChatModel
except Exception as ex:
    logger.warning(f"Не удалось импортировать UnifiedChatModel: {ex}")
    UnifiedChatModel = None

# Базовый список системных процессов ядра Windows (не являются программами клиента)
SYSTEM_PROCESS_NAMES: Set[str] = {
    "system", "system idle process", "idle", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "fontdrvhost.exe",
    "dwm.exe", "spoolsv.exe", "conhost.exe", "sihost.exe", "taskhostw.exe",
    "winlogon.exe", "memory compression", "werfault.exe", "wmiapsrv.exe",
    "wmiprvse.exe", "searchindexer.exe", "audiodg.exe", "dashost.exe",
    "securityhealthservice.exe", "msmpeng.exe", "nissrv.exe", "smartscreen.exe",
    "lsiso.exe", "rundll32.exe", "dllhost.exe"
}

# Каталог известных доверенных клиентских программ
KNOWN_CLIENT_APPS: Dict[str, Dict[str, str]] = {
    "chrome.exe": {"display_name": "Google Chrome", "publisher": "Google LLC", "category": "Браузер"},
    "msedge.exe": {"display_name": "Microsoft Edge", "publisher": "Microsoft Corporation", "category": "Браузер"},
    "firefox.exe": {"display_name": "Mozilla Firefox", "publisher": "Mozilla Foundation", "category": "Браузер"},
    "brave.exe": {"display_name": "Brave Browser", "publisher": "Brave Software", "category": "Браузер"},
    "opera.exe": {"display_name": "Opera Browser", "publisher": "Opera Norway", "category": "Браузер"},
    "code.exe": {"display_name": "Visual Studio Code", "publisher": "Microsoft Corporation", "category": "Разработка"},
    "devenv.exe": {"display_name": "Visual Studio", "publisher": "Microsoft Corporation", "category": "Разработка"},
    "pycharm64.exe": {"display_name": "PyCharm", "publisher": "JetBrains s.r.o.", "category": "Разработка"},
    "idea64.exe": {"display_name": "IntelliJ IDEA", "publisher": "JetBrains s.r.o.", "category": "Разработка"},
    "telegram.exe": {"display_name": "Telegram Desktop", "publisher": "Telegram FZ-LLC", "category": "Мессенджер"},
    "discord.exe": {"display_name": "Discord", "publisher": "Discord Inc.", "category": "Мессенджер"},
    "slack.exe": {"display_name": "Slack", "publisher": "Slack Technologies", "category": "Мессенджер"},
    "teams.exe": {"display_name": "Microsoft Teams", "publisher": "Microsoft Corporation", "category": "Мессенджер"},
    "steam.exe": {"display_name": "Steam Client", "publisher": "Valve Corporation", "category": "Игры"},
    "epicgameslauncher.exe": {"display_name": "Epic Games Launcher", "publisher": "Epic Games", "category": "Игры"},
    "spotify.exe": {"display_name": "Spotify", "publisher": "Spotify AB", "category": "Медиа"},
    "vlc.exe": {"display_name": "VLC Media Player", "publisher": "VideoLAN", "category": "Медиа"},
    "explorer.exe": {"display_name": "Проводник Windows", "publisher": "Microsoft Corporation", "category": "Система"},
    "powershell.exe": {"display_name": "PowerShell", "publisher": "Microsoft Corporation", "category": "Инструменты"},
    "pwsh.exe": {"display_name": "PowerShell 7", "publisher": "Microsoft Corporation", "category": "Инструменты"},
    "cmd.exe": {"display_name": "Командная строка", "publisher": "Microsoft Corporation", "category": "Инструменты"},
    "git.exe": {"display_name": "Git", "publisher": "Software Freedom Conservancy", "category": "Разработка"},
    "python.exe": {"display_name": "Python Interpreter", "publisher": "Python Software Foundation", "category": "Разработка"},
    "py.exe": {"display_name": "Python Launcher", "publisher": "Python Software Foundation", "category": "Разработка"},
    "node.exe": {"display_name": "Node.js Runtime", "publisher": "OpenJS Foundation", "category": "Разработка"},
    "docker.exe": {"display_name": "Docker Desktop", "publisher": "Docker Inc.", "category": "Разработка"},
    "postman.exe": {"display_name": "Postman", "publisher": "Postman Inc.", "category": "Разработка"},
    "winrar.exe": {"display_name": "WinRAR", "publisher": "win.rar GmbH", "category": "Утилиты"},
    "7z.exe": {"display_name": "7-Zip", "publisher": "Igor Pavlov", "category": "Утилиты"},
    "7zfm.exe": {"display_name": "7-Zip File Manager", "publisher": "Igor Pavlov", "category": "Утилиты"},
    "notepad.exe": {"display_name": "Блокнот", "publisher": "Microsoft Corporation", "category": "Утилиты"},
    "notepad++.exe": {"display_name": "Notepad++", "publisher": "Don HO", "category": "Разработка"},
}


class ClientResourceAnalyzer:
    """Анализатор потребления ресурсов клиентскими программами с диагностикой через Gemini."""

    def __init__(
        self,
        query_engine: Optional[TelemetryQueryEngine] = None,
        chat_model: Optional[Any] = None,
        cpu_heavy_threshold: float = 15.0,
        memory_heavy_mb_threshold: float = 500.0,
        disk_io_heavy_mb_threshold: float = 10.0,
    ) -> None:
        """Инициализация анализатора клиентских ресурсов.

        Args:
            query_engine: Движок запросов к telemetry.db.
            chat_model: Экземпляр модели AI (по умолчанию UnifiedChatModel с провайдером Gemini).
            cpu_heavy_threshold: Порог загрузки процессора (%) для классификации как ресурсоемкий.
            memory_heavy_mb_threshold: Порог памяти (МБ) для классификации как ресурсоемкий.
            disk_io_heavy_mb_threshold: Порог дискового ввода-вывода (МБ/с).
        """
        self.query_engine = query_engine or TelemetryQueryEngine()
        self._chat_model = chat_model
        self.cpu_heavy_threshold = cpu_heavy_threshold
        self.memory_heavy_mb_threshold = memory_heavy_mb_threshold
        self.disk_io_heavy_mb_threshold = disk_io_heavy_mb_threshold
        self._evaluations_cache: Dict[str, UnknownProgramEvaluation] = {}

    @property
    def chat_model(self) -> Any:
        """Получить активный экземпляр языковой модели."""
        if self._chat_model is None and UnifiedChatModel is not None:
            try:
                self._chat_model = UnifiedChatModel()
            except Exception as ex:
                logger.warning(f"Не удалось инициализировать UnifiedChatModel: {ex}")
                self._chat_model = None
        return self._chat_model

    def is_client_program(self, proc_name: str, username: Optional[str] = None, path: Optional[str] = None) -> bool:
        """Определить, запущена ли программа клиентом (пользователем), а не ядром системы.

        Args:
            proc_name: Имя исполняемого файла процесса.
            username: Учетная запись владельца процесса.
            path: Путь к исполняемому файлу.

        Returns:
            bool: True если процесс относится к пользовательским приложениям.
        """
        name_lower = (proc_name or "").strip().lower()
        if not name_lower or name_lower in SYSTEM_PROCESS_NAMES:
            return False

        # Если имя пользователя явно указывает на системные аккаунты NT AUTHORITY
        user_lower = (username or "").strip().lower()
        if user_lower in {"nt authority\\system", "nt authority\\local service", "nt authority\\network service", "system"}:
            # Некоторые пользовательские программы могут запускаться под SYSTEM как сервисы, но по умолчанию фильтруем
            if name_lower not in KNOWN_CLIENT_APPS:
                return False

        return True

    def is_known_software(self, proc_name: str, path: Optional[str] = None) -> bool:
        """Проверить, является ли программа известным доверенным ПО.

        Args:
            proc_name: Имя процесса.
            path: Путь к файлу.

        Returns:
            bool: True если программа находится в базе известных приложений или системных директорий.
        """
        name_lower = (proc_name or "").strip().lower()
        if name_lower in KNOWN_CLIENT_APPS or name_lower in SYSTEM_PROCESS_NAMES:
            return True

        if path:
            path_lower = path.lower()
            # Программы из Program Files с известными вендорами
            if ("program files" in path_lower or "windowsapps" in path_lower) and not ("temp" in path_lower):
                return True

        return False

    def get_file_size_mb(self, path: Optional[str]) -> Optional[float]:
        """Получить размер исполняемого файла программы на диске в МБ.

        Args:
            path: Путь к исполняемому файлу.

        Returns:
            Optional[float]: Размер файла в МБ или None если файл недоступен.
        """
        if not path:
            return None
        try:
            p = Path(path)
            if p.exists() and p.is_file():
                return round(p.stat().st_size / (1024.0 * 1024.0), 2)
        except Exception:
            pass
        return None

    def calculate_resource_score(self, cpu_pct: float, ram_mb: float, disk_io_mbs: float) -> float:
        """Рассчитать совокупный скор ресурсоемкости процесса (0..100+).

        Args:
            cpu_pct: Загрузка ЦП в %.
            ram_mb: Память в МБ.
            disk_io_mbs: Дисковая активность в МБ/с.

        Returns:
            float: Индекс ресурсоемкости.
        """
        # Веса: 1% CPU = 1.0 балл, 100 МБ RAM = 1.0 балл, 5 МБ/с Disk = 1.0 балл
        score = (cpu_pct * 1.0) + (ram_mb / 100.0) + (disk_io_mbs / 5.0)
        return round(score, 2)

    def is_heavy_resource_consumer(self, cpu_pct: float, ram_mb: float, disk_io_mbs: float) -> bool:
        """Определить, потребляет ли программа аномально много системных ресурсов.

        Args:
            cpu_pct: Загрузка ЦП в %.
            ram_mb: Память в МБ.
            disk_io_mbs: Скорость диска в МБ/с.

        Returns:
            bool: True если процесс превышает установленные пороговые значения.
        """
        if cpu_pct >= self.cpu_heavy_threshold:
            return True
        if ram_mb >= self.memory_heavy_mb_threshold:
            return True
        if disk_io_mbs >= self.disk_io_heavy_mb_threshold:
            return True
        return False

    def load_raw_client_processes(self, db_path: Optional[Union[str, Path]] = None, limit: int = 150) -> List[Dict[str, Any]]:
        """Загрузить сырые данные о процессах из telemetry.db и живого снимка.

        Args:
            db_path: Путь к базе данных SQLite.
            limit: Лимит выборки записей.

        Returns:
            List[Dict[str, Any]]: Список словарей процессов.
        """
        target_db = self.query_engine.get_db_path(db_path)
        raw_list: List[Dict[str, Any]] = []

        if target_db and target_db.exists():
            import sqlite3
            try:
                conn = sqlite3.connect(str(target_db), timeout=5.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 1. Извлекаем последние снимки процессов из process_snapshots
                cursor.execute("""
                    SELECT pid, name, cpu_percent, memory_mb, memory_percent,
                           num_threads, num_handles, username, read_bytes_sec, write_bytes_sec,
                           executable as executable_path, cmdline as command_line
                    FROM process_snapshots
                    WHERE id IN (
                        SELECT MAX(id) FROM process_snapshots GROUP BY pid
                    )
                    ORDER BY cpu_percent DESC, memory_mb DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                for r in rows:
                    raw_list.append(dict(r))

                # 2. Если таблица пуста, пробуем process_rollups_daily / process_outliers
                if not raw_list:
                    cursor.execute("""
                        SELECT 0 as pid, name, avg_cpu_percent as cpu_percent, avg_memory_mb as memory_mb,
                               0.0 as memory_percent, 1 as num_threads, 0 as num_handles,
                               'Client' as username, 0.0 as read_bytes_sec, 0.0 as write_bytes_sec,
                               '' as executable_path, '' as command_line
                        FROM process_rollups_daily
                        ORDER BY avg_cpu_percent DESC, avg_memory_mb DESC
                        LIMIT ?
                    """, (limit,))
                    for r in cursor.fetchall():
                        raw_list.append(dict(r))

                conn.close()
            except Exception as ex:
                logger.warning(f"Ошибка чтения процессов из SQLite базы {target_db}: {ex}")

        # 3. Дополняем активными процессами через psutil при наличии
        if not raw_list:
            try:
                import psutil
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'memory_percent', 'num_threads', 'num_handles', 'username', 'exe', 'cmdline']):
                    try:
                        info = p.info
                        mem_mb = (info.get('memory_info').rss / (1024 * 1024)) if info.get('memory_info') else 0.0
                        raw_list.append({
                            'pid': info.get('pid') or 0,
                            'name': info.get('name') or '',
                            'cpu_percent': info.get('cpu_percent') or 0.0,
                            'memory_mb': round(mem_mb, 2),
                            'memory_percent': round(info.get('memory_percent') or 0.0, 2),
                            'num_threads': info.get('num_threads') or 0,
                            'num_handles': info.get('num_handles') or 0,
                            'username': info.get('username') or '',
                            'read_bytes_sec': 0.0,
                            'write_bytes_sec': 0.0,
                            'executable_path': info.get('exe') or '',
                            'command_line': ' '.join(info.get('cmdline') or []),
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as ex:
                logger.debug(f"psutil fallback недоступен: {ex}")

        return raw_list

    async def evaluate_program_with_gemini(self, program: ClientProgramResource) -> UnknownProgramEvaluation:
        """Спросить у модели Gemini, насколько нормально такое потребление ресурсов для программы.

        Args:
            program: Объект с данными ресурсоемкости программы.

        Returns:
            UnknownProgramEvaluation: Структурированное заключение модели Gemini.
        """
        cache_key = f"{program.name}:{program.pid}:{round(program.cpu_percent, -1)}:{round(program.memory_mb, -2)}"
        if cache_key in self._evaluations_cache:
            return self._evaluations_cache[cache_key]

        disk_io = round((program.disk_read_bytes_sec + program.disk_write_bytes_sec) / (1024.0 * 1024.0), 2)
        path_str = program.executable_path or "Путь не определен (запуск из памяти/скрипта)"
        cmd_str = program.command_line or "Командная строка недоступна"

        prompt = (
            f"Ты — ведущий эксперт по информационной безопасности и оптимизации производительности Windows.\n"
            f"Проанализируй запущенную на компьютере пользователя программу и ответь, насколько нормально такое потребление ресурсов:\n\n"
            f"📌 **Параметры программы:**\n"
            f"- Имя процесса: `{program.name}` (PID: {program.pid})\n"
            f"- Путь к файлу: `{path_str}`\n"
            f"- Аргументы запуска: `{cmd_str}`\n"
            f"- Пользователь: `{program.username or 'Текущий клиент'}`\n"
            f"- Загрузка ЦП (CPU): **{program.cpu_percent}%**\n"
            f"- Использование RAM: **{program.memory_mb} МБ** ({program.memory_percent}% от общей памяти)\n"
            f"- Дисковый ввод-вывод (I/O): **{disk_io} МБ/с**\n"
            f"- Размер исполняемого файла: **{program.disk_size_mb or 'Неизвестен'} МБ**\n"
            f"- Потоков: {program.num_threads}, Дескрипторов: {program.num_handles}\n\n"
            f"Ответь строго в формате JSON со следующими полями:\n"
            f"{{\n"
            f'  "is_normal": true|false,\n'
            f'  "confidence": 0.0-1.0,\n'
            f'  "risk_level": "low"|"medium"|"high"|"critical",\n'
            f'  "verdict": "Краткий вывод на русском языке (до 10 слов)",\n'
            f'  "analysis": "Подробное объяснение на русском языке: что это за программа, нормально ли для нее такое потребление памяти/CPU/диска, может ли это быть майнер, утечка памяти или вредоносная активность.",\n'
            f'  "recommendations": ["Рекомендация 1", "Рекомендация 2"]\n'
            f"}}"
        )

        model_name = "gemini-2.5-flash"
        eval_result: Optional[UnknownProgramEvaluation] = None

        if self.chat_model and hasattr(self.chat_model, "ask"):
            try:
                raw_response = await asyncio.wait_for(self.chat_model.ask(prompt), timeout=6.0)
                if raw_response:
                    cleaned_json = raw_response.strip()
                    if "```json" in cleaned_json:
                        cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
                    elif "```" in cleaned_json:
                        cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()

                    parsed = json.loads(cleaned_json)
                    eval_result = UnknownProgramEvaluation(
                        program_name=program.name,
                        pid=program.pid,
                        executable_path=program.executable_path,
                        command_line=program.command_line,
                        cpu_percent=program.cpu_percent,
                        memory_mb=program.memory_mb,
                        disk_io_mb_s=disk_io,
                        disk_size_mb=program.disk_size_mb,
                        is_normal=bool(parsed.get("is_normal", True)),
                        confidence=float(parsed.get("confidence", 0.85)),
                        risk_level=str(parsed.get("risk_level", "medium")),
                        verdict=str(parsed.get("verdict", "Анализ завершен")),
                        analysis=str(parsed.get("analysis", "Экспертный анализ модели Gemini.")),
                        recommendations=list(parsed.get("recommendations", [])),
                        evaluated_at=datetime.now(timezone.utc).isoformat(),
                        model_used=model_name,
                    )
            except Exception as ex:
                logger.warning(f"Ошибка вызова Gemini для оценки программы {program.name}: {ex}")

        # Детерминированный fallback если LLM недоступна
        if eval_result is None:
            is_suspicious_location = any(
                loc in (program.executable_path or "").lower() for loc in ("\\temp\\", "\\appdata\\local\\temp", "\\users\\public\\")
            )
            is_high_risk = is_suspicious_location or (program.cpu_percent > 70.0 and not program.is_known_software)
            risk = "high" if is_high_risk else ("medium" if not program.is_known_software else "low")
            verdict = "Подозрительная активность" if is_high_risk else ("Штатная активность" if program.is_known_software else "Неизвестное приложение")
            analysis = (
                f"Программа {program.name} потребляет {program.cpu_percent}% ЦП и {program.memory_mb} МБ RAM. "
                + ("Запуск из временного каталога Temp требует повышенного внимания." if is_suspicious_location else "Рекомендуется проверить цифровую подпись исполняемого файла.")
            )
            recs = [
                "Проверить контрольную сумму и происхождение файла",
                "При непрекращающейся высокой нагрузке завершить процесс через диспетчер задач"
            ]
            eval_result = UnknownProgramEvaluation(
                program_name=program.name,
                pid=program.pid,
                executable_path=program.executable_path,
                command_line=program.command_line,
                cpu_percent=program.cpu_percent,
                memory_mb=program.memory_mb,
                disk_io_mb_s=disk_io,
                disk_size_mb=program.disk_size_mb,
                is_normal=not is_high_risk,
                confidence=0.75,
                risk_level=risk,
                verdict=verdict,
                analysis=analysis,
                recommendations=recs,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
                model_used="deterministic-heuristics",
            )

        self._evaluations_cache[cache_key] = eval_result
        return eval_result

    async def analyze_client_resources(
        self,
        db_path: Optional[Union[str, Path]] = None,
        ask_gemini_for_unknown: bool = True,
        limit: int = 50,
    ) -> ClientResourceSummary:
        """Провести комплексный аудит ресурсов клиентских программ.

        Args:
            db_path: Путь к базе данных телеметрии.
            ask_gemini_for_unknown: Опрашивать ли Gemini для неизвестных ресурсоемких программ.
            limit: Максимальное количество анализируемых программ.

        Returns:
            ClientResourceSummary: Сводка по ресурсам всех программ клиента и вердикты Gemini.
        """
        raw_procs = self.load_raw_client_processes(db_path=db_path, limit=limit * 2)
        client_programs: List[ClientProgramResource] = []
        evaluations: List[UnknownProgramEvaluation] = []

        seen_keys: Set[Tuple[str, int]] = set()

        for raw in raw_procs:
            p_name = raw.get("name") or "unknown.exe"
            p_pid = int(raw.get("pid") or 0)
            key = (p_name.lower(), p_pid)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            path = raw.get("executable_path") or raw.get("path")
            username = raw.get("username")

            # Проверяем, что это клиентская программа, а не системная служба
            if not self.is_client_program(p_name, username=username, path=path):
                continue

            cpu_pct = float(raw.get("cpu_percent") or 0.0)
            mem_mb = float(raw.get("memory_mb") or 0.0)
            mem_pct = float(raw.get("memory_percent") or 0.0)
            read_bytes = float(raw.get("read_bytes_sec") or 0.0)
            write_bytes = float(raw.get("write_bytes_sec") or 0.0)
            disk_io_mbs = round((read_bytes + write_bytes) / (1024.0 * 1024.0), 2)
            disk_size = self.get_file_size_mb(path)

            is_known = self.is_known_software(p_name, path=path)
            is_heavy = self.is_heavy_resource_consumer(cpu_pct, mem_mb, disk_io_mbs)
            score = self.calculate_resource_score(cpu_pct, mem_mb, disk_io_mbs)

            known_meta = KNOWN_CLIENT_APPS.get(p_name.lower(), {})
            disp_name = known_meta.get("display_name") or p_name
            publisher = known_meta.get("publisher")
            category = known_meta.get("category", "Клиентское приложение")

            prog = ClientProgramResource(
                pid=p_pid,
                name=p_name,
                display_name=disp_name,
                executable_path=path,
                command_line=raw.get("command_line"),
                username=username,
                cpu_percent=round(cpu_pct, 1),
                memory_mb=round(mem_mb, 1),
                memory_percent=round(mem_pct, 1),
                disk_read_bytes_sec=read_bytes,
                disk_write_bytes_sec=write_bytes,
                disk_size_mb=disk_size,
                num_threads=int(raw.get("num_threads") or 0),
                num_handles=int(raw.get("num_handles") or 0),
                is_known_software=is_known,
                is_client_program=True,
                is_resource_heavy=is_heavy,
                resource_score=score,
                category=category,
                publisher=publisher,
            )

            # Если программа неизвестная и ресурсоемкая — запрашиваем оценку Gemini
            if is_heavy and not is_known and ask_gemini_for_unknown:
                eval_item = await self.evaluate_program_with_gemini(prog)
                prog.gemini_evaluation = eval_item
                evaluations.append(eval_item)

            client_programs.append(prog)
            if len(client_programs) >= limit:
                break

        # Сортировка по скору ресурсоемкости (самые тяжелые вверху)
        client_programs.sort(key=lambda p: p.resource_score, reverse=True)

        total_ram = round(sum(p.memory_mb for p in client_programs), 1)
        total_cpu = round(sum(p.cpu_percent for p in client_programs), 1)
        total_disk = round(sum((p.disk_size_mb or 0.0) for p in client_programs), 1)
        heavy_count = sum(1 for p in client_programs if p.is_resource_heavy)
        unknown_heavy_count = sum(1 for p in client_programs if p.is_resource_heavy and not p.is_known_software)

        return ClientResourceSummary(
            total_client_programs=len(client_programs),
            total_ram_mb=total_ram,
            total_cpu_percent=total_cpu,
            total_disk_size_mb=total_disk,
            heavy_programs_count=heavy_count,
            unknown_heavy_programs_count=unknown_heavy_count,
            programs=client_programs,
            evaluations=evaluations,
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )
