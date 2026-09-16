# Глава 3. Локальный инференс: Hugging Face и ONNX DirectML

> **Цель главы:** Освоить запуск открытых моделей непосредственно внутри Python-процесса, работу с кэшем весов, применение шаблонов диалогов (chat_template) и аппаратное ускорение через DirectML на любых видеокартах.

---

## 3.1. Архитектура локального In-Process инференса

Большинство существующих решений (Ollama, LM Studio, vLLM) запускают отдельные серверные процессы и демоны, общаясь с ними через локальную сеть.

В ibreadboard реализован также **In-Process инференс** ([src/ai/providers/huggingface/](../../../src/ai/providers/huggingface/) и [src/ai/providers/onnx/](../../../src/ai/providers/onnx/)):
- Веса модели загружаются непосредственно в адресное пространство процесса (RAM / VRAM).
- Исключаются накладные расходы на сериализацию HTTP-запросов и межпроцессное взаимодействие.
- Асинхронные вызовы изолируются в syncio executor, предотвращая блокировку Event Loop сервера FastAPI.

---

## 3.2. Hugging Face In-Process: Загрузка, кэш и Chat Templates

Пакет [src/ai/providers/huggingface/](../../../src/ai/providers/huggingface/) решает три ключевые задачи:

### 1. Управление кэшем моделей
Функция _get_models_dir() автоматически считывает локальный кэш ~/.cache/huggingface/hub или путь, указанный в переменной HF_MODELS_DIR.

### 2. Шаблонизация диалогов (pply_chat_template)
Различные модели используют разные служебные токены для разметки диалога. Вместо ручной сборки строк используется токенизатор модели через pply_chat_template.

---

## 3.3. Microsoft ONNX Runtime и ускорение через DirectML

В [src/ai/providers/onnx/](../../../src/ai/providers/onnx/) используется **Microsoft ONNX Runtime** с провайдером **DirectML**:

### Преимущества DirectML:
1. **Кросс-вендорность:** Работает с любыми DirectX 12-совместимыми графическими процессорами.
2. **Низкое потребление памяти:** Квантованные ONNX-модели (INT4 / INT8).
3. **Плавная деградация:** Переключение на CPU без краха приложения.

`python
from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer

# Загрузка ONNX модели с DirectML ускорением
model = ORTModelForCausalLM.from_pretrained(
    model_path,
    provider='DirectMLExecutionProvider',
    session_options=session_options
)
tokenizer = AutoTokenizer.from_pretrained(model_path)
`

---

## 3.4. Резюме

1. In-process инференс позволяет запускать модели прямо в памяти приложения без сторонних демонов.
2. Использование pply_chat_template гарантирует корректную разметку диалоговых токенов.
3. Провайдер DirectMLExecutionProvider в ONNX Runtime открывает аппаратное ускорение ИИ на видеокартах любого производителя.
