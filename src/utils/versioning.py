# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Parse non-standard version string into list of integers
# =============================================================================
# Description:
#   Parse version strings in SemVer format, compare two versions and select best tag.
#   Implements semantic versioning 2.0 specification with backward compatibility.
#
# File: versioning.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import re
from typing import List, Optional, Tuple

def _parse_version_legacy(v: str) -> List[int]:
    """Parse non-standard version string into list of integers.

    Args:
        v (str): Version string of arbitrary format.

    Returns:
        List[int]: List of numeric version components; [0, 0, 0] for empty string.

    Examples:
        >>> _parse_version_legacy('2.10.3')
        [2, 10, 3]
    """
    if not v:
        return [0, 0, 0]
    parts = re.findall(r'(\d+)', v)
    return [int(p) for p in parts]

def parse_semver(v: str) -> Tuple[int, int, int, List[str]]:
    """Parse version string according to SemVer 2.0 specification.

    Args:
        v (str): Version string, optionally with 'v' prefix, prerelease and build metadata.

    Returns:
        Tuple[int, int, int, List[str]]: Tuple (major, minor, patch, prerelease).
            Prerelease field is empty list if no prerelease tag present.
            Returns empty tuple () for invalid string.

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
    """Compare two version strings with SemVer priority.

    Args:
        a (str): First version string.
        b (str): Second version string.

    Returns:
        int: -1 if a < b, 0 if equal, 1 if a > b.

    Examples:
        >>> compare_versions('1.2.3', '1.2.4')
        -1
        >>> compare_versions('v1.10.0', '1.9.9')
        1
        >>> compare_versions('1.2.3-alpha', '1.2.3')
        -1
    """
    def _compare(a_parsed: tuple, b_parsed: tuple) -> int:
        # Fallback to legacy parsing for invalid SemVer
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

        # Compare major.minor.patch
        for i in range(3):
            if a_parsed[i] < b_parsed[i]:
                return -1
            if a_parsed[i] > b_parsed[i]:
                return 1

        # Compare prerelease tags (SemVer §11)
        a_pr: List[str] = a_parsed[3]
        b_pr: List[str] = b_parsed[3]

        # Stable release is greater than prerelease
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
    """Choose greatest version from list of tags.

    Args:
        tags (List[str]): List of version/tag strings.
        allow_prerelease (bool): Allow prerelease tags if no stable versions available.
            Default: False.
        debug (bool): Output debug information via logger.
            Default: False.

    Returns:
        str: Tag with greatest version; empty string for empty list.

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
        from src.logger.logger import logger
        logger.debug(f'[versioning.choose_best_tag] candidates={candidates} allow_prerelease={allow_prerelease}')

    best = ''
    for t in candidates:
        if not best or compare_versions(best, t) < 0:
            best = t
    return best
