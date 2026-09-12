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

from src.utils.versioning import compare_versions, choose_best_tag

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


def test_version_manager_same_commit(monkeypatch, tmp_path):
    from src.version_manager import VersionManager, UpdateStatus

    vm = VersionManager(repo_path=tmp_path)

    def mock_run_git(command, cwd=None):
        cmd_str = " ".join(command)
        if "describe" in cmd_str:
            return 0, "9fc21fb", ""
        if "rev-parse --short HEAD" in cmd_str:
            return 0, "9fc21fb", ""
        if "rev-parse HEAD" in cmd_str:
            return 0, "9fc21fb1234567890abcdef1234567890abcdef", ""
        if "ls-remote --tags" in cmd_str:
            return 0, "", ""
        if "ls-remote" in cmd_str and "HEAD" in cmd_str:
            return 0, "9fc21fb1234567890abcdef1234567890abcdef\tHEAD", ""
        return 0, "", ""

    monkeypatch.setattr(vm, "_run_git_command", mock_run_git)

    current = vm.get_current_version()
    remote = vm.get_remote_version()
    assert current == "9fc21fb"
    assert remote == "9fc21fb"

    result = vm.check_updates()
    assert result["status"] == UpdateStatus.CURRENT.value
    assert result["is_update_available"] is False
    assert result["current_version"] == "9fc21fb"
    assert result["remote_version"] == "9fc21fb"


def test_version_manager_different_commit(monkeypatch, tmp_path):
    from src.version_manager import VersionManager, UpdateStatus

    vm = VersionManager(repo_path=tmp_path)

    def mock_run_git(command, cwd=None):
        cmd_str = " ".join(command)
        if "describe" in cmd_str:
            return 0, "9fc21fb", ""
        if "rev-parse --short HEAD" in cmd_str:
            return 0, "9fc21fb", ""
        if "rev-parse HEAD" in cmd_str:
            return 0, "9fc21fb1234567890abcdef1234567890abcdef", ""
        if "ls-remote --tags" in cmd_str:
            return 0, "", ""
        if "ls-remote" in cmd_str and "HEAD" in cmd_str:
            return 0, "abc1234567890abcdef1234567890abcdef1234\tHEAD", ""
        return 0, "", ""

    monkeypatch.setattr(vm, "_run_git_command", mock_run_git)

    current = vm.get_current_version()
    remote = vm.get_remote_version()
    assert current == "9fc21fb"
    assert remote == "abc1234"

    result = vm.check_updates()
    assert result["status"] == UpdateStatus.UPDATE_AVAILABLE.value
    assert result["is_update_available"] is True

