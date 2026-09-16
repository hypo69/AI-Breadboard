# 📦 Установка и подготовка проекта

**Статус:** ✅ Up to date  
**Версия:** 2.0  
**Платформы:** Windows, Linux, macOS  
**Последнее обновление:** сентябрь 2026

---

## 📋 Содержание
1. [Системные требования](#1-системные-требования)
2. [Установка (Windows)](#2-установка-windows)
3. [Установка (Linux/macOS)](#3-установка-linuxmacos)
4. [Проверка установки](#4-проверка-установки)
5. [Настройка конфигурации](#5-настройка-конфигурации)

---

## 1. Системные требования

### Обязательные

- **Python:** 3.12+
- **Node.js:** 18+
- **Git:** 2.30+
- **RAM:** минимально 4GB (рекомендуется 8GB+)
- **Место на диске:** 5GB+

### Опциональные (для локальных провайдеров)

- **Docker:** для запуска Ollama и других контейнеризированных сервисов
- **CUDA:** для GPU acceleration (NVIDIA)
- **DirectML:** для Windows AI APIs

---

## 2. Установка (Windows)

### Шаг 1: Клонирование репозитория

```powershell
git clone https://github.com/your-org/ai-breadboard.git
cd ai-breadboard
```

### Шаг 2: Создание виртуального окружения

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Шаг 3: Установка зависимостей

```powershell
pip install -r requirements.txt
```

### Шаг 4: Установка Node зависимостей (для веб-интерфейса)

```powershell
npm install
```

### Шаг 5: Подготовка конфигурации

```powershell
Copy-Item .env.example .env
# Отредактируйте .env с вашими API ключами
notepad .env
```

### Шаг 6: Запуск сервера

```powershell
python main.py
# или используя launcher
.\launchers\Run-Server.ps1
```

Сервер запустится на `http://localhost:8000`

---

## 3. Установка (Linux/macOS)

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your-org/ai-breadboard.git
cd ai-breadboard
```

### Шаг 2: Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

### Шаг 3: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 4: Установка Node зависимостей

```bash
npm install
```

### Шаг 5: Подготовка конфигурации

```bash
cp .env.example .env
# Отредактируйте .env с вашими API ключами
nano .env
```

### Шаг 6: Запуск сервера

```bash
python main.py
```

---

## 4. Проверка установки

### Проверка Python

```bash
python --version  # Должно быть 3.12+
pytest tests/ -v  # Запуск тестов
```

### Проверка веб-интерфейса

1. Откройте `http://localhost:8000` в браузере
2. Должна загрузиться страница администратора

### Проверка API

```bash
# Проверка статуса чата
curl http://localhost:8000/api/chat/status

# Проверка версии
curl http://localhost:8000/api/version
```

---

## 5. Настройка конфигурации

### Обязательные API ключи (`.env`)

```env
# Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI (опционально)
OPENAI_API_KEY=your_openai_key_here

# HuggingFace (опционально)
HUGGING_FACE_TOKEN=your_hf_token_here
```

### Конфигурация сервера (`config.json`)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "environment": "development"
  },
  "providers": {
    "gemini": {
      "enabled": true,
      "model": "gemini-2.5-flash"
    },
    "ollama": {
      "enabled": false,
      "base_url": "http://localhost:11434"
    }
  }
}
```

### Запуск с конфигом

```bash
# Production
python main.py --env production

# Developement
python main.py --env development
```

---

## 🔧 Решение проблем

### ModuleNotFoundError: No module named 'fastapi'

```bash
pip install -r requirements.txt
# или
pip install fastapi uvicorn
```

### Port 8000 already in use

```bash
# Используйте другой порт
python main.py --port 8001
```

### CORS ошибки

Убедитесь, что в `config.json` установлены правильные CORS параметры:

```json
{
  "cors": {
    "allow_origins": ["http://localhost:3000", "http://localhost:8000"],
    "allow_methods": ["GET", "POST"],
    "allow_headers": ["*"]
  }
}
```

---

## 📚 Дополнительно

- [`guides/LAUNCHERS.md`](LAUNCHERS.md) — Запуск сервисов через PowerShell scripts
- [`guides/CLI_TOOLS.md`](CLI_TOOLS.md) — Использование CLI инструментов
- [`standards/ENGINEERING.md`](../standards/ENGINEERING.md) — Стандарты разработки

**Последнее обновление:** сентябрь 2026
