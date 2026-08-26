# -*- coding: utf-8 -*-
import os
import asyncio
import datetime
from pathlib import Path
from core.ai import GoogleGenerativeAI
from core.logger import logger
from header import __root__

LOG_DIR = __root__ / 'tmp' / 'logs'
REPORTS_DIR = __root__ / 'tmp' / 'reports'

def get_max_size_bytes() -> float:
    try:
        from core.config import logging_cfg
        mb = float(getattr(logging_cfg, "max_size_mb", 10.0)) if logging_cfg else 10.0
        return mb * 1024 * 1024
    except Exception:
        return 10.0 * 1024 * 1024

async def analyze_log_file(file_path: Path, ai_model: GoogleGenerativeAI):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if not content.strip():
            return

        logger.info(f"Начало умного анализа лога {file_path.name}...")

        max_chars = 500 * 1024  # 500KB для экономии квоты
        if len(content) > max_chars:
            content = content[-max_chars:]

        prompt = f"""
Проанализируй следующий лог-файл ({file_path.name}).
Выяви ошибки, предупреждения, критические проблемы, а также общие тренды и дай рекомендации по исправлению.
Ответ предоставь на русском языке в чистом формате Markdown.

Содержимое лога:
{content}
"""
        report_text = await ai_model.ask(prompt)
        
        if not report_text:
            report_text = f"# Отчет об анализе лога {file_path.name}\n\nНе удалось получить анализ от модели Gemini."

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"report_{file_path.stem}_{timestamp}.md"
        report_path = REPORTS_DIR / report_name
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        # Clear the original log file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.truncate(0)

        logger.info(f"Лог {file_path.name} успешно проанализирован и очищен. Отчет сохранен в {report_name}")

        await update_master_journal(ai_model)

    except Exception as ex:
        logger.error(f"Ошибка при анализе лог-файла {file_path.name}", ex)

async def update_master_journal(ai_model: GoogleGenerativeAI):
    try:
        if not REPORTS_DIR.exists():
            return

        report_files = [p for p in REPORTS_DIR.glob("report_*.md") if p.name != "master_journal.md"]
        if not report_files:
            return

        report_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        reports_content = []
        for p in report_files[:10]:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    reports_content.append(f"### Файл: {p.name}\n{f.read()}\n")
            except Exception:
                pass

        if not reports_content:
            return

        prompt = f"""
На основе следующих индивидуающих отчетов об анализе логов составь общий единый журнал (Master Journal) состояния системы.
Выдели:
1. Повторяющиеся и постоянные ошибки.
2. Новые обнаруженные тенденции.
3. Актуальные проблемы, требующие внимания разработчика на текущий момент.
4. Устаревшие или неактуальные проблемы, которые перестали появляться.

Ответ выведи строго на русском языке в формате Markdown.

Индивидуальные отчеты:
{"".join(reports_content)}
"""
        master_text = await ai_model.ask(prompt)
        if not master_text:
            master_text = "# Общий журнал анализа логов\n\nНе удалось получить общий анализ от модели Gemini."

        master_path = REPORTS_DIR / "master_journal.md"
        with open(master_path, 'w', encoding='utf-8') as f:
            f.write(master_text)

        logger.info("Общий журнал (master_journal.md) успешно обновлен.")

    except Exception as ex:
        logger.error("Ошибка при обновлении общего журнала логов", ex)

async def log_analyzer_loop():
    logger.info("Запуск фоновой службы интеллектуального анализа логов...")
    
    # Проверяем, включён ли анализ логов
    from core.config import logging_cfg
    if not logging_cfg or not getattr(logging_cfg, "enable_log_analyzer", False):
        logger.info("Анализ логов отключён (в config.json)")
        return
    
    api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
    system_instruction = "Вы — профессиональный аналитик системных логов. Ваша задача — исследовать логи, выявлять ошибки, проблемы, тренды и давать рекомендации по устранению."
    
    ai_model = GoogleGenerativeAI(
        api_key_names=api_key_names,
        system_instruction=system_instruction
    )

    while True:
        try:
            if LOG_DIR.exists():
                max_bytes = get_max_size_bytes()
                for p in LOG_DIR.glob("*.log"):
                    if p.is_file() and p.stat().st_size >= max_bytes:
                        await analyze_log_file(p, ai_model)
                        
                json_log = LOG_DIR / "log.json"
                if json_log.exists() and json_log.is_file() and json_log.stat().st_size >= max_bytes:
                    await analyze_log_file(json_log, ai_model)

        except Exception as ex:
            logger.error("Ошибка в цикле анализатора логов", ex)

        await asyncio.sleep(60)

LOCK_FILE = LOG_DIR / 'log_analyzer.lock'

def start_log_analyzer():
    """Запускает анализатор логов только в одном процессе."""
    # Проверяем lock-файл
    try:
        if LOCK_FILE.exists():
            # Проверяем, жив ли процесс
            try:
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.read().strip())
                # Попытка проверить существование процесса (Windows)
                import psutil
                if psutil.pid_exists(pid):
                    logger.info(f"Анализатор логов уже запущен (PID: {pid})")
                    return
            except (ValueError, ImportError, psutil.NoSuchProcess):
                pass
            # Lock-файл устаревший, удаляем
            LOCK_FILE.unlink(missing_ok=True)
        
        # Создаём lock-файл с текущим PID
        import subprocess
        pid = subprocess.os.getpid()
        LOCK_FILE.write_text(str(pid), encoding='utf-8')
        
        asyncio.create_task(log_analyzer_loop())
    except Exception as ex:
        logger.error(f"Ошибка при запуске анализатора логов: {ex}")
