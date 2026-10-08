# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Images Module
# =============================================================================
# Description:
#   Mixin class for image operations in GoogleGenerativeAI.
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.images import GoogleGenerativeAIImagesMixin
#
#     service = GoogleGenerativeAIImagesMixin()
#
# File: images.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 10:48:10
# =============================================================================

"""Mixin class for image operations in GoogleGenerativeAI."""

import asyncio
import json
from io import IOBase
from pathlib import Path
from typing import Any
from google.genai import types
from logger import logger
from src.utils.image import get_image_bytes
from .core import GoogleGenerativeAICore
from .errors import GoogleGenerativeAIErrorMixin

class GoogleGenerativeAIImagesMixin:
    """Mixin class for image operations in GoogleGenerativeAI.

    Provides methods for image description and file upload.
    """

    async def describe_image(self, image: Path | bytes, mime_type: str='image/jpeg', prompt: str='', attempts: int=10) -> str | bool:
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
        effective_prompt = prompt or 'Опиши это изображение.'
        if hasattr(self, '_log_request_details'):
            self._log_request_details(method='describe_image', model=self.model_name, q=effective_prompt, generation_config={'mime_type': mime_type})
        for attempt in range(attempts):
            try:
                response = self._client.models.generate_content(model=self.model_name, contents=[types.Part.from_bytes(data=img_bytes, mime_type=mime_type), types.Part.from_text(text=effective_prompt)])
                if response and response.text:
                    if hasattr(self, '_log_response_details'):
                        self._log_response_details(method='describe_image', model=self.model_name, response_text=response.text, attempt=attempt + 1)
                    return response.text
                err_empty = {
                    'error': {
                        'code': 204,
                        'status': 'EMPTY_RESPONSE',
                        'message': f'Empty response describe_image on attempt {attempt + 1}',
                        'model': self.model_name,
                        'attempt': attempt + 1,
                    }
                }
                logger.warning(f'GoogleGenerativeAIImagesMixin: Empty response:\n{json.dumps(err_empty, ensure_ascii=False, indent=2)}')
                await asyncio.sleep(2 ** min(attempt, 4))
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return False
        return False

    async def upload_file(self, file: str | Path | IOBase, file_name: str='', attempts: int=10) -> bool:
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
        if hasattr(self, '_log_request_details'):
            self._log_request_details(method='upload_file', model=self.model_name, q=f'Upload file: {file_name or str(file)}')
        for attempt in range(attempts):
            try:
                upload_kwargs = {'config': types.UploadFileConfig(display_name=file_name)} if file_name else {}
                response = self._client.files.upload(path=file, **upload_kwargs)
                if response:
                    logger.info(f'GoogleGenerativeAI: Файл {file_name or str(file)} успешно загружен: {response.name if hasattr(response, "name") else response}')
                    return True
                return False
            except Exception as ex:
                should_retry: bool = await self._handle_api_error(ex, self.model_name, attempt, attempts)
                if not should_retry:
                    return False
        return False