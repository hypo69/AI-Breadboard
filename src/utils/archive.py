# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import tarfile
import zipfile
from pathlib import Path
from typing import List, Optional, Union
from src.logger.logger import logger

def is_system_file(name: str) -> bool:
    parts = Path(name).parts
    for part in parts:
        if part.startswith('__MACOSX') or part.startswith('~$') or part == '.DS_Store' or part == 'Thumbs.db':
            return True
    return False

def extract_archive(
    archive_path: Union[str, Path],
    extract_to: Optional[Union[str, Path]] = None,
    allowed_extensions: Optional[List[str]] = None,
) -> List[Path]:
    archive_path = Path(archive_path)
    if not archive_path.is_file():
        logger.error(f'Archive file not found: {archive_path}')
        return []

    if extract_to is None:
        extract_to = archive_path.parent / f'extracted_{archive_path.stem}'
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    extracted_files: List[Path] = []
    ext = archive_path.suffix.lower()

    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for member in zf.infolist():
                    if member.is_dir() or is_system_file(member.filename):
                        continue
                    target_path = (extract_to / member.filename).resolve()
                    if not str(target_path).startswith(str(extract_to.resolve())):
                        logger.warning(f'Skipping dangerous zip path: {member.filename}')
                        continue
                    if allowed_extensions:
                        if target_path.suffix.lower() not in [e.lower() for e in allowed_extensions]:
                            continue
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
                    extracted_files.append(target_path)

        elif ext in ['.tar', '.gz', '.tgz', '.bz2']:
            with tarfile.open(archive_path, 'r:*') as tf:
                for member in tf.getmembers():
                    if member.isdir() or is_system_file(member.name):
                        continue
                    target_path = (extract_to / member.name).resolve()
                    if not str(target_path).startswith(str(extract_to.resolve())):
                        logger.warning(f'Skipping dangerous tar path: {member.name}')
                        continue
                    if allowed_extensions:
                        if target_path.suffix.lower() not in [e.lower() for e in allowed_extensions]:
                            continue
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    tf.extract(member, path=extract_to)
                    extracted_files.append(target_path)
        else:
            logger.warning(f'Unsupported archive format: {ext}')

    except Exception as ex:
        logger.error(f'Failed to extract archive {archive_path}', ex)

    return extracted_files
