# Руководство по интеграционному тестированию

## Обзор

Интеграционное тестирование проверяет взаимодействие между модулями и компонентами системы.

## Сценарии интеграционного тестирования

### 1. Цепочка "Пользователь -> Chat -> AI -> Plugin -> Response"

```
Пользователь вводит сообщение
    ↓
Chat API получает запрос
    ↓
Плагины проверяют сообщение
    ↓
Если медиа запрос → RAG Plugin ищет в БД
    ↓
AI формирует ответ
    ↓
Ответ возвращается пользователю
```

**Тест-кейс: TC-INT-001**
```python
def test_chat_media_query():
    # 1. Пользователь ищет фильм
    response = client.post('/api/chat', json={
        'message': 'Фильмы про войну 2024'
    })
    
    # 2. Плагин RAG должен обработать запрос
    assert response.status_code == 200
    
    # 3. Ответ должен содержать рекомендации
    assert 'фильмы' in response.json().lower() or 'рекомендую' in response.json().lower()
```

### 2. Цепочка "Media Scanner -> TMDB API -> Database"

```
Сканирование диска
    ↓
Поиск медиафайлов
    ↓
Запрос TMDB API для метаданных
    ↓
Сохранение в БД
```

**Тест-кейс: TC-INT-002**
```python
def test_media_scan_workflow():
    # 1. Запуск сканирования
    response = client.post('/api/media-admin/scan', json={
        'disk': '1',
        'paths': ['E:']
    })
    
    # 2. Проверка статуса
    assert response.status_code == 200
    
    # 3. Получение результата
    status = client.get('/api/media-admin/scan/status')
    assert status.json()['status'] == 'completed'
```

### 3. Цепочка "Torrent Download -> qBittorrent -> Database"

```
Пользователь скачивает торрент
    ↓
Playwright ищет торрент файл
    ↓
Скачивание через qBittorrent
    ↓
Назначение категории
```

**Тест-кейс: TC-INT-003**
```python
def test_torrent_download_workflow():
    # 1. Скачивание торрента
    response = client.post('/api/torrents/download', json={
        'url': 'magnet:?xt=urn:btih:test',
        'title': 'Test Movie'
    })
    
    # 2. Проверка успешности
    assert response.status_code == 200
    assert response.json()['ok'] == True
```

## Тестирование базы данных

### CRUD операции

**TC-INT-DB-001: Создание записи**
```python
def test_db_create_record():
    record = db.add_record({
        'title': 'Test Movie',
        'type': 'movie',
        'path': 'E:/Test.mkv'
    })
    assert record > 0
```

**TC-INT-DB-002: Чтение записей**
```python
def test_db_read_records():
    records = db.export_all()
    assert isinstance(records, list)
```

**TC-INT-DB-003: Обновление записи**
```python
def test_db_update_record():
    updated = db.update_record(1, {'title': 'Updated Title'})
    assert updated == True
```

**TC-INT-DB-004: Удаление записи**
```python
def test_db_delete_record():
    deleted = db.delete_record(1)
    assert deleted == True
```

## Тестирование плагинов

### Загрузка плагинов

**TC-INT-PL-001: Загрузка всех плагинов**
```python
def test_load_all_plugins():
    plugins = load_plugins(model)
    assert len(plugins) > 0
    assert 'rag' in plugins
    assert 'media_organizer' in plugins
```

### Обработка сообщений

**TC-INT-PL-002: Обработка медиа запроса**
```python
def test_plugin_media_query():
    result = await plugins['rag']._handle('Фильмы про войну')
    assert result is not None
```

## Тестирование внешних API

### TMDB API

**TC-INT-TMDB-001: Поиск фильма**
```python
def test_tmdb_search_movie():
    client = TMDBClient(tmdb_api_key)
    result = client.search_movie('Titanic')
    assert result is not None
    assert len(result) > 0
```

### Gemini API

**TC-INT-GEM-001: Генерация текста**
```python
def test_gemini_generate_text():
    ai = GoogleGenerativeAI(api_key='test_key')
    result = await ai.ask('Напиши короткое описание')
    assert result is not None
```

### RAG Поиск

**TC-INT-RAG-001: Векторный поиск**
```python
def test_rag_vector_search():
    rag = build_media_rag('test_key')
    results = rag.search('фильмы про войну', top_k=5)
    assert len(results) > 0
```

## Тестирование WebSocket

### Подключение

**TC-INT-WS-001: Успешное подключение**
```python
async def test_websocket_connect():
    async with websockets.connect('ws://localhost:3000/api/control/ws?role=remote') as ws:
        assert ws.open == True
```

### Отправка команд

**TC-INT-WS-002: Команда play**
```python
async def test_websocket_play():
    await ws.send(json.dumps({'event': 'play', 'file': '/test.mp4'}))
    response = await ws.recv()
    assert 'status' in json.loads(response)
```

## Тестирование ошибок

### Обработка ошибок API

**TC-INT-ERR-001: Неверный токен**
```python
def test_invalid_token():
    response = client.get('/api/media/files', headers={
        'Authorization': 'Bearer invalid_token'
    })
    assert response.status_code == 401
```

### Обработка ошибок БД

**TC-INT-ERR-002: Ошибка подключения**
```python
def test_db_connection_error():
    db = MediaDatabase(Path('/invalid/path/db.db'))
    with pytest.raises(Exception):
        db.export_all()
```

### Обработка ошибок внешних API

**TC-INT-ERR-003: Таймаут TMDB**
```python
def test_tmdb_timeout():
    with patch('plugins.media_organizer.core.tmdb.TMDBClient') as mock:
        mock.side_effect = requests.Timeout
        with pytest.raises(requests.Timeout):
            tmdb_client.search_movie('Test')
```

---

[← API тестирование](api-testing.md) | [Инструменты QA →](qa-tools.md)