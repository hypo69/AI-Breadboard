# 🔬 Приложение: Исследования Телеметрии (Telemetry Research)

Модуль углубленного аналитического исследования, проверки системных гипотез, поиска корреляций и автоматического формирования экспертных отчетов на основе телеметрии оборудования и операционной системы.

---

## 📌 Назначение и возможности

Приложение `apps/telemetry_research` расширяет стек телеметрии платформы AI-Breadboard:

1. **Глубокий исследовательский анализ (Deep Research Engine)**:
   - Анализ временных рядов загрузки (CPU, RAM, GPU, Диск, Сеть).
   - Расчет матрицы корреляций Пирсона между всеми парами системных метрик.
   - Выявление скрытых зависимостей (например, перегрев CPU при пиковом дисковом I/O).

2. **Автоматическая проверка системных гипотез (Hypotheses Testing)**:
   - `H_CPU_THERMAL_STRESS`: Анализ перегрева и рисков троттлинга процессора.
   - `H_RAM_PRESSURE`: Детекция дефицита ОЗУ и интенсивного своппинга.
   - `H_DEVICE_INSTABILITY`: Детекция сбоящих и флаппирующих периферийных и системных устройств.
   - `H_GPU_THERMAL`: Анализ тепловых режимов видеокарты.

3. **Интерактивная визуализация и дашборды**:
   - Автономный HTML-дашборд с адаптивными графиками.
   - Векторные SVG-графики.
   - Встроенная вкладка в веб-интерфейсе `/apps` и `/tc` с боковой навигацией.

4. **Генерация рекомендаций и Health Score**:
   - Вычисление комплексного индекса здоровья системы (0-100%).
   - Формирование конкретных шагов по устранению аппаратных и программных узких мест.

---

## 🚀 Архитектура и структура файлов

```
apps/telemetry_research/
├── __init__.py       # Экспорт движка, моделей и роутера
├── __main__.py       # Точка входа для запуска python -m
├── cli.py            # Консольный интерфейс командной строки
├── config.json       # Конфигурация приложения и сетевых портов
├── engine.py         # TelemetryResearchEngine (исследовательский движок)
├── models.py         # Pydantic модели данных и отчетов
├── router.py         # FastAPI REST API роутер (/apps/telemetry_research)
└── README.md         # Документация модуля
```

---

## 💻 Использование

### 1. Запуск через Python API

```python
from apps.telemetry_research import TelemetryResearchEngine, ResearchScenarioRequest

engine = TelemetryResearchEngine()
scenario = ResearchScenarioRequest(source_path="logs/telemetry")
report = engine.run_deep_research(scenario)

print(f"Health Score: {report.base_report.health_score}/100")
for h in report.hypotheses:
    print(f"Гипотеза: {h.title} -> {'Подтверждена' if h.confirmed else 'В норме'}")
```

### 2. Консольный интерфейс (CLI)

```powershell
# Краткая сводка в консоли
py -m apps.telemetry_research --source logs/telemetry

# Экспорт интерактивного HTML-отчета
py apps/telemetry_research/cli.py --source logs/telemetry --output report.html --format html

# Экспорт JSON
py apps/telemetry_research/cli.py --source logs/telemetry --output report.json --format json
```

### 3. REST API Эндпоинты

- `GET /apps/telemetry_research/health` — проверка работоспособности сервиса.
- `POST /apps/telemetry_research/run-research` — запуск глубокого исследования.
- `GET /apps/telemetry_research/correlations` — получение матрицы корреляций.
- `GET /apps/telemetry_research/hypotheses` — проверка гипотез.
- `GET /apps/telemetry_research/charts` — получение спецификаций графиков (Chart.js).
- `GET /apps/telemetry_research/dashboard` — интерактивный HTML-дашборд.
- `GET /apps/telemetry_research/svg/{chart_id}` — векторный SVG-график.
- `GET /apps/telemetry_research/sources` — список обнаруженных файлов логов.
- `GET /apps/telemetry_research/records` — пагинированные нормализованные записи.
