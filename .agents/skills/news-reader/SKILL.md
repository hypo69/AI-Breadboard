---
name: news-reader
description: Intelligent personal news assistant and digest generator. Retrieves highly relevant personalized news feeds, filters by learned user interest profiles, generates AI digests, and adapts weights based on user feedback.
description_i18n:
  en: Intelligent personal news assistant and digest generator. Retrieves highly relevant personalized news feeds, filters by learned user interest profiles, generates AI digests, and adapts weights based on user feedback.
  ru: Интеллектуальный ассистент новостей и генератор дайджестов. Получает персонализированные релевантные новости, фильтрует по обучаемому профилю интересов, формирует ИИ-дайджесты и адаптирует веса на основе фидбека.
---

# 📰 News Reader Skill (Интеллектуальный новостной ассистент)

Навык для сбора, адаптивной фильтрации и суммаризации актуальных новостей под профиль конкретного пользователя с помощью движка `plugins/news_feed`.

---

## 🎯 Назначение и Сценарии применения

1. **Получение персональной ленты новостей**: Запрос только тех новостей, которые соответствуют интересам пользователя и имеют высокий match score.
2. **Формирование ИИ-дайджеста (Morning/Evening Digest)**: Синтез краткого резюме по главным событиям дня в сфере IT, ИИ, науки и мировых трендов.
3. **Обучение профиля пользователя**: Фиксация положительных (👍, закладки) и отрицательных (👎, скрытие) сигналов для переобучения весов тем.
4. **Управление темами и стоп-словами**: Настройка приоритетных тем и черных списков нежелательных категорий.

---

## 🚀 Протокол выполнения (Шаги для Агента)

При запросе пользователя предоставить новости или дайджест:

1. **Сгенерировать дайджест новостей**:
   ```powershell
   python skills/news-reader/scripts/news_cli.py digest --user-id default
   ```

2. **Получить персонализированный список топ-новостей**:
   ```powershell
   python skills/news-reader/scripts/news_cli.py feed --limit 5
   ```

3. **Отправить реакцию/обратную связь (обучение)**:
   ```powershell
   python skills/news-reader/scripts/news_cli.py feedback --article-id "art_id" --action like --title "Заголовок статьи" --category ai
   ```

4. **Просмотреть профиль выученных интересов**:
   ```powershell
   python skills/news-reader/scripts/news_cli.py profile
   ```

---

## 🛠️ Доступные CLI-параметры `scripts/news_cli.py`

| Команда | Описание |
|---|---|
| `feed [--limit N] [--refresh]` | Вывод ленты релевантных новостей |
| `digest [--user-id ID]` | Генерация структурированного ИИ-дайджеста |
| `profile` | Просмотр профиля интересов и накопленных весов |
| `feedback --article-id ID --action ACTION` | Обучение алгоритма (`like`, `dislike`, `bookmark`, `hide`) |
| `set-topics --preferred "ai, python" --ignored "gossip"` | Обновление ключевых тем и стоп-слов |
