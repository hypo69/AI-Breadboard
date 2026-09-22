# Admin Panel Documentation

## Overview
AI-Breadboard Admin Panel — единый контейнер для управления системой, который показывает выбранные вкладки и подключает релевантные приложения и плагины через основной сервер (порт 8000).

## Access
- **URL**: http://localhost:8000/admin
- **Authentication**: Требуется пароль администратора (из `.env`)

## Tabs Structure

### 1. RAG
- Управление режимами RAG (rag+model, rag, model)
- Настройка векторной базы знаний
- Индексация документов

### 2. PixelRAG
- Векторный поиск по изображениям
- Пиксельный анализ

### 3. Models AI
- Выбор активной модели ИИ
- Управление провайдерами (Gemini, OpenAI, Ollama, Foundry, ONNX)
- Настройка параметров моделей

### 4. Agents AI
- Управление ReAct-агентами
- Настройка инструментов агентов
- Конфигурация MCP-инструментов

### 5. Skills
- Управление навыками агентов (27+ навыков)
- Создание/редактирование навыков
- Пакетирование навыков

### 6. MCP Servers
- Управление MCP-серверами (8 серверов)
- Подключение Claude, Cursor, Antigravity CLI

### 7. All Plugins
- Управление плагинами (Telegram, Google Workspace, IFTTT и др.)
- Активация/деактивация плагинов
- Настройка конфигурации плагинов

### 8. Apps (Приложения)
- **Chat** — основной чат ИИ
- **Chat and Scenarios** — сценарии и тесты
- **User Assistant** — персональный ассистент
- **Google Cloud Monitor** — мониторинг GCP
- **Website Intelligence** — мониторинг веб-сайтов
- **Cloudflared Monitor** — мониторинг Cloudflare туннелей

### 9. Администрирование

#### 9.1 Управление
- Общие настройки системы
- Конфигурация RAG и поиска
- Настройка инструкций

#### 9.2 Внутренние пользователи
- Управление пользователями проекта (через `user_manager`)
- Создание/редактирование/удаление
- Сброс паролей
- Управление ролями (admin/user)
- Статистика по пользователям

#### 9.3 Пользователи Windows
- Управление локальными учетными записями Windows
- Создание/удаление пользователей
- Включение/отключение
- Сброс паролей
- Управление группами
- **Отдельный модуль**: `WindowsUserManager` (не путать с внутренними пользователями!)

#### 9.4 Google аккаунты
- Управление OAuth-аккаунтами Google
- Синхронизация с Gmail, Drive, Sheets, Docs

#### 9.5 Системные логи
- Просмотр логов сервера
- Анализ ошибок

#### 9.6 Системные инструкции
- Управление системными промптами
- Версионирование инструкций

#### 9.7 Справочник
- Документация по системе

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Admin Panel (port 8000/admin)          │
│  Single container with dynamic tabs                 │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           Main Server (port 8000)                   │
│  FastAPI + Uvicorn + SSL                            │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           Backend Services                          │
│  - UserAdminService (internal users)                │
│  - WindowsUserManager (OS users)                    │
│  - AdminConfigManager                               │
│  - Plugins Manager                                  │
│  - Skills Registry                                  │
└─────────────────────────────────────────────────────┘
```

## Key Modules

### Internal Users (Project Users)
- **Module**: `src/user_manager.py`
- **Service**: `UserAdminService`
- **Endpoints**: `/api/admin/users/*`
- **Purpose**: Управление пользователями проекта AI-Breadboard

### Windows Users (OS Users)
- **Module**: `apps/ai_breadboard_admin/src/windows_user_manager.py`
- **Manager**: `WindowsUserManager`
- **Endpoints**: `/api/windows-users/*`
- **Purpose**: Управление локальными учетными записями Windows

## API Endpoints

### Admin Endpoints (`/api/admin/*`)
- `/users` — список пользователей
- `/users/{id}` — детали пользователя
- `/users/orphaned/dirs` — осиротевшие директории
- `/rag/config` — настройки RAG
- `/web-search/config` — настройки поиска
- `/instructions` — системные инструкции
- `/skills` — управление навыками
- `/plugins` — управление плагинами

### Windows Users Endpoints (`/api/windows-users/*`)
- `GET /` — список пользователей Windows
- `GET /groups` — список групп
- `GET /groups/{name}/members` — члены группы
- `POST /` — создание пользователя
- `DELETE /` — удаление пользователя
- `POST /enable` — включение
- `POST /disable` — отключение
- `POST /password` — сброс пароля
- `POST /add-to-group` — добавление в группу
- `POST /remove-from-group` — удаление из группы

## Configuration

### config.json
```json
{
  "rag": {
    "mode": "rag+model"
  },
  "web_search": {
    "engine": "playwright",
    "gemini_model": "gemini-2.5-flash"
  }
}
```

### .env
```env
ADMIN_PASSWORD=your_admin_password
GEMINI_API_KEY=your_api_key
```

## Usage

1. **Access Admin Panel**: http://localhost:8000/admin
2. **Login**: Enter admin password
3. **Navigate Tabs**: Use dropdown menus
4. **Manage**: Configure settings, users, plugins, etc.

## Notes

- Admin panel uses **single container** architecture
- All tabs loaded dynamically via JavaScript
- No separate server for admin panel
- Windows users and internal users are **completely separated**
- All management operations require admin authentication