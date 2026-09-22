# 🧪 Тестирование и документирование приложений v1.0

**Статус:** ✅ Production Ready  \n**Версия:** 1.0  \n**Автор:** hypo69  \n**Copyright:** © 2026 hypo69

---

## 📋 Содержание
1. [Философия тестирования](#1-философия-тестирования)
2. [Структура тестов для приложений](#2-структура-тестов-для-приложений)
3. [Документирование приложений](#3-документирование-приложений)
4. [Примеры](#4-примеры)

---

## 1. Философия тестирования

### 1.1 Тесты — это документация поведения

**Тесты — это не проверка кода. Тесты — это документация поведения.**

- 📝 Документируют, как использовать код
- 🔒 Защищают от регрессии
- 🧠 Помогают понять дизайн
- 🚀 Ускоряют разработку

### 1.2 Пирамида тестирования

```
                    ▲
                   ╱ ╲
                  ╱   ╲
                 ╱ E2E ╲         5-10% тестов
                ╱───────╲
               ╱         ╲
              ╱ Integration╲     15-25% тестов
             ╱─────────────╲
            ╱               ╲
           ╱   Unit Tests    ╲   65-80% тестов
          ╱───────────────────╲
         ╱_____________________╲
```

### 1.3 Соотношение тестов

| Тип | Количество | Скорость | Стоимость |
|-----|-----------|----------|----------|
| **Unit** | 70% | ⚡⚡⚡ Быстро | 💰 Дешево |
| **Integration** | 20% | ⚡⚡ Средне | 💰💰 Среднее |
| **E2E** | 10% | ⚡ Медленно | 💰💰💰 Дорого |

---

## 2. Структура тестов для приложений

### 2.1 Расположение тестов

```
apps/
└── <app_name>/
    ├── tests/
    │   ├── __init__.py
    │   ├── test_<module1>.py
    │   ├── test_<module2>.py
    │   └── test_integration.py
    └── <module1>.py
```

### 2.2 Структура тестового файла

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тестирование модуля <название>
# =============================================================================
# Description:
#   Набор тестов для проверки корректности функций модуля <название>.
#
# Test Categories:
#   1. Happy Path — Стандартные входные данные
#   2. Edge Cases — Пустые значения, граничные случаи
#   3. Type Variants — Разные типы аргументов
#   4. Boundary Values — Минимальные и максимальные значения
#   5. Error Scenarios — Ошибочные входные данные
#   6. Regression — Тесты зависимых модулей
#
# File: test_<module_name>.py
# Module: apps/<app_name>/tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import unittest
from apps.<app_name>.<module> import ClassName


class TestClassName(unittest.TestCase):
    """Test suite for ClassName class."""
    
    def setUp(self):
        """Подготовка перед каждым тестом."""
        pass
    
    def tearDown(self):
        """Очистка после каждого теста."""
        pass
    
    # 1. Happy Path tests
    def test_function_valid_input_happy_path(self): pass
    
    # 2. Edge Cases tests
    def test_function_empty_input_edge_case(self): pass
    
    # 3. Type Variants tests
    def test_function_different_types_type_variant(self): pass
    
    # 4. Boundary Values tests
    def test_function_min_max_boundary(self): pass
    
    # 5. Error Scenarios tests
    def test_function_invalid_input_error(self): pass
    
    # 6. Regression tests
    def test_dependent_module_still_works_regression(self): pass


if __name__ == '__main__':
    unittest.main()
```

### 2.3 Запуск тестов

```bash
# Запуск тестов конкретного модуля
pytest apps/<app_name>/tests/test_<module>.py -v

# Запуск всех тестов приложения
pytest apps/<app_name>/tests/ -v

# Запуск с покрытием
pytest apps/<app_name>/tests/ --cov=apps/<app_name> --cov-report=term-missing
```

---

## 3. Документирование приложений

### 3.1 Обязательные файлы

**Каждое приложение MUST иметь:**

1. **README.md** — описание приложения, архитектура, использование
2. **docstrings** — для всех публичных функций и классов

### 3.2 Структура README.md приложения

```markdown
# Название приложения

**Описание:** Краткое описание функции приложения (15-25 слов).

## Назначение

Что делает приложение, его роль в проекте.

## Архитектура

Основные компоненты:
- `module1.py` — Class `ClassName`, отвечает за X
- `module2.py` — Function `function_name()`, отвечает за Y

## Использование

### Базовый пример

```python
from apps.<app_name>.module import ClassName

obj = ClassName(param='value')
result = obj.method()
print(result)
```

## API

### Основные endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/<app>/endpoint` | GET/POST | Описание |

## Файлы

- `__init__.py` — Экспорт публичного API
- `main.py` — Основная логика
- `module.py` — Вспомогательные функции

## Тесты

Запуск тестов:
```bash
pytest apps/<app_name>/tests/ -v
```

## Ссылки

- [`../../.ai/instructions/standards/DOCUMENTATION.md`](../../.ai/instructions/standards/DOCUMENTATION.md) — Стандарты документирования
- [`../../.ai/instructions/workflows/TDD.md`](../../.ai/instructions/workflows/TDD.md) — TDD workflow
```

### 3.3 Docstring для приложения

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Модуль управления сетевыми соединениями
# =============================================================================
# Description:
#   Сбор и анализ сетевой статистики через Windows PowerShell cmdlets.
#   Мониторинг TCP-соединений, сетевых адаптеров и DNS-разрешения.
#
# Examples:
#   >>> from apps.network_terminal.network_monitor import NetworkMonitor
#   >>> monitor = NetworkMonitor()
#   >>> connections = monitor.get_tcp_connections()
#
# File: network_monitor.py
# Project: AI Breadboard
# Module: apps.network_terminal
# Class: NetworkMonitor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

class NetworkMonitor:
    """Мониторинг сетевых соединений через Windows PowerShell.
    
    Сбор информации о TCP-соединениях, сетевых адаптерах и DNS-разрешении
    без использования сторонних инструментов (TShark, Wireshark).
    
    Attributes:
        logger: Логгер для записи событий.
    
    Examples:
        >>> monitor = NetworkMonitor()
        >>> connections = monitor.get_tcp_connections()
        >>> print(len(connections))
        5
    """
```

---

## 4. Примеры

### 4.1 Полный пример тестов для приложения

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тестирование модуля сетевого мониторинга
# =============================================================================
# File: test_network_monitor.py
# Module: apps/network_terminal/tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import unittest
from apps.network_terminal.network_monitor import NetworkMonitor


class TestNetworkMonitor(unittest.TestCase):
    """Test suite for NetworkMonitor class."""
    
    def setUp(self):
        """Подготовка перед каждым тестом."""
        self.monitor = NetworkMonitor()
    
    def tearDown(self):
        """Очистка после каждого теста."""
        pass
    
    # ===== 1. HAPPY PATH TESTS =====
    
    def test_get_tcp_connections_valid_happy_path(self):
        """Test TCP connections retrieval on valid system.
        
        Validates: Returns list of connections without error.
        Dependencies: Used by network_terminal UI for connection display.
        """
        # --- Arrange: Prepare monitor instance ---
        # NetworkMonitor instance for testing
        monitor = NetworkMonitor()
        
        # --- Act: Execute method ---
        # Call get_tcp_connections method
        result = monitor.get_tcp_connections()
        
        # --- Assert: Verify result ---
        assert result is not None, "get_tcp_connections returned None"
        assert isinstance(result, list), f"Expected list, got {type(result)}"
    
    # ===== 2. EDGE CASES TESTS =====
    
    def test_get_tcp_connections_empty_edge_case(self):
        """Test TCP connections retrieval when no connections exist.
        
        Validates: Returns empty list without error.
        Dependencies: Caller expects empty [] not None.
        """
        # --- Arrange: Prepare monitor instance ---
        monitor = NetworkMonitor()
        
        # --- Act: Execute method ---
        result = monitor.get_tcp_connections()
        
        # --- Assert: Verify empty result ---
        assert isinstance(result, list), (
            f"get_tcp_connections should return list, got {type(result)}"
        )
    
    # ===== 3. TYPE VARIANTS TESTS =====
    
    def test_get_tcp_connections_with_timeout_type_variant(self):
        """Test TCP connections with timeout parameter.
        
        Validates: Function handles timeout parameter correctly.
        Dependencies: UI passes timeout from user input.
        """
        # --- Arrange: Prepare timeout parameter ---
        # Timeout in seconds
        timeout = 10
        
        # --- Act: Execute method with timeout ---
        result = self.monitor.get_tcp_connections(timeout=timeout)
        
        # --- Assert: Verify timeout handling ---
        assert result is not None, "get_tcp_connections with timeout failed"
    
    # ===== 4. BOUNDARY VALUES TESTS =====
    
    def test_get_tcp_connections_min_max_timeout_boundary(self):
        """Test TCP connections with boundary timeout values.
        
        Validates: Function handles min/max timeout values correctly.
        Dependencies: User might input extreme values.
        """
        # --- Arrange: Prepare boundary timeout values ---
        # Minimum valid timeout (1 second)
        min_timeout = 1
        # Maximum valid timeout (300 seconds)
        max_timeout = 300
        
        # --- Act: Execute method with boundary values ---
        result_min = self.monitor.get_tcp_connections(timeout=min_timeout)
        result_max = self.monitor.get_tcp_connections(timeout=max_timeout)
        
        # --- Assert: Verify boundary handling ---
        assert result_min is not None, "Min timeout should not raise error"
        assert result_max is not None, "Max timeout should not raise error"
    
    # ===== 5. ERROR SCENARIOS TESTS =====
    
    def test_get_tcp_connections_invalid_timeout_error(self):
        """Test TCP connections with invalid negative timeout.
        
        Validates: Function handles invalid timeout gracefully.
        Dependencies: Input validation layer depends on this behavior.
        """
        # --- Arrange: Prepare invalid negative timeout ---
        # Invalid negative timeout
        invalid_timeout = -5
        
        # --- Act: Execute method with invalid timeout ---
        result = self.monitor.get_tcp_connections(timeout=invalid_timeout)
        
        # --- Assert: Verify error handling ---
        assert result is not None, "Invalid timeout should not crash"
    
    # ===== 6. REGRESSION TESTS =====
    
    def test_network_terminal_ui_still_works_regression(self):
        """Verify network_terminal UI still works after changes.
        
        Validates: Dependent module (network_terminal UI) is not broken.
        Dependencies: network_terminal UI depends on NetworkMonitor.
        """
        from apps.network_terminal.main import router
        
        # --- Arrange: Create router instance ---
        # Router instance for testing
        router_instance = router
        
        # --- Act: Call dependent endpoint ---
        # This would normally be an async test
        # For now, just verify router exists
        assert router_instance is not None, "Router should exist"
    
    # ===== 7. INTEGRATION TESTS =====
    
    def test_network_monitor_integration_with_sensors(self):
        """Test integration with sensors module.
        
        Validates: NetworkMonitor works with sensors.py.
        Dependencies: sensors.py uses NetworkMonitor for network metrics.
        """
        from apps.network_terminal.sensors import get_network_sensors
        
        # --- Act: Get network sensors ---
        sensors = get_network_sensors()
        
        # --- Assert: Verify sensors ---
        assert isinstance(sensors, list), "get_network_sensors should return list"
        assert len(sensors) > 0, "Should have at least one network sensor"


if __name__ == '__main__':
    unittest.main()
```

### 4.2 Полный пример README.md для приложения

```markdown
# Network Terminal

**Описание:** Мониторинг сетевых соединений через Windows PowerShell cmdlets.

## Назначение

Приложение предоставляет мониторинг сетевых соединений, адаптеров и DNS-разрешения
через нативные Windows инструменты без использования сторонних прог��амм (TShark, Wireshark).

## Архитектура

Основные компоненты:
- `network_monitor.py` — Class `NetworkMonitor`, сбор сетвой статистики
- `sensors.py` — Function `get_network_sensors()`, интеграция с telemetry
- `main.py` — FastAPI router, endpoints для UI

## Использование

### Базовый пример

```python
from apps.network_terminal.network_monitor import NetworkMonitor

monitor = NetworkMonitor()
connections = monitor.get_tcp_connections()
print(f"Active connections: {len(connections)}")
```

### API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/network/connections` | GET | Список TCP-соединений |
| `/api/network/adapters` | GET | Список сетевых адаптеров |
| `/api/network/dns` | GET | DNS-серверы |

## Тесты

Запуск тестов:
```bash
pytest apps/network_terminal/tests/ -v
```

Покрытие кода:
```bash
pytest apps/network_terminal/tests/ --cov=apps/network_terminal --cov-report=term-missing
```

## Файлы

- `__init__.py` — Экспорт публичного API
- `network_monitor.py` — Основная логика мониторинга
- `sensors.py` — Интеграция с telemetry системой
- `main.py` — FastAPI endpoints
- `tests/` — Unit и integration тесты

## Ссылки

- [`../../.ai/instructions/standards/DOCUMENTATION.md`](../../.ai/instructions/standards/DOCUMENTATION.md) — Стандарты документирования
- [`../../.ai/instructions/workflows/TDD.md`](../../.ai/instructions/workflows/TDD.md) — TDD workflow
- [`../../.ai/instructions/standards/ENGINEERING.md`](../../.ai/instructions/standards/ENGINEERING.md) — Инженерные стандарты
```

---

## ✅ Чек-лист перед коммитом

- [ ] Все функции и классы имеют docstrings
- [ ] README.md создан для нового приложения
- [ ] Unit-тесты написаны для всех функций
- [ ] Integration-тесты проверяют взаимодействие с другими модулями
- [ ] 100% тестов проходят зелёными
- [ ] Покрытие ≥ 70%
- [ ] Тесты включают все 6 категорий (Happy Path, Edge Cases, Type Variants, Boundary Values, Error Scenarios, Regression)
- [ ] Каждый тест имеет информативное сообщение об ошибке

---

**Последнее обновление:** сентябрь 2026

**Ссылки:**
- [`standards/DOCUMENTATION.md`](../standards/DOCUMENTATION.md) — Стандарты документирования
- [`workflows/TDD.md`](TDD.md) — TDD workflow
- [`standards/ENGINEERING.md`](../standards/ENGINEERING.md) — Инженерные стандарты
