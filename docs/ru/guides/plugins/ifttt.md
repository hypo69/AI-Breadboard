# Плагин IFTTT Smart Home (ifttt)

## Назначение
Подключает AI Breadboard к сервису IFTTT Webhooks, позволяя автоматизировать умный дом, управлять бытовыми приборами и настраивать уведомления безопасности.

## Структура
- `plugins/user-plugins/ifttt/`

## Запуск
Конфигурация через `.env` (`IFTTT_WEBHOOK_KEY`) или `config.json`.

## API
- `trigger_ifttt_event`: Инструмент для отправки событий.
- Административные действия: `test_connection`, `trigger_event`.
