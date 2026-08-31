# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Image processing utilities for asynchronous file operations
# =============================================================================
# Description:
#   Provides asynchronous functions for downloading, saving, and manipulating images.
#   Supports operations such as URL image downloads, image file saving, random image retrieval,
#   watermark addition, resizing, and format conversion using PIL and aiohttp libraries.
#
# File: image.py
# Project: ai-breadboard
# Package: core.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import aiohttp
import aiofiles
import asyncio
import random
from pathlib import Path
from typing import Optional, Union, Tuple
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from core.logger.logger import logger

class ImageError(Exception):
    """Custom exception for image-related errors."""
    pass

async def save_image_from_url(image_url: str, filename: Union[str, Path]) -> Optional[str]:
    """
    Asynchronous download of image from URL and save to local file.

    Args:
        image_url (str): The URL to download the image from.
        filename (Union[str, Path]): The name of the file to save the image to.

    Returns:
        Optional[str]: The path to the saved file, or None if the operation failed.

    Exceptions:
        ImageError: If the image download or save operation fails.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                image_data = await response.read()
    except Exception as ex:
        logger.error(f"Error downloading image from {image_url}", exc_info=True)
        raise ImageError(f"Failed to download image from {image_url}") from ex

    return await save_image(image_data, filename)

async def save_image(image_data: bytes, file_name: Union[str, Path], format: str = 'PNG') -> Optional[str]:
    """
    Asynchronous saving of image data to file in specified format.

    Args:
        image_data (bytes): The binary image data.
        file_name (Union[str, Path]): The name of the file to save the image to.
        format (str): The format to save the image in, default is PNG.

    Returns:
        Optional[str]: The path to the saved file, or None if the operation failed.

    Exceptions:
        ImageError: If the file cannot be created, saved, or if the saved file is empty.
    """
    file_path = Path(file_name)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)  # Creation of parent directories if they don't exist
        async with aiofiles.open(file_path, "wb") as file:
            await file.write(image_data)

        if not file_path.exists():
            logger.error(f"File {file_path} was not created.")
            raise ImageError(f"File {file_path} was not created.")

        img = Image.open(file_path)
        img.save(file_path, format=format)

        if file_path.stat().st_size == 0:
            logger.error(f"File {file_path} saved, but its size is 0 bytes.")
            raise ImageError(f"File {file_path} saved, but its size is 0 bytes.")

        return str(file_path)

    except Exception as ex:
        logger.critical(f"Failed to save file {file_path}", exc_info=True)
        raise ImageError(f"Failed to save file {file_path}") from ex

def get_image_bytes(image_path: Path, raw: bool = True) -> Optional[Union[BytesIO, bytes]]:
    """
    Reads an image using Pillow and returns its bytes in JPEG format.

    Args:
        image_path (Path): The path to the image file.
        raw (bool): If True, returns a BytesIO object; otherwise, returns bytes. Defaults to True.

    Returns:
        Optional[Union[BytesIO, bytes]]: The bytes of the image in JPEG format, or None if an error occurs.
    """
    try:
        img = Image.open(image_path)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="JPEG")
        return img_byte_arr if raw else img_byte_arr.getvalue()
    except Exception as ex:
        logger.error("Error reading image with Pillow:", exc_info=True)
        return None

def get_raw_image_data(file_name: Union[str, Path]) -> Optional[bytes]:
    """
    Retrieves the raw binary data of a file if it exists.

    Args:
        file_name (Union[str, Path]): The name or path of the file to read.

    Returns:
        Optional[bytes]: The binary data of the file, or None if the file does not exist or an error occurs.
    """
    file_path = Path(file_name)

    if not file_path.exists():
        logger.error(f"File {file_path} does not exist.")
        return None

    try:
        return file_path.read_bytes()
    except Exception as ex:
        logger.error(f"Error reading file {file_path}", exc_info=True)
        return None

def random_image(root_path: Union[str, Path]) -> Optional[str]:
    """
    Recursively searches for a random image in the specified directory.

    Args:
        root_path (Union[str, Path]): The directory to search for images.

    Returns:
        Optional[str]: The path to a random image, or None if no images are found.
    """
    root_path = Path(root_path)
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    image_files = [file_path for file_path in root_path.rglob("*") 
                   if file_path.is_file() and file_path.suffix.lower() in image_extensions]

    if not image_files:
        logger.warning(f"No images found in {root_path}.")
        return None

    return str(random.choice(image_files))

def add_text_watermark(image_path: Union[str, Path], watermark_text: str, output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
    """
    Adds a text watermark to an image.

    Args:
        image_path (Union[str, Path]): Path to the image file.
        watermark_text (str): Text to use as the watermark.
        output_path (Optional[Union[str, Path]]): Path to save the watermarked image.
            Defaults to overwriting the original image.

    Returns:
        Optional[str]: Path to the watermarked image, or None on failure.
    """
    image_path = Path(image_path)
    output_path = image_path if output_path is None else Path(output_path)

    try:
        image = Image.open(image_path).convert("RGBA")

        # Create a transparent layer for the watermark
        watermark_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_layer)

        font_size = min(image.size) // 10  # Adjust the font size based on the image
        try:
            font = ImageFont.truetype("arial.ttf", size=font_size)
        except IOError:
            font = ImageFont.load_default(size=font_size)
            logger.warning("Font arial.ttf not found; using default font.")

        text_width, text_height = draw.textsize(watermark_text, font=font)
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2

        # Draw text on the transparent layer
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))

        # Combine the image and watermark
        watermarked_image = Image.alpha_composite(image, watermark_layer)
        watermarked_image.save(output_path)

        return str(output_path)

    except Exception as ex:
        logger.error(f"Failed to add watermark to {image_path}", exc_info=True)
        return None

def add_image_watermark(input_image_path: Path, watermark_image_path: Path, output_image_path: Optional[Path] = None) -> Optional[Path]:
    """
    Adds a watermark to an image and saves the result to the specified output path.

    Args:
        input_image_path (Path): Path to the input image.
        watermark_image_path (Path): Path to the watermark image.
        output_image_path (Optional[Path]): Path to save the watermarked image.
            If not provided, the image will be saved in an "output" directory.

    Returns:
        Optional[Path]: Path to the saved watermarked image, or None if the operation failed.
    """
    try:
        # Open the base image
        base_image = Image.open(input_image_path)

        # Open the watermark image and convert it to RGBA
        watermark = Image.open(watermark_image_path).convert("RGBA")

        # Set the size of the watermark (8% of the width of the base image)
        position = base_image.size  # Size of the base image (width, height)
        newsize = (int(position[0] * 8 / 100), int(position[0] * 8 / 100))  # New size of the watermark
        watermark = watermark.resize(newsize)  # Resize the watermark

        # Determine the position to place the watermark (bottom-right corner with 20px padding)
        new_position = position[0] - newsize[0] - 20, position[1] - newsize[1] - 20

        # Create a new transparent layer for combining the images
        transparent = Image.new(mode='RGBA', size=position, color=(0, 0, 0, 0))

        # Paste the base image onto the new layer
        transparent.paste(base_image, (0, 0))

        # Paste the watermark on top of the base image
        transparent.paste(watermark, new_position, watermark)

        # Check the image mode and convert the transparent layer to the original mode
        image_mode = base_image.mode
        if image_mode == 'RGB':
            transparent = transparent.convert(image_mode)  # Convert to RGB
        else:
            transparent = transparent.convert('P')  # Convert to palette

        # Save the final_verdict image to the specified output path with optimized quality
        if output_image_path is None:
            output_image_path = input_image_path.parent / "output" / input_image_path.name
        output_image_path.parent.mkdir(parents=True, exist_ok=True)  # Create output directory if it doesn't exist
        transparent.save(output_image_path, optimize=True, quality=100)
        logger.info(f"Saving {output_image_path}...")

        return output_image_path

    except Exception as ex:
        logger.error(f"Failed to add watermark to {input_image_path}: {ex}", exc_info=True)
        return None

def resize_image(image_path: Union[str, Path], size: Tuple[int, int], output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
    """
    Resizes an image to the specified dimensions.

    Args:
        image_path (Union[str, Path]): Path to the image file.
        size (Tuple[int, int]): A tuple containing the desired width and height of the image.
        output_path (Optional[Union[str, Path]]): Path to save the resized image.
            Defaults to overwriting the original image.

    Returns:
        Optional[str]: Path to the resized image, or None on failure.
    """
    image_path = Path(image_path)
    output_path = image_path if output_path is None else Path(output_path)

    try:
        img = Image.open(image_path)
        resized_img = img.resize(size)
        resized_img.save(output_path)
        return str(output_path)

    except Exception as ex:
        logger.error(f"Failed to resize image {image_path}", exc_info=True)
        return None

def convert_image(image_path: Union[str, Path], format: str, output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
    """
    Converts an image to the specified format.

    Args:
        image_path (Union[str, Path]): Path to the image file.
        format (str): Format to convert image to (e.g., "JPEG", "PNG").
        output_path (Optional[Union[str, Path]]): Path to save the converted image.
            Defaults to overwriting the original image.

    Returns:
        Optional[str]: Path to the converted image or None on failure.
    """
    image_path = Path(image_path)
    output_path = image_path if output_path is None else Path(output_path)

    try:
        img = Image.open(image_path)
        img.save(output_path, format=format)
        return str(output_path)
    except Exception as ex:
        logger.error(f"Failed to convert image {image_path}", exc_info=True)
        return None

def process_images_with_watermark(folder_path: Path, watermark_path: Path) -> None:
    """
    Processes all images in the specified folder by adding a watermark and saving them in an "output" directory.

    Args:
        folder_path (Path): Path to the folder containing images.
        watermark_path (Path): Path to the watermark image.
    """
    if not folder_path.is_dir():
        logger.error(f"Folder {folder_path} does not exist.")
        return

    # Create an "output" directory if it doesn't exist
    output_dir = folder_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each file in the folder
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            output_image_path = output_dir / file_path.name
            add_image_watermark(file_path, watermark_path, output_image_path)

# Example usage
if __name__ == "__main__":
    folder = Path(input("Enter Folder Path: "))  # Path to the folder containing images
    watermark = Path(input("Enter Watermark Path: "))  # Path to the watermark image

    process_images_with_watermark(folder, watermark)