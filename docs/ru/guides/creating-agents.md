# Руководство по созданию Agents

> **Цель:** Научиться проектировать и создавать интеллектуальных агентов для решения сложных задач.

---

## 📋 Содержание

1. [Введение в Agents](#введение-в-agents)
2. [Архитектура Agents](#архитектура-agents)
3. [Жизненный цикл агента](#жизненный-цикл-агента)
4. [Интеграция с провайдерами ИИ](#интеграция-с-провайдерами-иИ)
5. [ReAct паттерн](#react-паттерн)
6. [Обработка состояния](#обработка-состояния)
7. [Лучшие практики](#лучшие-практики)
8. [Примеры агентов](#примеры-агентов)

---

## Введение в Agents

### Что такое Agent?

**Agent** (агент) — это автономная система, которая:

- 🧠 **Рассуждает** о проблеме и планирует решение
- 🔄 **Взаимодействует** с инструментами и API
- 📊 **Обрабатывает** результаты и адаптирует стратегию
- ✅ **Достигает** поставленной цели

### Категории агентов в платформе

В системе AI Breadboard и Antigravity поддерживаются 3 основные категории агентов:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. СТАНДАРТНЫЕ PYTHON RE-ACT АГЕНТЫ (Core Code Agents)                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Местоположение: src/ai/agents/ (на базе Python + LangChain / LangGraph) │
│ Использование: Бэкенд-сервисы, FastAPI эндпоинты, поиск медиафайлов     │
│ Подробно: docs/ru/guides/standard-agents.md                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 2. ДИНАМИЧЕСКИЕ СУБАГЕНТЫ (Dynamic Subagents)                           │
├─────────────────────────────────────────────────────────────────────────┤
│ Создание: Динамически через define_subagent / invoke_subagent           │
│ Использование: Фоновые задачи, параллельный аудит, изолированные ветки  │
│ Подробно: docs/ru/guides/dynamic-subagents.md                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 3. НАВЫКИ-АГЕНТЫ (Skills-based Agents)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Местоположение: .agents/skills/ (создание через py manage_tools.py)     │
│ Использование: Декларативные регламенты, автоматизация CLI, runbooks    │
│ Подробно: docs/ru/guides/developing-skills.md                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Архитектура Agents

### Компоненты агента

```
┌──────────────────────────────────────────┐
│ AGENT (Агент)                           │
├──────────────────────────────────────────┤
│ ┌────────────────────────────────────┐  │
│ │ Инициализация (Setup)              │  │
│ │ • Модель ИИ                        │  │
│ │ • Инструменты (Tools)              │  │
│ │ • Память (Memory)                  │  │
│ │ • Конфигурация                     │  │
│ └────────────────────────────────────┘  │
│          ↓                               │
│ ┌────────────────────────────────────┐  │
│ │ Обработка входных данных           │  │
│ │ • Валидация                        │  │
│ │ • Форматирование                   │  │
│ │ • Подготовка контекста             │  │
│ └────────────────────────────────────┘  │
│          ↓                               │
│ ┌────────────────────────────────────┐  │
│ │ Основной цикл (Main Loop)          │  │
│ │ • Рассуждение (Reasoning)          │  │
│ │ • Выбор действия (Action Selection)│  │
│ │ • Наблюдение (Observation)        │  │
│ │ • Обновление памяти                │  │
│ └────────────────────────────────────┘  │
│          ↓                               │
│ ┌────────────────────────────────────┐  │
│ │ Финализация (Finalization)         │  │
│ │ • Форматирование результата        │  │
│ │ • Сохранение истории               │  │
│ │ • Возврат результата               │  │
│ └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Иерархия компонентов

```
Agent
├── Model Provider (Модель ИИ)
│   ├── OpenAI
│   ├── Gemini
│   ├── Anthropic
│   └── Локальные модели
├── Tools Manager (Менеджер инструментов)
│   ├── Skill Tools
│   ├── API Tools
│   └── Custom Tools
├── Memory Manager (Менеджер памяти)
│   ├── Conversation History
│   ├── Task Memory
│   └── Context Store
└── State Manager (Менеджер состояния)
    ├── Current Status
    ├── Variables
    └── Decision History
```

---

## Жизненный цикл агента

### Этапы выполнения

```
1. ИНИЦИАЛИЗАЦИЯ (Initialize)
   ├─ Создание объекта Agent
   ├─ Установка провайдера ИИ
   ├─ Загрузка инструментов
   └─ Инициализация памяти

2. ПОДГОТОВКА (Preparation)
   ├─ Валидация входных данных
   ├─ Построение system prompt
   ├─ Загрузка контекста
   └─ Инициализация состояния

3. ВЫПОЛНЕНИЕ (Execution)
   ├─ Итерация 1:
   │  ├─ Получить мысль от модели
   │  ├─ Парсить действие
   │  ├─ Выполнить инструмент
   │  └─ Получить наблюдение
   │
   ├─ Итерация N:
   │  └─ Повторить цикл...
   │
   └─ Условие выхода:
      ├─ Финальный ответ получен
      ├─ Максимум итераций достигнут
      └─ Ошибка при выполнении

4. ФИНАЛИЗАЦИЯ (Finalization)
   ├─ Форматирование результата
   ├─ Сохранение истории
   └─ Возврат результата пользователю
```

---

## Интеграция с провайдерами ИИ

### Поддерживаемые провайдеры

#### OpenAI

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

agent = Agent(
    model="gpt-4",
    provider="openai",
    client=client
)
```

**Преимущества:**
- ✅ Мощные модели (GPT-4, GPT-3.5)
- ✅ Быстрые ответы
- ✅ Хорошая поддержка function calling

**Недостатки:**
- 💰 Платные API
- 🌐 Требует интернет
- 🔐 Отправляет данные на сервер

#### Gemini (Google)

```python
from anthropic import Anthropic

agent = Agent(
    model="claude-3-opus",
    provider="anthropic"
)
```

**Преимущества:**
- ✅ Длинный контекст (200K tokens)
- ✅ Хорошее качество
- ✅ API более доступен

#### Локальные модели

```python
from ollama import Ollama

agent = Agent(
    model="mistral",
    provider="local",
    base_url="http://localhost:11434"
)
```

**Преимущества:**
- ✅ Полный контроль данных
- ✅ Бесплатно
- ✅ Работает оффлайн

**Недостатки:**
- ❌ Слабее облачных моделей
- ❌ Требует вычислительные ресурсы

---

## ReAct паттерн

### Что такое ReAct?

**ReAct** (Reasoning + Acting) — паттерн, который заставляет модель:

1. **Thought** (Мысль) — рассуждает о проблеме
2. **Action** (Действие) — вызывает инструмент
3. **Observation** (Наблюдение) — обрабатывает результат
4. **Repeat** (Повтор) — идет дальше или завершает

### Пример цикла ReAct

```
User: "Какая была погода в Москве 5 дней назад?"

---

Thought: Мне нужно узнать текущую дату и найти исторические 
данные о погоде в Москве.

Action: get_current_date

Observation: Текущая дата: 2024-01-15

---

Thought: 5 дней назад это было 2024-01-10. Мне нужна информация 
о погоде на эту дату.

Action: get_weather(city="Москва", date="2024-01-10")

Observation: 
{
  "date": "2024-01-10",
  "city": "Москва",
  "temperature": "-5°C",
  "condition": "Снег",
  "humidity": "75%"
}

---

Thought: Я получил информацию о погоде. Могу дать финальный ответ.

Final Answer: 5 дней назад в Москве (10 января) было -5°C, 
шел снег, влажность 75%.
```

---

## Обработка состояния

### Типы памяти

```
┌─────────────────────────────────────────────┐
│ MEMORY HIERARCHY (Иерархия памяти)          │
├─────────────────────────────────────────────┤
│                                             │
│ SHORT-TERM MEMORY (Кратковременная)        │
│ ├─ Текущий запрос                          │
│ ├─ Последние 3-5 сообщений                │
│ └─ Размер: 1-5 KB                          │
│                                             │
│ CONTEXT MEMORY (Контекстная)               │
│ ├─ История разговора                       │
│ ├─ Переменные состояния                    │
│ └─ Размер: 5-50 KB                         │
│                                             │
│ LONG-TERM MEMORY (Долговременная)          │
│ ├─ Кэш результатов                         │
│ ├─ Знания о домене                         │
│ └─ Размер: 50 KB - 1 MB                    │
│                                             │
└─────────────────────────────────────────────┘
```

### Управление контекстом

```python
class AgentState:
    def __init__(self):
        self.task = None
        self.variables = {}
        self.iteration = 0
        self.history = []
    
    def add_to_history(self, role: str, content: str):
        """Добавить сообщение в историю"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
    
    def get_context(self, max_tokens: int = 2000) -> str:
        """Получить контекст в пределах ограничения"""
        recent = self.history[-10:]  # Последние 10 сообщений
        return "\n".join([f"{m['role']}: {m['content']}" 
                         for m in recent])
    
    def update_variable(self, name: str, value: Any):
        """Обновить переменную состояния"""
        self.variables[name] = value
```

---

## Лучшие практики

### 1. Дизайн агента

✅ **Правильно:**
- Четкое определение задачи
- Простой набор инструментов (3-5)
- Ограничение по итерациям (макс. 10)
- Обработка ошибок и fallback

❌ **Неправильно:**
- Размытая задача
- Слишком много инструментов (20+)
- Бесконечные итерации
- Нет обработки ошибок

### 2. Промп инжиниринг

✅ **Правильно:**
```
You are a helpful assistant that helps users find information.

Available tools:
1. search_web(query: str) - Search the internet
2. get_weather(city: str) - Get current weather

Think carefully about which tool to use.
Use the format:
Thought: <your reasoning>
Action: <tool_name>(parameters)
Observation: <result>
```

❌ **Неправильно:**
```
You are helpful. Find information.
```

### 3. Инструменты

✅ **Правильно:**
- Четкое описание (docstring)
- Типизированные параметры
- Обработка ошибок
- Валидация входных данных

❌ **Неправильно:**
- Нет описания
- Слабая типизация
- Нет обработки ошибок

### 4. Тестирование

✅ **Правильно:**
- Unit тесты для инструментов
- Интеграционные тесты для агента
- Примеры использования
- Документация

❌ **Неправильно:**
- Нет тестов
- Только ручное тестирование

---

## Примеры агентов

### Пример 1: Простой информационный агент

```python
class InformationAgent:
    def __init__(self, model_provider):
        self.model = model_provider
        self.tools = {
            "search_web": search_web,
            "get_weather": get_weather,
            "get_current_date": get_current_date
        }
    
    def run(self, query: str) -> str:
        """Выполнить запрос"""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": query}
        ]
        
        max_iterations = 10
        for i in range(max_iterations):
            response = self.model.chat(messages)
            
            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()
            
            # Парсить и выполнить действие
            tool_name, params = parse_action(response)
            result = self.tools[tool_name](**params)
            
            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": f"Observation: {result}"
            })
        
        return "Не удалось получить результат"
    
    def _get_system_prompt(self) -> str:
        return """You are a helpful information agent.
        Available tools: search_web, get_weather, get_current_date
        Use ReAct format with Thought, Action, Observation."""
```

### Пример 2: Данные-ориентированный агент

```python
class DataAnalysisAgent:
    def __init__(self, model_provider, database):
        self.model = model_provider
        self.db = database
        self.tools = {
            "query_database": self._query_db,
            "analyze_data": self._analyze,
            "generate_report": self._report
        }
    
    def analyze(self, question: str) -> str:
        """Анализировать данные на основе вопроса"""
        # Реализация анализа данных
        pass
    
    def _query_db(self, sql: str):
        """Выполнить SQL запрос"""
        return self.db.execute(sql)
    
    def _analyze(self, data: list):
        """Анализировать данные"""
        return {
            "mean": sum(data) / len(data),
            "max": max(data),
            "min": min(data)
        }
    
    def _report(self, analysis: dict) -> str:
        """Сгенерировать отчет"""
        return f"Анализ: {analysis}"
```

---

## 📚 Дополнительные ресурсы

- [Архитектура системы](../ARCHITECTURE.md)
- [Динамические субагенты (Subagents)](dynamic-subagents.md)
- [Разработка Skills](developing-skills.md)
- [Стратегия тестирования](testing-strategy.md)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)

---

**Успехов в создании агентов!** 🚀
