# Модуль `scripts/maintenance` — Системное обслуживание

## Назначение
Утилиты для регламентного технического обслуживания, управления сертификатами и поддержания поисковых индексов:

| Скрипт | Назначение | Использование |
|---|---|---|
| [`analyze_logs.py`](analyze_logs.py) | Сканирование файлов логов на наличие повторяющихся ошибок, предупреждений и сбоев API. | `python scripts/maintenance/analyze_logs.py` |
| [`generate_ssl_certs.py`](generate_ssl_certs.py) | Автоматическая генерация самоподписанных SSL-сертификатов для локального HTTPS-сервера. | `python scripts/maintenance/generate_ssl_certs.py` |
| [`rebuild_dev_rag.py`](rebuild_dev_rag.py) | Перестроение технического RAG-индекса кодовой базы для контекстной помощи агентов. | `python scripts/maintenance/rebuild_dev_rag.py` |
