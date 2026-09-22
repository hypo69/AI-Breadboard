# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Sync Google Drive to RAG Knowledge Base
# =============================================================================
# Description:
#   Downloads documents from Google Drive and converts them into searchable RAG chunks.
#
# File: sync_drive_rag.py
# Project: ai-breadboard
# Package: .agents.skills.google-drive.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from gdrive_manager import GDriveManager
from logger.logger import logger

try:
    from agents.skills.rag_cleaner.scripts.rag_cleaner import RAGDocumentCleaner
except ImportError:
    try:
        from plugins.user_plugins.rag_cleaner.cleaner import RAGDocumentCleaner
    except ImportError:
        RAGDocumentCleaner = None


def sync_and_clean_folder(folder_query: str, download_dir: Path, output_jsonl: Path, account: str = None):
    """Выгрузка файлов из Drive и формирование RAG-чанков."""
    manager = GDriveManager(account_name=account)
    if not manager.service:
        logger.error("Сервис Google Drive недоступен.")
        return

    logger.info(f"Поиск документов на Drive: {folder_query}")
    files = manager.list_files(query=folder_query, page_size=50)
    logger.info(f"Найдено {len(files)} файлов для синхронизации.")

    download_dir.mkdir(parents=True, exist_ok=True)
    cleaner = RAGDocumentCleaner() if RAGDocumentCleaner else None
    all_chunks = []

    for f in files:
        file_id = f["id"]
        name = f["name"]
        mime = f["mimeType"]
        dest = download_dir / name

        logger.info(f"Загрузка файла: {name}...")
        success = manager.download_or_export_file(file_id, mime, dest)
        if success and cleaner:
            target_files = list(download_dir.glob(f"{Path(name).stem}*"))
            for tf in target_files:
                chunks = list(cleaner.process_file(tf))
                all_chunks.extend(chunks)

    if all_chunks:
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with open(output_jsonl, "w", encoding="utf-8") as out:
            for chunk in all_chunks:
                out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        logger.info(f"Успешно создано {len(all_chunks)} RAG чанков в {output_jsonl}")
        print(f"✅ Синхронизировано и преобразовано {len(all_chunks)} чанков в {output_jsonl}")


def main():
    parser = argparse.ArgumentParser(description="Google Drive to RAG Sync")
    parser.add_argument("--query", "-q", default="mimeType = 'application/vnd.google-apps.document'", help="Фильтр файлов")
    parser.add_argument("--dest", "-d", default="data/gdrive_sync", help="Каталог сохранения")
    parser.add_argument("--output", "-o", default="data/gdrive_chunks.jsonl", help="Путь к результирующему JSONL")
    parser.add_argument("--account", "-a", default=None, help="Имя аккаунта")
    args = parser.parse_args()

    sync_and_clean_folder(
        folder_query=args.query,
        download_dir=Path(args.dest),
        output_jsonl=Path(args.output),
        account=args.account
    )


if __name__ == "__main__":
    main()

