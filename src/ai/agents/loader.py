# -*- coding: utf-8 -*-
"""Загрузчик агентов из JSON‑манифестов в каталоге ``.agents``.

Функция :func:`load_agent_from_manifest` читает файл ``.agents/<name>.json``,
извлекает поле ``class_path`` и импортирует указанный класс, возвращая его
инстанс. Это используется CLI‑утилитами ``gemini cli`` и ``agy cli`` для
динамического создания агентов без необходимости вручную прописывать импорт.
"""

import json
from importlib import import_module
from pathlib import Path
from typing import Any

# Путь к каталогу ``.agents`` – находится в корне проекта
_MANIFEST_ROOT = Path(__file__).resolve().parents[3] / ".agents"


def load_agent_from_manifest(name: str) -> Any:
    """Загрузить и инициализировать агент по его имени.

    Args:
        name: Имя манифеста без расширения (например, ``media_search``).

    Returns:
        Инстанс соответствующего класса агента.
    """
    manifest_path = _MANIFEST_ROOT / f"{name}.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Манифест {name}.json не найден в {_MANIFEST_ROOT}")
    with manifest_path.open(encoding="utf-8") as f:
        data = json.load(f)
    class_path = data.get("class_path")
    if not class_path:
        raise KeyError("Поле 'class_path' отсутствует в манифесте")
    module_path, class_name = class_path.rsplit(".", 1)
    module = import_module(module_path)
    cls = getattr(module, class_name)
    # Если в манифесте есть дополнительные параметры, их можно передать
    # в конструктор, но для базового случая достаточно просто создать объект.
    return cls()
