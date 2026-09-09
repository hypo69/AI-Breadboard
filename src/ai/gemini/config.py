# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Generative AI Configuration Builder
# =============================================================================
# Description:
#   Configuration building for Google Generative AI API requests.
#   Provides methods for building content config and text normalization.
#
# File: config.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import re
from typing import Any

from google.genai import types

from src.logger.logger import logger


def normalize_text(text: str) -> str:
    """Normalization of model response text.

    Replacement of escaped newline sequences with actual line break characters.

    Args:
        text (str): Input text for normalization.

    Returns:
        str: Normalized text with actual newlines.

    Examples:
        >>> normalize_text("Line 1\\nLine 2")
        'Line 1\\nLine 2'
    """
    if not text:
        return ''
    return re.sub(r'\\n', '\n', text)


def remove_html_blocks(text: str) -> str:
    """Removal of HTML markup blocks from model response.

    Args:
        text (str): Input text with possible HTML blocks.

    Returns:
        str: Text with ```html ... ``` blocks removed.

    Examples:
        >>> remove_html_blocks("```html<div>Test</div>```Hello")
        'Hello'
    """
    if not text:
        return ''
    return re.sub(r'```html.*?```', '', text, flags=re.DOTALL)


class GoogleGenerativeAIConfigMixin:
    """Mixin class for configuration building in GoogleGenerativeAI.

    Provides methods for building content config and text normalization.
    """

    def _build_content_config(
        self,
        instruction: str = '',
        tools: list = (),
        generation_config: dict = {},
    ) -> types.GenerateContentConfig:
        """Build content generation configuration object for Gemini SDK.

        Args:
            instruction (str): System instruction. Default: ''.
            tools (list): Set of model tools (functions).
            generation_config (dict): Additional generation parameters.

        Returns:
            types.GenerateContentConfig: Configured generation object.
        """
        cfg_kwargs: dict[str, Any] = {}
        gen_cfg: dict[str, Any] = {}

        if isinstance(self.generation_config, dict):
            gen_cfg.update(self.generation_config)
        if generation_config:
            gen_cfg.update(generation_config)

        response_type: str = gen_cfg.pop('response_type', 'both')
        inst: str = instruction or self.system_instruction or ''

        if inst:
            if response_type == 'chat':
                format_rule: str = (
                    '\n\nCRITICAL: You must format your response for reading on a screen.\n'
                    'Provide a detailed styled markdown response for the user to read.'
                )
            elif response_type == 'voice':
                format_rule = (
                    '\n\nCRITICAL: You must format your response for a voice narrator (TTS).\n'
                    'Provide a very concise, clear speech-friendly text, using simple language, '
                    'no markdown, no special symbols, write all numbers as words.'
                )
            else:
                format_rule = (
                    '\n\nCRITICAL: You must format your response exactly as follows, with no extra text outside these blocks:\n'
                    '[CHAT]\n<detailed styled markdown response for the user to read>\n'
                    '[VOICE]\n<very concise, clear speech-friendly text for narrator, using simple language, '
                    'no markdown, no special symbols, write all numbers as words>'
                )
            inst += format_rule
            cfg_kwargs['system_instruction'] = inst

        use_google_search: bool = gen_cfg.pop(
            'use_google_search',
            getattr(self, 'use_google_search', False)
        )
        all_tools: list = list(tools) if tools else []
        if use_google_search:
            has_search: bool = any(
                hasattr(t, 'google_search') or (isinstance(t, dict) and 'google_search' in t)
                for t in all_tools
            )
            if not has_search:
                all_tools.append(types.Tool(google_search=types.GoogleSearch()))
        if all_tools:
            cfg_kwargs['tools'] = all_tools

        # Configure automatic function calling (AFC)
        # Disable by default when direct models.generate_content / manual dispatcher is used
        # to prevent SDK warnings (Google GenAI recommends AFC only with Chat.send_message).
        afc_cfg = gen_cfg.pop('automatic_function_calling', None)
        if afc_cfg is not None:
            if isinstance(afc_cfg, dict):
                cfg_kwargs['automatic_function_calling'] = types.AutomaticFunctionCallingConfig(**afc_cfg)
            else:
                cfg_kwargs['automatic_function_calling'] = afc_cfg
        elif all_tools:
            cfg_kwargs['automatic_function_calling'] = types.AutomaticFunctionCallingConfig(disable=True)

        if gen_cfg:
            for k in ['temperature', 'top_p', 'top_k', 'response_mime_type']:
                val = gen_cfg.get(k)
                if val:
                    cfg_kwargs[k] = val

        return types.GenerateContentConfig(**cfg_kwargs)

    def _normalize_text(self, text: str) -> str:
        """Normalization of model response text.

        Args:
            text (str): Input text for normalization.

        Returns:
            str: Normalized text with actual newlines.
        """
        return normalize_text(text)

    def _remove_html_blocks(self, text: str) -> str:
        """Removal of HTML markup blocks from model response.

        Args:
            text (str): Input text with possible HTML blocks.

        Returns:
            str: Text with ```html ... ``` blocks removed.
        """
        return remove_html_blocks(text)

    def _log_request_details(
        self,
        method: str,
        model: str,
        q: str,
        history: Any = None,
        system_instruction: str = '',
        tools: Any = None,
        generation_config: dict = {},
    ) -> None:
        """Log outgoing request structure, prompt size, and configuration for debugging.

        Args:
            method (str): API calling method name (e.g., 'ask', 'chat_stream').
            model (str): Gemini model identifier.
            q (str): User query/prompt.
            history (Any): Dialog history entries if any.
            system_instruction (str): Applied system prompt.
            tools (Any): List of attached tools if any.
            generation_config (dict): Generation parameter overrides.
        """
        try:
            q_len: int = len(q) if q else 0
            q_preview: str = (q[:120] + '...') if q and len(q) > 120 else (q or '')
            inst: str = system_instruction or getattr(self, 'system_instruction', '') or ''
            inst_len: int = len(inst)
            inst_preview: str = (inst[:80] + '...') if inst and len(inst) > 80 else inst

            history_count: int = len(history) if history else 0
            history_chars: int = 0
            if history:
                for item in history:
                    if isinstance(item, dict):
                        parts = item.get('parts', [])
                        if isinstance(parts, list):
                            for p in parts:
                                if isinstance(p, dict):
                                    history_chars += len(str(p.get('text', '')))
                                else:
                                    history_chars += len(str(p))
                        elif isinstance(parts, str):
                            history_chars += len(parts)

            tools_list: list = list(tools) if tools else []
            tools_summary: list[str] = []
            for t in tools_list:
                if hasattr(t, 'google_search') or (isinstance(t, dict) and 'google_search' in t):
                    tools_summary.append('google_search')
                elif hasattr(t, 'function_declarations'):
                    tools_summary.append('custom_functions')
                else:
                    tools_summary.append(type(t).__name__)

            logger.info(
                f'Gemini Outgoing [{method}] -> Model: "{model}" | '
                f'Prompt ({q_len} chars): {q_preview!r} | '
                f'History: {history_count} msgs (~{history_chars} chars) | '
                f'SysInstruction ({inst_len} chars): {inst_preview!r} | '
                f'Tools: {tools_summary or "none"} | '
                f'GenConfig: {generation_config or "{}"}'
            )
        except Exception as log_ex:
            logger.debug(f'Gemini: Failed to log request payload details: {log_ex}')

