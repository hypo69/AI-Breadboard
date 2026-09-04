# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Manual log analysis script
# =============================================================================
# Description:
#   One-time script for analyzing application logs. Run manually when needed.
#
# File: analyze_logs.py
# Project: ai-breadboard
# Package: scripts.maintenance
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Manual log analysis script.

One-time script for analyzing application logs. Run manually: python scripts/analyze_logs.py"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.logger.log_analyzer import analyze_log_file, LOG_DIR, get_max_size_bytes
from src.ai import GoogleGenerativeAI
from src.logger import logger

async def main():
    logger.info("=" * 60)
    logger.info("STARTING LOG ANALYSIS (MANUAL MODE)")
    logger.info("=" * 60)

    if not LOG_DIR.exists():
        logger.error(f"Log directory not found: {LOG_DIR}")
        return

    # Setup AI
    api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
    system_instruction = "You are a professional system log analyst. Your task is to examine logs, identify errors, issues, trends and provide recommendations for resolution."

    ai_model = GoogleGenerativeAI(
        api_key_names=api_key_names,
        system_instruction=system_instruction
    )

    max_bytes = get_max_size_bytes()
    files_to_analyze = []

    # Search for .log files
    for p in LOG_DIR.glob("*.log"):
        if p.is_file() and p.stat().st_size >= max_bytes:
            files_to_analyze.append(p)
            logger.info(f"Found file: {p.name} ({p.stat().st_size / 1024 / 1024:.1f} MB)")

    # Search for log.json
    json_log = LOG_DIR / "log.json"
    if json_log.exists() and json_log.is_file() and json_log.stat().st_size >= max_bytes:
        files_to_analyze.append(json_log)
        logger.info(f"Found file: {json_log.name} ({json_log.stat().st_size / 1024 / 1024:.1f} MB)")

    if not files_to_analyze:
        logger.info("No files to analyze (all smaller than {} MB threshold)".format(
            float(os.getenv('LOG_MAX_SIZE_MB', '10.0'))
        ))
        return

    logger.info(f"Files to analyze: {len(files_to_analyze)}")

    # Analyze each file
    for file_path in files_to_analyze:
        await analyze_log_file(file_path, ai_model)

    logger.info("=" * 60)
    logger.info("LOG ANALYSIS COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
