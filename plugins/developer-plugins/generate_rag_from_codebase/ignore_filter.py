# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Codebase RAG Ignore and Secret Filter
# =============================================================================
# Description:
#   Provides glob pattern filtering, .ragignore parsing, and secret detection/redaction
#   to prevent sensitive keys, build artifacts, and logs from entering the RAG index.
#
# File: ignore_filter.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Ignore filter and secret detector for codebase RAG ingestion.

Handles path exclusions based on standard ignore patterns and .ragignore rules,
along with regex-based secret detection and redaction.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
import re
from typing import List, Optional, Sequence


# Common secret patterns
SECRET_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|password|passwd|jwt[_-]?secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),  # Google API key
    re.compile(r"sk-[a-zA-Z0-9]{20,48}"),  # OpenAI API key
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),    # GitHub Personal Access Token
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),       # AWS Access Key
]


class IgnoreFilter:
    """Filter to exclude unwanted paths and redact confidential credentials.

    Attributes:
        ignore_patterns (List[str]): List of glob match patterns to ignore.
        base_dir (Path): Base project directory root.
    """

    def __init__(self, base_dir: Path, ignore_patterns: Optional[Sequence[str]] = None) -> None:
        """Initialize the filter.

        Args:
            base_dir (Path): Project root directory.
            ignore_patterns (Optional[Sequence[str]]): List of pattern strings.
        """
        self.base_dir = Path(base_dir).resolve()
        self.ignore_patterns: List[str] = list(ignore_patterns or [])
        self._load_ragignore()

    def _load_ragignore(self) -> None:
        """Load .ragignore file from the project root if present."""
        ragignore_path = self.base_dir / ".ragignore"
        if ragignore_path.exists():
            try:
                lines = ragignore_path.read_text(encoding="utf-8").splitlines()
                for line in lines:
                    cleaned = line.strip()
                    if cleaned and not cleaned.startswith("#"):
                        self.ignore_patterns.append(cleaned)
            except Exception:
                pass

    def is_ignored(self, path: Path) -> bool:
        """Check if a path matches any ignore rule.

        Args:
            path (Path): Path to inspect.

        Returns:
            bool: True if the path should be ignored, False otherwise.
        """
        try:
            rel_path = path.resolve().relative_to(self.base_dir).as_posix()
        except ValueError:
            rel_path = path.as_posix()

        parts = rel_path.split("/")
        
        # Check explicit parts
        for part in parts:
            if part in {".git", ".venv", "venv", "env", "__pycache__", "logs", "site", "SANDBOX"}:
                return True

        for pattern in self.ignore_patterns:
            norm_pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, norm_pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(path.name, norm_pattern):
                return True
            # Also check matching for subdirectory prefixes
            if pattern.endswith("/**") and rel_path.startswith(pattern[:-3]):
                return True

        return False

    @staticmethod
    def contains_secrets(content: str) -> bool:
        """Check if content string appears to contain secrets.

        Args:
            content (str): Text content to inspect.

        Returns:
            bool: True if secret patterns are matched.
        """
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                return True
        return False

    @staticmethod
    def redact_secrets(content: str) -> str:
        """Redact sensitive patterns in text.

        Args:
            content (str): Raw text content.

        Returns:
            str: Content with detected secrets masked.
        """
        redacted = content
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
        return redacted
