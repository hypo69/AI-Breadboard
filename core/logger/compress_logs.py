# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Compress repeated lines in log files to [Nx] format
# =============================================================================
# Description:
#   Compresses repeated lines into [Nx] text format for log file reduction.
#
# File: compress_logs.py
# Project: ai-breadboard
# Package: core.logger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Script for log file compression - combines repeated lines.

Reduces log file size by consolidating identical lines into [Nx] format.
Usage: python scripts/compress_logs.py
"""

import sys
from collections import Counter
from pathlib import Path
from typing import List, Tuple

def compress_lines(lines: List[str], min_repeat: int = 2) -> List[str]:
    """Compress repeated lines into [Nx] text format.
    
    Args:
        lines (List[str]): Input lines to compress.
        min_repeat (int): Minimum repetitions to trigger compression.
        
    Returns:
        List[str]: Compressed lines.
    """
    counter = Counter(lines)
    result = []
    
    for line, count in counter.items():
        stripped = line.strip()
        if not stripped:
            continue
        if count >= min_repeat:
            result.append(f"[{count}x] {stripped}")
        else:
            # Unique lines added as-is
            result.append(stripped)
    
    return result

def compress_log_file(input_path: Path, output_path: Path = None, min_repeat: int = 2) -> Tuple[int, int]:
    """Compress log file.
    
    Args:
        input_path (Path): Input log file path.
        output_path (Path): Output log file path (default: .compressed.log).
        min_repeat (int): Minimum repetitions to compress.
        
    Returns:
        Tuple[int, int]: (original_lines_count, compressed_lines_count)
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
    """Main entry point for log compression."""
    from core.logger import logger
    
    logs_dir = Path(__file__).resolve().parent.parent.parent / 'tmp' / 'logs'
    
    if not logs_dir.exists():
        logger.error(f"Logs directory not found: {logs_dir}")
        return
    
    log_files = list(logs_dir.glob('*.log'))
    if not log_files:
        logger.info("No log files found")
        return
    
    logger.info(f"Found files to compress: {len(log_files)}")
    
    for log_file in log_files:
        original, compressed = compress_log_file(log_file)
        if original > 0:
            compression_pct = 100 - compressed * 100 // original
            logger.info(f"{log_file.name}: {original} → {compressed} lines (compression {compression_pct}%)")
        else:
            logger.info(f"{log_file.name}: empty file")

if __name__ == "__main__":
    main()
