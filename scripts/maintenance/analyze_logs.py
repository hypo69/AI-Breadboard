# -*- coding: utf-8 -*-
"""
Одноразовый скрипт для анализа логов.
Запускать вручную: python scripts/analyze_logs.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger.log_analyzer import analyze_log_file, LOG_DIR, get_max_size_bytes
from core.ai import GoogleGenerativeAI
from core.logger import logger


async def main():
    logger.info("=" * 60)
    logger.info("ЗАПУСК АНАЛИЗА ЛОГОВ (РУЧНОЙ РЕЖИМ)")
    logger.info("=" * 60)

    if not LOG_DIR.exists():
        logger.error(f"Директория логов не найдена: {LOG_DIR}")
        return

    # Настройка AI
    api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
    system_instruction = "Вы — профессиональный аналитик системных логов. Ваша задача — исследовать логи, выявлять ошибки, проблемы, тренды и давать рекомендации по устранению."

    ai_model = GoogleGenerativeAI(
        api_key_names=api_key_names,
        system_instruction=system_instruction
    )

    max_bytes = get_max_size_bytes()
    files_to_analyze = []

    # Поиск .log файлов
    for p in LOG_DIR.glob("*.log"):
        if p.is_file() and p.stat().st_size >= max_bytes:
            files_to_analyze.append(p)
            logger.info(f"Найден файл: {p.name} ({p.stat().st_size / 1024 / 1024:.1f} MB)")

    # Поиск log.json
    json_log = LOG_DIR / "log.json"
    if json_log.exists() and json_log.is_file() and json_log.stat().st_size >= max_bytes:
        files_to_analyze.append(json_log)
        logger.info(f"Найден файл: {json_log.name} ({json_log.stat().st_size / 1024 / 1024:.1f} MB)")

    if not files_to_analyze:
        logger.info("Нет файлов для анализа (все меньше порога {} MB)".format(
            float(os.getenv('LOG_MAX_SIZE_MB', '10.0'))
        ))
        return

    logger.info(f"Будет проанализировано файлов: {len(files_to_analyze)}")

    # Анализ каждого файла
    for file_path in files_to_analyze:
        await analyze_log_file(file_path, ai_model)

    logger.info("=" * 60)
    logger.info("АНАЛИЗ ЛОГОВ ЗАВЕРШЁН")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())