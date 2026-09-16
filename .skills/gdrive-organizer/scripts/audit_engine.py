## \file skills/gdrive-organizer/scripts/audit_engine.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Drive Audit Engine Module.
=================================

Analyzes Drive file hierarchies, calculates disorganization metrics,
and detects root clutter, duplicate candidates, chaotic versioning, and empty folders.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.logger.logger import logger


class GDriveAuditEngine:
    """Evaluates organization quality and detects structural issues in Google Drive."""

    # Regex patterns for messy versioning / copy naming
    COPY_PATTERNS = [
        re.compile(r"^copy\s+of\s+", re.IGNORECASE),
        re.compile(r"^копия\s+", re.IGNORECASE),
        re.compile(r"\s*\(\d+\)(\.[a-zA-Z0-9]+)?$"),
        re.compile(r"[_\-\s]+(v\d+|ver\d+|final|draft|backup|копия)(\.[a-zA-Z0-9]+)?$", re.IGNORECASE),
    ]

    GENERIC_FOLDER_NAMES = {
        "new folder", "новая папка", "untitled folder", "папка", "misc", "temp", "tmp", "stuff", "files", "1"
    }

    def __init__(self, hierarchy: Dict[str, Any]) -> None:
        """
        Initialize Audit Engine with hierarchy metadata.

        :param hierarchy: Output dictionary from GDriveScanner.build_hierarchy().
        """
        self.hierarchy = hierarchy
        self.items_by_id = hierarchy.get("items_by_id", {})
        self.folders = hierarchy.get("folders", {})
        self.files = hierarchy.get("files", [])
        self.paths_by_id = hierarchy.get("paths_by_id", {})

    def detect_root_files(self) -> List[Dict[str, Any]]:
        """
        Find files residing directly in the Drive root directory.

        :return: List of root file objects.
        """
        root_files = []
        for file in self.files:
            parents = file.get("parents", [])
            # If no parents, or none of the parents are known folders in self.folders
            if not parents or not any(p in self.folders for p in parents):
                root_files.append(file)
        return root_files

    def detect_duplicates(self) -> List[Dict[str, Any]]:
        """
        Identify exact duplicate candidates by MD5 checksum or (name + size).

        :return: List of duplicate group summaries.
        """
        checksum_map: Dict[str, List[Dict[str, Any]]] = {}
        name_size_map: Dict[str, List[Dict[str, Any]]] = {}

        for file in self.files:
            md5 = file.get("md5Checksum")
            name = file.get("name", "").strip().lower()
            size = file.get("size")

            if md5:
                checksum_map.setdefault(md5, []).append(file)
            elif name and size:
                key = f"{name}::{size}"
                name_size_map.setdefault(key, []).append(file)

        duplicate_groups = []

        # Process MD5 matches
        for md5, items in checksum_map.items():
            if len(items) > 1:
                duplicate_groups.append({
                    "type": "exact_md5",
                    "key": md5,
                    "count": len(items),
                    "items": items,
                })

        # Process name+size matches (if not already covered by MD5)
        for key, items in name_size_map.items():
            if len(items) > 1:
                # Check if already in duplicate_groups
                existing_ids = {f["id"] for group in duplicate_groups for f in group["items"]}
                uncovered = [f for f in items if f["id"] not in existing_ids]
                if len(uncovered) > 1:
                    duplicate_groups.append({
                        "type": "name_and_size",
                        "key": key,
                        "count": len(uncovered),
                        "items": uncovered,
                    })

        return duplicate_groups

    def detect_version_clutter(self) -> List[Dict[str, Any]]:
        """
        Find files with copy/version clutter names (e.g. 'Copy of Project (1).docx').

        :return: List of cluttered file records.
        """
        cluttered = []
        for file in self.files:
            name = file.get("name", "")
            for pat in self.COPY_PATTERNS:
                if pat.search(name):
                    cluttered.append({
                        "file": file,
                        "matched_pattern": pat.pattern,
                    })
                    break
        return cluttered

    def detect_empty_folders(self) -> List[Dict[str, Any]]:
        """
        Find folders containing no child files or subfolders.

        :return: List of empty folder objects.
        """
        parent_id_counts: Dict[str, int] = {}
        for item in self.items_by_id.values():
            for p in item.get("parents", []):
                parent_id_counts[p] = parent_id_counts.get(p, 0) + 1

        empty_folders = []
        for folder_id, folder in self.folders.items():
            if parent_id_counts.get(folder_id, 0) == 0:
                empty_folders.append(folder)

        return empty_folders

    def detect_generic_folders(self) -> List[Dict[str, Any]]:
        """
        Find folders with non-descriptive names like 'New Folder', 'temp', 'misc'.

        :return: List of generic folders.
        """
        generic = []
        for folder in self.folders.values():
            name = folder.get("name", "").strip().lower()
            base_name = re.sub(r"\s*\(\d+\)$", "", name).strip()
            if base_name in self.GENERIC_FOLDER_NAMES or re.match(r"^новая папка( \(\d+\))?$", name):
                generic.append(folder)
        return generic

    def run_full_audit(self) -> Dict[str, Any]:
        """
        Perform complete audit and return aggregated health metrics and findings.

        :return: Dictionary containing issues, metrics, score, and breakdown.
        """
        root_files = self.detect_root_files()
        duplicates = self.detect_duplicates()
        version_clutter = self.detect_version_clutter()
        empty_folders = self.detect_empty_folders()
        generic_folders = self.detect_generic_folders()

        total_files = len(self.files)
        total_folders = len(self.folders)
        total_items = total_files + total_folders

        # Calculate Health Score (100 is pristine, 0 is total disaster)
        score = 100.0
        if total_files > 0:
            root_ratio = len(root_files) / total_files
            score -= root_ratio * 30.0  # Max 30 pts penalty for root clutter

            duplicate_file_count = sum(len(g["items"]) - 1 for g in duplicates)
            dup_ratio = duplicate_file_count / total_files
            score -= dup_ratio * 25.0  # Max 25 pts penalty for duplicates

            clutter_ratio = len(version_clutter) / total_files
            score -= clutter_ratio * 20.0  # Max 20 pts penalty for version mess

        if total_folders > 0:
            empty_ratio = len(empty_folders) / total_folders
            score -= empty_ratio * 15.0  # Max 15 pts penalty for empty folders

            generic_ratio = len(generic_folders) / total_folders
            score -= generic_ratio * 10.0  # Max 10 pts penalty for generic folder names

        score = max(0.0, min(100.0, round(score, 1)))

        logger.info(f"Drive audit complete: Total items: {total_items}, Health Score: {score}/100")

        return {
            "health_score": score,
            "total_items": total_items,
            "total_files": total_files,
            "total_folders": total_folders,
            "root_files": root_files,
            "duplicates": duplicates,
            "version_clutter": version_clutter,
            "empty_folders": empty_folders,
            "generic_folders": generic_folders,
        }
