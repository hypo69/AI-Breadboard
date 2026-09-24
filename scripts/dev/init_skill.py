# -*- coding: utf-8 -*-
# =============================================================================
# Скрипт для инициализации структуры нового навыка
# =============================================================================

import argparse
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path для корректного импорта модулей
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

try:
    from logger.logger import logger
except ImportError:
    # Fallback на базовое логирование при отсутствии логгера проекта
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("skill_init")

def init_skill(name: str, description: str, description_ru: str) -> None:
    """
    Инициализирует директорию и файлы для нового навыка.

    Args:
        name (str): Имя навыка.
        description (str): Описание на английском.
        description_ru (str): Описание на русском.
    """
    base_skills_dir = Path(".skills")
    skill_dir = base_skills_dir / name

    try:
        if skill_dir.exists():
            logger.error(f"Директория навыка {name} уже существует: {skill_dir}")
            return

        skill_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Создана директория навыка: {skill_dir}")

        # SKILL.md
        skill_md_path = skill_dir / "SKILL.md"
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(f"""---
name: {name}
description: {description}
description_i18n:
  en: {description}
  ru: {description_ru}
---
# {name}

Здесь напишите описание возможностей навыка.
""")
        logger.info(f"Создан файл SKILL.md: {skill_md_path}")

        # README.md
        readme_md_path = skill_dir / "README.md"
        with open(readme_md_path, "w", encoding="utf-8") as f:
            f.write(f"""# {name}

{description_ru}

## Описание
Описание навыка и его функциональности.

## Установка
Описание процесса установки.

## Использование
Примеры использования навыка.
""")
        logger.info(f"Создан файл README.md: {readme_md_path}")

    except Exception as e:
        logger.error(f"Ошибка при создании навыка {name}: {e}")
        sys.exit(1)

def main() -> None:
    """
    Точка входа скрипта.
    """
    parser = argparse.ArgumentParser(description="Инициализация нового навыка.")
    parser.add_argument("--name", required=True, help="Имя навыка")
    parser.add_argument("--description", required=True, help="Описание на английском")
    parser.add_argument("--description-ru", required=True, help="Описание на русском")

    args = parser.parse_args()
    init_skill(args.name, args.description, args.description_ru)

if __name__ == "__main__":
    main()
