# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Dev - Update Model
# =============================================================================
# Description:
#   Update user model preference in database.
#
# Usage Examples:
#   Python API:
#     import scripts.dev.update_model as update_model
#
# File: update_model.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Update user model preference in database.

Updates default AI model selection for all users to latest Gemini model."""

import os
import sqlite3
import sys
from pathlib import Path
from src.config import storage_cfg

try:
    # Ensure users directory exists
    Path(storage_cfg.users_dir).mkdir(parents=True, exist_ok=True)
    # DB path next to users directory
    db_path = Path(storage_cfg.users_dir).with_name('users.db')
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("UPDATE user_settings SET model = 'gemini-2.0-flash'")
    conn.commit()
    print(f"Updated {cursor.rowcount} rows in users.db")
    conn.close()
except Exception as e:
    print(e)
    sys.exit(1)
