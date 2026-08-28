"""
Test configuration for ai-breadboard.
Provides fixtures and settings for all tests.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest

# Add project root to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Configure environment variables for tests
os.environ['TEST_MODE'] = 'true'
os.environ['USE_FOUNDRY'] = 'false'
os.environ['PRELOAD_SILERO'] = 'false'

import ssl
try:
    ssl.create_default_context()
except Exception:
    _orig_create_default_context = ssl.create_default_context
    def _safe_create_default_context(*args, **kwargs):
        try:
            return _orig_create_default_context(*args, **kwargs)
        except Exception:
            ctx = ssl._SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
    ssl.create_default_context = _safe_create_default_context


@pytest.fixture(scope='session')
def test_data_dir():
    """Path to test data."""
    return ROOT / 'tests' / 'data'


@pytest.fixture
def mock_ai_model():
    """Mock for AI model."""
    mock = Mock()
    mock.chat = AsyncMock()
    mock.chat_stream = AsyncMock()
    mock.ask = AsyncMock()
    mock.ask_with_tools = AsyncMock()
    mock.describe_image = AsyncMock()
    mock.upload_file = AsyncMock()
    mock.clear_history = Mock()
    return mock


@pytest.fixture
def mock_db():
    """Mock for MediaDatabase."""
    mock = Mock()
    mock.export_all = Mock(return_value=[])
    mock.export_movies = Mock(return_value=[])
    mock.export_series = Mock(return_value=[])
    mock.find_by_title = Mock(return_value=None)
    mock.find_duplicates = Mock(return_value=[])
    mock.get_categories = Mock(return_value=[])
    mock.add_record = Mock(return_value=1)
    mock.update_record = Mock(return_value=True)
    mock.delete_record = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_qbt_client():
    """Mock for QBittorrentClient."""
    mock = Mock()
    mock.torrents = Mock(return_value=[])
    mock.add_torrent_by_url = Mock(return_value=True)
    mock.add_torrent_by_file = Mock(return_value=True)
    mock.recheck = Mock(return_value=True)
    mock.set_location = Mock(return_value=True)
    return mock


@pytest.fixture
def temp_db_path(tmp_path):
    """Temporary database path for tests."""
    return tmp_path / 'test_media.db'


@pytest.fixture
def sample_media_records():
    """Example media records for tests."""
    return [
        {
            'id': 1,
            'title': 'Test Movie',
            'title_ru': 'Тестовый Фильм',
            'title_orig': 'Test Movie',
            'type': 'movie',
            'disk_name': 'DISK_1',
            'year': 2024,
            'path': 'E:/Movies/Test Movie.mkv',
            'main_category': 'Боевики',
            'imdb_rating': 8.5,
            'kinopoisk_rating': 8.7,
        },
        {
            'id': 2,
            'title': 'Test Series',
            'title_ru': 'Тестовый Сериал',
            'title_orig': 'Test Series',
            'type': 'series',
            'disk_name': 'DISK_1',
            'year': 2024,
            'path': 'E:/Series/Test Series/S01E01.mkv',
            'main_category': 'Драмы',
            'season': 1,
            'episode': 1,
        },
    ]


@pytest.fixture
def sample_torrents():
    """Example torrents for tests."""
    return [
        {
            'hash': 'abc123',
            'name': 'Test Torrent',
            'state': 'Downloading',
            'progress': 0.45,
            'size': 1073741824,
            'save_path': 'E:/Downloads',
        },
    ]


@pytest.fixture(autouse=True)
def setup_env():
    """Configure environment for each test."""
    with patch.dict(os.environ, {
        'GOOGLE_CLIENT_ID': 'test_client_id',
        'GOOGLE_CLIENT_SECRET': 'test_secret',
        'JWT_SECRET': 'test_jwt_secret',
        'NGROK_AUTOTOKEN': 'test_ngrok',
        'GEMINI_API_KEY_NAMES': 'test_key',
    }, clear=True):
        yield
