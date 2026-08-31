# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Save content to file at specified path
# =============================================================================
# Description:
#   Saves file content to disk at specified path with directory creation
#   and error handling. Useful for programmatic file writing operations.
#
# File: save_file.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""File content saving utility.

Provides function to save text content to files with automatic directory
creation and proper error handling."""

import os
import argparse

def save_file(path: str, content: str) -> bool:
    """Save content to file at specified path.

    Creates necessary directories if they don't exist and writes
    content to file with UTF-8 encoding.

    Args:
        path: File path where content should be saved.
        content: Text content to write to file.

    Returns:
        True if save successful, False if error occurred.

    Examples:
        >>> save_file("test.txt", "hello")
        True
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        # Write content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        # In production, logging should use src.logger.logger
        print(f"Error saving file: {e}")
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
