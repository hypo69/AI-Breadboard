# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Saves содержимое в файл по указанному пути.
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: save_file.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import argparse

def save_file(path: str, content: str) -> bool:
    """
    Saves содержимое в файл по указанному пути.

    Args:
        path (str): Путь к файлу (string).
        content (str): Содержимое для сохранения (string).

    Returns:
        bool: True, если сохранение successfully, иначе False.

    Examples:
        >>> save_file("test.txt", "hello")
        True
    """
    try:
        # Создание директории, если она отсутствует
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        # Запись содержимого
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        # В реальном проекте здесь должно быть логирование через src.logger.logger
        print(f"Error при сохранении файла: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save content to a file.")
    parser.add_argument("--path", required=True, help="Path to the file.")
    parser.add_argument("--content", required=True, help="Content to save.")
    args = parser.parse_args()
    
    success = save_file(args.path, args.content)
    if success:
        print(f"File saved successfully to {args.path}")
    else:
        print("Failed to save file.")
