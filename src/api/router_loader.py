"""Модуль авто‑обнаружения FastAPI‑роутеров.

Содержит функцию :func:`discover_routers`, которая ищет и импортирует все роутеры,
расположенные в ``src/api/routers/core`` (глобальные роутеры) и в каталоге
``apps/*/routers`` / ``src/plugins/*/routers``.  Роутеры, экспортируемые как
``router`` (объект :class:`fastapi.APIRouter`), сразу добавляются в список.
Если модуль предоставляет функцию ``init_router``, она вызывается без аргументов;
при необходимости аргументы (например, ``state``) могут быть переданы вручную
в вызывающем коде.

Все обнаруженные роутеры возвращаются в виде списка, который можно передать в
``app.include_router``.
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import List, Any

logger = logging.getLogger(__name__)


def _load_module(module_path: str) -> Any:
    """Импортировать модуль по строковому пути.

    Если импорт не удался, записывается предупреждение и возвращается ``None``.
    """
    try:
        return importlib.import_module(module_path)
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Не удалось импортировать модуль {module_path}: {exc}")
        return None


def _extract_router(module: Any) -> Any:
    """Получить объект роутера из модуля.

    Приоритет:
    1. Атрибут ``router``.
    2. Функция ``init_router`` без аргументов.
    Если ни один из вариантов не найден, возвращается ``None``.
    """
    if hasattr(module, "router"):
        return getattr(module, "router")
    if hasattr(module, "init_router"):
        try:
            return module.init_router()
        except TypeError:
            logger.debug(
                f"init_router в {module.__name__} требует параметры – пропускаем автодискавери"
            )
            return None
    return None


def discover_routers() -> List[Any]:
    """Автоматически найти все роутеры проекта.

    Возвращает список объектов ``APIRouter`` (или совместимых), которые можно
    добавить в FastAPI‑приложение через ``app.include_router``.
    """
    routers: List[Any] = []

    # 1. Глобальные роутеры из src/api/routers/core
    core_dir = Path(__file__).parent / "routers" / "core"
    if core_dir.is_dir():
        for module_info in pkgutil.iter_modules([str(core_dir)]):
            module_name = f"src.api.routers.core.{module_info.name}"
            module = _load_module(module_name)
            if module:
                router_obj = _extract_router(module)
                if router_obj:
                    routers.append(router_obj)

    # 2. Роутеры из приложений (apps/*/routers/router.py)
    apps_dir = Path(__file__).parents[2] / "apps"
    if apps_dir.is_dir():
        for app_path in apps_dir.iterdir():
            router_path = app_path / "routers" / "router.py"
            if router_path.is_file():
                module_name = f"apps.{app_path.name}.routers.router"
                module = _load_module(module_name)
                if module:
                    router_obj = _extract_router(module)
                    if router_obj:
                        routers.append(router_obj)

    # 3. Роутеры из плагинов (src/plugins/*/routers/*.py)
    plugins_dir = Path(__file__).parents[2] / "src" / "plugins"
    if plugins_dir.is_dir():
        for plugin_path in plugins_dir.iterdir():
            routers_dir = plugin_path / "routers"
            if routers_dir.is_dir():
                for py_file in routers_dir.glob('*.py'):
                    if py_file.name == '__init__.py':
                        continue
                    module_name = f"src.plugins.{plugin_path.name}.routers.{py_file.stem}"
                    module = _load_module(module_name)
                    if module:
                        router_obj = _extract_router(module)
                        if router_obj:
                            routers.append(router_obj)

    # 4. Роутеры из корневых плагинов (plugins/*/routers/*.py)
    root_plugins_dir = Path(__file__).parents[2] / "plugins"
    if root_plugins_dir.is_dir():
        for plugin_path in root_plugins_dir.iterdir():
            routers_dir = plugin_path / "routers"
            if routers_dir.is_dir():
                for py_file in routers_dir.glob('*.py'):
                    if py_file.name == '__init__.py':
                        continue
                    module_name = f"plugins.{plugin_path.name}.routers.{py_file.stem}"
                    module = _load_module(module_name)
                    if module:
                        router_obj = _extract_router(module)
                        if router_obj:
                            routers.append(router_obj)

    return routers
