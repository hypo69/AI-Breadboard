# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Video file download and processing utilities
# =============================================================================
# Description:
#   This module provides asynchronous functions for downloading and saving video files, as well as retri
#
# File: video.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Video saving utilities for generating and saving video files."""

""" This module provides asynchronous functions for downloading and saving video files, as well as retrieving video data.  It includes error handling and logging for robust operation.

Functions:
    save_video_from_url(url: str, save_path: str) -> Optional[Path]:
        Download a video from a URL and save it locally asynchronously.  Handles potential network issues and file saving errors.

    get_video_data(file_name: str) -> Optional[bytes]:
        Retrieve binary data of a video file if it exists.  Handles file not found and read errors.

Examples:
    >>> import asyncio
    >>> asyncio.run(save_video_from_url("https://example.com/video.mp4", "local_video.mp4"))
    PosixPath('local_video.mp4')  # or None if failed

    >>> data = get_video_data("local_video.mp4")
    >>> if data:
    ...     print(data[:10])  # Print first 10 bytes to check
    b'\x00\x00\x00...'
    """

import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
import asyncio
from src.logger.logger import logger

async def save_video_from_url(
    url: str,
    save_path: str
) -> Optional[Path]:
    """Download a video from a URL and save it locally asynchronously.

    Args:
        url (str): The URL from which to download the video.
        save_path (str): The path to save the downloaded video.

    Returns:
        Optional[Path]: The path to the saved file, or `None` if the operation failed.  Returns None on errors and if file is 0 bytes.

    Raises:
        aiohttp.ClientError: on network issues during the download.
    """
    save_path = Path(save_path)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Check for HTTP errors

                # Create parent directories if they don't exist
                save_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(save_path, "wb") as file:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        await file.write(chunk)

        # Crucial checks after saving
        if not save_path.exists():
            logger.error(f"File {save_path} not saved successfully.")
            return None

        if save_path.stat().st_size == 0:
            logger.error(f"Downloaded file {save_path} is empty.")
            return None

        return save_path

    except aiohttp.ClientError as e:
        logger.error(f"Network error downloading video: {e}")
        return None
    except Exception as e:
        logger.error(f"Error saving video {save_path}: {e}", exc_info=True)
        return None

def get_video_data(file_name: str) -> Optional[bytes]:
    """Retrieve binary data of a video file if it exists.

    Args:
        file_name (str): The path to the video file to read.

    Returns:
        Optional[bytes]: The binary data of the file if it exists, or `None` if the file is not found or an error occurred.
    """
    file_path = Path(file_name)

    if not file_path.exists():
        logger.error(f"File {file_name} not found.")
        return None

    try:
        with open(file_path, "rb") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_name}: {e}", exc_info=True)
        return None

def main():
    url = "https://example.com/video.mp4"  # Replace with a valid URL!
    save_path = "local_video.mp4"
    result = asyncio.run(save_video_from_url(url, save_path))
    if result:
        print(f"Video saved to {result}")

if __name__ == "__main__":
    main()