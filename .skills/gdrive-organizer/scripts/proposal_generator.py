## \file skills/gdrive-organizer/scripts/proposal_generator.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Drive Restructuring Proposal Generator.
==============================================

Analyzes audit findings and produces a structured reorganization proposal,
categorizing files into logical folder trees and generating actionable plans.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
import re
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from logger.logger import logger


class GDriveProposalGenerator:
    """Generates structural recommendations and migration plans for Google Drive."""

    # Categorization keywords and rules
    RULES = [
        {
            "target": "/Finance/Invoices & Receipts",
            "extensions": [".pdf", ".xlsx", ".csv"],
            "keywords": ["invoice", "receipt", "счет", "квитанция", "чек", "оплата", "payment", "bill", "tax", "налог"],
        },
        {
            "target": "/Documents/Contracts & Legal",
            "extensions": [".pdf", ".docx", ".doc"],
            "keywords": ["contract", "agreement", "nda", "договор", "соглашение", "акт", "устав", "legal", "доверенность"],
        },
        {
            "target": "/Media/Images",
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".heic"],
            "keywords": ["photo", "screenshot", "снимок", "фото", "img", "image", "screen"],
        },
        {
            "target": "/Media/Videos",
            "extensions": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
            "keywords": ["video", "видео", "recording", "запись", "screen-recording"],
        },
        {
            "target": "/Projects/Presentations & Pitches",
            "extensions": [".pptx", ".ppt", ".key", ".gslides"],
            "keywords": ["pitch", "presentation", "презентация", "deck", "slides", "доклад"],
        },
        {
            "target": "/Archives/Backups & Dumps",
            "extensions": [".zip", ".tar", ".gz", ".7z", ".rar", ".bak", ".sql", ".dump"],
            "keywords": ["backup", "бэкап", "dump", "archive", "архив", "копия"],
        },
        {
            "target": "/Documents/Notes & Drafts",
            "extensions": [".md", ".txt", ".rtf"],
            "keywords": ["note", "draft", "заметка", "черновик", "todo", "ideas", "мысли"],
        },
    ]

    def __init__(self, audit_results: Dict[str, Any], hierarchy: Dict[str, Any]) -> None:
        """
        Initialize Proposal Generator.

        :param audit_results: Results dictionary from GDriveAuditEngine.
        :param hierarchy: Hierarchy metadata from GDriveScanner.
        """
        self.audit = audit_results
        self.hierarchy = hierarchy
        self.files = hierarchy.get("files", [])
        self.folders = hierarchy.get("folders", {})

    def _infer_category(self, file: Dict[str, Any]) -> str:
        """
        Determine logical destination directory based on name, mimeType, and modified date.

        :param file: File metadata dictionary.
        :return: Proposed directory path.
        """
        name = file.get("name", "").lower()
        mime = file.get("mimeType", "").lower()

        # Check keyword and extension rules
        for rule in self.RULES:
            ext_match = any(name.endswith(ext) for ext in rule["extensions"])
            kw_match = any(kw in name for kw in rule["keywords"])

            if ext_match and kw_match:
                return rule["target"]

        for rule in self.RULES:
            if any(kw in name for kw in rule["keywords"]):
                return rule["target"]

        # MIME type fallbacks
        if "spreadsheet" in mime or name.endswith((".xlsx", ".csv", ".ods")):
            return "/Documents/Spreadsheets"
        if "document" in mime or name.endswith((".docx", ".doc", ".odt", ".pdf")):
            return "/Documents/General"
        if "image" in mime:
            return "/Media/Images"
        if "video" in mime:
            return "/Media/Videos"
        if "zip" in mime or "compressed" in mime or name.endswith((".zip", ".tar.gz", ".rar")):
            return "/Archives"

        return "/Miscellaneous"

    def generate_plan(self) -> Dict[str, Any]:
        """
        Generate list of proposed actions (MOVE, RENAME, DEDUPLICATE).

        :return: Restructuring plan dictionary.
        """
        actions: List[Dict[str, Any]] = []
        handled_file_ids = set()

        # 1. Duplicate removal/archival suggestions first
        for dup_group in self.audit.get("duplicates", []):
            items = sorted(dup_group["items"], key=lambda x: x.get("modifiedTime", ""), reverse=True)
            # Keep newest, suggest archiving others
            master = items[0]
            for copy_item in items[1:]:
                actions.append({
                    "action": "ARCHIVE_DUPLICATE",
                    "file_id": copy_item["id"],
                    "file_name": copy_item.get("name"),
                    "current_path": copy_item.get("full_path"),
                    "target_folder": "/Archives/Duplicates",
                    "reason": f"Duplicate copy of master file '{master.get('name')}' (ID: {master.get('id')}).",
                })
                handled_file_ids.add(copy_item["id"])

        # 2. Root loose files -> Move to logical categories (if not already handled as duplicate)
        root_files = self.audit.get("root_files", [])
        for file in root_files:
            if file["id"] in handled_file_ids:
                continue
            target_folder = self._infer_category(file)
            actions.append({
                "action": "MOVE",
                "file_id": file["id"],
                "file_name": file.get("name"),
                "current_path": file.get("full_path", "/[Root]"),
                "target_folder": target_folder,
                "reason": "File is loose in Root directory; categorized by content and type.",
            })
            handled_file_ids.add(file["id"])

        # 3. Version clutter cleanup recommendations
        for clutter in self.audit.get("version_clutter", []):
            f = clutter["file"]
            clean_name = re.sub(r"^copy\s+of\s+|^копия\s+", "", f.get("name", ""), flags=re.IGNORECASE)
            actions.append({
                "action": "RENAME_SUGGESTION",
                "file_id": f["id"],
                "file_name": f.get("name"),
                "current_path": f.get("full_path"),
                "suggested_name": clean_name,
                "reason": "Redundant copy/version prefix detected.",
            })

        return {
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_actions": len(actions),
            "actions": actions,
        }

    def generate_markdown_report(self, plan: Optional[Dict[str, Any]] = None) -> str:
        """
        Format audit findings and restructuring plan into human-readable Markdown.

        :param plan: Optional restructuring plan (generated if None).
        :return: Markdown text.
        """
        if plan is None:
            plan = self.generate_plan()

        health = self.audit.get("health_score", 100.0)
        total_files = self.audit.get("total_files", 0)
        total_folders = self.audit.get("total_folders", 0)
        root_count = len(self.audit.get("root_files", []))
        dup_count = len(self.audit.get("duplicates", []))
        clutter_count = len(self.audit.get("version_clutter", []))
        empty_count = len(self.audit.get("empty_folders", []))

        # Status indicator
        if health >= 85:
            health_badge = "🟢 **Excellent**"
        elif health >= 60:
            health_badge = "🟡 **Moderate Disorganization**"
        else:
            health_badge = "🔴 **Severe Disorganization**"

        lines = [
            "# 📊 Google Drive Organization & Cleanup Report",
            "",
            f"**Organization Health Score:** {health}/100 ({health_badge})  ",
            f"**Scanned Items:** {total_files} files, {total_folders} folders  ",
            "",
            "---",
            "",
            "## 🔍 Disorganization Summary",
            "",
            "| Issue Type | Count | Impact & Description |",
            "| :--- | :--- | :--- |",
            f"| **Root Clutter** | `{root_count}` | Loose files dumped in root without categorization |",
            f"| **Duplicate Groups** | `{dup_count}` | Redundant copies consuming quota and causing confusion |",
            f"| **Version / Copy Clutter** | `{clutter_count}` | Files with 'Copy of', '(1)', or messy version tags |",
            f"| **Empty / Orphan Folders** | `{empty_count}` | Unused empty directories cluttering navigation |",
            "",
            "---",
            "",
            "## 💡 Proposed Restructuring Plan",
            "",
            f"Total recommended actions: **{plan['total_actions']}**",
            "",
        ]

        if plan["actions"]:
            lines.extend([
                "| Action | File Name | Current Location | Proposed Action / Target | Rationale |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ])
            for act in plan["actions"][:30]:  # Cap preview at 30 rows
                action_type = act["action"]
                name = act.get("file_name", "Untitled")
                current = act.get("current_path", "/")
                target = act.get("target_folder") or act.get("suggested_name", "-")
                reason = act.get("reason", "")
                lines.append(f"| `{action_type}` | **{name}** | `{current}` | `{target}` | {reason} |")

            if len(plan["actions"]) > 30:
                lines.append(f"\n*(... and {len(plan['actions']) - 30} more actions)*\n")
        else:
            lines.append("🎉 *Your Google Drive is in great shape! No structural changes needed.*")

        lines.extend([
            "",
            "---",
            "",
            "## 🚀 Next Steps",
            "- To preview or apply this reorganization plan via CLI:",
            "  ```powershell",
            "  python skills/gdrive-organizer/scripts/main.py propose --out plan.json",
            "  python skills/gdrive-organizer/scripts/main.py apply --plan plan.json --dry-run",
            "  ```",
        ])

        return "\n".join(lines)
