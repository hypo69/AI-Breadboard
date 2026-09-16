# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: delete_media.py
# Project: ai-breadboard
# Package: .agents.skills.smart-deletion-duplicates.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sqlite3
import os
import pandas as pd
import argparse
import ast

DB_PATH = r'C:\mediateka\plugins\media_organizer\data\media.db'

def delete_media(file_path):
    # 1. Удаление файла с диска
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Файл удален: {file_path}")
        except Exception as e:
            print(f"Error при удалении файла {file_path}: {e}")
            return False
    else:
        print(f"Файл не найден: {file_path}")
        return False
    
    # 2. Удаление записи из БД
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM media WHERE path = ?", (file_path,))
        conn.commit()
        conn.close()
        print(f"Запись удалена из БД: {file_path}")
        return True
    except Exception as e:
        print(f"Error при удалении записи из БД {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, help='Path to CSV with paths to delete')
    parser.add_argument('--execute', action='store_true', help='Execute deletion')
    args = parser.parse_args()
    
    df = pd.read_csv(args.file)
    
    files_to_delete = []
    for _, row in df.iterrows():
        paths = ast.literal_eval(row['to_delete'])
        files_to_delete.extend(paths)
        
    if not args.execute:
        print("Dry run: list of files to delete:")
        for f in files_to_delete:
            print(f)
        print("Run with --execute to proceed.")
        return

    for f in files_to_delete:
        delete_media(f)

if __name__ == '__main__':
    main()
