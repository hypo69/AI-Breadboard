# 🌐 Network Terminal

Интерактивный инструмент для глубокого анализа сетевого трафика, мониторинга пакетов в реальном времени, статистики трафика, анализа протоколов и обнаружения аномалий с помощью AI.

## 📋 Оглавление
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Использование](#использование)
- [FastAPI endpoints](#fastapi-endpoints)
- [Конфигурация](#конфигурация)

---

## Возможности

- **Deep Packet Inspection** — детальный анализ сетевых пакетов в реальном времени
- **Live Traffic Monitor** — отображение потока пакетов в терминале
- **Traffic Statistics** — расчёт скорости, объёма, распределения протоколов
- **AI Security Detection** — обнаружение аномалий и угроз с помощью TShark
- **FastAPI REST API** — программный доступ к сетевым данным

---

## Архитектура

```
apps/network_terminal/
├── tui.py                # TUI-рендерер и цикл захвата пакетов
├── router.py             # FastAPI endpoints для REST API
├── __main__.py           # Точка входа (CLI + standalone server)
├── __init__.py           # Экспорт пакета
└── config.json           # Конфигурация сервера (порт 8101)
```

**Разделение ответственности:**
- `tui.py` — TUI-рендеринг, управление состоянием (`NetworkTerminalState`)
- `router.py` — FastAPI HTTP-роутеры и обработчики запросов
- `__main__.py` — CLI-интерфейс и запуск standalone-сервера

---

## Установка

```bash
cd apps/network_terminal
pip install -r ../../requirements.txt
pip install rich  # Для TUI-интерфейса
```

**Требуется TShark** для захвата реального сетевого трафика:
- Установите [Wireshark](https://www.wireshark.org/)
- Или установите TShark отдельно

---

## Использование

### Интерактивный dashboard (TUI)

```bash
python -m apps.network_terminal --interface 1 --filter "tcp port 80"
```

Аргументы:
- `--interface` — номер или имя сетевого интерфейса (по умолчанию: 1)
- `--filter` — фильтр Wireshark (например, `tcp port 80`, `http`, `tls`)
- `--simulate` — запуск в режиме симуляции без TShark

Клавиши управления:
- `Ctrl+C` — остановка и выход

### FastAPI сервер

```bash
python -m apps.network_terminal --mode server
```

По умолчанию сервер запускается на `http://127.0.0.1:8101`.

### CLI-команды

```bash
# Список доступных интерфейсов
python -m apps.network_terminal --list-interfaces

# Режим симуляции (без TShark)
python -m apps.network_terminal --simulate
```

---

## FastAPI endpoints

### `GET /api/network/status`

```json
{
  "interface": "1",
  "filter": "",
  "total_packets": 1234,
  "total_bytes": 567890,
  "protocol_counts": {"TCP": 800, "UDP": 400, "TLS": 34},
  "latest_ai_report": null,
  "latest_heuristics": []
}
```

### `GET /api/network/packets`

```json
{
  "packets": [
    {
      "packet_number": 1,
      "timestamp": "2024-01-15T10:30:00Z",
      "source": "192.168.1.15",
      "destination": "142.250.180.206",
      "protocol": "TCP",
      "length": 128,
      "source_port": 443,
      "destination_port": 52000,
      "info": "HTTP/1.1 200 OK"
    }
  ]
}
```

### `GET /api/network/stats`

```json
{
  "total_packets": 1234,
  "total_bytes": 567890,
  "avg_packet_size": 460.2,
  "avg_bps": 4523.5,
  "avg_pps": 12.3,
  "top_protocols": ["TCP", "UDP", "TLS"],
  "top_sources": ["192.168.1.15"],
  "top_destinations": ["142.250.180.206"]
}
```

### `GET /api/network/security`

```json
{
  "heuristics": ["Multiple connection attempts to single port"],
  "ai_report": null
}
```

---

## Конфигурация

Файл `config.json`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8101,
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
