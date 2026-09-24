# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тестирование роутера и компонентов Восстановления файлов (R-Studio)
# =============================================================================
# Description:
#   Проверяет корректность работы роутера File Recovery (R-Studio Technician Portable):
#   - Проверка статуса наличия исполняемого файла R-Studio
#   - Запуск программы через subprocess.Popen с корректными параметрами
#   - Обработка граничных ситуаций и ошибок запуска
#   - Интеграция вкладки file_recovery в конфигурацию меню tc_menu_config.json и tabs-config.js
#
# File: test_file_recovery_router.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты роутера и интеграции File Recovery (R-Studio)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from header import __root__
from src.api.router_recovery import init_router, RSTUDIO_EXE


@pytest.fixture
def recovery_client():
    """Создаёт тестовый клиент FastAPI с подключенным роутером восстановления файлов."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


# =============================================================================
# 1. HAPPY PATH — Проверка статуса и запуска утилиты
# =============================================================================

class TestRecoveryRouterHappyPath:
    """Happy path сценарии для роутера восстановления файлов."""

    def test_get_status_happy_path(self, recovery_client):
        """GET /api/recovery/status должен возвращать информацию об утилите."""
        response = recovery_client.get("/api/recovery/status")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "tool" in data
        tool = data["tool"]
        assert "name" in tool
        assert "R-Studio" in tool["name"]
        assert "path" in tool
        assert "exists" in tool

    def test_launch_recovery_tool_happy_path(self, recovery_client):
        """POST /api/recovery/launch должен запускать R-Studio через subprocess.Popen."""
        with patch("src.api.router_recovery._check_rstudio_exists", return_value=True), \
             patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            response = recovery_client.post("/api/recovery/launch")
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True
            assert data.get("pid") == 12345
            assert "успешно запущена" in data.get("message", "")
            mock_popen.assert_called_once()


# =============================================================================
# 2. EDGE CASES & ERRORS — Граничные случаи и ошибки
# =============================================================================

class TestRecoveryRouterEdgeCases:
    """Граничные случаи и ошибки для роутера восстановления файлов."""

    def test_launch_recovery_tool_file_not_found(self, recovery_client):
        """POST /api/recovery/launch должен возвращать 404, если исполняемый файл не найден."""
        with patch("src.api.router_recovery._check_rstudio_exists", return_value=False):
            response = recovery_client.post("/api/recovery/launch")
            assert response.status_code == 404
            data = response.json()
            assert "не найден" in data.get("detail", "")

    def test_launch_recovery_tool_popen_exception(self, recovery_client):
        """POST /api/recovery/launch должен возвращать 500 при непредвиденной ошибке Popen."""
        with patch("src.api.router_recovery._check_rstudio_exists", return_value=True), \
             patch("subprocess.Popen", side_effect=OSError("Access denied")):
            response = recovery_client.post("/api/recovery/launch")
            assert response.status_code == 500
            data = response.json()
            assert "Не удалось запустить" in data.get("detail", "")


# =============================================================================
# 3. MENU & TABS INTEGRATION — Проверка интеграции в систему меню
# =============================================================================

class TestRecoveryMenuIntegration:
    """Проверка регистрации вкладки и кнопки восстановления в конфигурациях меню."""

    def test_menu_config_contains_file_recovery_tab(self):
        """tc_menu_config.json должен содержать вкладку file_recovery в sidebarItems."""
        cfg_file = __root__ / "src" / "api" / "webgui" / "config" / "tc_menu_config.json"
        assert cfg_file.exists(), f"Файл {cfg_file} не найден"

        data = json.loads(cfg_file.read_text(encoding="utf-8"))
        sidebar_items = data.get("menu", {}).get("sidebarItems", [])

        item = next((x for x in sidebar_items if x.get("id") == "file_recovery"), None)
        assert item is not None, "Элемент file_recovery должен присутствовать в sidebarItems"
        assert item.get("tab") == "tab-file-recovery"
        assert item.get("label") == "Восстановить удаленные файлы"

    def test_tabs_config_contains_file_recovery(self):
        """tabs-config.js должен содержать определение file_recovery."""
        tabs_cfg_file = __root__ / "src" / "api" / "webgui" / "apps" / "modules" / "tabs-config.js"
        assert tabs_cfg_file.exists()
        content = tabs_cfg_file.read_text(encoding="utf-8")
        assert "file_recovery" in content
        assert "tab-file-recovery" in content

    def test_apps_index_html_contains_file_recovery_pane(self):
        """apps/index.html должен содержать контейнер tab-file-recovery."""
        apps_html = __root__ / "src" / "api" / "webgui" / "apps" / "index.html"
        assert apps_html.exists()
        content = apps_html.read_text(encoding="utf-8")
        assert 'id="tab-file-recovery"' in content

    def test_locales_contain_file_recovery_translation(self):
        """Локали ru, en, he должны содержать ключ tabs.fileRecovery."""
        for lang in ("ru", "en", "he"):
            loc_file = __root__ / "src" / "api" / "webgui" / "locales" / f"{lang}.json"
            assert loc_file.exists()
            data = json.loads(loc_file.read_text(encoding="utf-8"))
            assert "fileRecovery" in data.get("tabs", {}), f"Ключ fileRecovery отсутствует в {lang}.json"
