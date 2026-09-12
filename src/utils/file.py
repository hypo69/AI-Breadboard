# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: File system operations and text file utilities
# =============================================================================
# Description:
#   Module for file operations including saving, reading, and searching text files.
#   Provides utilities for directory traversal and file pattern matching.
#
# File: file.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
File system operations and text file utilities.

Provides functions for file manipulation, reading, writing, and searching.
"""

import os
import json
import fnmatch
from pathlib import Path
from typing import List, Optional, Union, Generator
from src.logger.logger import logger

def save_text_file(
    data: str | list[str] | dict,
    file_path: Union[str, Path],
    mode: str = "w",
    exc_info: bool = True,
) -> bool:
    """
    Save data to a text file.

    Args:
        data (str | list[str] | dict): Data to write (can be string, list of strings, or dictionary).
        file_path (str | Path): Path where the file will be saved.
        mode (str, optional): Write mode (`w` for write, `a` for append). Defaults to 'w'.
        exc_info (bool, optional): If True, logs traceback on error. Defaults to True.

    Returns:
        bool: True if the file was successfully saved, False otherwise.
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open(mode, encoding="utf-8") as file:
            if isinstance(data, list):
                file.writelines(f"{line}\n" for line in data)
            elif isinstance(data, dict):
                json.dump(data, file, ensure_ascii=False, indent=4)
            else:
                file.write(data)
        return True
    except Exception as ex:
        logger.error(f"Failed to save file {file_path}.", ex, exc_info=exc_info)
        return False

def read_text_file(
    file_path: Union[str, Path],
    as_list: bool = False,
    extensions: Optional[list[str]] = None,
    exc_info: bool = True,
) -> Union[str, list[str], None]:
    """
    Read the contents of a file.

    Args:
        file_path (str | Path): Path to the file or directory.
        as_list (bool, optional): If True, returns content as list of lines. Defaults to False.
        extensions (list[str], optional): List of file extensions to include if reading a directory. Defaults to None.
        exc_info (bool, optional): If True, logs traceback on error. Defaults to True.

    Returns:
        str | list[str] | None: File content as a string or list of lines, or None if an error occurs.
    """
    try:
        path = Path(file_path)
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                return f.readlines() if as_list else f.read()
        elif path.is_dir():
            files = [
                p for p in path.rglob("*") if p.is_file() and (not extensions or p.suffix in extensions)
            ]
            contents = [read_text_file(p, as_list) for p in files]
            return [item for sublist in contents if sublist for item in sublist] if as_list else "\n".join(filter(None, contents))
        else:
            logger.warning(f"Path '{file_path}' is invalid.")
            return None
    except Exception as ex:
        logger.error(f"Failed to read file {file_path}.", ex, exc_info=exc_info)
        return None

def get_filenames(
    directory: Union[str, Path], extensions: Union[str, list[str]] = "*", exc_info: bool = True
) -> list[str]:
    """
    Get filenames in a directory optionally filtered by extension.

    Args:
        directory (str | Path): Directory to search.
        extensions (str | list[str], optional): Extensions to filter. Defaults to '*'.

    Returns:
        list[str]: Filenames found in the directory.
    """
    try:
        path = Path(directory)
        if isinstance(extensions, str):
            extensions = [extensions] if extensions != "*" else []
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]

        return [
            file.name
            for file in path.iterdir()
            if file.is_file() and (not extensions or file.suffix in extensions)
        ]
    except Exception as ex:
        logger.warning(f"Failed to list filenames in '{directory}'.", ex, exc_info=exc_info)
        return []

def recursively_yield_file_path(
    root_dir: Union[str, Path], patterns: Union[str, list[str]] = "*", exc_info: bool = True
) -> Generator[Path, None, None]:
    """
    Recursively yield file paths matching given patterns.

    Args:
        root_dir (str | Path): Root directory to search.
        patterns (str | list[str]): Patterns to filter files.

    Yields:
        Path: File paths matching the patterns.
    """
    try:
        patterns = [patterns] if isinstance(patterns, str) else patterns
        for pattern in patterns:
            yield from Path(root_dir).rglob(pattern)
    except Exception as ex:
        logger.error(f"Failed to search files in '{root_dir}'.", ex, exc_info=exc_info)

def recursively_get_file_path(
    root_dir: Union[str, Path], 
    patterns: Union[str, list[str]] = "*", 
    exc_info: bool = True
) -> list[Path]:
    """
    Recursively get file paths matching given patterns.

    Args:
        root_dir (str | Path): Root directory to search.
        patterns (str | list[str]): Patterns to filter files.

    Returns:
        list[Path]: List of file paths matching the patterns.
    """
    try:
        file_paths = []
        patterns = [patterns] if isinstance(patterns, str) else patterns
        for pattern in patterns:
            file_paths.extend(Path(root_dir).rglob(pattern))
        return file_paths
    except Exception as ex:
        logger.error(f"Failed to search files in '{root_dir}'.", ex, exc_info=exc_info)
        return []

def recursively_read_text_files(
    root_dir: str | Path, 
    patterns: str | list[str], 
    as_list: bool = False, 
    exc_info: bool = True
) -> list[str]:
    """
    Recursively reads text files from the specified root directory that match the given patterns.

    Args:
        root_dir (str | Path): Path to the root directory for the search.
        patterns (str | list[str]): Filename pattern(s) to filter the files.
                                    Can be a single pattern (e.g., '*.txt') or a list of patterns.
        as_list (bool, optional): If True, returns the file content as a list of lines.
                                  Defaults to False.
        exc_info (bool, optional): If True, includes exception information in warnings. Defaults to True.

    Returns:
        list[str]: List of file contents (or lines if `as_list=True`) that match the specified patterns.

    Example:
        >>> contents = recursively_read_text_files("/path/to/root", ["*.txt", "*.md"], as_list=True)
        >>> for line in contents:
        ...     print(line)
        This will print each line from all matched text files in the specified directory.
    """
    matches = []
    root_path = Path(root_dir)

    # Check if the root directory exists
    if not root_path.is_dir():
        logger.debug(f"The root directory '{root_path}' does not exist or is not a directory.")
        return []

    print(f"Searching in directory: {root_path}")

    # Normalize patterns to a list if it's a single string
    if isinstance(patterns, str):
        patterns = [patterns]

    for root, dirs, files in os.walk(root_path):
        for filename in files:
            # Check if the filename matches any of the specified patterns
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
                file_path = Path(root) / filename

                try:
                    with file_path.open("r", encoding="utf-8") as file:
                        if as_list:
                            # Read lines if `as_list=True`
                            matches.extend(file.readlines())
                        else:
                            # Read entire content otherwise
                            matches.append(file.read())
                except Exception as ex:
                    logger.warning(f"Failed to read file '{file_path}'.", exc_info=exc_info)

    return matches

def get_directory_names(directory: str | Path, exc_info: bool = True) -> list[str]:
    """
    Retrieves all directory names from the specified directory.

    Args:
        directory (str | Path): Path to the directory from which directory names should be retrieved.
        exc_info (bool, optional): If True, logs traceback information in case of an error. Defaults to True.

    Returns:
        list[str]: List of directory names found in the specified directory.

    Example:
        >>> directories: list[str] = get_directory_names(directory=".") 
        >>> print(directories)
        ['dir1', 'dir2']
    
    More documentation: https://github.com/hypo69/tiny-utils/wiki/Files-and-Directories#get_directory_names
    """
    try:
        return [entry.name for entry in Path(directory).iterdir() if entry.is_dir()]
    except Exception as ex:
        if exc_info:
            logger.warning(
                f"Failed to get directory names from '{directory}'.",
                ex,
                exc_info=exc_info,
            )
        return 

def read_files_content(
    root_dir: Union[str, Path],
    patterns: Union[str, list[str]],
    as_list: bool = False,
    exc_info: bool = True,
) -> list[str]:
    """
    Read contents of files matching patterns.

    Args:
        root_dir (str | Path): Root directory to search.
        patterns (str | list[str]): File patterns to match.
        as_list (bool, optional): Return content as list of lines. Defaults to False.

    Returns:
        list[str]: List of file contents.
    """
    content = []
    for file_path in recursively_get_files(root_dir, patterns, exc_info):
        file_content = read_text_file(file_path, as_list, exc_info=exc_info)
        if file_content:
            content.extend(file_content if as_list else [file_content])
    return content

def remove_bom(file_path: Union[str, Path]) -> None:
    """
    Remove BOM from a text file.

    Args:
        file_path (str | Path): File to process.
    """
    path = Path(file_path)
    try:
        with path.open("r+", encoding="utf-8") as file:
            content = file.read().replace("\ufeff", "")
            file.seek(0)
            file.write(content)
            file.truncate()
    except Exception as ex:
        logger.error(f"Failed to remove BOM from '{file_path}'.", ex)

def traverse_and_clean(directory: Union[str, Path]) -> None:
    """
    Traverse directory and remove BOM from Python files.

    Args:
        directory (str | Path): Root directory to process.
    """
    for file in recursively_get_files(directory, "*.py"):
        remove_bom(file)

def main() -> None:
    """Entry point for BOM removal in Python files."""
    root_dir = Path("..", "src")
    logger.info(f"Starting BOM removal in {root_dir}")
    traverse_and_clean(root_dir)

if __name__ == "__main__":
    main()
