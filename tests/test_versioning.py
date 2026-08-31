# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: test_versioning.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest

from core.utils.versioning import compare_versions, choose_best_tag

def test_compare_versions_basic():
    assert compare_versions('1.2.3', '1.2.4') == -1
    assert compare_versions('1.2.3', '1.2.3') == 0
    assert compare_versions('v1.10.0', '1.9.9') == 1
    assert compare_versions('1.2', '1.2.0') == 0

def test_compare_prerelease():
    assert compare_versions('1.2.3-alpha', '1.2.3') == -1
    assert compare_versions('1.2.3-alpha.1', '1.2.3-alpha.2') == -1
    assert compare_versions('1.2.3-alpha', '1.2.3-alpha') == 0

def test_choose_best_tag_prefers_stable():
    tags = ['v1.0.0', 'v1.1.0-alpha', 'v1.0.1']
    best = choose_best_tag(tags, allow_prerelease=False, debug=False)
    assert best == 'v1.0.1'

def test_choose_best_tag_allows_prerelease():
    tags = ['v1.0.0', 'v1.1.0-alpha', 'v1.0.1']
    best = choose_best_tag(tags, allow_prerelease=True, debug=False)
    # v1.1.0-alpha has higher major.minor.patch so should be preferred when prerelease allowed
    assert best == 'v1.1.0-alpha'
