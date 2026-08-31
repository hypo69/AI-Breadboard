# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User profile JSON file management and watch progress tracking
# =============================================================================
# Description:
#   Management of individual user JSON profile files stored in user_rags directory.
#   Tracks watch history, search queries, preferences, and generates recommendation context.
#
# File: user_profile.py
# Project: ai-breadboard
# Package: core.user_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger

# User profiles directory (same as user RAG storage location)
_USER_PROFILES_DIR = Path(__file__).parent.parent / 'ai' / 'gemini' / 'user_rags'
_USER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def _get_profile_path(user_id: str | int) -> Path:
    """Return path to user profile JSON file."""
    safe_id = str(user_id).replace('.', '_').replace('/', '_').replace('\\', '_')
    return _USER_PROFILES_DIR / f'user_profile_{safe_id}.json'

def _default_profile_structure(user_id: str | int) -> Dict[str, Any]:
    """Default user profile structure."""
    return {
        "user_id": str(user_id),
        "created_at": time.time(),
        "updated_at": time.time(),
        "watch_history": {},  # { file_path: { "name": str, "last_position": float, "duration": float, "updated_at": float, "completed": bool } }
        "last_watched": None,  # { "path": str, "position": float }
        "search_history": [],  # [ { "query": str, "timestamp": float } ]
        "preferences": {
            "liked_titles": [],    # ["Interstellar", ...]
            "disliked_titles": [], # ["Movie X", ...]
            "favorite_genres": {}, # { "Science Fiction": count, "Action": count }
            "favorite_categories": {} # { "Action": count }
        }
    }

def load_user_profile(user_id: str | int) -> Dict[str, Any]:
    """Load user JSON profile or create default."""
    path = _get_profile_path(user_id)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            return data
        except Exception as ex:
            logger.error(f"Error reading profile {user_id}", ex, False)

    profile = _default_profile_structure(user_id)
    save_user_profile(user_id, profile)
    return profile

def save_user_profile(user_id: str | int, profile: Dict[str, Any]) -> bool:
    """Save user profile to JSON."""
    try:
        path = _get_profile_path(user_id)
        profile["updated_at"] = time.time()
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except Exception as ex:
        logger.error(f"Error saving profile {user_id}", ex, False)
        return False

def update_watch_progress(
    user_id: str | int,
    file_path: str,
    file_name: str,
    current_time: float,
    duration: float
) -> Dict[str, Any]:
    """Update playback timestamp for file and mark as last watched."""
    profile = load_user_profile(user_id)
    watch_history = profile.setdefault("watch_history", {})
    
    completed = duration > 0 and (current_time / duration) >= 0.90

    watch_history[file_path] = {
        "name": file_name,
        "last_position": round(current_time, 2),
        "duration": round(duration, 2),
        "updated_at": time.time(),
        "completed": completed
    }

    profile["last_watched"] = {
        "path": file_path,
        "name": file_name,
        "position": round(current_time, 2)
    }

    save_user_profile(user_id, profile)
    return watch_history[file_path]

def get_watch_progress(user_id: str | int, file_path: str) -> Optional[Dict[str, Any]]:
    """Get saved watch progress for specific file."""
    profile = load_user_profile(user_id)
    return profile.get("watch_history", {}).get(file_path)

def log_user_search(user_id: str | int, query: str):
    """Log user search query for preference collection."""
    if not query or len(query.strip()) < 2:
        return
    profile = load_user_profile(user_id)
    search_history = profile.setdefault("search_history", [])
    
    search_history.append({
        "query": query.strip(),
        "timestamp": time.time()
    })

    # Limit to last 200 searches
    if len(search_history) > 200:
        profile["search_history"] = search_history[-200:]

    save_user_profile(user_id, profile)

def set_user_preference(
    user_id: str | int,
    title: str,
    sentiment: str, # 'like' | 'dislike'
    genre: Optional[str] = "",
    category: Optional[str] = ""
):
    """Record user preference (like/dislike/genres)."""
    profile = load_user_profile(user_id)
    prefs = profile.setdefault("preferences", {
        "liked_titles": [],
        "disliked_titles": [],
        "favorite_genres": {},
        "favorite_categories": {}
    })

    liked = set(prefs.get("liked_titles", []))
    disliked = set(prefs.get("disliked_titles", []))

    if sentiment == 'like':
        liked.add(title)
        disliked.discard(title)
    elif sentiment == 'dislike':
        disliked.add(title)
        liked.discard(title)

    prefs["liked_titles"] = list(liked)
    prefs["disliked_titles"] = list(disliked)

    if genre:
        fav_genres = prefs.setdefault("favorite_genres", {})
        fav_genres[genre] = fav_genres.get(genre, 0) + 1

    if category:
        fav_cats = prefs.setdefault("favorite_categories", {})
        fav_cats[category] = fav_cats.get(category, 0) + 1

    save_user_profile(user_id, profile)

def get_recommendation_context(user_id: str | int) -> str:
    """Generate summary text prompt of user preferences for AI."""
    profile = load_user_profile(user_id)
    prefs = profile.get("preferences", {})
    history = profile.get("watch_history", {})

    recent_watched = sorted(history.values(), key=lambda x: x.get('updated_at', 0), reverse=True)[:5]
    recent_names = [w.get('name') for w in recent_watched if w.get('name')]

    liked = prefs.get("liked_titles", [])
    disliked = prefs.get("disliked_titles", [])

    context_lines = []
    if liked:
        context_lines.append(f"User likes: {', '.join(liked[-10:])}")
    if disliked:
        context_lines.append(f"User dislikes: {', '.join(disliked[-10:])}")
    if recent_names:
        context_lines.append(f"Recently watched: {', '.join(recent_names)}")

    return "\n".join(context_lines) if context_lines else ""
