# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Markdown Hierarchy Chunker
# =============================================================================
# Description:
#   Parses Markdown and documentation files into hierarchical sections based on headings
#   retaining breadcrumbs, document types, and section context.
#
# File: md_parser.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Hierarchical Markdown section parser for codebase RAG.

Splits documentation into logical sections by headings rather than arbitrary character
splits, maintaining parent breadcrumbs and document type tagging.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Tuple


class MarkdownParser:
    """Parses Markdown files into hierarchical section chunks.

    Attributes:
        base_dir (Path): Project root directory.
    """

    def __init__(self, base_dir: Path) -> None:
        """Initialize the Markdown parser.

        Args:
            base_dir (Path): Base project directory root.
        """
        self.base_dir = Path(base_dir).resolve()

    def infer_doc_type(self, file_path: Path) -> str:
        """Infer document category from path and filename.

        Args:
            file_path (Path): Path to document.

        Returns:
            str: Document type ('project_overview', 'changelog', 'prompt', 'documentation').
        """
        name_lower = file_path.name.lower()
        rel_posix = file_path.as_posix().lower()

        if name_lower.startswith("readme"):
            return "project_overview"
        if name_lower.startswith("changelog"):
            return "changelog"
        if "prompt" in rel_posix:
            return "prompt"
        return "documentation"

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Markdown file into section chunks.

        Args:
            file_path (Path): Path to the Markdown file.

        Returns:
            List[Dict[str, Any]]: List of hierarchical section chunks.
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        rel_path = file_path.resolve().relative_to(self.base_dir).as_posix() if file_path.is_relative_to(self.base_dir) else file_path.as_posix()
        doc_type = self.infer_doc_type(file_path)

        lines = content.splitlines()
        chunks: List[Dict[str, Any]] = []

        # Stack of (level, heading_text)
        heading_stack: List[Tuple[int, str]] = []
        current_heading = file_path.stem
        current_lines: List[str] = []
        section_idx = 0

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            match = heading_pattern.match(line)
            if match:
                # Flush previous section
                if current_lines:
                    section_text = "\n".join(current_lines).strip()
                    if section_text:
                        chunks.append(self._create_section_chunk(
                            rel_path=rel_path,
                            doc_type=doc_type,
                            heading=current_heading,
                            heading_stack=list(heading_stack),
                            text_body=section_text,
                            section_idx=section_idx
                        ))
                        section_idx += 1
                    current_lines = []

                level = len(match.group(1))
                heading_text = match.group(2).strip()

                # Pop headings of equal or deeper level
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                heading_stack.append((level, heading_text))
                current_heading = heading_text
            else:
                current_lines.append(line)

        # Flush final section
        if current_lines:
            section_text = "\n".join(current_lines).strip()
            if section_text:
                chunks.append(self._create_section_chunk(
                    rel_path=rel_path,
                    doc_type=doc_type,
                    heading=current_heading,
                    heading_stack=list(heading_stack),
                    text_body=section_text,
                    section_idx=section_idx
                ))

        return chunks

    def _create_section_chunk(
        self,
        rel_path: str,
        doc_type: str,
        heading: str,
        heading_stack: List[Tuple[int, str]],
        text_body: str,
        section_idx: int
    ) -> Dict[str, Any]:
        """Create a section chunk dictionary."""
        breadcrumb = " > ".join([h[1] for h in heading_stack]) if heading_stack else heading
        parent_heading = heading_stack[-2][1] if len(heading_stack) > 1 else None

        clean_slug = re.sub(r"[^\w\-]", "_", heading.lower())
        chunk_id = f"{rel_path}#{clean_slug}_{section_idx}"

        text = (
            f"DOCUMENT: {rel_path}\n"
            f"TYPE: {doc_type}\n"
            f"HEADING: {heading}\n"
            f"{'PARENT_HEADING: ' + parent_heading + chr(10) if parent_heading else ''}"
            f"BREADCRUMB: {breadcrumb}\n\n"
            f"{text_body}"
        )

        return {
            "id": chunk_id,
            "path": rel_path,
            "type": doc_type,
            "heading": heading,
            "parent_heading": parent_heading,
            "breadcrumb": breadcrumb,
            "text": text,
            "body": text_body
        }
