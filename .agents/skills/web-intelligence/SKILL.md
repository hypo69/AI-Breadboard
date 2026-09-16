---
name: web-intelligence
description: Website intelligence, GA4/GSC monitoring and observability toolkit
description_i18n:
  en: Website intelligence, GA4/GSC monitoring and observability toolkit
  ru: Инструментарий для веб-аналитики, мониторинга GA4/GSC и наблюдаемости
---

# Навык: Web Intelligence

## 🎯 Назначение
Навык `web-intelligence` обеспечивает взаимодействие с монитором веб-сайтов (`apps/website_monitor`). Предназначен для получения данных из GA4/GSC, анализа доступности веб-ресурсов, мониторинга ошибок (404/5xx) и AI-диагностики причин отклонений.

## 🚀 Протокол выполнения
1. **Активация**: Навык активируется при запросах на аналитику трафика, проверку доступности сайта или диагностику SEO-показателей.
2. **Взаимодействие**: Навык использует API монитора (по умолчанию `http://localhost:8107/api/v1/website-monitor/*`).
3. **Безопасность**: Требуется авторизация в Google Analytics/Search Console для доступа к данным.

## 🛠️ Основные команды
- `get_traffic_stats`: Получение данных GA4 (трафик, каналы).
- `get_seo_metrics`: Получение данных GSC (CTR, позиции).
- `check_availability`: Проверка доступности и времени отклика сайта.
- `diagnose_root_cause`: AI-диагностика отклонений в метриках.

## ⚠️ Важное замечание
Навык требует настроенных учетных данных Google и запущенного `website_monitor`.
