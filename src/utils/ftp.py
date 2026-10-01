# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard UTILS - Ftp Module
# =============================================================================
# Description:
#   FTP interface for sending, receiving, and deleting files from FTP servers.
#
# Usage Examples:
#   Python API:
#     from src.utils.ftp import write
#
#     res = write()
#     print(res)
#
# File: ftp.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""FTP interface for sending, receiving, and deleting files from FTP servers.

Allows for sending media files, spreadsheets, and other files to and from an FTP server.

Dependencies:
- typing: Type hints for function parameters and return values.
- ftplib: Provides FTP protocol client capabilities.
- pathlib: For handling file system paths.

Functions:
    - `write`: Sends a file to an FTP server.
    - `read`: Retrieves a file from an FTP server.
    - `delete`: Deletes a file from an FTP server."""

from logger import logger
from typing import Union
import ftplib
from pathlib import Path
_connection = {'server': 'ftp.example.com', 'port': 21, 'user': 'username', 'password': 'password'}

def write(source_file_path: str, dest_dir: str, dest_file_name: str) -> bool:
    """
    Sends a file to an FTP server.

    Args:
        source_file_path (str): The path of the file to be sent.
        dest_dir (str): The destination directory on the FTP server.
        dest_file_name (str): The name of the file on the FTP server.

    Returns:
        bool: True if the file is successfully sent, False otherwise.

    Example:
        >>> success = write('local_path/to/file.txt', '/remote/directory', 'file.txt')
        >>> print(success)
        True
    """
    try:
        session = ftplib.FTP(_connection['server'], _connection['user'], _connection['password'])
        session.cwd(dest_dir)
    except Exception as ex:
        logger.error(f'Failed to connect to FTP server. Error: {ex}')
        return False
    try:
        with open(source_file_path, 'rb') as f:
            session.storbinary(f'STOR {dest_file_name}', f)
        return True
    except Exception as ex:
        logger.error(f'Failed to send file to FTP server. Error: {ex}')
        return False
    finally:
        try:
            session.quit()
        except Exception as ex:
            logger.error(f'Failed to close FTP session. Error: {ex}')

def read(source_file_path: str, dest_dir: str, dest_file_name: str) -> Union[str, bytes, None]:
    """
    Retrieves a file from an FTP server.

    Args:
        source_file_path (str): The path where the file will be saved locally.
        dest_dir (str): The directory on the FTP server where the file is located.
        dest_file_name (str): The name of the file on the FTP server.

    Returns:
        Union[str, bytes, None]: The file content if successfully retrieved, None otherwise.

    Example:
        >>> content = read('local_path/to/file.txt', '/remote/directory', 'file.txt')
        >>> print(content)
        b'Some file content'
    """
    try:
        session = ftplib.FTP(_connection['server'], _connection['user'], _connection['password'])
        session.cwd(dest_dir)
        with open(source_file_path, 'wb') as f:
            session.retrbinary(f'RETR {dest_file_name}', f.write)
        with open(source_file_path, 'rb') as f:
            return f.read()
    except Exception as ex:
        logger.error(f'Failed to retrieve file from FTP server. Error: {ex}')
        return
    finally:
        try:
            session.quit()
        except Exception as ex:
            logger.error(f'Failed to close FTP session. Error: {ex}')

def delete(source_file_path: str, dest_dir: str, dest_file_name: str) -> bool:
    """
    Deletes a file from an FTP server.

    Args:
        source_file_path (str): The path where the file is located locally (not used).
        dest_dir (str): The directory on the FTP server where the file is located.
        dest_file_name (str): The name of the file on the FTP server.

    Returns:
        bool: True if the file is successfully deleted, False otherwise.

    Example:
        >>> success = delete('local_path/to/file.txt', '/remote/directory', 'file.txt')
        >>> print(success)
        True
    """
    try:
        session = ftplib.FTP(_connection['server'], _connection['user'], _connection['password'])
        session.cwd(dest_dir)
        session.delete(dest_file_name)
        return True
    except Exception as ex:
        logger.error(f'Failed to delete file from FTP server. Error: {ex}')
        return False
    finally:
        try:
            session.quit()
        except Exception as ex:
            logger.error(f'Failed to close FTP session. Error: {ex}')