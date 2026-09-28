# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Update user model preference in database
# =============================================================================
# Description:
#   Script to update the default AI model preference for all users in the database
#   to the latest Gemini version available.
#
# File: update_model.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Update user model preference in database.

Updates default AI model selection for all users to latest Gemini model."""

import sqlite3
import sys

try:
    import os
from pathlib import Path
from src.config import storage_cfg
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
