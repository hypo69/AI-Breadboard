# Безопасное изменение системных параметров и точки восстановления Windows

## 📌 Введение

В платформе **AI-Breadboard** реализован надежный механизм управления системными параметрами Windows и платформы — **`SafeSystemParamManager`** и **`WindowsSystemRestoreManager`**.

Главный принцип безопасности: **при изменении любых чувствительных параметров системы автоматически создается точка восстановления Windows (System Restore Point)** и сохраняется снимок текущего состояния в журнале аудита до внесения изменений.

---

## 🔒 Защита от замещения и вытеснения точек восстановления

В операционной системе Windows могут действовать системные ограничения (лимит частоты создания точек в 24 часа — `SystemRestorePointCreationFrequency`, либо квота дискового пространства теневого хранилища VSS). 

Для предотвращения потери и **замещения/вытеснения уже существующих точек восстановления**:
1. **Проверка хранилища VSS**: `get_shadow_storage_info()` отслеживает объем теневого хранилища и предупреждает о рисках вытеснения старых снимков ОС при заполнении > 85%.
2. **Неизменяемое локальное хранилище (Immutable State Snapshots)**:
   - Каждый раз перед изменением любого параметра система создает независимый локальный снимок состояния в `data/state_snapshots/snapshot_<uuid>.json`.
   - Файлы снимков строго неизменяемы (`immutable = True`), их перезапись запрещена.
   - Даже если создание точки восстановления Windows заблокировано лимитом частоты (1440 минут) или квотой, все предыдущие и текущие состояния параметров сохраняются навсегда и гарантируют 100% возможность отката (`rollback`).


## 🛡️ Классификация чувствительности параметров

Параметры делятся по уровню риска и флагу чувствительности `is_sensitive`:

| Категория | Тип | Чувствительность | Уровень риска | Автоматическая точка восстановления |
|---|---|---|---|---|
| **Безопасность (UAC, Defender, SMB1)** | Реестр / WMI | `is_sensitive = True` | `CRITICAL` | ✅ Да |
| **Конфиденциальность (Телеметрия)** | Реестр | `is_sensitive = True` | `CAUTION` | ✅ Да |
| **Системные службы (SysMain, Updates, DiagTrack)** | Служба Windows | `is_sensitive = True` | `CAUTION` / `CRITICAL` | ✅ Да |
| **Платформенные настройки (Интервалы, JSON)** | Config | `is_sensitive = False` | `SAFE` | ❌ Нет (локальный бэкап) |

---

## 🚀 Использование через CLI (`manage_tools.py`)

### 1. Просмотр списка параметров
```powershell
py manage_tools.py sys-param list
```

### 2. Предварительный просмотр (Dry-Run симуляция)
Перед внесением изменений можно увидеть текущее и новое значение, признак чувствительности и факт необходимости точки восстановления:
```powershell
py manage_tools.py sys-param preview sec.uac_level 0
```

### 3. Безопасное изменение параметра
При выполнении команды для чувствительного параметра система автоматически вызовет `Checkpoint-Computer` в Windows и сохранит запись в `data/system_param_history.json`:
```powershell
py manage_tools.py sys-param set sec.uac_level 1
```

### 4. Просмотр и ручное создание точек восстановления
```powershell
# Список точек восстановления
py manage_tools.py sys-param restore-points

# Ручное создание контрольной точки
py manage_tools.py sys-param create-rp "Ручной снимок перед установкой драйвера"
```

### 5. Журнал изменений и откат (Rollback)
```powershell
# Просмотр истории
py manage_tools.py sys-param history

# Откат изменения по Change ID
py manage_tools.py sys-param rollback <change_id>
```

---

## 🌐 REST API (`apps/system_control_center`)

Микросервис Центра управления предоставляет REST API:
- `GET /api/system-control/params` — Каталог параметров с текущими значениями.
- `POST /api/system-control/params/preview` — Симуляция изменения.
- `POST /api/system-control/params/apply` — Применение с автоматической точкой восстановления.
- `GET /api/system-control/params/history` — Журнал аудита изменений.
- `POST /api/system-control/params/rollback` — Откат по `change_id`.
- `GET /api/system-control/restore-points` — Список точек восстановления Windows.
- `POST /api/system-control/restore-points` — Создание новой точки восстановления.
