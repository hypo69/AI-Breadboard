# 🐛 AI Responder DEBUG - Полное руководство по отладке

## 📋 Что это за версия?

Это специальная DEBUG версия плагина с **МАКСИМАЛЬНО ПОДРОБНЫМ** логированием всех операций.

### Отличия от обычной версии:

| Обычная версия                           | DEBUG версия                                    |
| ----------------------------------------------------- | ----------------------------------------------------- |
| Минимальные логи                       | Подробные логи ВСЕХ операций |
| Логи только в error_log                    | Логи в файл + error_log                      |
| Нет интерфейса для просмотра | Встроенный просмотр логов      |
| Нет тестирования API                   | Встроенный тест Gemini                  |

## 🚀 Установка DEBUG версии

### Шаг 1: Загрузка файлов

```bash
/wp-content/plugins/ai-responder-debug/
├── ai-responder-debug.php     # DEBUG версия плагина
├── GEMINI.md                  # Файл с промптами
└── ai-responder-debug.log     # Файл логов (создается автоматически)
```

### Шаг 2: Активация

1. В админке WordPress: **Плагины → Установленные**
2. Найдите **AI Responder DEBUG - Full Logging**
3. Нажмите **Активировать**

### Шаг 3: Настройка

1. Перейдите: **Настройки → AI Responder DEBUG**
2. Заполните настройки:
   * ✅ Включить автоответы
   * 🔑 Gemini API Key
   * ✅ Автоодобрение (опционально)
   * ⏱️ Задержка (опционально)

## 📊 Где смотреть логи?

### Способ 1: В админке WordPress

1. **Настройки → AI Responder DEBUG**
2. Прокрутите вниз до раздела **"📜 Просмотр логов"**
3. Вы увидите содержимое лог-файла в реальном времени

### Способ 2: Через файл

```bash
# Путь к файлу логов
/wp-content/plugins/ai-responder-debug/ai-responder-debug.log

# Просмотр в реальном времени
tail -f /wp-content/plugins/ai-responder-debug/ai-responder-debug.log

# Последние 100 строк
tail -n 100 /wp-content/plugins/ai-responder-debug/ai-responder-debug.log

# Поиск ошибок
grep "❌" /wp-content/plugins/ai-responder-debug/ai-responder-debug.log
```

### Способ 3: Через WordPress error_log

```bash
# Стандартный лог WordPress
tail -f /wp-content/debug.log

# Фильтр по AIResponder
tail -f /wp-content/debug.log | grep AIResponder
```

### Способ 4: На странице сайта (shortcode)

Добавьте на любую страницу:

```
[ai_responder_logs lines="50"]
```

Покажет последние 50 строк лога (доступно только администраторам).

## 🧪 Тестирование подключения

### В админке

1. **Настройки → AI Responder DEBUG**
2. Найдите раздел **"🧪 Тест подключения к Gemini"**
3. Нажмите **"▶️ Запустить тест"**
4. Результат появится ниже кнопки

### Вручную через curl

```bash
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Test connection. Reply with: Connection OK"
      }]
    }]
  }'
```

## 📝 Что логируется?

### 1. Инициализация плагина

```
========================================
AI RESPONDER DEBUG STARTED
========================================
Time: 2025-10-09 15:30:00
PHP Version: 8.1.0
WordPress Version: 6.3.0
Settings loaded:
Array
(
    [enabled] => 1
    [gemini_api_key] => AIza***...
    [auto_approve] => 1
    [reply_delay] => 0
    [debug_mode] => 1
)
Prompt file path: /var/www/.../GEMINI.md
Prompt file exists: YES
Constructor completed. Hooks registered.
========================================
```

### 2. Получение нового комментария

```
==================================================
NEW COMMENT RECEIVED
==================================================
Comment ID: 123
Approved status: 1
Comment data:
Array
(
    [comment_author] => Иван Петров
    [comment_content] => Отличная статья!
    ...
)
✓ Plugin is ENABLED
✓ Gemini API key is SET (length: 39)
✓ Comment is APPROVED

🚀 Starting comment processing...
```

### 3. Обработка комментария

```
--- STEP 1: Get comment data ---
✓ Comment found:
  - ID: 123
  - Author: Иван Петров
  - Email: ivan@example.com
  - Post ID: 456
  - Parent: 0
  - Content: Отличная статья! Подскажите...
  - Content length: 85

--- STEP 2: Get post content ---
Getting post 456...
✓ Post retrieved:
  - Title: Как настроить WordPress
  - Content length: 5420
  - Excerpt length: 150

--- STEP 3: Get comment thread ---
Building comment thread for 123...
  Thread iteration 1:
    - Comment ID: 123
    - Author: Иван Петров
    - Parent: 0
✓ Thread built: 1 comments
```

### 4. Чтение промпта

```
--- STEP 4: Generate reply with Gemini ---
==================================================
GEMINI API CALL
==================================================
Reading prompt from GEMINI.md...
✓ File found, size: 2048 bytes
✓ File read, content length: 2048
Looking for ```text block...
✓ Prompt extracted from markdown
Prompt length: 1850
Prompt preview:
Ты — помощник на сайте, который отвечает...
```

### 5. Формирование запроса

```
Thread text length: 150
Filling prompt template...
Template length: 1850
Variables: post_title, post_excerpt, comment_thread, comment_author, comment_content
  {POST_TITLE} => 28 chars
  {POST_EXCERPT} => 150 chars
  {COMMENT_THREAD} => 150 chars
  {COMMENT_AUTHOR} => 12 chars
  {COMMENT_CONTENT} => 85 chars
✓ Template filled, result length: 2200

📝 FINAL PROMPT:
--------------------------------------------------
Ты — помощник на сайте, который отвечает на комментарии читателей.

Контекст статьи:
Заголовок: Как настроить WordPress
...
--------------------------------------------------
```

### 6. Запрос к Gemini API

```
📦 PAYLOAD:
Size: 2500 bytes
{"contents":[{"parts":[{"text":"Ты — помощник..."}]}]}

🌐 API CALL:
URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIza***...
Method: POST
Timeout: 60s
Starting request...
Request completed in 1234.56ms
✓ No WP errors

📊 HTTP RESPONSE:
Status code: 200
Headers:
  content-type: application/json
  ...

Response body length: 856
Response body:
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Спасибо за ваш вопрос!..."
          }
        ]
      }
    }
  ]
}
```

### 7. Парсинг ответа

```
🔍 PARSING JSON...
✓ JSON parsed successfully
Parsed structure:
Array
(
    [candidates] => Array
        (
            [0] => Array
                (
                    [content] => Array
                    ...
                )
        )
)

✅ REPLY EXTRACTED:
Length: 450
--------------------------------------------------
Спасибо за ваш вопрос! Рад, что статья вам понравилась.

Для более детального изучения WordPress, я рекомендую...
--------------------------------------------------
```

### 8. Публикация ответа

```
--- STEP 5: Post reply ---
==================================================
POSTING REPLY
==================================================
Comment data prepared:
Array
(
    [comment_post_ID] => 456
    [comment_parent] => 123
    [comment_content] => Спасибо за ваш вопрос!...
    [comment_author] => My Blog (AI)
    ...
)

Inserting comment...
✅ SUCCESS: Comment inserted with ID: 124

==================================================
COMMENT PROCESSING COMPLETED
==================================================
```

## 🔍 Типичные проблемы и их решения

### Проблема 1: "Ничего не происходит"

**Проверьте лог на наличие:**

```bash
grep "NEW COMMENT RECEIVED" ai-responder-debug.log
```

**Если НЕТ:**

* Плагин не получает события комментариев
* Проверьте, активирован ли плагин
* Проверьте хуки WordPress

**Если ЕСТЬ, но дальше:**

```
❌ Plugin is DISABLED in settings
```

* Включите плагин в настройках

### Проблема 2: "API ключ не работает"

**В логе ищите:**

```bash
grep "API" ai-responder-debug.log
```

**Возможные ошибки:**

```
❌ Gemini API key is EMPTY
```

→ Добавьте API ключ в настройках

```
Status code: 401
```

→ API ключ неверный

```
Status code: 429
```

→ Превышен лимит запросов

### Проблема 3: "Файл GEMINI.md не читается"

**В логе:**

```
❌ File NOT FOUND: /path/to/GEMINI.md
```

**Решение:**

```bash
# Проверьте наличие файла
ls -la /wp-content/plugins/ai-responder-debug/GEMINI.md

# Если нет - создайте
touch /wp-content/plugins/ai-responder-debug/GEMINI.md

# Установите права
chmod 644 /wp-content/plugins/ai-responder-debug/GEMINI.md
```

### Проблема 4: "JSON parse error"

**В логе:**

```
❌ JSON PARSE ERROR:
Error: Syntax error
```

**Причины:**

* Gemini вернул некорректный JSON
* Ответ слишком большой
* Ответ содержит спецсимволы

**Решение:**

* Проверьте `Response body:` в логе
* Упростите промпт
* Уменьшите размер контекста

### Проблема 5: "Ответ не публикуется"

**В логе:**

```
❌ FAILED: wp_insert_comment returned false
```

**Причины:**

* Нет прав на создание комментариев
* Антиспам блокирует
* База данных недоступна

**Решение:**

```php
// Проверьте права
// В wp-config.php временно добавьте:
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);

// Проверьте /wp-content/debug.log
```

## 📈 Мониторинг производительности

### Время выполнения

В логе ищите:

```
Request completed in 1234.56ms
```

**Нормальные значения:**

* < 2000ms - отлично
* 2000-5000ms - нормально
* > 5000ms - медленно
  >

### Размер промптов

```
Prompt length: 2200
```

**Рекомендации:**

* < 4000 символов - оптимально
* 4000-8000 - приемлемо
* > 8000 - слишком большой
  >

## 🛠️ Полезные команды

### Мониторинг в реальном времени

```bash
# Следить за логом
tail -f ai-responder-debug.log

# Только ошибки
tail -f ai-responder-debug.log | grep "❌"

# Только успехи
tail -f ai-responder-debug.log | grep "✅"

# Время запросов
tail -f ai-responder-debug.log | grep "completed in"
```

### Анализ логов

```bash
# Сколько комментариев обработано
grep -c "NEW COMMENT RECEIVED" ai-responder-debug.log

# Сколько успешно
grep -c "SUCCESS: Comment inserted" ai-responder-debug.log

# Сколько ошибок
grep -c "❌" ai-responder-debug.log

# Среднее время запросов
grep "completed in" ai-responder-debug.log | awk '{print $NF}' | sed 's/ms//' | awk '{s+=$1; n++} END {print s/n "ms"}'
```

### Очистка и ротация

```bash
# Очистить лог
> ai-responder-debug.log

# Архивировать старый лог
mv ai-responder-debug.log ai-responder-debug-$(date +%Y%m%d).log
touch ai-responder-debug.log

# Автоматическая ротация (добавить в cron)
find /wp-content/plugins/ai-responder-debug/ -name "*.log" -mtime +7 -delete
```

## 📞 Поддержка

Если проблема не решается:

1. **Скопируйте последние 200 строк лога:**
   ```bash
   tail -n 200 ai-responder-debug.log > debug-report.txt
   ```
2. **Добавьте информацию о системе:**
   ```bash
   echo "PHP: $(php -v)" >> debug-report.txt
   echo "WordPress: $(wp core version)" >> debug-report.txt
   ```
3. **Отправьте файл** на support@your-domain.com

---

**Важно:** DEBUG версия создает большие логи. Не используйте её на продакшене постоянно!
