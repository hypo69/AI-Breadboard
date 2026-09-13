# 🖥️ System Inspector

Интерактивный инструмент для мониторинга системной производительности, аппаратного обеспечения, потоков процессов в реальном времени, диагностики производительности с помощью AI и просмотра спецификаций оборудования по формату AIDA64.

## 📋 Оглавление
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Использование](#использование)
- [FastAPI endpoints](#fastapi-endpoints)
- [Конфигурация](#конфигурация)

---

## Возможности

- **Live Process Stream** — отображение процессов в реальном времени (PID, CPU, RAM, потоки, пользователь)
- **Hardware Tree** — дерево оборудования по формату AIDA64 (процессор, память, GPU, сенсоры)
- **AI Performance Copilot** — диагностика производительности и выявление аномалий
- **FastAPI REST API** — программный доступ к системной информации
- **Интерактивная TUI** — визуализация данных в терминале с Rich

---

## Архитектура

```
apps/system_inspector/
├── tui.py                # TUI-рендерер и цикл сбора телеметрии
├── router.py             # FastAPI endpoints для REST API
├── __main__.py           # Точка входа (CLI + standalone server)
├── __init__.py           # Экспорт пакета
└── config.json           # Конфигурация сервера (порт 8102)
```

**Разделение ответственности:**
- `tui.py` — TUI-рендеринг, управление состоянием (`SystemInspectorState`)
- `router.py` — FastAPI HTTP-роутеры и обработчики запросов
- `__main__.py` — CLI-интерфейс и запуск standalone-сервера

---

## Установка

```bash
cd apps/system_inspector
pip install -r ../../requirements.txt
pip install rich  # Для TUI-интерфейса
```

---

## Использование

### Интерактивный dashboard (TUI)

```bash
python -m apps.system_inspector --interval 1.0 --sort cpu
```

Аргументы:
- `--interval` — интервал обновления в секундах (по умолчанию: 1.0)
- `--sort` — сортировка по `cpu` или `memory` (по умолчанию: cpu)
- `--limit` — количество процессов (по умолчанию: 20)

Клавиши управления:
- `Q` — выход
- `S` — переключение сортировки (CPU/RAM)
- `D` — запуск AI-диагностики

### FastAPI сервер

```bash
python -m apps.system_inspector --mode server
```

По умолчанию сервер запускается на `http://127.0.0.1:8102`.

### CLI-команды

```bash
# Одноразовая диагностика
python -m apps.system_inspector --diagnose

# Просмотр оборудования
python -m apps.system_inspector --hardware

# JSON output
python -m apps.system_inspector --json
```

---

## FastAPI endpoints

### `GET /api/system/status`

```json
{
  "hostname": "WORKSTATION",
  "os_name": "Windows 11",
  "uptime_seconds": 86400,
  "cpu": {...},
  "memory": {...},
  "process_count": 150
}
```

### `GET /api/system/processes`

```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "chrome.exe",
      "status": "Running",
      "cpu_percent": 25.5,
      "memory_mb": 512.3,
      "memory_percent": 12.5,
      "num_threads": 23,
      "username": "Administrator"
    }
  ],
  "sort_by": "cpu"
}
```

### `GET /api/system/hardware`

```json
{
  "hardware": [
    {
      "category": "CPU",
      "name": "Intel Core i7-12700K",
      "properties": {
        "Cores": 12,
        "Threads": 20,
        "Base Clock": "3.6 GHz"
      }
    }
  ],
  "sensors": [
    {
      "name": "CPU Core 0",
      "value": 65.0,
      "unit": "°C"
    }
  ]
}
```

### `GET /api/system/diagnostic`

```json
{
  "health_score": 85,
  "summary": "System Health: 85/100. Telemetry stream nominal.",
  "ai_model_used": "Heuristic Monitor",
  "anomalies": [],
  "recommendations": []
}
```

---

## Конфигурация

Файл `config.json`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8102,
    "use_ssl": false,
    "workers": 1
  },
  "cors": {
    "allow_origins": [],
    "allow_origin_regex": null,
    "allow_credentials": true,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
  }
}
```

### Порт по умолчанию

Каждое приложение запускается на своем порту:
- `windows_sysadmin`: **8100**
- `network_terminal`: **8101**
- `system_inspector`: **8102**

---

## Лицензия

© 2026 hypo69. Все права защищены.
