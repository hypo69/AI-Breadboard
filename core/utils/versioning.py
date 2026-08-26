# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Сравнение и выбор версий по стандарту SemVer
# =============================================================================
# Описание:
#   Разбор строк версий в формате SemVer, сравнение двух версий и выбор
#   наилучшего тега из списка с учётом пре-релизных меток.
#
# Примеры:
#   >>> from core.utils.versioning import compare_versions, choose_best_tag
#   >>> compare_versions('1.2.3', '1.2.4')
#   -1
#   >>> choose_best_tag(['v1.0.0', 'v1.1.0-alpha', 'v1.0.1'])
#   'v1.0.1'
#
# File: versioning.py
# Project: ai-assistant
# Package: core.utils
# Module: Versioning
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
import re
from typing import List, Optional, Tuple


def _parse_version_legacy(v: str) -> List[int]:
    """Разбор нестандартной строки версии в список целых чисел.

    Args:
        v (str): Строка версии произвольного формата.

    Returns:
        List[int]: Список числовых компонентов версии; [0, 0, 0] для пустой строки.

    Examples:
        >>> _parse_version_legacy('2.10.3')
        [2, 10, 3]
    """
    if not v:
        return [0, 0, 0]
    parts = re.findall(r'(\d+)', v)
    return [int(p) for p in parts]


def parse_semver(v: str) -> Tuple[int, int, int, List[str]]:
    """Разбор строки версии по стандарту SemVer 2.0.

    Args:
        v (str): Строка версии, опционально с префиксом 'v', пре-релизом и build-метаданными.

    Returns:
        Tuple[int, int, int, List[str]]: Кортеж (major, minor, patch, prerelease).
            Поле prerelease — пустой список при отсутствии пре-релизной метки.
            Возвращает пустой кортеж () при невалидной строке.

    Examples:
        >>> parse_semver('v1.2.3-alpha.1')
        (1, 2, 3, ['alpha', '1'])
        >>> parse_semver('1.0')
        (1, 0, 0, [])
    """
    if not v:
        return ()
    m = re.match(
        r'^v?(?P<major>0|[1-9]\d*)(?:\.(?P<minor>0|[1-9]\d*))?(?:\.(?P<patch>0|[1-9]\d*))?'
        r'(?:-(?P<prerelease>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$',
        v,
    )
    if not m:
        return ()
    major = int(m.group('major'))
    minor = int(m.group('minor') or 0)
    patch = int(m.group('patch') or 0)
    prerelease_raw = m.group('prerelease')
    prerelease = prerelease_raw.split('.') if prerelease_raw else []
    return (major, minor, patch, prerelease)


def compare_versions(a: str, b: str) -> int:
    """Сравнение двух строк версий с приоритетом SemVer.

    Args:
        a (str): Первая строка версии.
        b (str): Вторая строка версии.

    Returns:
        int: -1 если a < b, 0 если равны, 1 если a > b.

    Examples:
        >>> compare_versions('1.2.3', '1.2.4')
        -1
        >>> compare_versions('v1.10.0', '1.9.9')
        1
        >>> compare_versions('1.2.3-alpha', '1.2.3')
        -1
    """
    def _compare(a_parsed: tuple, b_parsed: tuple) -> int:
        # Откат на legacy-разбор при невалидном SemVer
        if not a_parsed and not b_parsed:
            return 0
        if not a_parsed or not b_parsed:
            pa = _parse_version_legacy(a)
            pb = _parse_version_legacy(b)
            length = max(len(pa), len(pb))
            pa += [0] * (length - len(pa))
            pb += [0] * (length - len(pb))
            if pa < pb:
                return -1
            if pa > pb:
                return 1
            return 0

        # Сравнение major.minor.patch
        for i in range(3):
            if a_parsed[i] < b_parsed[i]:
                return -1
            if a_parsed[i] > b_parsed[i]:
                return 1

        # Сравнение пре-релизных меток (SemVer §11)
        a_pr: List[str] = a_parsed[3]
        b_pr: List[str] = b_parsed[3]

        # Стабильный релиз старше пре-релиза
        if not a_pr and not b_pr:
            return 0
        if not a_pr:
            return 1
        if not b_pr:
            return -1

        for ai, bi in zip(a_pr, b_pr):
            if ai == bi:
                continue
            if ai.isdigit() and bi.isdigit():
                diff = int(ai) - int(bi)
                if diff < 0:
                    return -1
                if diff > 0:
                    return 1
            else:
                if ai < bi:
                    return -1
                if ai > bi:
                    return 1

        if len(a_pr) < len(b_pr):
            return -1
        if len(a_pr) > len(b_pr):
            return 1
        return 0

    return _compare(parse_semver(a), parse_semver(b))


def choose_best_tag(tags: List[str], allow_prerelease: bool = False, debug: bool = False) -> str:
    """Выбор наибольшей версии из списка тегов.

    Args:
        tags (List[str]): Список строк версий/тегов.
        allow_prerelease (bool): Разрешить пре-релизные теги при отсутствии стабильных.
            Значение по умолчанию: False.
        debug (bool): Вывод отладочной информации через logger.
            Значение по умолчанию: False.

    Returns:
        str: Тег с наибольшей версией; пустая строка при пустом списке.

    Examples:
        >>> choose_best_tag(['v1.0.0', 'v1.1.0-alpha', 'v1.0.1'])
        'v1.0.1'
        >>> choose_best_tag(['v1.0.0', 'v1.1.0-alpha'], allow_prerelease=True)
        'v1.1.0-alpha'
    """
    if not tags:
        return ''

    def _is_prerelease(t: str) -> bool:
        return '-' in t.split('+', 1)[0]

    stable = [t for t in tags if not _is_prerelease(t)]
    candidates = stable if stable and not allow_prerelease else tags

    if debug:
        from core.logger.logger import logger
        logger.debug(f'[versioning.choose_best_tag] candidates={candidates} allow_prerelease={allow_prerelease}')

    best = ''
    for t in candidates:
        if not best or compare_versions(best, t) < 0:
            best = t
    return best
