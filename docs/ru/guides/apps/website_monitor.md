# Мониторинг веб-сайтов (`apps/website_monitor`)

**Статус:** ✅ Активно  
**Язык:** Русский (документация) / Английский (код)  
**Автор:** hypo69  
**Пакет:** `apps.website_monitor`

---

## 📋 Обзор

**Мониторинг веб-сайтов** — инструмент для мониторинга сайтов:
1. **Business (GA4):** Статистика посещений.
2. **Search (GSC):** SEO метрики.
3. **Technical:** Здоровье сайта (uptime, latency, ошибки).
4. **AI:** Диагностика аномалий.

---

## 🚀 Использование

### TUI
```powershell
python -m apps.website_monitor
```

### FastAPI
```powershell
python -m apps.website_monitor --mode server --port 8107
```

---

## 🌐 API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/website-monitor/summary` | Итоговый отчет. |
| `GET` | `/api/v1/website-monitor/technical` | Технические метрики. |
| `GET` | `/api/v1/website-monitor/diagnostic` | ИИ-диагностика. |
