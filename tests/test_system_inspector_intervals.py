# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test System Inspector Intervals Editor
# =============================================================================
# Description:
#   Тесты для проверки интеграции попап-окна редактора интервалов в вкладке
#   «Потребление ресурсов» (System & Hardware Inspector) и API автологгирования.
#
# File: test_system_inspector_intervals.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
import pytest


def test_system_inspector_html_contains_intervals_modal():
    """Проверяет наличие кнопок и модального окна интервалов в index.html вкладки."""
    html_path = Path("src/api/webgui/system_inspector_tab/index.html")
    assert html_path.exists(), "Файл index.html вкладки system_inspector_tab не найден"

    content = html_path.read_text(encoding="utf-8")
    
    # Кнопки вызова модала
    assert 'id="btn-sys-intervals"' in content, "Кнопка 'Интервалы' отсутствует в верхней панели"
    assert 'id="btn-sys-intervals-lhm"' in content, "Кнопка 'Интервалы' отсутствует в шапке панели сенсоров LHM"
    
    # Модальное окно редактора интервалов
    assert 'id="sysIntervalsModal"' in content, "Модальное окно #sysIntervalsModal отсутствует"
    assert 'id="modal-intervals-cfg-file"' in content, "Индикатор config.json отсутствует в модале"
    assert 'id="modal-ui-refresh-select"' in content, "Селектор частоты UI отсутствует в модале"
    assert 'id="modal-core-loggers-container"' in content, "Контейнер основных логгеров ресурсов отсутствует"
    assert 'id="btn-modal-intervals-save"' in content, "Кнопка сохранения в config.json отсутствует"


def test_system_inspector_main_js_contains_intervals_controller():
    """Проверяет наличие функций управления интервалами в main.js вкладки."""
    js_path = Path("src/api/webgui/system_inspector_tab/main.js")
    assert js_path.exists(), "Файл main.js вкладки system_inspector_tab не найден"

    content = js_path.read_text(encoding="utf-8")

    assert "openSysIntervalsModal" in content, "Функция openSysIntervalsModal отсутствует в main.js"
    assert "loadSysIntervalsConfig" in content, "Функция loadSysIntervalsConfig отсутствует в main.js"
    assert "saveSysIntervalsConfig" in content, "Функция saveSysIntervalsConfig отсутствует в main.js"
    assert "setupSysSensorInterval" in content, "Функция setupSysSensorInterval отсутствует в main.js"
    assert "librehardwaremonitor" in content, "Логгер librehardwaremonitor отсутствует в main.js"


def test_system_inspector_contains_realtime_live_watcher():
    """Проверяет наличие панелиИзменения файлов в реальном времени во вкладке 'Потребление ресурсов'."""
    html_path = Path("src/api/webgui/system_inspector_tab/index.html")
    content = html_path.read_text(encoding="utf-8")
    assert "Real-Time Live Watcher" in content
    assert 'id="sys-watcher-tbody"' in content
    assert 'id="sys-watch-dir-path"' in content
    assert 'id="btn-sys-change-watch-dir"' in content

    js_path = Path("src/api/webgui/system_inspector_tab/main.js")
    js_content = js_path.read_text(encoding="utf-8")
    assert "fetchLiveFileEvents" in js_content
    assert "openWatchFoldersModal" in js_content
    assert "showLiveWatcherHelpModal" in js_content


def test_windows_admin_does_not_contain_live_watcher():
    """Проверяет, что панельИзменения файлов в реальном времени была удалена из вкладки Windows Sysadmin."""
    html_path = Path("src/api/webgui/windows_admin_tab/index.html")
    content = html_path.read_text(encoding="utf-8")
    assert "Real-Time Live Watcher" not in content
    assert 'id="winadmin-live-tbody"' not in content

