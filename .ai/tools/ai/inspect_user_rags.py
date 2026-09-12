# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: inspect_user_rags.py
# Project: ai-breadboard
# Package: .ai.tools.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3

for dbpath in [
    'src/ai/gemini/user_rags/user_rag_1.db',
    'src/ai/gemini/user_rags/user_rag_anon_10.0.0.4.db',
]:
    conn = sqlite3.connect(dbpath)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f'--- {dbpath} ---')
    print('Tables:', [t[0] for t in tables])
    for t in tables:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info({t[0]})').fetchall()]
        print(f'  {t[0]}: {cnt} rows, cols={cols}')
        if cnt > 0:
            row = conn.execute(f'SELECT * FROM {t[0]} LIMIT 1').fetchone()
            # Print all non-blob columns
            for i, c in enumerate(cols):
                val = row[i]
                if not isinstance(val, bytes):
                    print(f'    {c}: {str(val)[:200]}')
    conn.close()
