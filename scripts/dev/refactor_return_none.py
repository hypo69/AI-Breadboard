# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Root - Refactor Return None
# =============================================================================
# Description:
#   refactor_return_none.py
#
# Usage Examples:
#   CLI:
#     python refactor_return_none.py
#   Python API:
#     from refactor_return_none import ReturnNoneTransformer
#
#     service = ReturnNoneTransformer()
#
# File: refactor_return_none.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

"""refactor_return_none.py

Скрипт автоматически ищет функции, которые возвращают ``None`` и заменяет
их на «пустой» объект, соответствующий типу, указанному в аннотации
возвращаемого значения.

Поддерживаемые типы:
- ``str`` → ``""``
- ``list`` → ``[]``
- ``dict`` → ``{}``
- ``int`` → ``0``
- ``float`` → ``0.0``
- ``bool`` → ``False``
- ``set`` → ``set()``
- ``tuple`` → ``()``

Если тип не указан или не поддерживается – оставляем ``None`` и добавляем
комментарий ``# TODO: вернуть корректное значение``.

Перед заменой проверяется наличие вызова ``logger.error`` в функции.
Если его нет – он вставляется перед оператором ``return``.

Используется модуль ``ast`` для безопасного анализа и ``ast.unparse``
(доступно в Python\u202f3.9+). После трансформации файл перезаписывается."""

import ast
import os
import sys
from pathlib import Path
try:
    from logger import logger
except Exception:
    import logging
    logger = logging.getLogger('refactor_return_none')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
TYPE_DEFAULTS = {'str': ast.Constant(value=''), 'list': ast.List(elts=[], ctx=ast.Load()), 'dict': ast.Dict(keys=[], values=[]), 'int': ast.Constant(value=0), 'float': ast.Constant(value=0.0), 'bool': ast.Constant(value=False), 'set': ast.Call(func=ast.Name(id='set', ctx=ast.Load()), args=[], keywords=[]), 'tuple': ast.Tuple(elts=[], ctx=ast.Load())}

def get_default_node(type_name: str) -> ast.AST:
    """Вернуть AST‑узел, представляющий «пустой» объект для ``type_name``.

    Если тип неизвестен – возвращаем ``None`` (т.е. ``ast.Constant(value=None)``).
    """
    return TYPE_DEFAULTS.get(type_name, ast.Constant(value=None))

class ReturnNoneTransformer(ast.NodeTransformer):
    """Трансформирует ``return None`` в возвращаемое значение по типу.

    При отсутствии подходящего типа оставляем ``None`` и вставляем TODO‑комментарий.
    """

    def __init__(self, source_path: Path):
        self.source_path = source_path
        super().__init__()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        returns_none = []
        for stmt in node.body:
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant) and (stmt.value.value is None):
                returns_none.append(stmt)
        if not returns_none:
            return node
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Subscript) and isinstance(node.returns.value, ast.Name):
                return_type = node.returns.value.id
        for ret_stmt in returns_none:
            default_node = get_default_node(return_type) if return_type else ast.Constant(value=None)
            if isinstance(default_node, ast.Constant) and default_node.value is None:
                todo_comment = ast.Expr(value=ast.Constant(value='# TODO: вернуть корректное значение'))
                node.body.insert(node.body.index(ret_stmt), todo_comment)
                new_return = ast.Return(value=ast.Constant(value=None))
            else:
                new_return = ast.Return(value=default_node)
            has_logging = any((isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Attribute) and (s.value.func.attr == 'error') for s in node.body))
            if not has_logging:
                log_call = ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id='logger', ctx=ast.Load()), attr='error', ctx=ast.Load()), args=[ast.Constant(value=f'Функция {node.name} вернула пустой результат')], keywords=[]))
                node.body.insert(node.body.index(ret_stmt), log_call)
            idx = node.body.index(ret_stmt)
            node.body[idx] = new_return
        return node

def process_file(file_path: Path) -> bool:
    """Обработать один файл. Возвращает ``True`` если файл был изменён."""
    try:
        source = file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f'Не удалось прочитать {file_path}: {e}')
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        logger.error(f'Синтаксическая ошибка в {file_path}: {e}')
        return False
    transformer = ReturnNoneTransformer(file_path)
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    new_source = ast.unparse(new_tree)
    if new_source != source:
        file_path.write_text(new_source, encoding='utf-8')
        logger.info(f'Обновлен файл {file_path}')
        return True
    return False

def main():
    root = Path('c:/Users/onela/AppData/Local/AI-Breadboard')
    py_files = list(root.rglob('*.py'))
    changed = 0
    for p in py_files:
        if 'venv' in p.parts or '__pycache__' in p.parts:
            continue
        if process_file(p):
            changed += 1
    logger.info(f'Обработано файлов: {len(py_files)}; изменено: {changed}')
if __name__ == '__main__':
    main()