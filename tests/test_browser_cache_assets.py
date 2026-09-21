"""
test_browser_cache_assets.py - Тестирование файлов и структуры подсистемы браузерного кеширования
"""

import json
from pathlib import Path
import pytest

WEBGUI_DIR = Path(__file__).resolve().parent.parent / "src" / "api" / "webgui"


def test_browser_cache_js_exists_and_contains_stores():
    """Проверка наличия и структуры модуля browser-cache.js."""
    cache_file = WEBGUI_DIR / "js" / "browser-cache.js"
    assert cache_file.exists(), "browser-cache.js должен существовать"
    content = cache_file.read_text(encoding="utf-8")

    assert "class BrowserCacheManager" in content
    assert "STORES" in content
    assert "api_cache" in content
    assert "rag_embeddings" in content
    assert "chat_history" in content
    assert "media_blobs" in content
    assert "models_registry" in content
    assert "key_value" in content
    assert "cleanupExpired" in content
    assert "getDetailedStats" in content
    assert "requestPersistence" in content
    assert "exportData" in content
    assert "importData" in content


def test_api_cache_integration():
    """Проверка интеграции api-cache.js с BrowserCacheManager."""
    api_cache_file = WEBGUI_DIR / "js" / "api-cache.js"
    assert api_cache_file.exists(), "api-cache.js должен существовать"
    content = api_cache_file.read_text(encoding="utf-8")

    assert "import { browserCache, STORES } from './browser-cache.js'" in content
    assert "getAsync" in content
    assert "usePersistentStorage" in content


def test_cache_ui_controller_exists():
    """Проверка наличия и методов контроллера интерфейса cache-ui.js."""
    cache_ui_file = WEBGUI_DIR / "js" / "cache-ui.js"
    assert cache_ui_file.exists(), "cache-ui.js должен существовать"
    content = cache_ui_file.read_text(encoding="utf-8")

    assert "initCacheUI" in content
    assert "openCacheModal" in content
    assert "refreshCacheModalStats" in content
    assert "cacheManagerModal" in content


def test_index_html_modal_and_nav_bindings():
    """Проверка разметки модального окна и кнопок в index.html."""
    index_html = WEBGUI_DIR / "index.html"
    assert index_html.exists(), "index.html должен существовать"
    content = index_html.read_text(encoding="utf-8")

    assert 'id="cacheManagerModal"' in content
    assert 'id="btn-open-cache-manager"' in content
    assert 'id="user-menu-btn-cache"' in content
    assert 'id="cache-usage-progressbar"' in content
    assert 'id="cache-stores-list"' in content


def test_locales_contain_cache_manager():
    """Проверка наличия ключей локализации cacheManager в ru.json, en.json, he.json."""
    for lang in ["ru", "en", "he"]:
        locale_path = WEBGUI_DIR / "locales" / f"{lang}.json"
        assert locale_path.exists(), f"Локаль {lang}.json должна существовать"
        data = json.loads(locale_path.read_text(encoding="utf-8"))
        assert "cacheManager" in data, f"Ключ cacheManager отсутствует в {lang}.json"
        assert "title" in data["cacheManager"]
        assert "quotaTitle" in data["cacheManager"]
