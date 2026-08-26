# Начало работы для разработчиков

## Требования

- Python 3.10+
- Node.js 18+ (для MCP сервера)
- PostgreSQL/SQLite (для базы данных)
- Git

## Клонирование репозитория

```bash
git clone https://github.com/hypo69/ai-assistant.git
cd ai-assistant
```

## Установка зависимостей

### Python зависимости

```bash
pip install -r requirements.txt
```

### Node зависимости (для MCP сервера)

```bash
cd .mcp
npm install
cd ../.mcp/playwright
npm install
cd ../..
```

## Структура проекта

```
ai-assistant/
├── docs/                    # Документация (MkDocs)
├── core/                     # Исходный код Python
│   ├── ai/                  # AI модули (Gemini)
│   ├── fastapi/             # FastAPI роутеры и endpoints
│   ├── logger/              # Логирование
│   ├── media_granularity.py # Управление медиа-таймингами
│   ├── secrets/             # Управление API ключами
│   ├── user_manager/        # Управление пользователями
│   └── utils/               # Утилиты
├── plugins/                 # Плагины
│   ├── media_layer/         # Управление медиа-слоями
│   ├── media_organizer/     # Организация медиатеки
│   ├── qbittorrent/         # Управление qBittorrent
│   ├── rag/                 # RAG поиск
│   ├── telegram_bot/        # Telegram бот
│   └── torrent_playwright/  # Поиск торрентов
├── webinterface/            # Веб-интерфейс
│   ├── admin/               # Админ-панель
│   ├── chat/                # Чат
│   ├── css/                 # CSS стили
│   ├── help/                # Справка
│   ├── js/                  # JavaScript
│   ├── player/              # Плеер
│   ├── rc/                  # Пульт ДУ
│   ├── tgmini/              # Telegram Mini App
│   └── user/                # Пользовательский интерфейс
├── .ai_instructions/        # Инструкции для AI
├── .mcp/                    # MCP серверы
├── .github/workflows/       # CI/CD
├── main.py                  # Точка входа
├── requirements.txt         # Python зависимости
├── mkdocs.yml               # Конфигурация MkDocs
└── README.md                # Основная документация
```

## Запуск в режиме разработки

### 1. Локальный запуск (Рекомендуемый)

Для быстрого локального запуска без настройки SSL, туннелей и Google OAuth используйте скрипт:
```powershell
.\Run-LightServer.ps1
```
Сервер будет доступен по адресу `http://127.0.0.1:3000` с автоматическим входом под `user_id = 1`. Подробнее см. руководство [Localhost vs Tunnel](localhost_vs_tunnel.md).

Для стандартного запуска:
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
python main.py
```

### 2. Запуск с автоматической перезагрузкой

```bash
# Установите uvicorn для dev режима
pip install uvicorn[standard]

# Запуск в dev режиме
uvicorn main:app --reload
```

### 3. Запуск через Docker

```bash
# Соберите образ
docker build -t ai-assistant .

# Запустите контейнер
docker run -p 3000:3000 ai-assistant
```

## Отладка

### Логирование

Все логи пишутся в терминал и в файл `logs/app.log`.

```python
from core.logger import logger

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

### Отладка API

Используйте `/api/docs` для просмотра OpenAPI спецификации:

```
http://localhost:3000/api/docs
```

## Настройка окружения

### Создание .env файла

```bash
cp .env.example .env
```

### Обязательные переменные

```env
# AI
GEMINI_API_KEY_NAMES=your_api_key_name

# Auth
JWT_SECRET=generate_secure_random_string_here

# Optional
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TMDB_API_KEY=your_tmdb_api_key
```

## Запуск тестов

```bash
# Установка pytest
pip install pytest pytest-asyncio

# Запуск тестов
pytest
```

## Деплойment

См. раздел [Деплоймент](deployment.md) для подробной информации.

---

[← Меню](../index.md) | [Архитектура →](architecture.md)