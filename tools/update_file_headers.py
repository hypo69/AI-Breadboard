# Updated: 2026-10-03 22:16:40
"""update_file_headers.py

Скрипт для массового обновления заголовков файлов проекта согласно стандарту.
Поддерживаемые расширения и маркеры комментариев:
    .py, .ps1, .sh -> '#'
    .html -> '<!-- -->'
    .js, .css, .php -> '//'
    .sql -> '--'
    .bat, .cmd -> 'rem'

В начале каждого файла будет строка `# Updated: YYYY-MM-DD HH:MM:SS` (или соответствующий маркер).
Точность даты‑времени берётся в локальном часовом поясе проекта (+03:00).
"""

import os
import re
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = r"c:\\Users\\onela\\AppData\\Local\\AI-Breadboard"

TARGET_EXTS = {
    ".py": "#",
    ".ps1": "#",
    ".sh": "#",
    ".html": "<!--",
    ".js": "//",
    ".css": "//",
    ".php": "//",
    ".sql": "--",
    ".bat": "rem",
    ".cmd": "rem",
}

# Регулярное выражение для уже существующего заголовка
HEADER_REGEX = re.compile(r"^\s*(#|//|<!--|--|rem)\s*Updated:\s*\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

def format_timestamp() -> str:
    """Возвращает текущий timestamp в локальном часовом поясе (+03:00)."""
    tz = timezone(timedelta(hours=3))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def build_header(marker: str) -> str:
    """Создаёт строку заголовка для заданного маркера комментария."""
    ts = format_timestamp()
    if marker == "<!--":
        return f"<!-- Updated: {ts} -->"
    return f"{marker} Updated: {ts}"

def process_file(path: str, marker: str) -> bool:
    """Обрабатывает один файл.

    Возвращает True, если файл был изменён (добавлен или исправлен заголовок).
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    header_idx = None
    for i, line in enumerate(lines[:5]):
        if HEADER_REGEX.match(line):
            header_idx = i
            break
    new_header = build_header(marker) + "\n"
    updated = False
    if header_idx is not None:
        if lines[header_idx].strip() != new_header.strip():
            lines[header_idx] = new_header
            updated = True
    else:
        lines.insert(0, new_header)
        updated = True
    if updated:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return updated

def main():
    total = 0
    changed = 0
    for root, _, files in os.walk(PROJECT_ROOT):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in TARGET_EXTS:
                total += 1
                full_path = os.path.join(root, fname)
                if process_file(full_path, TARGET_EXTS[ext]):
                    changed += 1
    print(f"Processed {total} files, updated {changed} headers.")

if __name__ == "__main__":
    main()
