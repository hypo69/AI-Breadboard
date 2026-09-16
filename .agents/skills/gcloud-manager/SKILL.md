---
name: gcloud-manager
description: Google Cloud observability and monitor toolkit
description_i18n:
  en: Google Cloud observability and monitor toolkit
  ru: Инструментарий для наблюдаемости и мониторинга Google Cloud
---

# Навык: GCloud Manager

## 🎯 Назначение
Навык `gcloud-manager` обеспечивает взаимодействие с монитором Google Cloud (`apps/gcloud_monitor`). Предназначен для анализа логов, метрик мониторинга, аудита безопасности IAM и диагностики инцидентов в инфраструктуре GCP.

## 🚀 Протокол выполнения
1. **Активация**: Навык активируется при запросах на проверку метрик, анализ логов или диагностику ошибок в облачной среде.
2. **Взаимодействие**: Навык использует API монитора (по умолчанию `http://localhost:8106/api/gcloud/*`).
3. **Безопасность**: Доступ к данным мониторинга и аудита требует настроенных учетных данных GCP.

## 🛠️ Основные команды
- `query_logs`: Выполнение запросов к Cloud Logging.
- `get_metrics`: Получение данных из Cloud Monitoring.
- `audit_security`: Запуск инспекции безопасности IAM.
- `diagnose_issue`: AI-диагностика причин инцидента.

## ⚠️ Важное замечание
Навык требует настроенного окружения GCP (Service Account или OAuth) и запущенного `gcloud_monitor`.
