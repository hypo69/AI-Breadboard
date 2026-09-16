# Маршрутизация, изоляция доменов и защита документации

> **Цель:** Описание архитектуры маршрутизации запросов в AI Breadboard, изоляции внешнего пользовательского домена (`kino.davidka.net`), политики запрета несанкционированных редиректов и разграничения доступа к интерактивной документации API (`/docs`, `/redoc`, `/openapi.json`) и панели управления (`/admin`).

---

## 📋 Содержание

1. [Общая концепция изоляции периметров](#общая-концепция-изоляции-периметров)
2. [Политика запрета редиректов на внешнем домене](#политика-запрета-редиректов-на-внешнем-домене)
3. [Защита документации API (`/docs`, `/redoc`, `/openapi.json`)](#защита-документации-api-docs-redoc-openapijson)
4. [Разграничение интерфейсов пользователя и администратора](#разграничение-интерфейсов-пользователя-и-администратора)
5. [Алгоритм определения локального клиента (`is_localhost`)](#алгоритм-определения-локального-клиента-is_localhost)
6. [Тестирование и верификация (`tests/test_routing_access.py`)](#тестирование-и-верификация-teststest_routing_accesspy)

---

## Общая концепция изоляции периметров

AI Breadboard разграничивает входящий трафик на два независимых контура:

1. **Внешний периметр (Пользовательский домен — `USER_DOMAIN` / `kino.davidka.net`):**
   - Предоставляет исключительно пользовательский интерфейс (вкладки чата, RAG-поиска, TTS и голосового управления) и публичные/клиентские страницы (`/`, `/rc`, `/tv`, `/tgmini`, `/user_tts`).
   - Все административные страницы, системные логи и метаданные API скрыты.

2. **Локальный доверенный периметр (`localhost` / LAN):**
   - Доступен разработчику и администратору внутри локальной сети (`127.0.0.1`, `192.168.*`, `10.*`, `172.16-31.*`).
   - Предоставляет полный доступ к панели администратора (`/admin`), логам (`/logs`), интерактивной документации Swagger UI (`/docs`), ReDoc (`/redoc`) и схеме OpenAPI (`/openapi.json`).

```
                              Входящий запрос
                                     │
                                     ▼
                      get_request_hostname(request)
                      & is_localhost(request)
                                     │
                   ┌─────────────────┴─────────────────┐
                   │                                   │
      Хост == kino.davidka.net                Хост == localhost / LAN
      (или внешний IP)                                 │
                   │                                   ▼
                   │                     ┌───────────────────────────┐
                   │                     │ • /admin, /logs           │
                   │                     │ • /docs (Swagger UI)      │
                   │                     │ • /redoc (ReDoc)          │
                   │                     │ • /openapi.json (OpenAPI) │
                   │                     │ • Пользовательские роуты  │
                   │                     └───────────────────────────┘
                   ▼
      ┌─────────────────────────────────┐
      │ • /docs, /redoc, /openapi.json  │ ──► 404 Not Found (без редиректов)
      │ • /admin, /logs                 │ ──► 303 Redirect на корень /
      │ • /, /user/*, /rc, /tv          │ ──► Пользовательский интерфейс
      └─────────────────────────────────┘
```

---

## Политика запрета редиректов на внешнем домене

Для предотвращения раскрытия внутренней структуры сервиса, обхода авторизации или утечки внутренних URL во внешнем периметре (`kino.davidka.net`) соблюдаются следующие правила:

1. **Запрет редиректов на документацию и системные роуты:**
   - Попытка запроса к `/docs`, `/redoc` или `/openapi.json` снаружи возвращает строгий код `404 Not Found`. Никаких редиректов на страницы входа или документацию не выполняется.
2. **Скрытый возврат на главную для `/admin`:**
   - При попытке обратиться к `/admin` или отправить POST-запрос на `/admin` с внешнего домена запрос безусловно перенаправляется на корень `/` (`303 See Other`), не раскрывая форму авторизации администратора.

---

## Защита документации API (`/docs`, `/redoc`, `/openapi.json`)

### 1. Отключение стандартных авто-роутов FastAPI
По умолчанию FastAPI автоматически регистрирует роуты `/docs` и `/redoc`, доступные для всех хостов. В `main.py` встроенная генерация отключена:

```python
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
```

### 2. Регистрация защищенных кастомных хендлеров
В `main.py` зарегистрированы явные хендлеры, проверяющие происхождение запроса:

```python
@app.get('/docs', include_in_schema=False)
async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
    """Serve Swagger UI documentation strictly for localhost / local network requests."""
    user_domain = os.getenv('USER_DOMAIN', 'kino.davidka.net').strip().lower()
    req_host = get_request_hostname(request)
    if req_host == user_domain or not is_localhost(request):
        raise HTTPException(status_code=404, detail='Not Found')
    return get_swagger_ui_html(openapi_url='/openapi.json', title=f"{app.title} - Swagger UI")

@app.get('/redoc', include_in_schema=False)
async def custom_redoc_html(request: Request) -> HTMLResponse:
    """Serve ReDoc documentation strictly for localhost / local network requests."""
    user_domain = os.getenv('USER_DOMAIN', 'kino.davidka.net').strip().lower()
    req_host = get_request_hostname(request)
    if req_host == user_domain or not is_localhost(request):
        raise HTTPException(status_code=404, detail='Not Found')
    return get_redoc_html(openapi_url='/openapi.json', title=f"{app.title} - ReDoc")

@app.get('/openapi.json', include_in_schema=False)
async def custom_openapi(request: Request) -> JSONResponse:
    """Serve OpenAPI JSON schema strictly for localhost / local network requests."""
    user_domain = os.getenv('USER_DOMAIN', 'kino.davidka.net').strip().lower()
    req_host = get_request_hostname(request)
    if req_host == user_domain or not is_localhost(request):
        raise HTTPException(status_code=404, detail='Not Found')
    return JSONResponse(get_openapi(title=app.title, version=app.version, routes=app.routes))
```

---

## Разграничение интерфейсов пользователя и администратора

| Путь | Доступ с `kino.davidka.net` | Доступ с `localhost` / LAN | Назначение |
|---|---|---|---|
| `/` | `200 OK` (User Interface) | `200 OK` (User Interface) | Основной интерфейс (Chat, RAG, TTS, Voice) |
| `/user` | `303 Redirect` на `/` | `303 Redirect` на `/` | Алиас пользовательского интерфейса |
| `/rc`, `/tv`, `/tgmini` | `200 OK` | `200 OK` | Публичные специализированные веб-интерфейсы |
| `/docs` | `404 Not Found` | `200 OK` (Swagger UI) | Интерактивная документация API |
| `/redoc` | `404 Not Found` | `200 OK` (ReDoc) | Альтернативная документация API |
| `/openapi.json` | `404 Not Found` | `200 OK` (JSON Schema) | Спецификация OpenAPI v3 |
| `/admin` | `303 Redirect` на `/` | `200 OK` (Login / Admin Panel) | Панель управления системой |
| `/logs` | `303 Redirect` на `/` | `303 Redirect` на `/admin#tab-logs` | Просмотр системных логов |

---

## Алгоритм определения локального клиента (`is_localhost`)

Определение принадлежности клиента к доверенному периметру выполняется функцией `is_localhost` в `main.py`:

```python
def is_localhost(request: Request) -> bool:
    """Check if the incoming request originates from localhost/loopback or local network."""
    client_host = request.client.host if request.client else ''
    return (
        client_host in ('127.0.0.1', '::1', 'localhost', 'testserver', 'testclient', '0.0.0.0')
        or client_host.startswith('192.168.')
        or client_host.startswith('10.')
        or client_host.startswith('172.')
    )
```

Также проверяется нормализованный заголовок хоста через `get_request_hostname(request)`, который извлекает хост из `x-forwarded-host`, `host` или `url.hostname`.

---

## Тестирование и верификация (`tests/test_routing_access.py`)

Набор тестов в `tests/test_routing_access.py` проверяет корректность изоляции:

- `test_is_localhost_helper`: проверка корректности определения `localhost` и удаленных хостов.
- `test_root_serves_user_interface`: проверка отдачи 4 вкладок пользовательского UI на домене `kino.davidka.net`.
- `test_admin_access_allowed_for_localhost`: проверка доступности `/admin` для локального разработчика.
- `test_admin_access_redirects_for_user_domain`: проверка перенаправления запросов `/admin` с `kino.davidka.net` на корень `/`.
- `test_docs_endpoints_allowed_for_localhost`: проверка статуса `200 OK` для `/docs`, `/redoc` и `/openapi.json` на `localhost`.
- `test_docs_endpoints_return_404_for_user_domain`: проверка статуса `404 Not Found` для `/docs`, `/redoc` и `/openapi.json` при запросе с `kino.davidka.net`.

Запуск тестов:
```powershell
py -m pytest tests/test_routing_access.py -v
```
