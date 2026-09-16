# 📚 Руководство по Миграции: Старая → Новая Архитектура

Это руководство поможет разработчикам и пользователям понять, как старые 9 независимых приложений были переведены в новую единую архитектуру с 15 доменными модулями.

---

## 🔄 Быстрое Сопоставление

### Если вы использовали Process Explorer...

**Старое:**
```bash
python -m apps.windows.apps.process_explorer
```

**Новое:**
```bash
# Через CLI
python -m apps.windows --mode full

# Через REST API
curl http://localhost:8105/api/windows/audit/processes

# Через TUI
python -m apps.windows --tui

# Программно
from apps.windows.core.modules.process_collector import ProcessCollector
result = ProcessCollector().collect()
```

**Где найти:** `apps/windows/core/modules/process_collector.py`

---

### Если вы использовали Memory Monitor...

**Старое:**
```bash
python -m apps.windows.apps.memory_monitor
```

**Новое:**
```bash
# Через CLI - видит память, CPU, утечки
python -m apps.windows --mode performance

# Через REST API
curl http://localhost:8105/api/windows/audit/performance

# Программно
from apps.windows.core.modules.performance_collector import PerformanceCollector
result = PerformanceCollector().collect()
```

**Где найти:** `apps/windows/core/modules/performance_collector.py`

**✨ Новое:** Теперь выявляет утечки памяти (процессы > 500 MB)

---

### Если вы использовали Network Diagnostics...

**Старое:**
```bash
python -m apps.windows.apps.network_diagnostics
```

**Новое:**
```bash
# Через CLI
python -m apps.windows --mode full

# Через REST API
curl http://localhost:8105/api/windows/audit/network

# Программно
from apps.windows.core.modules.network_collector import NetworkCollector
result = NetworkCollector().collect()
```

**Где найти:** `apps/windows/core/modules/network_collector.py`

**✨ Новое:** Проверка брандмауэра, обнаружение подозрительных портов

---

### Если вы использовали Security Analyzer...

**Старое:**
```bash
python -m apps.windows.apps.security_analyzer
```

**Новое:**
```bash
# Через CLI - полный аудит безопасности
python -m apps.windows --mode security

# Через REST API
curl http://localhost:8105/api/windows/audit/security

# Программно
from apps.windows.core.modules.security_collector import SecurityCollector
result = SecurityCollector().collect()
```

**Где найти:** `apps/windows/core/modules/security_collector.py`

**✨ Новое:** Проверка WMI Event Subscriptions, IFEO, AppInit DLLs для персистентности

---

### Если вы использовали Services Manager...

**Старое:**
```bash
python -m apps.windows.apps.services_manager
```

**Новое:**
```bash
# Через REST API
curl http://localhost:8105/api/windows/audit/services

# Программно
from apps.windows.core.modules.services_collector import ServicesCollector
result = ServicesCollector().collect()
```

**Где найти:** `apps/windows/core/modules/services_collector.py`

---

### Если вы использовали Hardware Explorer...

**Старое:**
```bash
python -m apps.windows.apps.hardware_explorer
```

**Новое:**
```bash
# Через REST API - диски
curl http://localhost:8105/api/windows/audit/storage

# Через REST API - драйверы и устройства
curl http://localhost:8105/api/windows/audit/drivers

# Программно
from apps.windows.core.modules.storage_collector import StorageCollector
from apps.windows.core.modules.driver_collector import DriverCollector
result = StorageCollector().collect()
```

**Где найти:** 
- Диски: `apps/windows/core/modules/storage_collector.py`
- Драйверы: `apps/windows/core/modules/driver_collector.py`

---

### Если вы использовали Baseline Detector...

**Старое:**
```bash
python -m apps.windows.apps.baseline_detector
```

**Новое:**
```bash
# Через REST API
curl http://localhost:8105/api/windows/audit/baseline

# Программно
from apps.windows.core.modules.baseline_collector import BaselineCollector
result = BaselineCollector().collect()
```

**Где найти:** `apps/windows/core/modules/baseline_collector.py`

---

### Если вы использовали Real-Time Monitor...

**Старое:**
```bash
python -m apps.windows.apps.realtime_monitor
```

**Новое:**
```bash
# Через REST API - Event Log корреляция
curl http://localhost:8105/api/windows/audit/events

# Программно
from apps.windows.core.modules.eventlog_collector import EventLogCollector
result = EventLogCollector().collect(hours=24)
```

**Где найти:** `apps/windows/core/modules/eventlog_collector.py`

---

### Если вы использовали Registry Viewer...

**Старое:**
```bash
python -m apps.windows.apps.registry_viewer
```

**Новое:** Анализ реестра распределена по разным collectors:

- **Performance Registry:** `apps/windows/core/modules/performance_collector.py` (Run ключи)
- **Security Registry:** `apps/windows/core/modules/security_collector.py` (UAC, Defender)
- **Software Registry:** `apps/windows/core/modules/software_collector.py` (Uninstall ключи)

---

### Если вы использовали Web Dashboard...

**Старое:**
```bash
python -m apps.windows.apps.dashboard
```

**Новое:**
```bash
# 1. REST API сервер
python -m apps.windows --server --port 8105

# 2. TUI Dashboard (локально)
python -m apps.windows --tui

# 3. Веб-фронтенд (находится в src/api/webgui/apps/)
# Откройте приложение Kiro IDE и переходите на localhost:8105
```

---

## 🆕 НОВЫЕ КОЛЛЕКТОРЫ (их раньше не было)

Эти 3 коллектора - новые дополнения, которые расширяют функциональность:

### 1. Clean Collector
**Файл:** `apps/windows/core/modules/clean_collector.py`

Очистка системы: `%TEMP%`, кэши браузеров, корзина, старые обновления

```bash
curl http://localhost:8105/api/windows/audit/clean
```

---

### 2. Integrity Collector  
**Файл:** `apps/windows/core/modules/integrity_collector.py`

Проверка целостности системы: SFC, DISM, статус обслуживания

```bash
curl http://localhost:8105/api/windows/audit/integrity
```

---

### 3. Update Collector
**Файл:** `apps/windows/core/modules/update_collector.py`

Проверка обновлений: версия Windows, установленные KB, статус служб обновления

```bash
curl http://localhost:8105/api/windows/audit/updates
```

---

### 4. Tasks Collector
**Файл:** `apps/windows/core/modules/tasks_collector.py`

Аудит Task Scheduler: обнаружение подозрительных закодированных команд

```bash
curl http://localhost:8105/api/windows/audit/tasks
```

---

### 5. Post-Install Collector
**Файл:** `apps/windows/core/modules/postinstall_collector.py`

Чек-лист готовности системы после установки Windows

```bash
python -m apps.windows --mode postinstall
```

---

## 🎯 Режимы Использования

Вместо запуска 9 отдельных приложений, теперь используйте режимы:

### CLI Режимы

```bash
# 1. Быстрая проверка (3 сек)
python -m apps.windows --mode quick

# 2. Полный аудит (все 15 доменов)
python -m apps.windows --mode full

# 3. Только безопасность
python -m apps.windows --mode security

# 4. Только производительность
python -m apps.windows --mode performance

# 5. Только драйверы
python -m apps.windows --mode drivers

# 6. Post-install checklist
python -m apps.windows --mode postinstall

# 7. Расследование симптома
python -m apps.windows --investigate "Компьютер тормозит после установки X"

# С JSON выводом
python -m apps.windows --mode full --json

# TUI Dashboard
python -m apps.windows --tui

# REST API сервер
python -m apps.windows --server --port 8105
```

---

## 📊 Health Score

**НОВОЕ:** Система теперь рассчитывает комплексный индекс здоровья (0-100):

```
100-95: Excellent (Отлично)
85-94:  Good (Хорошо)
70-84:  Fair (Приемлемо)
50-69:  Degraded (Деградировано)
< 50:   Critical (Критически)
```

Рассчитывается на основе:
- 25 пунктов за каждую CRITICAL ошибку
- 15 пунктов за каждую CAUTION ошибку
- 5 пунктов за MEDIUM
- 2 пункта за LOW

---

## 🤖 AI Диагностика

**НОВОЕ:** Система теперь может расследовать первопричины:

```bash
python -m apps.windows --investigate "Высокая нагрузка на CPU"
```

Система:
1. Анализирует 15 доменов
2. Собирает цепочку доказательств
3. Рассчитывает уверенность (0-100%)
4. Предлагает план действий

Программно:
```python
from apps.windows.ai.root_cause_analyzer import WindowsAIRootCauseAnalyzer

analyzer = WindowsAIRootCauseAnalyzer()
result = await analyzer.analyze_incident("Компьютер начал тормозить")
print(result.probable_root_cause)
print(result.confidence_score)
print(result.remediation_plan)
```

---

## 🔒 SafeOps Протокол

**НОВОЕ:** Все действия безопасны по умолчанию:

```python
from apps.windows.core.safe_executor import SafeExecutor

executor = SafeExecutor()

# 1. Dry-run симуляция (не изменяет систему!)
sim_result = executor.simulate(action)
print(f"Освобождается {sim_result['releasable_mb']} MB")

# 2. Выполнение после подтверждения
result = executor.execute(action, confirmed_by_user=True)
```

---

## 🔌 REST API Интеграция

**НОВОЕ:** 23 endpoint'а для интеграции:

```bash
# Запуск сервера
python -m apps.windows --server --port 8105

# Health Score
GET http://localhost:8105/api/windows/health?mode=quick

# Все 15 аудитов
GET /api/windows/audit/full
GET /api/windows/audit/clean
GET /api/windows/audit/performance
GET /api/windows/audit/drivers
GET /api/windows/audit/software
GET /api/windows/audit/integrity
GET /api/windows/audit/storage
GET /api/windows/audit/security
GET /api/windows/audit/events
GET /api/windows/audit/processes
GET /api/windows/audit/services
GET /api/windows/audit/tasks
GET /api/windows/audit/network
GET /api/windows/audit/updates
GET /api/windows/audit/baseline
GET /api/windows/audit/postinstall

# Расследование
POST /api/windows/investigate
{"symptom": "..."}

# SafeOps действия
POST /api/windows/actions/simulate
POST /api/windows/actions/execute
```

---

## 🧪 Тестирование Миграции

### 1. Проверить CLI режимы

```bash
python -m apps.windows --mode quick
python -m apps.windows --mode full
python -m apps.windows --investigate "test symptom"
```

### 2. Проверить REST API

```bash
python -m apps.windows --server &
sleep 2
curl http://localhost:8105/api/windows/health
curl http://localhost:8105/api/windows/audit/processes
```

### 3. Проверить TUI

```bash
python -m apps.windows --tui
```

### 4. Проверить программное использование

```python
from apps.windows import WindowsAIDiagnostician
diag = WindowsAIDiagnostician()
report = await diag.diagnose_system(mode="full")
print(report.health_score.score)
```

---

## 📦 Структура Файлов

```
apps/windows/
├── core/
│   ├── modules/
│   │   ├── clean_collector.py
│   │   ├── performance_collector.py
│   │   ├── driver_collector.py
│   │   ├── software_collector.py
│   │   ├── integrity_collector.py
│   │   ├── storage_collector.py
│   │   ├── security_collector.py
│   │   ├── eventlog_collector.py
│   │   ├── process_collector.py
│   │   ├── services_collector.py
│   │   ├── tasks_collector.py
│   │   ├── network_collector.py
│   │   ├── update_collector.py
│   │   ├── baseline_collector.py
│   │   └── postinstall_collector.py
│   ├── api/
│   │   ├── kernel32.py
│   │   ├── psapi.py
│   │   ├── advapi32.py
│   │   ├── ntdll.py
│   │   └── etw.py
│   ├── winapi.py
│   ├── process_intelligence.py
│   ├── safe_executor.py
│   ├── root_cause_engine.py
│   └── correlation_engine.py
├── ai/
│   ├── diagnostician.py
│   ├── root_cause_analyzer.py
│   └── prompt_templates.py
├── cli.py
├── tui.py
├── router.py
├── __main__.py
├── README.md
├── ARCHITECTURE.md
├── AUDIT_REPORT.md (новый)
├── MIGRATION_GUIDE.md (этот файл)
├── TESTING.md
└── INSTALLATION.md
```

---

## ⚠️ Важные Отличия

### 1. Единая Точка Входа

**Старое:**
```bash
python -m apps.windows.apps.process_explorer
python -m apps.windows.apps.security_analyzer
python -m apps.windows.apps.network_diagnostics
```

**Новое:**
```bash
python -m apps.windows --mode full
# или
python -m apps.windows --mode security
# или
python -m apps.windows --mode network  # (если это специальный режим)
```

### 2. Интеграция Данных

**Старое:** Каждое приложение работало независимо  
**Новое:** Система видит всё целиком и рассчитывает Health Score

### 3. Безопасность Действий

**Старое:** Прямое выполнение команд  
**Новое:** Все действия требуют:
- Dry-run симуляцию
- Явное подтверждение пользователя
- Проверка уровня риска (Green/Yellow/Red)

---

## 🎓 Обучение Пользователей

Если ваши пользователи привыкли к старым приложениям:

1. **Скажите им:** "Теперь это одно интегрированное приложение"
2. **Покажите:** `python -m apps.windows --tui` (красивая визуализация)
3. **Объясните:** Health Score (0-100) показывает общее состояние
4. **Упростите:** Режимы (quick/full/security) вместо 9 приложений

---

## 🆘 Troubleshooting

### "У меня не работает CLI"

Попробуйте:
```bash
# Проверьте импорты
python -c "from apps.windows import WindowsAIDiagnostician; print('OK')"

# Запустите с дебаг информацией
python -m apps.windows --mode quick 2>&1 | head -20
```

### "REST API не запускается"

```bash
# Проверьте, что FastAPI установлена
pip install fastapi uvicorn

# Проверьте порт
lsof -i :8105

# Используйте другой порт
python -m apps.windows --server --port 9999
```

### "TUI не отображается"

```bash
# Проверьте Rich библиотеку
pip install rich

# Попробуйте CLI вывод
python -m apps.windows --mode full
```

---

## ✅ Чеклист Миграции

- [ ] Установлены все зависимости (psutil, fastapi, rich и т.д.)
- [ ] Протестированы все 7 CLI режимов
- [ ] Протестирован REST API
- [ ] Протестирован TUI Dashboard
- [ ] Понимаете новую структуру папок
- [ ] Обновлены документы для пользователей
- [ ] Обновлены скрипты/автоматизация

---

## 📞 Поддержка

Вопросы? Читайте:
- `README.md` - Общая информация
- `ARCHITECTURE.md` - Подробная архитектура
- `AUDIT_REPORT.md` - Результаты аудита
- Исходный код - Хорошо документирован на русском

---

**Миграция завершена! Добро пожаловать в новую архитектуру! 🎉**
