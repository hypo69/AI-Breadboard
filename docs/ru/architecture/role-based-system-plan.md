# План архитектуры ролевой системы AI-Breadboard

## Обзор

Система должна поддерживать несколько ролей пользователей с разными наборами доступных функций, используя общий код и компоненты. Каждая роль имеет свой конфигурационный профиль и набор разрешений.

## Текущее состояние

### Роли

| Роль | Запуск | Конфиг | Описание |
|------|--------|--------|----------|
| **Полный администратор** | `run.ps1` | `config.json` | Полный доступ ко всем функциям |
| **Компьютерный техник** | `tc.ps1` | `config_tc.json` | Только системные приложения и диагностика |
| **Личный секретарь** | ? | ? | Планируется - ограниченный доступ |

### Структура конфигов

```
AI-Breadboard/
├── config.json              # Администратор (run.ps1)
├── config_tc.json           # Техник (tc.ps1)
├── config_secretary.json    # Секретарь (планируется)
└── src/api/webgui/config/
    ├── tc_menu_config.json  # Меню для tc
    └── admin_menu_config.json  # Меню для admin (планируется)
```

## Параметры, которые можно вынести в отдельные конфиги

### 1. Меню навигации (Уже реализовано)
- `tc_menu_config.json` — элементы меню для Test Computer
- `admin_menu_config.json` — элементы меню для Admin Panel

**Параметры:**
- `topButtons` — кнопки верхнего меню (Quick Access)
- `sidebarItems` — элементы бокового меню
- `settings` — общие настройки отображения

### 2. Настройки интерфейса
**Файл:** `ui_config.json`

```json
{
  "theme": {
    "default": "dark",
    "allowed": ["dark", "light", "system"]
  },
  "language": {
    "default": "ru",
    "allowed": ["ru", "en", "he"]
  },
  "layout": {
    "showTopMenu": true,
    "showSidebar": true,
    "showModelBadge": true,
    "showSearchBadge": true
  },
  "animations": {
    "enabled": true,
    "duration": 300
  }
}
```

### 3. Разрешения и доступ (Роли)
**Файл:** `role_permissions.json`

```json
{
  "roles": {
    "admin": {
      "description": "Полный доступ ко всем функциям",
      "permissions": [
        "admin_panel",
        "user_management",
        "system_config",
        "plugins_management",
        "rag_management",
        "models_management",
        "all_apps",
        "all_skills",
        "all_mcp_servers"
      ]
    },
    "technician": {
      "description": "Только системные приложения и диагностика",
      "permissions": [
        "system_inspector",
        "system_control_center",
        "system_logs",
        "network_terminal",
        "windows_sysadmin",
        "hardware_monitor",
        "software_audit",
        "registry_viewer",
        "startup_auditor",
        "backup_manager"
      ]
    },
    "secretary": {
      "description": "Ограниченный доступ к бизнес-функциям",
      "permissions": [
        "chat",
        "rag_search",
        "google_workspace",
        "email",
        "docs",
        "calendar",
        "news_feed",
        "invoice_processor"
      ]
    }
  },
  "default_role": "admin",
  "oauth_role_mapping": {
    "admin@gmail.com": "admin",
    "tech@gmail.com": "technician",
    "secretary@gmail.com": "secretary"
  }
}
```

### 4. Доступные приложения по роли
**Файл:** `role_apps_config.json`

```json
{
  "roles": {
    "admin": {
      "enabled_apps": ["all"],
      "disabled_apps": []
    },
    "technician": {
      "enabled_apps": [
        "about_system",
        "scenarios",
        "windows_sysadmin",
        "system_inspector",
        "system_control_center",
        "system_log_viewer",
        "software_audit",
        "registry_viewer",
        "windows_startup_auditor",
        "windows_defender",
        "windows_backup_manager",
        "hardware_monitor",
        "librehardwaremonitor",
        "autolog_manager"
      ],
      "disabled_apps": [
        "chat",
        "network_terminal",
        "cloudflared_monitor",
        "gcloud_monitor",
        "website_monitor",
        "user_assistant",
        "wikipedia_research",
        "trading_terminal",
        "helpdesk",
        "ai_breadboard_admin",
        "research_and_statistic"
      ]
    },
    "secretary": {
      "enabled_apps": [
        "chat",
        "rag_search",
        "google_workspace",
        "email",
        "docs",
        "calendar",
        "news_feed",
        "invoice_processor"
      ],
      "disabled_apps": ["all"]
    }
  }
}
```

### 5. Доступные навыки по роли
**Файл:** `role_skills_config.json`

```json
{
  "roles": {
    "admin": {
      "enabled_skills": ["all"]
    },
    "technician": {
      "enabled_skills": [
        "project-installer",
        "cert-installer",
        "system-updater",
        "file-saver",
        "pdf-exporter",
        "tdd-doc-gen",
        "doc-generator",
        "skill-factory",
        "db-inspector",
        "storage-tool",
        "smart-deletion-duplicates"
      ]
    },
    "secretary": {
      "enabled_skills": [
        "rag-search-manager",
        "rag-cleaner",
        "google-workspace",
        "invoice-extractor",
        "news-reader",
        "travel-agent",
        "web-chat-cli"
      ]
    }
  }
}
```

### 6. Доступные плагины по роли
**Файл:** `role_plugins_config.json`

```json
{
  "roles": {
    "admin": {
      "enabled_plugins": ["all"]
    },
    "technician": {
      "enabled_plugins": [
        "application_log_analyzer",
        "rag_cleaner",
        "generate_rag_from_codebase"
      ],
      "disabled_plugins": [
        "facebook",
        "gdrive_sync",
        "google_oauth",
        "ifttt",
        "invoice_processor",
        "news_feed",
        "telegram_bot",
        "telegram_channel_rag",
        "user_storage"
      ]
    },
    "secretary": {
      "enabled_plugins": [
        "google_oauth",
        "google_workspace",
        "gdrive_sync",
        "invoice_processor",
        "news_feed",
        "user_storage"
      ],
      "disabled_plugins": [
        "application_log_analyzer",
        "facebook",
        "ifttt",
        "telegram_bot",
        "telegram_channel_rag"
      ]
    }
  }
}
```

### 7. Настройки TTS по роли
**Файл:** `role_tts_config.json`

```json
{
  "roles": {
    "admin": {
      "default_voice": "ru-RU-DmitryNeural",
      "allowed_voices": ["all"]
    },
    "technician": {
      "default_voice": "ru-RU-DmitryNeural",
      "allowed_voices": ["ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"]
    },
    "secretary": {
      "default_voice": "ru-RU-SvetlanaNeural",
      "allowed_voices": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural", "en-US-AvaMultilingualNeural"]
    }
  }
}
```

### 8. Настройки RAG по роли
**Файл:** `role_rag_config.json`

```json
{
  "roles": {
    "admin": {
      "mode": "rag+model",
      "max_results": 10,
      "similarity_threshold": 0.4
    },
    "technician": {
      "mode": "rag",
      "max_results": 5,
      "similarity_threshold": 0.6
    },
    "secretary": {
      "mode": "rag+model",
      "max_results": 8,
      "similarity_threshold": 0.5
    }
  }
}
```

### 9. Настройки AI-провайдеров по роли
**Файл:** `role_ai_config.json`

```json
{
  "roles": {
    "admin": {
      "enabled_providers": ["all"],
      "default_provider": "gemini",
      "default_model": "gemini-2.5-flash"
    },
    "technician": {
      "enabled_providers": ["gemini", "gemini_cli", "ollama"],
      "default_provider": "gemini",
      "default_model": "gemini-2.5-flash"
    },
    "secretary": {
      "enabled_providers": ["gemini", "openai"],
      "default_provider": "gemini",
      "default_model": "gemini-2.5-flash"
    }
  }
}
```

## План реализации

### Этап 1: Централизация конфигов (Готово)
- ✅ Создана папка `src/api/webgui/config/`
- ✅ Перемещен `tc_menu_config.json`
- ✅ Создан `README.md` с описанием

### Этап 2: Создание конфигов для ролей
1. Создать `role_permissions.json`
2. Создать `role_apps_config.json`
3. Создать `role_skills_config.json`
4. Создать `role_plugins_config.json`
5. Создать `ui_config.json`

### Этап 3: Обновление лончеров
1. Обновить `run.ps1` для загрузки `config.json` + `role_permissions.json`
2. Обновить `tc.ps1` для загрузки `config_tc.json` + `role_permissions.json`
3. Добавить `secretary.ps1` для запуска роли секретаря

### Этап 4: Обновление веб-интерфейса
1. Обновить `admin/index.html` для проверки разрешений
2. Обновить `apps/index.html` для проверки разрешений
3. Добавить динамическую генерацию меню на основе ролей
4. Добавить проверку доступа к навыкам и плагинам

### Этап 5: Документация
1. Обновить `docs/ru/architecture/centralized-config.md`
2. Создать `docs/ru/architecture/role-based-access.md`
3. Обновить `docs/ru/architecture/index.md`

## Принципы проектирования

1. **DRY (Don't Repeat Yourself)** — общий код, разные конфиги
2. **Конфигурация через JSON** — легко редактировать без кода
3. **Версионирование** — каждая конфигурация имеет версию
4. **Изоляция** — каждый файл отвечает за одну функцию
5. **Расширяемость** — легко добавить новые роли и параметры
6. **Безопасность** — проверка разрешений на клиенте и сервере

## Будущие улучшения

- [ ] UI для редактирования конфигов через Admin Panel
- [ ] Валидация конфигов по JSON Schema
- [ ] Поддержка окружений (dev/staging/production)
- [ ] История изменений конфигов
- [ ] Экспорт/импорт конфигов
- [ ] Шаблоны конфигов для разных сценариев использования