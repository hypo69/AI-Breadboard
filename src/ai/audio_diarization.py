# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Audio Diarization and Conversation Summary Service
# =============================================================================
# Description:
#   Multimodal audio processor using Google Gemini models for speaker
#   diarization, turn-by-turn transcription, executive summaries, and action item extraction.
#
# File: audio_diarization.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from src.logger import logger
from src.secrets.api_key_state import load_api_keys, update_last_run


@dataclass
class Utterance:
    """Individual speaker utterance in dialogue."""
    speaker: str
    text: str
    timestamp: str = ""


@dataclass
class DiarizationResult:
    """Result of audio diarization and conversation analysis."""
    summary: str
    key_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    speakers: List[str] = field(default_factory=list)
    transcript: List[Dict[str, Any]] = field(default_factory=list)
    markdown_report: str = ""
    language: str = "ru"
    model: str = "gemini-2.5-flash"


class AudioDiarizationService:
    """
    ## hypo69 docblock
    Service for processing voice notes and meeting audio files,
    extracting speaker-attributed transcripts and executive summaries.
    """

    def __init__(self, default_model: str = "gemini-2.5-flash") -> None:
        """Initialize Audio Diarization Service.

        Args:
            default_model (str): Gemini model with multimodal audio support.
        """
        self.default_model = default_model

    def _get_api_key(self, custom_key: str = "") -> str:
        """Resolve available API key from parameter, secrets pool, or environment."""
        if custom_key:
            return custom_key

        # Try secrets pool
        keys, _, _ = load_api_keys()
        if keys:
            return keys[0]

        # Try environment variables
        return (
            os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GEMINI_API_KEY_1", "")
        )

    def _build_prompt(self, target_lang: str = "ru") -> str:
        """Construct system prompt guiding the model to perform diarization and summarization."""
        return f"""
Ты эксперт по анализу аудиозаписей, совещаний и голосовых сообщений.
Прослушай прикрепленный аудиофайл и выполни глубокий анализ:

1. **Диаризация собеседников (Speaker Diarization)**:
   - Распознай речь каждого участника диалога.
   - Раздели реплики по собеседникам (например: "Собеседник 1", "Собеседник 2", или реальные имена, если они назывались в речи).
   - Если слышны временные метки, укажи их (например: "00:05").

2. **Краткая сводка (Executive Summary)**:
   - Сформулируй 2-4 предложениями главную суть и цель разговора.

3. **Ключевые темы (Key Points)**:
   - Список основных тем и фактов, затронутых в беседе.

4. **Задачи, договоренности и следующие шаги (Action Items)**:
   - Список решений, обязательств, сроков или поручений.

Верни ответ СТРОГО в виде валидного JSON-объекта со следующей структурой (без лишнего вводного текста вне JSON):
```json
{{
  "summary": "Краткая суть разговора...",
  "key_points": [
    "Пункт 1...",
    "Пункт 2..."
  ],
  "action_items": [
    "Договоренность 1...",
    "Задача 2..."
  ],
  "speakers": ["Собеседник 1", "Собеседник 2"],
  "transcript": [
    {{
      "speaker": "Собеседник 1",
      "timestamp": "00:00",
      "text": "Текст первой реплики..."
    }},
    {{
      "speaker": "Собеседник 2",
      "timestamp": "00:15",
      "text": "Текст ответа..."
    }}
  ]
}}
```
Язык ответов и резюме: {target_lang}.
"""

    def _format_markdown_report(self, data: Dict[str, Any]) -> str:
        """Format structured dictionary into a clean, human-readable Markdown report."""
        summary = data.get("summary", "")
        key_points = data.get("key_points", [])
        action_items = data.get("action_items", [])
        transcript = data.get("transcript", [])
        speakers = data.get("speakers", [])

        lines = ["# 🎙️ Сводка и диаризация разговора\n"]

        if summary:
            lines.append(f"## 📋 Краткое содержание\n{summary}\n")

        if key_points:
            lines.append("## 🔑 Ключевые темы")
            for kp in key_points:
                lines.append(f"- {kp}")
            lines.append("")

        if action_items:
            lines.append("## ✅ Задачи и договоренности")
            for ai in action_items:
                lines.append(f"- [ ] {ai}")
            lines.append("")

        if speakers:
            lines.append(f"**Участники:** {', '.join(speakers)}\n")

        if transcript:
            lines.append("## 🗣️ Стенограмма по собеседникам")
            for turn in transcript:
                speaker = turn.get("speaker", "Собеседник")
                ts = turn.get("timestamp", "")
                ts_str = f" `[{ts}]`" if ts else ""
                text = turn.get("text", "")
                lines.append(f"**{speaker}**{ts_str}:\n> {text}\n")

        return "\n".join(lines).strip()

    def analyze_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/mp3",
        model_name: Optional[str] = None,
        api_key: str = "",
        language: str = "ru",
    ) -> DiarizationResult:
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
            raise ValueError("No Gemini API key available for audio diarization")

        selected_model = model_name or self.default_model

        # Normalize mime type
        if "webm" in mime_type.lower():
            clean_mime = "audio/webm"
        elif "wav" in mime_type.lower():
            clean_mime = "audio/wav"
        elif "ogg" in mime_type.lower():
            clean_mime = "audio/ogg"
        elif "m4a" in mime_type.lower() or "mp4" in mime_type.lower():
            clean_mime = "audio/mp4"
        else:
            clean_mime = "audio/mp3"

        client = genai.Client(api_key=active_key)
        prompt_text = self._build_prompt(target_lang=language)

        logger.info(
            f"[AudioDiarization] Processing audio ({len(audio_bytes)} bytes, mime={clean_mime}) with {selected_model}"
        )

        response = client.models.generate_content(
            model=selected_model,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=clean_mime),
                prompt_text,
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        raw_text = response.text or ""
        parsed_data = self._parse_json_response(raw_text)
        markdown_report = self._format_markdown_report(parsed_data)

        return DiarizationResult(
            summary=parsed_data.get("summary", ""),
            key_points=parsed_data.get("key_points", []),
            action_items=parsed_data.get("action_items", []),
            speakers=parsed_data.get("speakers", []),
            transcript=parsed_data.get("transcript", []),
            markdown_report=markdown_report,
            language=language,
            model=selected_model,
        )

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Safely parse model JSON output with fallback heuristics."""
        clean_text = text.strip()
        # Remove Markdown code fences if present
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```[a-zA-Z]*\n", "", clean_text)
            clean_text = re.sub(r"\n```$", "", clean_text).strip()

        try:
            return json.loads(clean_text)
        except Exception:
            # Try finding json bracket substring
            match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass

        # Fallback dictionary if JSON parsing failed completely
        return {
            "summary": clean_text,
            "key_points": [],
            "action_items": [],
            "speakers": ["Собеседник"],
            "transcript": [{"speaker": "Собеседник", "text": clean_text, "timestamp": "00:00"}],
        }


# Global singleton instance
_diarization_service: Optional[AudioDiarizationService] = None


def get_audio_diarization_service() -> AudioDiarizationService:
    """Get or create singleton AudioDiarizationService."""
    global _diarization_service
    if _diarization_service is None:
        _diarization_service = AudioDiarizationService()
    return _diarization_service
