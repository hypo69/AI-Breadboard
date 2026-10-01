# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Audio Diarization Module
# =============================================================================
# Description:
#   Individual speaker utterance in dialogue.
#
# Usage Examples:
#   Python API:
#     from src.ai.audio_diarization import Utterance
#
#     service = Utterance()
#
# File: audio_diarization.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""Individual speaker utterance in dialogue."""

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from logger import logger
from src.ai.gemini.gemini_api_key_state import load_api_keys, update_last_run

@dataclass
class Utterance:
    """Individual speaker utterance in dialogue."""
    speaker: str
    text: str
    timestamp: str = ''

@dataclass
class DiarizationResult:
    """Result of audio diarization and conversation analysis."""
    summary: str
    key_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    speakers: List[str] = field(default_factory=list)
    transcript: List[Dict[str, Any]] = field(default_factory=list)
    markdown_report: str = ''
    language: str = 'ru'
    model: str = 'gemini-2.5-flash'

class AudioDiarizationService:
    """Service for processing voice notes and meeting audio files,
    extracting speaker-attributed transcripts and executive summaries.
    """

    def __init__(self, default_model: str='gemini-2.5-flash') -> None:
        """Initialize Audio Diarization Service.

        Args:
            default_model (str): Gemini model with multimodal audio support.
        """
        self.default_model = default_model

    def _get_api_key(self, custom_key: str='') -> str:
        """Resolve available API key from parameter, secrets pool, or environment."""
        if custom_key:
            return custom_key
        keys, _, _ = load_api_keys()
        if keys:
            return keys[0]
        return os.getenv('GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY_1', '')

    def _build_prompt(self, target_lang: str='ru') -> str:
        """Construct system prompt guiding the model to perform diarization and summarization."""
        return f'\nТы эксперт по анализу аудиозаписей, совещаний и голосовых сообщений.\nПрослушай прикрепленный аудиофайл и выполни глубокий анализ:\n\n1. **Диаризация собеседников (Speaker Diarization)**:\n   - Распознай речь каждого участника диалога.\n   - Раздели реплики по собеседникам (например: "Собеседник 1", "Собеседник 2", или реальные имена, если они назывались в речи).\n   - Если слышны временные метки, укажи их (например: "00:05").\n\n2. **Краткая сводка (Executive Summary)**:\n   - Сформулируй 2-4 предложениями главную суть и цель разговора.\n\n3. **Ключевые темы (Key Points)**:\n   - Список основных тем и фактов, затронутых в беседе.\n\n4. **Задачи, договоренности и следующие шаги (Action Items)**:\n   - Список решений, обязательств, сроков или поручений.\n\nВерни ответ СТРОГО в виде валидного JSON-объекта со следующей структурой (без лишнего вводного текста вне JSON):\n```json\n{{\n  "summary": "Краткая суть разговора...",\n  "key_points": [\n    "Пункт 1...",\n    "Пункт 2..."\n  ],\n  "action_items": [\n    "Договоренность 1...",\n    "Задача 2..."\n  ],\n  "speakers": ["Собеседник 1", "Собеседник 2"],\n  "transcript": [\n    {{\n      "speaker": "Собеседник 1",\n      "timestamp": "00:00",\n      "text": "Текст первой реплики..."\n    }},\n    {{\n      "speaker": "Собеседник 2",\n      "timestamp": "00:15",\n      "text": "Текст ответа..."\n    }}\n  ]\n}}\n```\nЯзык ответов и резюме: {target_lang}.\n'

    def _format_markdown_report(self, data: Dict[str, Any]) -> str:
        """Format structured dictionary into a clean, human-readable Markdown report."""
        summary = data.get('summary', '')
        key_points = data.get('key_points', [])
        action_items = data.get('action_items', [])
        transcript = data.get('transcript', [])
        speakers = data.get('speakers', [])
        lines = ['# 🎙️ Сводка и диаризация разговора\n']
        if summary:
            lines.append(f'## 📋 Краткое содержание\n{summary}\n')
        if key_points:
            lines.append('## 🔑 Ключевые темы')
            for kp in key_points:
                lines.append(f'- {kp}')
            lines.append('')
        if action_items:
            lines.append('## ✅ Задачи и договоренности')
            for ai in action_items:
                lines.append(f'- [ ] {ai}')
            lines.append('')
        if speakers:
            lines.append(f"**Участники:** {', '.join(speakers)}\n")
        if transcript:
            lines.append('## 🗣️ Стенограмма по собеседникам')
            for turn in transcript:
                speaker = turn.get('speaker', 'Собеседник')
                ts = turn.get('timestamp', '')
                ts_str = f' `[{ts}]`' if ts else ''
                text = turn.get('text', '')
                lines.append(f'**{speaker}**{ts_str}:\n> {text}\n')
        return '\n'.join(lines).strip()

    def analyze_audio(self, audio_bytes: bytes, mime_type: str='audio/mp3', model_name: Optional[str]=None, api_key: str='', language: str='ru') -> DiarizationResult:
        """Analyze audio recording, extract speaker utterances, and generate summary.

        Args:
            audio_bytes (bytes): Binary audio data.
            mime_type (str): Audio MIME type (e.g. 'audio/mp3', 'audio/wav', 'audio/webm', 'audio/ogg').
            model_name (Optional[str]): Gemini model identifier.
            api_key (str): Optional API key.
            language (str): Target output language.

        Returns:
            DiarizationResult: Complete parsed result.
        """
        active_key = self._get_api_key(api_key)
        if not active_key:
            raise ValueError('No Gemini API key available for audio diarization')
        selected_model = model_name or self.default_model
        if 'webm' in mime_type.lower():
            clean_mime = 'audio/webm'
        elif 'wav' in mime_type.lower():
            clean_mime = 'audio/wav'
        elif 'ogg' in mime_type.lower():
            clean_mime = 'audio/ogg'
        elif 'm4a' in mime_type.lower() or 'mp4' in mime_type.lower():
            clean_mime = 'audio/mp4'
        else:
            clean_mime = 'audio/mp3'
        client = genai.Client(api_key=active_key)
        prompt_text = self._build_prompt(target_lang=language)
        logger.info(f'[AudioDiarization] Processing audio ({len(audio_bytes)} bytes, mime={clean_mime}) with {selected_model}')
        response = client.models.generate_content(model=selected_model, contents=[types.Part.from_bytes(data=audio_bytes, mime_type=clean_mime), prompt_text], config=types.GenerateContentConfig(temperature=0.2, response_mime_type='application/json'))
        raw_text = response.text or ''
        parsed_data = self._parse_json_response(raw_text)
        markdown_report = self._format_markdown_report(parsed_data)
        return DiarizationResult(summary=parsed_data.get('summary', ''), key_points=parsed_data.get('key_points', []), action_items=parsed_data.get('action_items', []), speakers=parsed_data.get('speakers', []), transcript=parsed_data.get('transcript', []), markdown_report=markdown_report, language=language, model=selected_model)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Safely parse model JSON output with fallback heuristics."""
        clean_text = text.strip()
        if clean_text.startswith('```'):
            clean_text = re.sub('^```[a-zA-Z]*\\n', '', clean_text)
            clean_text = re.sub('\\n```$', '', clean_text).strip()
        try:
            return json.loads(clean_text)
        except Exception:
            match = re.search('(\\{.*\\})', clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return {'summary': clean_text, 'key_points': [], 'action_items': [], 'speakers': ['Собеседник'], 'transcript': [{'speaker': 'Собеседник', 'text': clean_text, 'timestamp': '00:00'}]}
_diarization_service: Optional[AudioDiarizationService] = None

def get_audio_diarization_service() -> AudioDiarizationService:
    """Get or create singleton AudioDiarizationService."""
    global _diarization_service
    if _diarization_service is None:
        _diarization_service = AudioDiarizationService()
    return _diarization_service