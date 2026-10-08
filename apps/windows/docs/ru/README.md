# AI Windows Diagnostic & Administration Center

Документация по модулю `apps/windows` для сбора телеметрии, мониторинга и аудита Windows-систем.

## 📋 Содержание

1. [Архитектура](#архитектура)
2. [Модули](#модули)
3. [Точка входа](#точка-входа)
4. [API Endpoints](#api-endpoints)
5. [Веб-интерфейс](#веб-интерфейс)
6. [Телеметрия](#телеметрия)
7. [Диагностика](#диагностика)
8. [Запуск](#запуск)
9. [Устранение неполадок](#устранение-неполадок)

---

## Архитектура

Модуль `apps/windows` построен на архитектуре:

```
apps/windows/
├── api/              # FastAPI роутеры и HTTP endpoints
├── telemetry/        # Сбор телеметрии и датчиков
├── telemetry_research/  # Анализ и исследование телеметрии
├── hardware/         # Датчики и аудит оборудования
├── core/             # Базовые компоненты диагностики
└── docs/ru/          # Русская документация
```

### Основные принципы

- **Read-only API**: Все POST-эндпоинты преобразованы в заглушки, данные только через GET
- **telemetry.db**: Единое хранилище данных через SQLite
- **WMI**: Используются нативные Windows API, LHM удален
- **polling**: Данные опрашиваются раз в 5 секунд или по настройке

---

## Модули

### 1. api/ — FastAPI роутеры

```
api/
├── internal_app.py   # Выделенный внутренний сервис
├── router.py         # Основной роутер Windows diagnostics
├── router_dashboard.py  # Dashboard эндпоинты (только GET)
└── webgui/           # Веб-интерфейс (HTML/JS/CSS)
```

### 2. telemetry/ — Сбор телеметрии

```
telemetry/
├── storage.py        # TelemetryStorage (SQLite с буферизацией)
├── sensor_collector.py  # Коллектор данных со всех сенсоров
├── sensors.py        # Датчики WMI (CPU, RAM, GPU, Storage)
├── collector.py      # Основной коллектор
├── main.py           # Точка входа в telemetry
└── config.json       # Конфигурация сбора
```

### 3. telemetry_research/ — Исследование телеметрии

```
telemetry_research/
├── server.py         # FastAPI сервер с веб-интерфейсом
├── analyzer.py       # Движок анализа
├── extractor.py      # Извлечение данных из telemetry.db
├── charts.py         # Генерация графиков (Chart.js)
└── models.py         # Модели данных
```

### 4. hardware/ — Аппаратное обеспечение

```
hardware/
├── hardware_monitor.py   # HardwareMonitor (CPU, RAM, GPU, Storage)
├── gpu_prober.py         # WMI датчики GPU
├── cpuz_aida_prober.py   # CPU-Z / AIDA64 обертки
├── cross_validator.py    # Кросс-валидация данных
└── stress_benchmark.py   # Стресс-тесты (CPU/GPU)
```

---

## Точка входа

### HTTP Server

```
http://localhost:8000/tc
http://localhost:8000/docs      # OpenAPI документация
```

### Командная строка

```bash
# Запуск через main.py
python -m apps.windows.main

# С параметрами
python -m apps.windows.main --host 127.0.0.1 --port 8000
```

### Телеметрия research server

```bash
# Запуск исследовательского сервера
python -m apps.windows.telemetry_research.main

# Доступен по
http://localhost:8090/
```

---

## API Endpoints

### Dashboard (GET только)

| Endpoint | Описание |
|----------|----------|
| `GET /api/windows/dashboard/snapshot` | Последний снепшот системы (CPU, RAM, GPU, Disks) |
| `GET /api/windows/dashboard/sensors` | Последние значения всех сенсоров |
| `GET /api/windows/dashboard/processes` | Список процессов из последнего снепшота |
| `GET /api/windows/dashboard/history` | История системных срезов |
| `GET /api/windows/dashboard/sensor-history` | История показаний датчика |
| `GET /api/windows/dashboard/events` | События телеметрии |
| `GET /api/windows/dashboard/process-stats` | Агрегированная статистика процессов |

### Windows Diagnostics (GET только)

| Endpoint | Описание |
|----------|----------|
| `GET /api/windows/health` | Health Score системы |
| `GET /api/windows/audit/full` | Полный глубокий аудит (15 доменов) |
| `GET /api/windows/audit/performance` | Аудит производительности |
| `GET /api/windows/audit/drivers` | Аудит драйверов |
| `GET /api/windows/audit/software` | Инвентарь программ |
| `GET /api/windows/defender/status` | Статус Microsoft Defender |
| `GET /api/windows/defender/threats` | История обнаружений |
| `GET /api/windows/hardware/monitor` | Полный снепшот оборудования |
| `GET /api/windows/hardware/sensors` | Список датчиков |
| `GET /api/windows/hardware/smart` | S.M.A.R.T. данные дисков |
| `GET /api/windows/hardware/gpu` | Телеметрия GPU |

### Заглушки POST (запись невозможна)

| Endpoint | Статус |
|----------|--------|
| `POST /api/windows/investigate` | Заглушка, используйте GET /api/windows/audit/full |
| `POST /api/windows/actions/execute` | Заглушка, все операции read-only |
| `POST /api/windows/defender/scan` | Заглушка, используйте GET /api/windows/defender/status |

---

## Веб-интерфейс

### Точки входа

- **Main**: `http://localhost/tc`
- **API Docs**: `http://localhost/docs`

### Доступные вкладки (42 таба)

**Основные:**
- 💬 Чат (`tab-chat`)
- 🧠 RAG (`tab-rag`)
- 📰 Новости (`tab-news`)
- ⚙️ Управление (`tab-admin`)
- 📚 Справочник (`tab-help`)

**Диагностика и форензика:**
- 🔍 Утечки и микрофризы (`tab-process-leaks`)
- ⏱️ Поведенческая форензика (`tab-forensics`)
- ⚡ Качество ядра и Троттлинг (`tab-throttling`)
- 💽 Износ дисков и батареи (`tab-storage-wear`)
- 🔌 Сеть и периферия (`tab-peripherals`)
- 📜 Логи операционной системы (`tab-system-logs`)

**Системные:**
- ℹ️ О системе (`tab-about-system`)
- 🧩 Управление плагинами (`tab-plugins`)
- 🔬 Исследование телеметрии (`tab-telemetry-research`)
- 💻 Мониторинг оборудования (`tab-hardware-monitor`)
- и др. (всего 42)

---

## Телеметрия

### База данных

**telemetry.db** находится по пути:
```
%APPDATA%\AI-Breadboard\apps\windows\telemetry\logs\telemetry.db
```

### Таблицы

| Таблица | Описание |
|---------|----------|
| `system_snapshots` | Системные снапшоты (CPU, RAM, GPU, Disks) |
| `process_snapshots` | Снимки процессов с CPU/memory |
| `sensor_polls` | Показания датчиков (температура, напряжение и т.д.) |
| `telemetry_events` | События телеметрии |
| `hardware_audits` | Аудиты оборудования |
| `process_rollups_2min` | Роллапы процессов за 2 минуты |
| `process_rollups_daily` | Суточные агрегации процессов |
| `process_outliers` | Выбросы по процессам |

### Сбор сенсоров (WMI)

- **CPU**: загрузка, температура, частота
- **RAM**: использование, swap
- **GPU**: загрузка, температура, VRAM
- **Storage**: S.M.A.R.T., температура, износ
- **Network**: throughput, пакеты, ошибки
- **Internet**: ping, download/upload speed

---

## Диагностика

### Автоматические проверки

1. **Hardware Audit** — драйверы, устройства PnP, DriverStore
2. **Software Audit** — инвентарь программ, запуски
3. **Security Audit** — Defender, UAC, персистентность
4. **Integrity Audit** — SFC, DISM, Servicing
5. **Storage Audit** — диски, тома, свободное место
6. **Network Audit** — соединения, порты
7. **Process Audit** — запущенные процессы
8. **Service Audit** — служба Windows
9. **Task Audit** — задачи Планировщика

### Health Score

Система вычисляет Health Score (0-100) на основе:
- Состояния драйверов
- Наличия обновлений
- Свободного места на диске
- Использования RAM
- Температурных показателей
- Наличия проблем с оборудованием

---

## Запуск

### Продакшн

```bash
# Запуск основного сервера
python -m apps.windows.main

# С SSL
python -m apps.windows.main --ssl

# С автоперезагрузкой
python -m apps.windows.main --reload
```

### Dev

```bash
# Запуск telemetry collector
python -m apps.windows.telemetry

# Запуск исследовательского сервера
python -m apps.windows.telemetry_research.main --port 8090
```

---

## Устранение неполадок

### Сервер не запускается

```bash
# Проверка зависимостей
pip install fastapi uvicorn python-dotenv

# Проверка порта
netstat -ano | findstr :8000
```

### Данные не собираются

```bash
# Проверка telemetry.db
python -m apps.windows.telemetry

# Проверка прав администратора
# Для некоторых данных требуются права администратора
```

### Веб-интерфейс не загружается

```bash
# Очистка кеша браузера
Ctrl+Shift+Delete (Chrome)

# Проверка статических файлов
ls -la apps/windows/api/webgui/
```

---

## 🔧 Настройка

### Конфигурация

Файл: `apps/windows/config.json`

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "protocol": "http"
  },
  "apps": {
    "enabled": ["hardware_monitor", "telemetry", "defender"],
    "disabled": ["trading_terminal", "website_monitor"]
  },
  "telemetry": {
    "poll_interval_seconds": 5,
    "buffer_mode": "memory",
    "buffer_size": 50
  }
}
```

---

## 📝 Примечания

- Все данные берутся из `telemetry.db` только через GET-эндпоинты
- POST-запросы возвращают заглушки с указанием использования GET
- LHM (LibreHardwareMonitor) полностью удален из кода
- Используются нативные Windows WMI API
- Веб-интерфейс обновляется каждые 5 секунд (настраивается)

---

**Версия**: 1.0 (FastAPI Foundry Edition)  
**Последнее обновление**: Октябрь 2026  
**Статус**: ✅ Production Ready
