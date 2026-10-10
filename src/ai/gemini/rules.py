# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Gemini - Unsupported Models Rule Engine
# =============================================================================
# Description:
#   Движок правил и условий исключения неподдерживаемых моделей Gemini
#   (поддержка условий версий <2, подстрок -image, масок и явных списков).
#
# Usage Examples:
#   Python API:
#     from src.ai.gemini.rules import is_gemini_model_unsupported, load_unsupported_rules
#
#     unsupported = is_gemini_model_unsupported("gemini-1.5-flash")
#     print(unsupported)  # True (по условию <2)
#
# File: rules.py
# Project: ai-breadboard
# Package: src.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 10:46:00
# =============================================================================

"""Движок правил и условий исключения неподдерживаемых моделей Gemini."""

from __future__ import annotations

import fnmatch
import operator
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from header import __root__
from logger import logger
from src.utils.jjson import j_dumps, j_loads

_PRIMARY_CONFIG_PATH: Path = __root__ / "src" / "ai" / "gemini" / "unsopported_gemini_models.json"
_FALLBACK_CONFIG_PATH: Path = __root__ / "src" / "ai" / "gemini" / "unsupported_gemini_models.json"

_OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
    "==": operator.eq,
    "=": operator.eq,
}

_VERSION_RULE_REGEX = re.compile(r"^\s*(<=|>=|<|>|==|=)\s*(\d+(?:\.\d+)?)\s*$")
_MODEL_VERSION_REGEX = re.compile(r"(?:gemini-)?(?:v)?(\d+(?:\.\d+)?)", re.IGNORECASE)


def get_unsupported_config_path() -> Path:
    """Возвращает путь к существующему файлу unsopported_gemini_models.json.

    Returns:
        Path: Путь к конфигурационному файлу.
    """
    if _PRIMARY_CONFIG_PATH.exists():
        return _PRIMARY_CONFIG_PATH
    if _FALLBACK_CONFIG_PATH.exists():
        return _FALLBACK_CONFIG_PATH
    return _PRIMARY_CONFIG_PATH


def _normalize_name(model_name: str) -> str:
    """Нормализует имя модели, удаляя префиксы `models/` и `gemini:`.

    Args:
        model_name (str): Исходное имя модели.

    Returns:
        str: Нормализованное имя модели в нижнем регистре.
    """
    res = (model_name or "").strip().lower()
    if res.startswith("gemini:"):
        res = res[len("gemini:"):]
    if res.startswith("models/"):
        res = res[len("models/"):]
    return res


def _extract_model_version(model_name: str) -> Optional[float]:
    """Извлекает числовую версию модели из её названия (например, 'gemini-1.5-flash' -> 1.5).

    Args:
        model_name (str): Имя модели.

    Returns:
        Optional[float]: Числовая версия модели или None при отсутствии.
    """
    match = _MODEL_VERSION_REGEX.search(model_name)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            return None
    return None


def matches_rule(model_name: str, rule: str) -> bool:
    """Проверяет соответствие названия модели заданному правилу или условию.

    Поддерживаемые типы правил:
    - Условия версии: '<2', '<=2.5', '>=3.0', '==1.0'
    - Исключение по подстроке/префиксу: '-image', '-tts', '-preview'
    - Маски/шаблоны: '*image*', '*-tts', 'gemini-1.*'
    - Точное совпадение: 'gemini-1.5-flash', 'gemini-old'

    Args:
        model_name (str): Проверяемое имя модели.
        rule (str): Строковое правило исключения.

    Returns:
        bool: True, если модель соответствует правилу (т.е. должна быть исключена).
    """
    norm_name = _normalize_name(model_name)
    raw_rule = (rule or "").strip()
    if not norm_name or not raw_rule:
        return False

    # 1. Проверка условия числовой версии (например, "<2", "<=2.5")
    ver_match = _VERSION_RULE_REGEX.match(raw_rule)
    if ver_match:
        op_str = ver_match.group(1)
        target_ver_str = ver_match.group(2)
        try:
            target_ver = float(target_ver_str)
            model_ver = _extract_model_version(norm_name)
            if model_ver is not None and op_str in _OPERATORS:
                return _OPERATORS[op_str](model_ver, target_ver)
        except Exception as exc:
            logger.debug(f"Ошибка вычисления правила версии '{raw_rule}': {exc}")
        return False

    # 2. Проверка отрицания / подстроки (например, "-image", "-tts", "-preview-tts")
    if raw_rule.startswith("-"):
        keyword = raw_rule[1:].strip().lower()
        if keyword:
            return keyword in norm_name

    # 3. Проверка шаблонов подстановки (например, "*image*", "gemini-1.*")
    if "*" in raw_rule or "?" in raw_rule:
        rule_lower = raw_rule.lower()
        return fnmatch.fnmatch(norm_name, rule_lower)

    # 4. Точное совпадение с нормализацией
    norm_rule = _normalize_name(raw_rule)
    return norm_name == norm_rule


def load_unsupported_rules_and_models() -> Tuple[List[str], Set[str]]:
    """Загружает список правил и явно заданных моделей из unsopported_gemini_models.json.

    Returns:
        Tuple[List[str], Set[str]]: Кортеж из (список правил, множество явных моделей).
    """
    cfg_path = get_unsupported_config_path()
    rules: List[str] = []
    explicit_models: Set[str] = set()

    if not cfg_path.exists():
        return rules, explicit_models

    data = j_loads(cfg_path)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item.strip():
                clean_item = item.strip()
                if _VERSION_RULE_REGEX.match(clean_item) or clean_item.startswith("-") or "*" in clean_item:
                    rules.append(clean_item)
                else:
                    explicit_models.add(_normalize_name(clean_item))
    elif isinstance(data, dict):
        raw_rules = data.get("rules", [])
        if isinstance(raw_rules, list):
            for r in raw_rules:
                if isinstance(r, str) and r.strip():
                    rules.append(r.strip())

        raw_models = data.get("unsupported_models", []) or data.get("models", [])
        if isinstance(raw_models, list):
            for m in raw_models:
                if isinstance(m, str) and m.strip():
                    clean_m = m.strip()
                    if _VERSION_RULE_REGEX.match(clean_m) or clean_m.startswith("-") or "*" in clean_m:
                        rules.append(clean_m)
                    else:
                        explicit_models.add(_normalize_name(clean_m))

    return rules, explicit_models


def is_gemini_model_unsupported(model_name: str, additional_rules: Optional[List[str]] = None) -> bool:
    """Проверяет, является ли модель Gemini неподдерживаемой по правилам и спискам.

    Args:
        model_name (str): Имя проверяемой модели.
        additional_rules (Optional[List[str]]): Дополнительные динамические правила.

    Returns:
        bool: True, если модель заблокирована / не поддерживается.
    """
    norm_name = _normalize_name(model_name)
    if not norm_name:
        return True

    rules, explicit_models = load_unsupported_rules_and_models()

    if norm_name in explicit_models:
        return True

    all_rules = list(rules)
    if additional_rules:
        all_rules.extend(additional_rules)

    for rule in all_rules:
        if matches_rule(norm_name, rule):
            return True

    return False


def filter_unsupported_gemini_models(models: List[str]) -> List[str]:
    """Фильтрует список моделей Gemini, исключая неподдерживаемые по всем правилам.

    Args:
        models (List[str]): Исходный список моделей.

    Returns:
        List[str]: Отфильтрованный список поддерживаемых моделей.
    """
    rules, explicit_models = load_unsupported_rules_and_models()
    supported: List[str] = []

    for m in models:
        norm_m = _normalize_name(m)
        if norm_m in explicit_models:
            continue
        if any(matches_rule(norm_m, r) for r in rules):
            continue
        supported.append(m)

    return supported


def add_unsupported_gemini_model(model_name: str, reason: str = "") -> bool:
    """Добавляет модель в список unsupported_models файла unsopported_gemini_models.json.

    Args:
        model_name (str): Название модели.
        reason (str): Причина блокировки модели.

    Returns:
        bool: True при успешной записи.
    """
    if not model_name:
        return False

    cfg_path = get_unsupported_config_path()
    data: Dict[str, Any] = {}
    if cfg_path.exists():
        loaded = j_loads(cfg_path)
        if isinstance(loaded, dict):
            data = loaded

    norm_name = _normalize_name(model_name)
    current_models: List[str] = list(data.get("unsupported_models", []))
    if norm_name not in current_models:
        current_models.append(norm_name)
        data["unsupported_models"] = sorted(list(set(current_models)))
        j_dumps(data, cfg_path)
        logger.warning(f"Модель '{norm_name}' добавлена в {cfg_path.name} (причина: {reason[:120]})")
        return True
    return False
