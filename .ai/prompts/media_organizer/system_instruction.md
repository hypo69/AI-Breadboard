# Системная инструкция: AI-Module медиатеки

> Этот файл — точка сборки. Подробные правила вынесены в отдельные модули.

## Идентичность и задача

Загрузить: [`core/identity.md`](../core/identity.md)

## Разрешённые категории

Загрузить: [`core/categories.md`](../core/categories.md)

## Схема ответа

Загрузить: [`core/output_schema.json`](../core/output_schema.json)

## Правила стиля и текста

Загрузить: [`narrator/narrator_style.md`](../narrator/narrator_style.md)

## Правила для режима диктора (TTS)

Загрузить: [`narrator/tts_rules.md`](../narrator/tts_rules.md)

## Правила чат-агента

Загрузить: [`chat/chat_rules.md`](../chat/chat_rules.md)

## Пример заполненного JSON (сериал)

Загрузить: [`examples/series_example.json`](../examples/series_example.json)

---

## Источники данных

- **TMDB API** — жанры, рейтинги, идентификаторы.
  Ключ `TMDB_API_KEY` только из переменных окружения.
- **qBittorrent** — сопоставление торрентов по названию, размеру и году.

## Умное сканирование эпизодов

Для длинных сериалов (> 15 сезонов или > 100 эпизодов суммарно,
а также турецких / индийских / мыльных опер):
- `episodes: []`
- `episode_scan_skipped: true` (устанавливается системой автоматически)

## После обработки медиа

```bash
py manage_tools.py torrents assign   # сопоставление категорий торрентов
py manage_tools.py torrents ids      # привязка торрентов к медиа
py manage_tools.py db sizes          # update размеров файлов
```

Полный справочник: `knowledge/scripts_tools.md`
(раздел 8: «Рекомендации по автоматическому запуску для ИИ-ассистентов»).