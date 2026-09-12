# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: News Reader Skill CLI Helper
# =============================================================================
# Description:
#   CLI helper script for the news-reader skill enabling autonomous agents
#   and users to fetch feeds, trigger digests, and train the adaptive learner.
#
# File: news_cli.py
# Project: ai-breadboard
# Package: .agents.skills.news-reader.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI interface for News Reader Skill."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from plugins.news_feed import get_news_engine, UserFeedbackRequest


def cmd_feed(args):
    """Retrieve and display personalized news feed."""
    engine = get_news_engine()
    feed = engine.get_personalized_feed(
        user_id=args.user_id,
        force_refresh=args.refresh,
        limit=args.limit
    )
    if args.json:
        print(json.dumps([a.model_dump() for a in feed], ensure_ascii=False, indent=2))
        return

    print(f"\n📰 Персональная лента новостей для [{args.user_id}] ({len(feed)} статей):")
    print("=" * 70)
    for i, a in enumerate(feed, 1):
        match_pct = int((a.relevance_score or 0.5) * 100)
        print(f"{i}. [{a.source_name}] ({match_pct}% match) {a.title}")
        if a.ai_summary or a.summary:
            text = (a.ai_summary or a.summary).strip()
            print(f"   💡 {text[:150]}...")
        print(f"   🔗 {a.link}")
        print(f"   🆔 ID: {a.id}\n")


def cmd_digest(args):
    """Generate and display AI news digest."""
    engine = get_news_engine()
    digest = asyncio.run(engine.generate_user_digest(user_id=args.user_id))
    if args.json:
        print(json.dumps(digest, ensure_ascii=False, indent=2))
        return

    print(f"\n✨ {digest.get('title', 'ИИ-Дайджест')}")
    print("=" * 70)
    print(digest.get("digest_text", ""))
    print("=" * 70)


def cmd_feedback(args):
    """Send user interaction feedback to train adaptive learner."""
    engine = get_news_engine()
    fb = UserFeedbackRequest(
        article_id=args.article_id,
        action=args.action,
        article_title=args.title or "",
        category=args.category or "general"
    )
    profile = engine.learner.apply_feedback(user_id=args.user_id, feedback=fb)
    print(f"✅ Реакция '{args.action}' зафиксирована! Всего реакций: {profile.interaction_count}")


def cmd_profile(args):
    """Show learned interest weights."""
    engine = get_news_engine()
    profile = engine.learner.get_profile(user_id=args.user_id)
    if args.json:
        print(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2))
        return

    print(f"\n🧠 Профиль предпочтений пользователя [{args.user_id}]:")
    print(f"- Обработано взаимодействий: {profile.interaction_count}")
    print(f"- Стоп-слова: {', '.join(profile.negative_keywords) or 'нет'}")
    print("\nТоп выученных тем и весов:")
    sorted_topics = sorted(profile.topic_weights.items(), key=lambda x: x[1], reverse=True)
    for kw, w in sorted_topics[:15]:
        print(f"  • {kw}: {w}")


def main():
    parser = argparse.ArgumentParser(description="News Reader Skill CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Feed
    p_feed = subparsers.add_parser("feed", help="Get personalized feed")
    p_feed.add_argument("--user-id", default="default", help="User ID")
    p_feed.add_argument("--limit", type=int, default=10, help="Max articles")
    p_feed.add_argument("--refresh", action="store_true", help="Force refresh RSS")
    p_feed.add_argument("--json", action="store_true", help="Output JSON")

    # Digest
    p_digest = subparsers.add_parser("digest", help="Generate AI digest")
    p_digest.add_argument("--user-id", default="default", help="User ID")
    p_digest.add_argument("--json", action="store_true", help="Output JSON")

    # Feedback
    p_fb = subparsers.add_parser("feedback", help="Send training feedback")
    p_fb.add_argument("--article-id", required=True, help="Article ID")
    p_fb.add_argument("--action", required=True, choices=["like", "dislike", "bookmark", "read", "hide"])
    p_fb.add_argument("--title", default="", help="Article title")
    p_fb.add_argument("--category", default="general", help="Category")
    p_fb.add_argument("--user-id", default="default", help="User ID")

    # Profile
    p_prof = subparsers.add_parser("profile", help="Show user profile")
    p_prof.add_argument("--user-id", default="default", help="User ID")
    p_prof.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()
    if args.command == "feed":
        cmd_feed(args)
    elif args.command == "digest":
        cmd_digest(args)
    elif args.command == "feedback":
        cmd_feedback(args)
    elif args.command == "profile":
        cmd_profile(args)


if __name__ == "__main__":
    main()
