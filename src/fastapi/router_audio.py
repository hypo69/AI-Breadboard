# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI router for Audio Diarization and Voice Analysis
# =============================================================================
# Description:
#   REST API endpoints for processing voice recordings, performing speaker
#   diarization, generating executive summaries, and saving results to RAG.
#
# File: router_audio.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from src.ai.audio_diarization import AudioDiarizationService, get_audio_diarization_service
from src.logger import logger
from src.rag.document_rag import get_document_rag_manager


class SaveToRAGRequest(BaseModel):
    """Payload to save diarization result into RAG database."""
    title: str = Field(default="Voice Meeting Note", description="Title for the saved document")
    summary: str = Field(..., description="Executive summary of the dialogue")
    transcript: List[Dict[str, Any]] = Field(default_factory=list, description="Turn-by-turn dialogue transcript")
    key_points: List[str] = Field(default_factory=list, description="Key points of discussion")
    action_items: List[str] = Field(default_factory=list, description="Action items and decisions")
    markdown_report: str = Field(default="", description="Optional full Markdown report")


def init_router() -> APIRouter:
    """Initialize and configure Audio Diarization FastAPI router.

    Returns:
        APIRouter: Configured APIRouter instance.
    """
    router = APIRouter(prefix="/api/audio", tags=["Audio Diarization"])

    @router.post("/diarize", summary="Analyze voice message: diarize speakers and summarize")
    async def diarize_audio(
        request: Request,
        file: UploadFile = File(...),
        model: Optional[str] = Form(None),
        api_key: Optional[str] = Form(""),
        language: Optional[str] = Form("ru"),
    ) -> Dict[str, Any]:
        """Process uploaded audio or microphone recording with Gemini multimodal."""
        from src.fastapi.router_auth import get_current_user_data
        get_current_user_data(request)
        if not file:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No audio file provided")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty")

        mime_type = file.content_type or "audio/mp3"
        service = get_audio_diarization_service()

        try:
            result = service.analyze_audio(
                audio_bytes=content,
                mime_type=mime_type,
                model_name=model,
                api_key=api_key or "",
                language=language or "ru",
            )
            return {
                "status": "success",
                "filename": file.filename,
                "size_bytes": len(content),
                "data": asdict(result),
            }
        except Exception as e:
            logger.error(f"[router_audio] Diarization failed for {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio diarization failed: {str(e)}"
            )

    @router.post("/save-to-rag", summary="Save audio transcript and summary to RAG knowledge base")
    async def save_diarization_to_rag(req: SaveToRAGRequest, request: Request) -> Dict[str, Any]:
        """Save diarization outcome as a document in RAG knowledge base."""
        from src.fastapi.router_auth import get_current_user_data
        get_current_user_data(request)
        rag_mgr = get_document_rag_manager()
        safe_title = req.title.strip().replace(" ", "_") or "voice_recording"
        timestamp_str = int(time.time())
        filename = f"voice_meeting_{safe_title}_{timestamp_str}.md"

        # Build document content
        content_lines = [
            f"# {req.title}\n",
            f"**Дата записи:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"## 📋 Краткая сводка\n{req.summary}\n",
        ]

        if req.key_points:
            content_lines.append("## 🔑 Ключевые темы")
            for kp in req.key_points:
                content_lines.append(f"- {kp}")
            content_lines.append("")

        if req.action_items:
            content_lines.append("## ✅ Задачи и договоренности")
            for ai in req.action_items:
                content_lines.append(f"- [ ] {ai}")
            content_lines.append("")

        if req.transcript:
            content_lines.append("## 🗣️ Стенограмма по собеседникам")
            for t in req.transcript:
                sp = t.get("speaker", "Собеседник")
                ts = t.get("timestamp", "")
                ts_str = f" `[{ts}]`" if ts else ""
                tx = t.get("text", "")
                content_lines.append(f"**{sp}**{ts_str}:\n> {tx}\n")

        doc_bytes = "\n".join(content_lines).encode("utf-8")
        info = rag_mgr.save_document(filename, doc_bytes)

        # Auto-rebuild index
        rag_mgr.build_index()

        return {
            "status": "success",
            "message": f"Saved voice meeting to RAG document '{filename}'",
            "document": asdict(info),
        }

    return router
