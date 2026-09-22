# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI router for Telegram Channel & Group RAG Search
# =============================================================================
# Description:
#   REST API endpoints for managing Telegram channel RAG indexes, subscriptions,
#   re-indexing, and executing fast unified or per-channel searches.
#
# File: router_telegram_rag.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI Router for Telegram Multi-Channel RAG & Search."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from header import __root__
from logger import logger
from plugins.telegram_channel_rag.channel_manager import ChannelManager

router = APIRouter(prefix="/api/telegram_rag", tags=["telegram_rag"])

_DEFAULT_STORAGE_DIR = __root__ / "data" / "telegram_rag"
_channel_manager = ChannelManager(base_storage_dir=_DEFAULT_STORAGE_DIR)


def init_router() -> APIRouter:
    """Return initialized Telegram RAG APIRouter."""
    return router


class ChannelSubscribeRequest(BaseModel):
    """Payload for subscribing to or indexing a channel."""
    channel: str = Field(..., min_length=1, description="Channel username or link (e.g. canozrimb or https://t.me/canozrimb)")
    user_id: Optional[str] = Field(default="default_user", description="User identifier")
    max_messages: Optional[int] = Field(default=500, ge=10, le=20000, description="Max messages to fetch/parse")


class ChannelUnsubscribeRequest(BaseModel):
    """Payload for unsubscribing from a channel."""
    channel: str = Field(..., min_length=1, description="Channel username")
    user_id: Optional[str] = Field(default="default_user", description="User identifier")


class ChannelReindexRequest(BaseModel):
    """Payload for force re-indexing a channel."""
    channel: str = Field(..., min_length=1, description="Channel username")
    max_messages: Optional[int] = Field(default=500, ge=10, le=20000, description="Max messages to fetch/parse")


class TelegramSearchRequest(BaseModel):
    """Payload for searching Telegram messages across RAG index."""
    query: str = Field(..., min_length=1, description="Search text or question")
    user_id: Optional[str] = Field(default="default_user", description="User identifier")
    channel: Optional[str] = Field(default=None, description="Specific channel override or 'all'")
    search_mode: Optional[str] = Field(default="unified", description="Search mode: 'unified' (pool) or 'individual'")
    top_k: Optional[int] = Field(default=5, ge=1, le=100, description="Number of top results")


@router.get("/channels")
async def list_channels(user_id: str = Query(default="default_user")) -> Dict[str, Any]:
    """Retrieve all available Telegram channel RAG indexes and user subscriptions."""
    try:
        available = _channel_manager.list_available_channels()
        user_subs = _channel_manager.get_user_channels(user_id=user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "user_subscriptions": user_subs,
            "available_channels": available,
            "total_channels": len(available),
        }
    except Exception as exc:
        logger.error(f"Error listing Telegram channels: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Telegram channels: {str(exc)}",
        )


@router.post("/subscribe")
async def subscribe_channel(payload: ChannelSubscribeRequest) -> Dict[str, Any]:
    """Attach user to a Telegram channel, indexing it if not present."""
    try:
        res = _channel_manager.subscribe_user(
            channel_input=payload.channel,
            user_id=payload.user_id or "default_user",
            max_messages=payload.max_messages or 500,
        )
        return res
    except Exception as exc:
        logger.error(f"Error subscribing to Telegram channel: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to subscribe to channel: {str(exc)}",
        )


@router.post("/unsubscribe")
async def unsubscribe_channel(payload: ChannelUnsubscribeRequest) -> Dict[str, Any]:
    """Detach user from a Telegram channel."""
    try:
        res = _channel_manager.unsubscribe_user(
            channel_input=payload.channel,
            user_id=payload.user_id or "default_user",
        )
        return res
    except Exception as exc:
        logger.error(f"Error unsubscribing from Telegram channel: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe from channel: {str(exc)}",
        )


@router.post("/reindex")
async def reindex_channel(payload: ChannelReindexRequest) -> Dict[str, Any]:
    """Force re-scrape and rebuild the RAG index for a specific channel."""
    try:
        indexer, newly_created = _channel_manager.ensure_channel_indexed(
            channel_input=payload.channel,
            max_messages=payload.max_messages or 500,
            force_refresh=True,
        )
        clean_name = _channel_manager._sanitize_channel(payload.channel)
        return {
            "status": "success",
            "channel": clean_name,
            "indexed_messages": len(indexer.messages),
            "vocab_size": len(indexer.vocab),
            "message": f"Channel @{clean_name} re-indexed with {len(indexer.messages)} messages.",
        }
    except Exception as exc:
        logger.error(f"Error reindexing Telegram channel: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex channel: {str(exc)}",
        )


@router.post("/search")
async def search_telegram_rag(payload: TelegramSearchRequest) -> Dict[str, Any]:
    """Execute search across Telegram channel RAG indexes."""
    try:
        channel_param = payload.channel.strip() if payload.channel else None
        if channel_param in ("all", "", "*", "null"):
            channel_param = None

        channels_override = [channel_param] if channel_param else None

        results = _channel_manager.search_user_channels(
            query=payload.query.strip(),
            user_id=payload.user_id or "default_user",
            channels_override=channels_override,
            top_k=payload.top_k or 5,
        )

        return {
            "status": "success",
            "query": payload.query,
            "user_id": payload.user_id or "default_user",
            "channel": channel_param or "all",
            "search_mode": payload.search_mode or "unified",
            "results_count": len(results),
            "results": results,
        }
    except Exception as exc:
        logger.error(f"Error executing Telegram RAG search: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(exc)}",
        )
