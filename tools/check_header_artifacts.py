# Updated: 2026-10-03 22:23:00
"""check_header_artifacts.py

Скрипт рекурсивно проверяет все файлы проекта на наличие артефактов в шапке
(дублирующие строки "Updated:" или несоответствие даты в шапке реальному
времени изменения файла).

Выводит список проблемных файлов в стандартный вывод.
"""

import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = r"c:\\Users\\onela\\AppData\\Local\\AI-Breadboard"

# Поддерживаемые расширения и маркеры комментариев (см. update_file_headers.py)
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

# Регулярное выражение для строки заголовка
HEADER_REGEX = re.compile(r"^\s*(#|//|<!--|--|rem)\s*Updated:\s*\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def parse_timestamp(text: str) -> datetime:
    """Преобразует строку вида 'Updated: YYYY-MM-DD HH:MM:SS' в datetime.
    Возвращается в часовом поясе проекта (+03:00)."""
    # Находим последнюю часть после слова Updated:
    ts_str = text.split('Updated:')[-1].strip()
    tz = timezone(timedelta(hours=3))
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)


def check_file(file_path: Path):
    """Проверяет один файл и возвращает список найденных проблем.
    Проблемы могут быть:
    - отсутствует строка заголовка;
    - несколько строк заголовка (дубли);
    - дата в заголовке сильно отличается от времени изменения файла.
    """
    issues = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()[:20]
    except Exception as e:
        issues.append(f"Не удалось прочитать файл: {e}")
        return issues

    header_lines = [ln for ln in lines if HEADER_REGEX.match(ln)]
    if not header_lines:
        issues.append("Отсутствует строка Updated")
        return issues
    if len(header_lines) > 1:
        issues.append(f"Найдено {len(header_lines)} строк Updated (дубли)")

    # Проверка актуальности даты
    try:
        header_dt = parse_timestamp(header_lines[0])
        # Время изменения файла в той же таймзоне
        mtime_ts = file_path.stat().st_mtime
        file_dt = datetime.fromtimestamp(mtime_ts, tz=header_dt.tzinfo)
        # Если разница более 5 минут, считаем устаревшим
        if abs((file_dt - header_dt).total_seconds()) > 300:
            issues.append(f"Дата Updated ({header_dt.strftime('%Y-%m-%d %H:%M:%S')}) отличается от mtime ({file_dt.strftime('%Y-%m-%d %H:%M:%S')})")
    except Exception as e:
        issues.append(f"Ошибка парсинга даты Updated: {e}")
    return issues


def main():
    problematic = []
    for root, _, files in os.walk(PROJECT_ROOT):
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in TARGET_EXTS:
                full_path = Path(root) / fname
                issues = check_file(full_path)
                if issues:
                    problematic.append((full_path, issues))
    if not problematic:
        print("Артефактов в заголовках не обнаружено.")
        return
    print(f"Найдено проблемных файлов: {len(problematic)}")
    for path, issues in problematic:
        print(f"\n{path}:")
        for iss in issues:
            print(f"  - {iss}")

if __name__ == "__main__":
    main()
