# 🛡️ Контрольные точки системы и образы восстановления Windows (`apps/windows/system_checkpoints`)

**Status:** ✅ Active  
**Author:** hypo69  
**Version:** 1.0.0  

Нативное приложение операционной системы Windows для комплексного управления **контрольными точками системы**, **WIM-образами восстановления** и **средой восстановления Windows RE**.

---

## 💡 Концепция и разделение механизмов

Приложение строго разграничивает три независимых нативных механизма защиты и восстановления Windows:

1. **System Image (DISM / WIM / FFU)**:
   - **Базовый эталонный образ (Baseline Gold Image)**: создается однократно после чистой установки Windows, настройки драйверов, обновлений и базовых программ (`Recovery_YYYY-MM-DD_Baseline.wim`).
   - **Периодические контрольные точки (Periodic / Incremental WIM)**: периодические версионированные снимки (`Recovery_YYYY-MM-DD_HHMMSS.wim` или добавление индекса через `DISM /Append-Image`). Исключает слепую перезапись единственного образа.
2. **Recovery Environment (WinRE / reagentc)**:
   - Инспекция статуса Windows RE (`reagentc /info`), проверка расположения `Winre.wim` и GUID BCD.
   - Включение (`reagentc /enable`), отключение (`reagentc /disable`) и перенаправление путей (`reagentc /setreimage`).
3. **Restore Point (System Restore / VSS)**:
   - Нативные точки восстановления Windows через PowerShell `Checkpoint-Computer` и VSS.
   - Категоризация: 🟢 Базовая, 🔵 После настройки, 🟡 Перед обновлением, 🟠 Перед экспериментом, 🔴 Периодическая.
   - Автоматическая ротация и контроль дискового пространства теневых копий.

---

## 📊 Аудит актуальности («Проверить актуальность образа» / System Drift)

Аудитор вычисляет дрейф системы с момента создания последнего образа:
* Возраст образа (в днях);
* Количество изменившихся системных компонентов и KB-обновлений;
* Количество вновь установленных программ;
* Количество обновленных или добавленных драйверов;
* Индекс актуальности: 🟢 **Высокая** / 🟡 **Умеренная** / 🟠 **Низкая** / 🔴 **Критически устарел**;
* Интеллектуальные рекомендации по созданию контрольных точек или обновлению базового образа.

---

## 🚀 Запуск из терминала (Rich TUI)

```powershell
python -m apps.windows.system_checkpoints
```

---

## 🌐 FastAPI REST API Endpoints (`/api/v1/windows-checkpoints`)

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/v1/windows-checkpoints/health` | Сводный отчет готовности всех 3 механизмов (Health Score 0-100) |
| `GET` | `/api/v1/windows-checkpoints/freshness` | Отчет об актуальности последнего образа и системном дрейфе |
| `GET` | `/api/v1/windows-checkpoints/catalog` | Список всех зарегистрированных контрольных точек системы |
| `POST` | `/api/v1/windows-checkpoints/catalog` | Создание новой контрольной точки (Базовая, После настройки и др.) |
| `DELETE` | `/api/v1/windows-checkpoints/catalog/{id}` | Удаление контрольной точки из каталога |
| `GET` | `/api/v1/windows-checkpoints/images` | Инвентаризация WIM/ESD образов на дисках |
| `POST` | `/api/v1/windows-checkpoints/images/create-baseline` | Создание базового эталонного WIM-образа через DISM |
| `POST` | `/api/v1/windows-checkpoints/images/create-periodic` | Создание периодической контрольной точки WIM |
| `GET` | `/api/v1/windows-checkpoints/winre/status` | Диагностика статуса среды WinRE (`reagentc /info`) |
| `POST` | `/api/v1/windows-checkpoints/winre/action` | Включение/отключение/настройка среды WinRE |
| `GET` | `/api/v1/windows-checkpoints/restore-points` | Список нативных точек восстановления Windows |
| `POST` | `/api/v1/windows-checkpoints/restore-points` | Создание нативной точки восстановления |
