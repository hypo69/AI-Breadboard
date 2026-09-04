# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Image Operations
# =============================================================================
# Description:
#   Image-related operations for Google Generative AI.
#   Provides methods for image description and file upload.
#
# File: images.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from io import IOBase
from pathlib import Path
from typing import Any

from google.genai import types

from src.logger.logger import logger
from src.utils.image import get_image_bytes

from .core import GoogleGenerativeAICore
from .errors import GoogleGenerativeAIErrorMixin


class GoogleGenerativeAIImagesMixin:
    """Mixin class for image operations in GoogleGenerativeAI.

    Provides methods for image description and file upload.
    """

    async def describe_image(
        self,
        image: Path | bytes,
        mime_type: str = 'image/jpeg',
        prompt: str = '',
        attempts: int = 10,
    ) -> str | bool:
        """Formation текстового описания переданного изображения.

        Args:
            image (Path | bytes): Путь к изображению или его бинарное содержимое.
            mime_type (str): MIME-тип изображения. Значение по умолчанию: 'image/jpeg'.
            prompt (str): Дополнительный текстовый промпт. Значение по умолчанию: ''.
            attempts (int): Максимальное число попыток. Значение по умолчанию: 10.

        Returns:
            str | bool: Текстовое описание или False при сбое.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> desc = await ai.describe_image(Path("poster.jpg"))
        """
        img_bytes: bytes = get_image_bytes(image) if isinstance(image, Path) else image
        if not img_bytes:
            return False

        for attempt in range(attempts):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                        types.Part.from_text(text=prompt or 'Опиши это изображение.'),
                    ],
                )
                if response and response.text:
                    return response.text

                logger.debug(f'GoogleGenerativeAI: Empty ответ describe_image (попытка {attempt + 1})')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return False

        return False

    async def upload_file(
        self,
        file: str | Path | IOBase,
        file_name: str = '',
        attempts: int = 10,
    ) -> bool:
        """Loading медиа-файла в хранилище Google GenAI File API.

        Args:
            file (str | Path | IOBase): Путь к файлу или файловый дескриптор.
            file_name (str): Отображаемое имя файла. Значение по умолчанию: ''.
            attempts (int): Максимальное количество попыток. Значение по умолчанию: 10.

        Returns:
            bool: True при успешной загрузке, False при ошибке.

        Examples:
            >>> ai = GoogleGenerativeAI()
            >>> success = await ai.upload_file(Path("data.pdf"), file_name="data.pdf")
        """
        for attempt in range(attempts):
            try:
                upload_kwargs = (
                    {'config': types.UploadFileConfig(display_name=file_name)}
                    if file_name
                    else {}
                )
                response = self._client.files.upload(path=file, **upload_kwargs)
                if response:
                    logger.debug(f'GoogleGenerativeAI: Файл {file_name} successfully загружен')
                    return True
                return False
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return False

        return False
