# Начало работы

Этот раздел поможет вам запустить AI-Breadboard за несколько минут.

Полное описание возможностей платформы — в **[README.md](https://github.com/hypo69/AI-Breadboard#readme)**.

---

## Что вам понадобится

- **Python 3.10+** — [скачать](https://www.python.org/downloads/), при установке отметить «Add python.exe to PATH»
- **Git** — для клонирования репозитория
- **API-ключ Google Gemini** — [получить бесплатно](https://aistudio.google.com/api-keys)
- **PowerShell 5.1+** (Windows) — встроен в систему

---

## Быстрый старт (Windows)

### 1. Установка одной командой

Откройте PowerShell **от имени администратора**:

```powershell
irm https://raw.githubusercontent.com/hypo69/AI-Breadboard/master/install.ps1 | iex
```

Установщик проведёт вас через 8 шагов: создание `venv`, установка зависимостей, SSL-сертификаты, регистрация команды `assist`.

### 2. Настройка `.env`

После установки откройте файл `.env` в папке проекта и добавьте минимальный набор:

```ini
GEMINI_API_KEY=ваш_ключ_gemini
JWT_SECRET=любая_случайная_строка
ADMIN_PASSWORD=ваш_пароль
```

### 3. Запуск

```powershell
.\run.ps1
```

Сервер стартует на `http://localhost:8000/`. Откройте браузер — вы увидите главную панель с чатом.

---

## Быстрый старт (Linux / macOS)

```bash
git clone https://github.com/hypo69/AI-Breadboard.git
cd AI-Breadboard
bash install.sh
cp .env.example .env
# отредактируйте .env
python main.py
```

---

## Первые шаги после запуска

| Что сделать | Где |
|---|---|
| Отправить первый запрос к модели | `http://localhost:8000/` → чат |
| Сменить провайдер или модель | `assist select provider gemini` |
| Включить плагин (Telegram, Google) | `http://localhost:8000/admin` → Plugins |
| Загрузить документы в базу знаний | Admin UI → RAG или `POST /api/user/files/upload` |
| Посмотреть все команды CLI | `assist help` |

---

## Что дальше?

- [Установка](installation.md) — подробное руководство, ручная установка, структура пакетов
- [Запуск сервера](RUN.md) — параметры `run.ps1`, сопутствующие сервисы
- [Конфигурация](configuration.md) — `config.json`, пул ключей Gemini, секреты
- [Примеры использования](usage-examples.md) — реальные сценарии работы
- [Решение проблем](troubleshooting.md) — типичные ошибки и их устранение
