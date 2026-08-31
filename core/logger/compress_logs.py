# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Сжимает повторяющиеся строки в формат [Nx] text.""
# =============================================================================
# Description:
#   Сжимает повторяющиеся строки в формат [Nx] text."""
#
# File: compress_logs.py
# Project: ai-breadboard
# Package: scripts.maintenance
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Скрипт для сжатия логов — объединяет повторяющиеся строки.
Запуск: python scripts/compress_logs.py
"""

import sys
from collections import Counter
from pathlib import Path
from typing import List, Tuple

def compress_lines(lines: List[str], min_repeat: int = 2) -> List[str]:
    """Сжимает повторяющиеся строки в формат [Nx] text."""
    counter = Counter(lines)
    result = []
    
    for line, count in counter.items():
        stripped = line.strip()
        if not stripped:
            continue
        if count >= min_repeat:
            result.append(f"[{count}x] {stripped}")
        else:
            # Уникальные строки добавляем как есть
            result.append(stripped)
    
    return result

def compress_log_file(input_path: Path, output_path: Path = None, min_repeat: int = 2) -> Tuple[int, int]:
    """
    Сжимает лог-файл.
    
    Returns:
        Tuple[исходных_строк, уникальных_строк_после_сжатия]
    """
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    if not lines:
        return 0, 0
    
    original_count = len(lines)
    compressed = compress_lines(lines, min_repeat)
    
    if output_path is None:
        output_path = input_path.with_suffix('.compressed.log')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(compressed))
        if compressed:
            f.write('\n')
    
    return original_count, len(compressed)

def main():
    from core.logger import logger
    
    logs_dir = Path(__file__).resolve().parent.parent.parent / 'tmp' / 'logs'
    
    if not logs_dir.exists():
        logger.error(f"Директория логов не найдена: {logs_dir}")
        return
    
    log_files = list(logs_dir.glob('*.log'))
    if not log_files:
        logger.info("Лог-файлы не найдены")
        return
    
    logger.info(f"Найдено файлов для сжатия: {len(log_files)}")
    
    for log_file in log_files:
        original, compressed = compress_log_file(log_file)
        if original > 0:
            logger.info(f"{log_file.name}: {original} → {compressed} строк (compression {100 - compressed*100//original}%)")
        else:
            logger.info(f"{log_file.name}: empty файл")

if __name__ == "__main__":
    main()