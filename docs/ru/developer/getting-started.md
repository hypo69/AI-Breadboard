# Developer Guide — Getting Started

## Project Structure

```
main.py                  # Entry point (thin, ~60 lines)
src/
  app/                   # Application factory, lifespan, middleware, routes
  ai/                    # AI providers, UnifiedChatModel, agents
  fastapi/               # HTTP routers (25+)
  rag/                   # RAG engine
  plugins/               # Hot-reload plugin system
  logger/                # Singleton logger
  db/                    # SQLite migration manager
  user_manager/          # User management
  tts/                   # Text-to-speech
  utils/                 # Utilities
  secrets/               # Private credential files (gitignored)
apps/                    # Standalone application modules
plugins/                 # User plugins directory
tests/                   # 80+ test files
```

## Setup

```powershell
git clone https://github.com/hypo69/ai-breadboard.git
cd ai-breadboard
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-test.txt
cp .env.example .env
```

## Running Tests

```powershell
pytest --tb=short -q
```

## Code Style

- Python 3.11+
- Type hints everywhere
- `from logger import logger` (not `logging.getLogger`)
- English for all log messages and comments
