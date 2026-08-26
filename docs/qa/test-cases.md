# Тест-кейсы

## AI модуль

### test_ai.py

| ID | Тест | Описание | Ожидаемый результат |
|----|------|----------|---------------------|
| TC-AI-001 | test_chat_with_mock | Тест метода chat с моком | Метод возвращает response |
| TC-AI-002 | test_chat_stream_with_mock | Тест метода chat_stream | Генератор выдает chunks |
| TC-AI-003 | test_ask_with_mock | Тест метода ask | Метод возвращает answer |
| TC-AI-004 | test_build_dev_rag | Тест построения dev RAG | RAG строится без ошибок |
| TC-AI-005 | test_rag_search_tool | Тест функции rag_search_tool | Возвращает результат поиска |
| TC-AI-006 | test_foundry_chat_initialization | Тест инициализации FoundryChatBase | Клиент инициализирован |

## FastAPI модуль

### test_fastapi.py

| ID | Тест | Описание | Ожидаемый результат |
|----|------|----------|---------------------|
| TC-FA-001 | test_create_jwt_token | Тест создания JWT токена | Токен генерируется |
| TC-FA-002 | test_verify_jwt_token | Тест верификации JWT | Токен валиден |
| TC-FA-003 | test_verify_jwt_token_invalid | Тест невалидного токена | Возвращает None |
| TC-FA-004 | test_init_router | Тест инициализации чат-роутера | Роутер создан |
| TC-FA-005 | test_get_media_files | Тест получения медиафайлов | Возвращает список файлов |
| TC-FA-006 | test_post_media_by_title | Тест поиска по названию | Возвращает найденный файл |
| TC-FA-007 | test_get_torrents | Тест получения торрента | Возвращает список торрентов |

## TTS модуль

### test_tts.py

| ID | Тест | Описание | Ожидаемый результат |
|----|------|----------|---------------------|
| TC-TTS-001 | test_synthesize_edge | Тест синтеза edge-tts | Функция существует |
| TC-TTS-002 | test_synthesize_gtts | Тест синтеза gtts | Функция существует |
| TC-TTS-003 | test_get_silero_model | Тест загрузки модели Silero | Модель загружена |
| TC-TTS-004 | test_synthesize_speech | Тест синтеза речи | Генерируется аудио |

## User Manager

### test_user_manager.py

| ID | Тест | Описание | Ожидаемый результат |
|----|------|----------|---------------------|
| TC-UM-001 | test_get_profile_path | Тест пути к профилю | Путь сгенерирован |
| TC-UM-002 | test_default_profile_structure | Тест структуры профиля | Структура валидна |
| TC-UM-003 | test_load_user_profile | Тест загрузки профиля | Профиль загружен |
| TC-UM-004 | test_save_user_profile | Тест сохранения профиля | Профиль сохранен |
| TC-UM-005 | test_add_user | Тест добавления пользователя | Пользователь добавлен |
| TC-UM-006 | test_get_user_by_id | Тест получения по ID | Пользователь найден |

## Logger

### test_logger.py

| ID | Тест | Описание | Ожидаемый результат |
|----|------|----------|---------------------|
| TC-LG-001 | test_format | Тест форматирования лога | JSON лог сгенерирован |
| TC-LG-002 | test_logger_singleton | Тест синглтона логера | Один инстанс |
| TC-LG-003 | test_logger_methods | Тест методов логера | Методы существуют |

## Плагины

### test_plugins.py

| ID | Тест | Описание | Ожидаемый результат |
|----|------|----------|---------------------|
| TC-PL-001 | test_media_organizer_handle | Тест media_organizer | Обработка сообщения |
| TC-PL-002 | test_qbittorrent_client_init | Тест qBittorrentClient | Клиент инициализирован |
| TC-PL-003 | test_torrents_list | Тест списка торрентов | Возвращает список |
| TC-PL-004 | test_rag_is_media_query | Тест определения медиа запроса | Возвращает True |
| TC-PL-005 | test_telegram_handle | Тест telegram бота | Обработка сообщения |

---

[← Стратегия](testing-strategy.md) | [Чеклист QA →](qa-checklist.md)