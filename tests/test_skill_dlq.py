"""Модульные тесты для навыка dlq (Dead Letter Queue & TUI)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS_DIR = PROJECT_ROOT / ".agents" / "skills" / "dlq" / "scripts"
if str(SKILL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

from storage import DLQStorage
from tui import render_dlq_dashboard, run_dlq_tui, _build_summary_panel, _build_table


@pytest.fixture
def temp_dlq_storage(tmp_path: Path) -> DLQStorage:
    """Фикстура для создания временного хранилища DLQ."""
    db_file = tmp_path / "test_dlq.db"
    return DLQStorage(db_path=db_file)


def test_dlq_storage_push_and_list(temp_dlq_storage: DLQStorage) -> None:
    """Проверка добавления и получения записей DLQ."""
    msg_id = temp_dlq_storage.push(
        source="test-agent",
        error_message="Connection timeout error",
        payload={"url": "https://api.example.com", "timeout": 30},
    )
    assert msg_id > 0

    messages = temp_dlq_storage.list_all()
    assert len(messages) == 1
    msg = messages[0]
    assert msg["id"] == msg_id
    assert msg["source"] == "test-agent"
    assert msg["error_message"] == "Connection timeout error"
    assert msg["status"] == "PENDING"
    assert msg["retry_count"] == 0

    payload_parsed = json.loads(msg["payload"])
    assert payload_parsed["timeout"] == 30


def test_dlq_storage_get_by_id(temp_dlq_storage: DLQStorage) -> None:
    """Проверка получения конкретной записи по ID."""
    msg_id = temp_dlq_storage.push(source="subagent", error_message="API 500 Server Error")
    item = temp_dlq_storage.get_by_id(msg_id)
    assert item is not None
    assert item["id"] == msg_id
    assert item["error_message"] == "API 500 Server Error"

    assert temp_dlq_storage.get_by_id(99999) is None


def test_dlq_storage_status_and_retry(temp_dlq_storage: DLQStorage) -> None:
    """Проверка обновления статуса и инкремента счетчика попыток."""
    msg_id = temp_dlq_storage.push(source="worker", error_message="Memory limit exceeded")

    # Инкремент попытки
    retry_ok = temp_dlq_storage.increment_retry(msg_id)
    assert retry_ok is True

    item = temp_dlq_storage.get_by_id(msg_id)
    assert item is not None
    assert item["retry_count"] == 1
    assert item["status"] == "RETRYING"

    # Изменение статуса на RESOLVED
    status_ok = temp_dlq_storage.update_status(msg_id, "RESOLVED")
    assert status_ok is True

    item_resolved = temp_dlq_storage.get_by_id(msg_id)
    assert item_resolved is not None
    assert item_resolved["status"] == "RESOLVED"


def test_dlq_storage_purge_and_stats(temp_dlq_storage: DLQStorage) -> None:
    """Проверка очистки базы и формирования статистики."""
    id1 = temp_dlq_storage.push(source="src1", error_message="Err 1")
    id2 = temp_dlq_storage.push(source="src2", error_message="Err 2")

    temp_dlq_storage.update_status(id1, "RESOLVED")

    stats = temp_dlq_storage.get_stats()
    assert stats["TOTAL"] == 2
    assert stats["RESOLVED"] == 1
    assert stats["PENDING"] == 1

    # Очищаем только RESOLVED
    deleted_count = temp_dlq_storage.purge(status="RESOLVED")
    assert deleted_count == 1

    remaining = temp_dlq_storage.list_all()
    assert len(remaining) == 1
    assert remaining[0]["id"] == id2

    # Полная очистка
    temp_dlq_storage.purge()
    assert len(temp_dlq_storage.list_all()) == 0


def test_dlq_validation_errors(temp_dlq_storage: DLQStorage) -> None:
    """Проверка выброса ошибок валидации при неверных параметрах."""
    with pytest.raises(ValueError, match="source"):
        temp_dlq_storage.push(source="", error_message="Valid Error")

    with pytest.raises(ValueError, match="error_message"):
        temp_dlq_storage.push(source="Valid Source", error_message="  ")

    with pytest.raises(ValueError, match="Недопустимый статус"):
        temp_dlq_storage.update_status(1, "INVALID_STATUS")


def test_tui_render_functions(temp_dlq_storage: DLQStorage) -> None:
    """Проверка вызова функций рендеринга TUI дашборда."""
    temp_dlq_storage.push(source="tui-test", error_message="TUI Render Check Error")

    summary_panel = _build_summary_panel(temp_dlq_storage)
    assert summary_panel is not None

    table = _build_table(temp_dlq_storage)
    assert table is not None

    layout = render_dlq_dashboard(temp_dlq_storage)
    assert layout is not None

    # Проверка однократного рендеринга без выброса исключений
    run_dlq_tui(once=True, storage=temp_dlq_storage)
