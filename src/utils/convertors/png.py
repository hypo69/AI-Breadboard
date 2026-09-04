# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Convert text to PNG images
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: png.py
# Project: ai-breadboard
# Package: src.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Text to PNG image conversion utilities.

Reads text from files, generates PNG images for each line using Pillow,
and saves them to output directory with customizable appearance options."""
"""

from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
from src.logger.logger import logger  # Logging

class TextToImageGenerator:
    """
    A class for generating PNG images from text lines.

    **Functions**:
    - `assign_path`: Determines the correct path for output PNG files, creating the directory if necessary.
    - `center_text_position`: Calculates the position to center text on the canvas.
    - `generate_png`: Creates a PNG image with the specified text, font, colors, etc.
    - `not_comment_or_blank`: Checks if a line is neither a comment nor blank.
    - `which_exist`: Checks which file names already exist in the directory.
    - `get_characters`: Extracts text lines from the input file or list, filtering out comments and blank lines.
    - `parse_size`: Parses a string into a `Size` object.
    - `get_max_text_size`: Computes the maximum text size based on the font and text lines.
    - `get_font`: Determines the font size based on canvas size and padding.
    - `setup_logging`: Configures logging based on the specified logging level.
    - `error`: Logs an error message and raises an exception.
    - `overlay_images`: Overlays one PNG image on top of another.
    """

    def __init__(self):
        """
        Initializes the TextToImageGenerator class with default settings.
        """
        self.default_output_dir = Path("./output")
        self.default_canvas_size = (1024, 1024)
        self.default_padding = 0.10
        self.default_background = "white"
        self.default_text_color = "black"
        self.default_log_level = "WARNING"

    async def generate_images(
        self,
        lines: List[str],
        output_dir: str | Path = None,
        font: str | ImageFont.ImageFont = "sans-serif",
        canvas_size: Tuple[int, int] = None,
        padding: float = None,
        background_color: str = None,
        text_color: str = None,
        log_level: int | str | bool = None,
        clobber: bool = False,
    ) -> List[Path]:
        """
        Generates PNG images from the provided text lines.

        Args:
            lines (List[str]): A list of strings containing the text to generate images from.
            output_dir (str | Path, optional): Directory to save the output images. Defaults to "./output".
            font (str | ImageFont.ImageFont, optional): Font to use for the text. Defaults to "sans-serif".
            canvas_size (Tuple[int, int], optional): Size of the canvas in pixels. Defaults to (1024, 1024).
            padding (float, optional): Percentage of canvas size to use as a blank border. Defaults to 0.10.
            background_color (str, optional): Background color for the images. Defaults to "white".
            text_color (str, optional): Color of the text. Defaults to "black".
            log_level (int | str | bool, optional): Logging verbosity level. Defaults to "WARNING".
            clobber (bool, optional): If True, overwrites existing files. Defaults to False.

        Returns:
            List[Path]: A list of paths to the generated PNG images.

        Example:
            >>> generator = TextToImageGenerator()
            >>> lines = ["Text 1", "Text 2", "Text 3"]
            >>> output_dir = "./output"
            >>> images = await generator.generate_images(lines, output_dir=output_dir)
            >>> print(images)
            [PosixPath('./output/Text 1.png'), PosixPath('./output/Text 2.png'), PosixPath('./output/Text 3.png')]
        """
        output_directory = Path(output_dir) if output_dir else self.default_output_dir
        self.setup_logging(level=log_level)

        if not canvas_size:
            canvas_size = self.default_canvas_size

        if not padding:
            padding = self.default_padding

        generated_images = []
        for line in lines:
            img_path = output_directory / f"{line}.png"
            if img_path.exists() and not clobber:
                logger.warning(f"File {img_path} already exists. Skipping...")
                continue
            img = self.generate_png(line, canvas_size, padding, background_color, text_color, font)
            img.save(img_path)
            generated_images.append(img_path)

        return generated_images

    def generate_png(
        self,
        text: str,
        canvas_size: Tuple[int, int],
        padding: float,
        background_color: str,
        text_color: str,
        font: str | ImageFont.ImageFont,
    ) -> Image:
        """
        Creates a PNG image with the specified text, font, and colors.

        Args:
            text (str): Text to render on the image.
            canvas_size (Tuple[int, int]): Size of the canvas in pixels.
            padding (float): Padding percentage to use as a border.
            background_color (str): Background color of the image.
            text_color (str): Color of the text.
            font (str | ImageFont.ImageFont): Font to use for the text.

        Returns:
            Image: The generated PNG image.
        """
        img = Image.new("RGB", canvas_size, background_color)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font, size=self.get_font_size(canvas_size, padding))

        text_position = self.center_text_position(draw, text, font, canvas_size)
        draw.text(text_position, text, fill=text_color, font=font)

        return img

    def center_text_position(
        self, draw: ImageDraw.Draw, text: str, font: ImageFont.ImageFont, canvas_size: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Calculates the position to center the text on the canvas.

        Args:
            draw (ImageDraw.Draw): The ImageDraw instance.
            text (str): Text to be rendered.
            font (ImageFont.ImageFont): Font used for the text.
            canvas_size (Tuple[int, int]): Size of the canvas in pixels.

        Returns:
            Tuple[int, int]: Coordinates for centering the text.
        """
        text_width, text_height = draw.textsize(text, font=font)
        return (canvas_size[0] - text_width) // 2, (canvas_size[1] - text_height) // 2

    def overlay_images(
        self,
        background_path: str | Path,
        overlay_path: str | Path,
        position: tuple[int, int] = (0, 0),
        alpha: float = 1.0,
    ) -> Image:
        """Overlays one PNG image on top of another at a specified position.

        Args:
            background_path (str | Path): Path to the background PNG image.
            overlay_path (str | Path): Path to the overlay PNG image.
            position (tuple[int, int], optional): (x, y) coordinates where the overlay will be placed. Defaults to (0, 0).
            alpha (float, optional): Transparency level of the overlay image (0.0 - 1.0). Defaults to 1.0.

        Returns:
            Image: The resulting image with the overlay.

        Example:
            >>> result_image = overlay_images("background.png", "overlay.png", position=(50, 50), alpha=0.8)
            >>> result_image.save("result.png")
        """
        # Open the background and overlay images
        background = Image.open(background_path).convert("RGBA")
        overlay = Image.open(overlay_path).convert("RGBA")

        # Resize overlay to fit the background if needed
        if overlay.size != background.size:
            overlay = overlay.resize(background.size, Image.ANTIALIAS)

        # Adjust transparency of overlay
        overlay = overlay.copy()
        overlay.putalpha(int(alpha * 255))

        # Paste overlay onto background
        background.paste(overlay, position, overlay)

        return background

def webp2png(webp_path: str, png_path: str) -> bool:
    """
    Converts a WEBP image to PNG format.

    Args:
        webp_path (str): Path to the input WEBP file.
        png_path (str): Path to save the converted PNG file.

    Example:
        webp2png('image.webp', 'image.png')
    """
    try:
        # Open the webp image
        with Image.open(webp_path) as img:
            # Convert to PNG and save
            img.save(png_path, 'PNG')
        return True
    except Exception as e:
        print(f"Error during conversion: {e}")
        return

