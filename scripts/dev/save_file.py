# -*- coding: utf-8 -*-
# =============================================================================
# Название модуля: save_file
# =============================================================================
# Описание:
#   Модуль для безопасного сохранения данных в файл.
#
# File: save_file.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import argparse

def save_file(path: str, content: str) -> bool:
    """
    Сохраняет содержимое в файл по указанному пути.

    Args:
        path (str): Путь к файлу (строка).
        content (str): Содержимое для сохранения (строка).

    Returns:
        bool: True, если сохранение успешно, иначе False.

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
        print(f"Ошибка при сохранении файла: {e}")
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
