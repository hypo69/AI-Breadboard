# Test Suite (`tests/`)

## Structure

```
tests/
├── __init__.py              # Test suite package root
├── conftest.py              # Shared Pytest fixtures and mock objects
├── data/                    # Test fixtures and static sample payloads
│   └── __init__.py
├── test_ai.py               # Unit tests for AI models and UnifiedChatModel
├── test_fastapi.py          # Unit & integration tests for FastAPI routers
├── test_tts.py              # Tests for Edge-TTS and speech synthesis
├── test_user_manager.py     # Tests for user profile database CRUD
├── test_logger.py           # Tests for logging subsystem and formatters
├── test_plugins.py          # Tests for plugin lifecycle and drive scanners
├── test_integration_api.py  # End-to-end API integration tests
└── test_environment.py      # Environment and configuration sanity checks
```

---

## Running Tests

### Execute All Tests
```bash
pytest
```

### Run Specific Test Modules
```bash
pytest tests/test_ai.py
pytest tests/test_fastapi.py
```

### Run with Code Coverage
```bash
pytest --cov=core --cov=webinterface --cov-report=term-missing
```

### Run by Marker
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration
```

---

## Key Fixtures (`conftest.py`)

- `mock_ai_model`: Mocked AI chat model for predictable response testing.
- `mock_db`: In-memory SQLite media database fixture.
- `mock_qbt_client`: Mocked qBittorrent client.
- `temp_db_path`: Isolated temporary database file path.
- `sample_media_records`: Standard sample media datasets.
- `setup_env`: Automatic test environment variable bootstrap.
