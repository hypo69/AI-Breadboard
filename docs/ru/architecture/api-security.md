# Защита API и архитектура аутентификации

> **Цель:** Руководство по модели безопасности платформы AI Breadboard: правила аутентификации, защита эндпоинтов, разграничение прав (RBAC), безопасная конфигурация CORS и работа в локальной/внешней сети.

---

## 📋 Содержание

1. [Обзор архитектуры безопасности](#обзор-архитектуры-безопасности)
2. [Модель доверия и сегментация сети](#модель-доверия-и-сегментация-сети)
3. [Зависимости аутентификации (`router_auth.py`)](#зависимости-аутентификации-router_authpy)
4. [Матрица защиты API-эндпоинтов](#матрица-защиты-api-эндпоинтов)
5. [Безопасная конфигурация CORS](#безопасная-конфигурация-cors)
6. [Практические примеры вызовов API](#практические-примеры-вызовов-api)
7. [Тестирование и верификация](#тестирование-и-верификация)

---

## Обзор архитектуры безопасности

В платформе AI Breadboard реализована гибридная модель безопасности:
- **Бесшовный локальный опыт (Local Zero-Config):** При локальной разработке и обращении из домашней/офисной локальной сети (LAN) запросы автоматически связываются с учетной записью администратора (`user_id = 1`).
- **Строгая аутентификация внешнего периметра (External Strict Auth):** Любые запросы из глобальной сети (Интернет, обратные прокси, Cloudflare туннели) обязаны передавать валидный JWT-токен в заголовке `Authorization: Bearer <token>` или сессионной cookie `auth_token`. В противном случае запрос отклоняется со статусом `401 Unauthorized`.
- **Ролевое разграничение (RBAC):** Чувствительные системные операции (управление API-ключами, чтение логов, обновление приложения, перезапуск хранилищ) требуют прав администратора (`403 Forbidden` для обычных пользователей).

```
                      Входящий HTTP / WS запрос
                                 │
                                 ▼
                     auto_login_local_user (main.py)
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
        Локальный IP / LAN             Внешний IP адрес
                 │                               │
       Внедрение JWT (id=1)           Проверка Bearer / Cookie
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                  FastAPI Router / Dependency Check
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
get_current_user_data    require_admin_user     get_current_user_optional
(401 если не авторизован) (403 если не админ)   (мягкая аутентификация)
```

---

## Модель доверия и сегментация сети

### Определение локального запроса (`is_local_request`)

Запрос классифицируется как локальный, если хост клиента принадлежит следующим диапазонам:
* **Loopback адреса:** `127.0.0.1`, `localhost`, `::1`, `0.0.0.0`, `testserver`
* **Приватные подсети LAN:**
  * `192.168.0.0/16` (`192.168.*`)
  * `10.0.0.0/8` (`10.*`)
  * `172.16.0.0/12` (`172.16.*` – `172.31.*`)

Если запрос поступает с этих адресов, система автоматически предоставляет доступ от имени локального профиля администратора.

### Внешние запросы

Любые запросы с публичных IP-адресов или сторонних доменов требуют явной авторизации. Попытка вызвать защищенный эндпоинт без токена немедленно прерывается с ошибкой `401 Unauthorized`.

---

## Зависимости аутентификации (`router_auth.py`)

Все проверки инкапсулированы в модуле `src/fastapi/router_auth.py`:

### 1. `get_current_user_data(request: Request) -> TokenData`
Основная зависимость для пользовательских эндпоинтов:
1. Проверяет наличие `auth_token` в cookie или токена в заголовке `Authorization: Bearer <JWT>`.
2. Валидирует подпись и срок действия JWT через `verify_jwt_token`.
3. Если токен валиден — возвращает объект `TokenData`.
4. Если токен отсутствует, но запрос локальный (`is_local_request`) — возвращает `TokenData(id=1)`.
5. Иначе выбрасывает `HTTPException(status_code=401, detail="Authentication required")`.

### 2. `require_admin_user(request: Request) -> TokenData`
Зависимость для административных эндпоинтов:
1. Вызывает `get_current_user_data(request)`.
2. Если запрос локальный — разрешает доступ.
3. Если запрос внешний — проверяет флаг `is_admin` или роль `admin` в базе данных (`user_manager`).
4. Если прав недостаточно — выбрасывает `HTTPException(status_code=403, detail="Admin privileges required")`.

### 3. `get_current_user_optional(request: Request) -> Optional[TokenData]`
Для эндпоинтов с публичным доступом, где профиль пользователя используется опционально (например, для подгрузки персональных тем).

---

## Матрица защиты API-эндпоинтов

| Роутер | Префикс URL | Требуемый уровень доступа | Описание |
|---|---|---|---|
| **Chat** | `/api/chat`, `/models`, `/test-model` | `get_current_user_data` (401) | Отправка сообщений, стриминг, тестирование моделей |
| **OpenAI** | `/v1/models`, `/v1/chat/completions` | `get_current_user_data` (401) | OpenAI-совместимый API для внешних клиентов |
| **RAG** | `/api/rag/*` | `get_current_user_data` (401) | Поиск по базе знаний, индексация кодовой базы и документов |
| **Audio** | `/api/audio/*` | `get_current_user_data` (401) | Диаризация аудио, сохранение стенограмм |
| **TTS** | `/api/tts/*` | `get_current_user_data` (401) | Каталог голосов, синтез речи, стриминг аудио |
| **User Storage** | `/api/user/files/*` | `get_current_user_data` (401) | Персональное хранилище файлов пользователя |
| **Agents** | `/api/agents/*` | `get_current_user_data` (401) | Управление и запуск AI-агентов |
| **API Keys** | `/api/keys/*` | `require_admin_user` (403) | Управление и ротация ключей Google Gemini |
| **Logs** | `/api/logs/*` | `require_admin_user` (403) | Просмотр и анализ серверных логов |
| **Control** | `/api/control/rescan` | `require_admin_user` (403) | Пересканирование подключенных дисков |
| **Version** | `/api/version/update`, `/backups`, `/restore` | `require_admin_user` (403) | Автообновление и управление бэкапами |
| **Docs & Schema** | `/docs`, `/redoc`, `/openapi.json` | `is_localhost` (404 на внешнем домене) | Интерактивная документация Swagger UI и схема OpenAPI |
| **Admin Panel** | `/admin`, `/admin/*` | `is_localhost` + Auth (303 на внешнем домене) | Панель управления и статика администратора |
| **Auth** | `/auth/*` | Публичный (Public) | Логин, Google OAuth, статус сессии |

---

## Безопасная конфигурация CORS

В `main.py` глобальный wildcard `allow_origins=['*']` заменен на строгую политику:

```python
def _build_cors_config() -> tuple[list[str], str | None]:
    origins = [
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    ]
    # Добавление client_url и user_domain из config.json
    ...
    # Регулярное выражение для локальной сети и домена
    origin_regex = (
        r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
        f"{domain_pattern})(:\\d+)?$"
    )
    return origins, origin_regex
```

Это гарантирует:
1. Поддержку `allow_credentials=True` без нарушения спецификации CORS.
2. Блокировку несанкционированных кросс-доменных запросов из браузера со сторонних сайтов.

---

## Практические примеры вызовов API

### 1. Локальный вызов (cURL)
При вызове с той же машины аутентификация происходит автоматически:
```bash
curl -X GET "http://localhost:8000/v1/models"
```

### 2. Внешний авторизованный вызов с Bearer JWT (Python)
```python
import httpx

API_URL = "https://your-domain.net/v1/chat/completions"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gemini-flash-latest",
    "messages": [
        {"role": "user", "content": "Привет! Расскажи о возможностях системы."}
    ]
}

response = httpx.post(API_URL, json=payload, headers=headers)
print(response.json())
```

### 3. Авторизованный вызов через Cookie (JavaScript / Fetch)
```javascript
const response = await fetch('/api/keys', {
    method: 'GET',
    credentials: 'include', // Отправляет cookie auth_token
    headers: {
        'Accept': 'application/json'
    }
});

if (response.status === 401) {
    console.error('Требуется авторизация');
} else if (response.status === 403) {
    console.error('Доступ разрешен только администраторам');
} else {
    const data = await response.json();
    console.log('API Keys:', data);
}
```

---

## Тестирование и верификация

Все аспекты безопасности покрыты автоматическими тестами в [`tests/test_api_security.py`](file:///c:/Users/onela/AppData/Local/AI-Breadboard/tests/test_api_security.py):

* Проверка распознавания локальных и внешних IP.
* Проверка извлечения данных из Bearer токенов и cookies.
* Проверка генерации статуса `401` для неавторизованных внешних запросов.
* Проверка генерации статуса `403` для пользователей без прав администратора.
* Проверка эндпоинтов `/api/keys`, `/v1/models` и роутеров чата.

Запуск тестов безопасности:
```powershell
pytest tests/test_api_security.py -v
```
