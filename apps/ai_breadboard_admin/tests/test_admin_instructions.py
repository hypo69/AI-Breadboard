from pathlib import Path
import pytest
from apps.ai_breadboard_admin.src.instructions_manager import InstructionsManager

@pytest.fixture
def temp_prompts_root(tmp_path: Path) -> Path:
    """Фикстура создания структуры каталогов с промптами."""
    chat_dir = tmp_path / 'prompts' / 'chat'
    narrator_dir = tmp_path / 'prompts' / 'narrator'
    chat_versions = chat_dir / 'versions'
    chat_versions.mkdir(parents=True, exist_ok=True)
    narrator_dir.mkdir(parents=True, exist_ok=True)
    (chat_dir / 'system_instruction.md').write_text('Default Chat Instruction', encoding='utf-8')
    (narrator_dir / 'narrator_style.md').write_text('Default Narrator Style', encoding='utf-8')
    (chat_versions / 'v1_2026-01-01.md').write_text('Version 1 Chat', encoding='utf-8')
    return tmp_path

def test_get_instruction_happy_path(temp_prompts_root: Path) -> None:
    """Happy Path: чтение активной инструкции чата и диктора."""
    mgr = InstructionsManager(root_dir=temp_prompts_root)
    chat_data = mgr.get_instruction('chat')
    narrator_data = mgr.get_instruction('narrator')
    assert chat_data['content'] == 'Default Chat Instruction'
    assert chat_data['file'] == 'system_instruction.md'
    assert narrator_data['content'] == 'Default Narrator Style'
    assert narrator_data['file'] == 'narrator_style.md'

def test_get_instruction_invalid_mode(temp_prompts_root: Path) -> None:
    """Error Scenario: запрос несуществующего режима."""
    mgr = InstructionsManager(root_dir=temp_prompts_root)
    with pytest.raises(ValueError, match='Неизвестный режим'):
        mgr.get_instruction('invalid_mode_xyz')

def test_save_instruction_versioning(temp_prompts_root: Path) -> None:
    """Happy Path & Boundary Values: сохранение новой версии с автоинкрементом."""
    mgr = InstructionsManager(root_dir=temp_prompts_root)
    new_text = 'Updated Chat Prompt Content v2'
    res = mgr.save_instruction('chat', new_text)
    assert res['status'] == 'ok'
    assert res['version'].startswith('v2_')
    active_content = mgr.get_instruction('chat')['content']
    assert active_content == new_text

def test_list_versions(temp_prompts_root: Path) -> None:
    """Happy Path: получение списка версий с признаком активности."""
    mgr = InstructionsManager(root_dir=temp_prompts_root)
    versions_data = mgr.list_versions('chat')
    assert versions_data['status'] if 'status' in versions_data else True
    versions = versions_data['versions']
    assert len(versions) >= 1
    assert versions[0]['filename'] == 'v1_2026-01-01.md'

def test_activate_version(temp_prompts_root: Path) -> None:
    """Happy Path & Edge Cases: активация версии и проверка отсутствующей."""
    mgr = InstructionsManager(root_dir=temp_prompts_root)
    res = mgr.activate_version('chat', 'v1_2026-01-01.md')
    active_content = mgr.get_instruction('chat')['content']
    assert res['status'] == 'ok'
    assert active_content == 'Version 1 Chat'
    with pytest.raises(FileNotFoundError):
        mgr.activate_version('chat', 'v999_missing.md')