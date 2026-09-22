# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Channel RAG Message Ingestion & Web Scraping
# =============================================================================
# Description:
#   Collects Telegram messages from public channel web previews or exported
#   JSON archives, normalizes text content, and constructs message permalinks.
#
# File: collector.py
# Project: ai-breadboard
# Package: plugins.telegram_channel_rag
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Telegram message collection and parsing module.

Provides web scrapers for public Telegram channels and parsers for exported JSON
chat logs, extracting message IDs, sender names, text content, media captions,
and formatted Telegram URLs.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

from logger import logger


class TelegramMessageCollector:
    """Collects and extracts structured message dictionaries from channels or files.

    Attributes:
        channel_username (str): Target channel or group username (e.g. 'canozrimb').
        headers (Dict[str, str]): HTTP request headers for web scraping.
    """

    def __init__(self, channel_username: str = "canozrimb") -> None:
        """Initialize the message collector.

        Args:
            channel_username (str): Username of the channel or group (without @ or URL).
        """
        self.channel_username = self._clean_username(channel_username)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        }

    def _clean_username(self, raw_input: str) -> str:
        """Clean channel username or link.

        Args:
            raw_input (str): Raw string containing URL, @name, or channel name.

        Returns:
            str: Clean alphanumeric username.
        """
        s = raw_input.strip()
        s = re.sub(r"^https?://t\.me/(s/)?", "", s)
        s = s.lstrip("@").rstrip("/")
        return s.split("/")[0]

    def build_message_url(self, message_id: Union[int, str]) -> str:
        """Build direct Telegram permalink to message.

        Args:
            message_id (Union[int, str]): Numerical message identifier.

        Returns:
            str: Public Telegram message URL.
        """
        return f"https://t.me/{self.channel_username}/{message_id}"

    def fetch_from_web_preview(self, max_messages: int = 500) -> List[Dict[str, Any]]:
        """Scrape public messages from Telegram web preview (t.me/s/<channel>).

        Args:
            max_messages (int): Maximum number of messages to retrieve.

        Returns:
            List[Dict[str, Any]]: List of structured message dictionaries.
        """
        results: List[Dict[str, Any]] = []
        seen_ids = set()
        base_url = f"https://t.me/s/{self.channel_username}"
        current_url = base_url

        try:
            while current_url and len(results) < max_messages:
                req = urllib.request.Request(current_url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    html_content = response.read().decode("utf-8", errors="replace")

                soup = BeautifulSoup(html_content, "html.parser")
                message_elements = soup.find_all("div", class_=re.compile(r"tgme_widget_message"))

                if not message_elements:
                    break

                batch_msgs: List[Dict[str, Any]] = []
                for el in message_elements:
                    data_post = el.get("data-post", "")
                    if "/" not in data_post:
                        continue
                    try:
                        msg_id = int(data_post.split("/")[-1])
                    except ValueError:
                        continue

                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)

                    # Extract author
                    author_el = el.find("div", class_="tgme_widget_message_owner_name")
                    author = author_el.get_text(strip=True) if author_el else self.channel_username

                    # Extract datetime
                    time_el = el.find("time")
                    timestamp_str = time_el.get("datetime", "") if time_el else ""

                    # Extract text content
                    text_el = el.find("div", class_="tgme_widget_message_text")
                    text = text_el.get_text(separator="\n", strip=True) if text_el else ""

                    # Check for media captions or photo/video indicators if text is empty
                    if not text:
                        photo_el = el.find("a", class_="tgme_widget_message_photo_wrap")
                        video_el = el.find("video")
                        doc_el = el.find("div", class_="tgme_widget_message_document_title")
                        if doc_el:
                            text = f"[Document: {doc_el.get_text(strip=True)}]"
                        elif photo_el:
                            text = "[Photo Attachment]"
                        elif video_el:
                            text = "[Video Attachment]"

                    if not text.strip():
                        continue

                    url = self.build_message_url(msg_id)

                    batch_msgs.append({
                        "id": msg_id,
                        "channel": self.channel_username,
                        "author": author,
                        "timestamp": timestamp_str,
                        "text": text,
                        "url": url,
                        "source": "web_preview",
                    })

                if not batch_msgs:
                    break

                results.extend(batch_msgs)

                # Pagination backwards if needed
                prev_link = soup.find("link", rel="prev")
                if prev_link and prev_link.get("href"):
                    next_href = prev_link.get("href")
                    if next_href.startswith("/"):
                        current_url = f"https://t.me{next_href}"
                    else:
                        current_url = next_href
                else:
                    break

            logger.info(f"Fetched {len(results)} messages from Telegram channel preview: {self.channel_username}")
        except Exception as exc:
            logger.error(f"Error scraping Telegram channel preview for {self.channel_username}: {exc}")

        return results[:max_messages]

    def parse_export_json(self, export_file_path: Union[Path, str]) -> List[Dict[str, Any]]:
        """Parse exported Telegram Desktop chat history (result.json).

        Args:
            export_file_path (Union[Path, str]): Path to the result.json export file.

        Returns:
            List[Dict[str, Any]]: List of structured message dictionaries.
        """
        p = Path(export_file_path)
        if not p.exists():
            logger.error(f"Telegram export file not found at {p}")
            return []

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            raw_messages = data.get("messages", [])
            results: List[Dict[str, Any]] = []

            for msg in raw_messages:
                if msg.get("type") != "message":
                    continue

                msg_id = msg.get("id")
                if not msg_id:
                    continue

                author = msg.get("from") or self.channel_username
                date_str = msg.get("date", "")
                
                # Text can be a string or a list of mixed text/link objects
                text_raw = msg.get("text", "")
                if isinstance(text_raw, list):
                    text_parts = []
                    for chunk in text_raw:
                        if isinstance(chunk, str):
                            text_parts.append(chunk)
                        elif isinstance(chunk, dict) and "text" in chunk:
                            text_parts.append(chunk["text"])
                    text = "".join(text_parts).strip()
                else:
                    text = str(text_raw).strip()

                if not text:
                    if msg.get("media_type"):
                        text = f"[{msg.get('media_type').capitalize()} Attachment]"
                    elif msg.get("file"):
                        text = f"[File: {msg.get('file')}]"
                    elif msg.get("photo"):
                        text = "[Photo Attachment]"

                if not text.strip():
                    continue

                url = self.build_message_url(msg_id)

                results.append({
                    "id": msg_id,
                    "channel": self.channel_username,
                    "author": author,
                    "timestamp": date_str,
                    "text": text,
                    "url": url,
                    "source": "json_export",
                })

            logger.info(f"Parsed {len(results)} messages from Telegram export file {p.name}")
            return results
        except Exception as exc:
            logger.error(f"Failed to parse Telegram JSON export: {exc}")
            return []
