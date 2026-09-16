# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Admin Instructions Manager
# =============================================================================
# Description:
#   Тестирование функционала InstructionsManager: чтение инструкций,
#   версионирование, сохранение новых версий и активация версий промптов.
#
# File: test_admin_instructions.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
import pytest

from apps.ai_breadboard_admin.src.instructions_manager import InstructionsManager


@pytest.fixture
def temp_prompts_root(tmp_path: Path) -> Path:
    """Фикстура создания структуры каталогов с промптами."""
    chat_dir = tmp_path / "prompts" / "chat"
    narrator_dir = tmp_path / "prompts" / "narrator"
    chat_versions = chat_dir / "versions"

    chat_versions.mkdir(parents=True, exist_ok=True)
    narrator_dir.mkdir(parents=True, exist_ok=True)

    # Исходная инструкция
    (chat_dir / "system_instruction.md").write_text("Default Chat Instruction", encoding="utf-8")
    (narrator_dir / "narrator_style.md").write_text("Default Narrator Style", encoding="utf-8")

    # Версия v1
    (chat_versions / "v1_2026-01-01.md").write_text("Version 1 Chat", encoding="utf-8")

    return tmp_path


def test_get_instruction_happy_path(temp_prompts_root: Path) -> None:
    """Happy Path: чтение активной инструкции чата и диктора."""
    # Arrange: инициализируем менеджер
    mgr = InstructionsManager(root_dir=temp_prompts_root)

    # Act: читаем чат и диктора
    chat_data = mgr.get_instruction("chat")
    narrator_data = mgr.get_instruction("narrator")

    # Assert: проверяем полученные данные
    assert chat_data["content"] == "Default Chat Instruction"
    assert chat_data["file"] == "system_instruction.md"
    assert narrator_data["content"] == "Default Narrator Style"
    assert narrator_data["file"] == "narrator_style.md"


def test_get_instruction_invalid_mode(temp_prompts_root: Path) -> None:
    """Error Scenario: запрос несуществующего режима."""
    # Arrange: менеджер
    mgr = InstructionsManager(root_dir=temp_prompts_root)

    # Act & Assert: ожидаем ValueError
    with pytest.raises(ValueError, match="Неизвестный режим"):
        mgr.get_instruction("invalid_mode_xyz")


def test_save_instruction_versioning(temp_prompts_root: Path) -> None:
    """Happy Path & Boundary Values: сохранение новой версии с автоинкрементом."""
    # Arrange: менеджер
    mgr = InstructionsManager(root_dir=temp_prompts_root)
    new_text = "Updated Chat Prompt Content v2"

    # Act: сохраняем инструкцию
    res = mgr.save_instruction("chat", new_text)

    # Assert: проверяем, что создалась версия v2
    assert res["status"] == "ok"
    assert res["version"].startswith("v2_")

    # Проверяем, что активный файл также обновился
    active_content = mgr.get_instruction("chat")["content"]
    assert active_content == new_text


def test_list_versions(temp_prompts_root: Path) -> None:
    """Happy Path: получение списка версий с признаком активности."""
    # Arrange: менеджер
    mgr = InstructionsManager(root_dir=temp_prompts_root)

    # Act: получаем список версий
    versions_data = mgr.list_versions("chat")

    # Assert: проверяем наличие версий
    assert versions_data["status"] if "status" in versions_data else True
    versions = versions_data["versions"]
    assert len(versions) >= 1
    assert versions[0]["filename"] == "v1_2026-01-01.md"


def test_activate_version(temp_prompts_root: Path) -> None:
    """Happy Path & Edge Cases: активация версии и проверка отсутствующей."""
    # Arrange: менеджер
    mgr = InstructionsManager(root_dir=temp_prompts_root)

    # Act: активируем v1_2026-01-01.md
    res = mgr.activate_version("chat", "v1_2026-01-01.md")
    active_content = mgr.get_instruction("chat")["content"]

    # Assert: активный текст равен версии v1
    assert res["status"] == "ok"
    assert active_content == "Version 1 Chat"

    # Error Scenario: попытка активировать несуществующий файл
    with pytest.raises(FileNotFoundError):
        mgr.activate_version("chat", "v999_missing.md")
