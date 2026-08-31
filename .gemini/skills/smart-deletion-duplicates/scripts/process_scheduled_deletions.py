# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: process_scheduled_deletions.py
# Project: ai-breadboard
# Package: .gemini.skills.smart-deletion-duplicates.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import os
import argparse

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'

def process_deletions(execute=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM media WHERE status = 'кандидат на удаление'")
    candidates = cursor.fetchall()
    
    if not candidates:
        print("Нет записей со статусом 'кандидат на удаление'.")
        conn.close()
        return

    print(f"Найдено {len(candidates)} кандидатов на удаление.")
    
    for id, path in candidates:
        # Check существования файла
        if os.path.exists(path):
            if execute:
                try:
                    os.remove(path)
                    print(f"Файл удален: {path}")
                    # Удаление записи из БД
                    cursor.execute("DELETE FROM media WHERE id = ?", (id,))
                    print(f"Запись {id} удалена из БД.")
                except Exception as e:
                    print(f"Error при удалении {path}: {e}")
            else:
                print(f"[DRY RUN] Файл доступен для удаления: {path}")
        else:
            print(f"[SKIP] Файл недоступен (диск отключен?): {path}")
    
    if execute:
        conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='Execute deletion')
    args = parser.parse_args()
    
    process_deletions(execute=args.execute)

if __name__ == '__main__':
    main()
