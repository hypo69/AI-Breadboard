## \file .agents/skills/google-workspace/scripts/sync_drive_rag.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Sync Google Drive folder to Local RAG Pipeline.
===============================================

Downloads files from Google Drive and feeds them to the RAGDocumentCleaner.
"""

from pathlib import Path
import argparse
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Ensure scripts directory is on sys.path
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from src.logger.logger import logger

try:
    from gdrive_manager import GDriveManager
except ImportError:
    from .gdrive_manager import GDriveManager

try:
    from agents.skills.rag_cleaner.scripts.rag_cleaner import RAGDocumentCleaner
except ImportError:
    RAGDocumentCleaner = None


def sync_and_clean_folder(folder_query: str, download_dir: Path, output_jsonl: Path):
    """Download files from Google Drive and process them via RAGDocumentCleaner."""
    manager = GDriveManager()
    if not manager.service:
        logger.error("Drive service not available.")
        return

    logger.info(f"Searching Drive files for sync: {folder_query}")
    files = manager.list_files(query=folder_query, page_size=50)
    logger.info(f"Found {len(files)} files to download.")

    download_dir.mkdir(parents=True, exist_ok=True)
    cleaner = RAGDocumentCleaner()
    all_chunks = []

    for f in files:
        file_id = f["id"]
        name = f["name"]
        mime = f["mimeType"]
        dest = download_dir / name

        logger.info(f"Downloading: {name}...")
        success = manager.download_or_export_file(file_id, mime, dest)
        if success:
            # Check resulting file (it might have had an extension appended, e.g. .docx)
            target_files = list(download_dir.glob(f"{Path(name).stem}*"))
            for tf in target_files:
                chunks = list(cleaner.process_file(tf))
                all_chunks.extend(chunks)

    # Save chunks to output JSONL
    if all_chunks:
        import json
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with open(output_jsonl, "w", encoding="utf-8") as out:
            for chunk in all_chunks:
                out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        logger.info(f"Successfully generated {len(all_chunks)} RAG chunks at: {output_jsonl}")
        print(f"✅ Synced and parsed {len(all_chunks)} chunks to {output_jsonl}")
    else:
        logger.warning("No chunks were parsed.")


def main():
    parser = argparse.ArgumentParser(description="Sync Google Drive to RAG Knowledge Base")
    parser.add_argument("--query", "-q", default="trashed = false", help="Drive search query / folder filter")
    parser.add_argument("--dest", "-d", default="data/gdrive_sync", help="Local download directory")
    parser.add_argument("--output", "-o", default="data/gdrive_chunks.jsonl", help="Output JSONL path for RAG")
    args = parser.parse_args()

    sync_and_clean_folder(
        folder_query=args.query,
        download_dir=Path(args.dest),
        output_jsonl=Path(args.output)
    )


if __name__ == "__main__":
    main()
