# Быстрый старт

## Требования

- Python 3.10+
- Google Gemini API Key
- qBittorrent (опционально, для управления торрентами)
- Node.js 18+ (для MCP сервера, опционально)

## Установка

> [!TIP]
> Подробная пошаговая инструкция доступна в [Руководстве по установке](installation.md).

### 1. Быстрая установка (PowerShell)

```powershell
.\install.ps1
```

### 2. Ручная установка (Альтернатива)

#### Клонирование репозитория

```bash
git clone https://github.com/hypo69/ai-assistant.git
cd ai-assistant
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Обязательные переменные:

```env
GEMINI_API_KEY_NAMES=your_api_key_name
JWT_SECRET=generate_secure_random_string
```

Опциональные переменные:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TMDB_API_KEY=your_tmdb_api_key
```

### 5. Запуск сервера

```bash
python main.py
```

Сервер запустится по умолчанию на `http://localhost:3000` (или `https://` если настроены SSL сертификаты).

## Доступные интерфейсы

| Интерфейс | URL | Описание |
|-----------|-----|----------|
| Плеер | `/user` | Основной плеер с чатом AI |
| Пульт ДУ | `/rc` | Управление голосом + TTS |
| Telegram | `/tgmini` | Telegram Mini App |
| Админка | `/admin` | Управление медиатекой |

## Конфигурация

Конфигурационные файлы:

- `core/fastapi/config.json` — настройки сервера, OAuth, Telegram Mini App
- `core/fastapi/search_dirs.json` — директории для сканирования медиа

## Дальнейшие шаги

- 📖 [Читать руководство пользователя](user/getting-started.md)
- 💻 [Читать руководство разработчика](dev/getting-started.md)
- 🏗️ [Архитектура проекта](dev/architecture.md)

## Устранение проблем

При ошибках проверьте:
1. Наличие `.env` файла с правильными ключами
2. Доступность Gemini API
3. Права доступа к медиа-директориям
4. Логи в терминале при запуске

---

Для разработчиков: [Начало работы](dev/getting-started.md)