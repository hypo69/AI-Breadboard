# Устранение проблем

## Частые проблемы

### 1. Сервер не запускается

**Ошибка:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Решение:**
```bash
pip install -r requirements.txt
```

### 2. Gemini API недоступна

**Ошибка:**
```
API key is not valid
```

**Решение:**
1. Проверьте `.env` файл
2. Убедитесь, что API ключ активен
3. Проверьте лимиты использования

### 3. qBittorrent недоступен

**Ошибка:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Решение:**
1. Убедитесь, что qBittorrent запущен
2. Включите веб-интерфейс в настройках qBittorrent
3. Проверьте порт (по умолчанию: 8080)

### 4. WebSocket соединение не устанавливается

**Ошибка:**
```
WebSocket connection failed
```

**Решение:**
1. Проверьте, что сервер запущен
2. Убедитесь, что порт не заблокирован
3. Проверьте настройки CORS

### 5. Голосовое управление не работает

**Проблема:**
```
SpeechRecognition не распознаёт голос
```

**Решение:**
1. Разрешите использование микрофона
2. Выберите правильный язык в настройках
3. Проверьте настройки микрофона в системе

### 6. Медиатека не сканируется

**Проблема:**
```
No files found
```

**Решение:**
1. Проверьте пути в `search_dirs.json`
2. Убедитесь, что у пользователя есть права на доступ к директориям
3. Проверьте логи на предмет ошибок

## Логирование

### Просмотр логов

```bash
# В терминале
tail -f logs/app.log

# Или в коде
from core.logger import logger
logger.error("Ошибка", exc_info=True)
```

## Дебагging

### VS Code

1. Откройте `Run and Debug` (Ctrl+Shift+D)
2. Выберите `Python: main.py`
3. Нажмите `Start Debugging` (F5)

### Chrome DevTools

1. Откройте DevTools (F12)
2. Перейдите на вкладку `Network`
3. Проверьте запросы к API

## Проверка системы

### 1. Проверка API ключей

```bash
python -c "from core.secrets.api_key_state import load_api_keys; print(load_api_keys())"
```

### 2. Проверка базы данных

```bash
python -c "from plugins.media_organizer.core.database import MediaDatabase; db = MediaDatabase('plugins/media_organizer/media.db'); print(db.export_all()[:5])"
```

### 3. Проверка qBittorrent

```bash
curl -X POST http://localhost:8080/api/v2/auth/login -d "username=admin&password=adminadmin"
```

## Контакты

Если вы столкнулись с проблемой, которой нет в списке:

1. Проверьте логи
2. Создайте issue на GitHub
3. Приложите логи и описание проблемы

---

[← Integrations](integrations/rc.md) | [Changelog →](changelog.md)