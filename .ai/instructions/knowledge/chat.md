  Вот основные аспекты реализации чат-логики:

  1. Единый интерфейс взаимодействия (UnifiedChatModel)
  Ключевым компонентом является core/ai/unified_chat.py. Вместо прямой работы с API конкретного провайдера, приложение использует class UnifiedChatModel.
   * Автоматическое переключение: Если Google Gemini недоступен (или Returns ошибку), система автоматически переключается на Microsoft AI Foundry (локально развернутый
     qwen3-0.6b-generic-cpu).
   * Управление ключами: UnifiedChatModel управляет ротацией API-ключей Gemini, которые хранятся в защищенном файле core/secrets/gemini_keys.json.

  2. Структура запросов к модели
  В зависимости от типа задачи используются разные методы UnifiedChatModel:
   * chat(message, system_instruction, model_name): Базовый чат. Системная инструкция (System Prompt) загружается из .ai_instructions/prompts/chat/system_instruction.md.
   * ask_with_tools(question, tools, dispatch_tool_call): Сложные запросы, требующие доступа к инструментам (Function Calling). Модель receives list доступных функций, а
     dispatch_tool_call отвечает за исполнение выбранного инструмента.
   * embed(text): Используется для RAG (Retrieval-Augmented Generation), преобразуя текстовые запросы в векторные представления через Gemini Embeddings API.

  3. Integration API и Плагины
   * Маршрутизация: API-запросы чата обрабатываются в core/fastapi/router_chat.py (поддерживаются WebSockets/SSE для потоковых ответов).
   * Динамические плагины: Function load_plugins(ai_model) в plugins/__init__.py динамически сканирует директорию plugins/, импортирует каждый плагин и передает ему экземпляр
     модели. Это позволяет легко добавлять новые инструменты без изменения ядра чата.

  4. RAG-поиск по медиатеке
   * Логика RAG сосредоточена в core/ai/gemini/rag.py и media_rag.py.
   * Используется комбинация FAISS (для векторного поиска) и Gemini Embeddings для глубокого поиска по данным SQLite-базы медиатеки. Это позволяет боту отвечать на вопросы,
     опираясь на реальный состав библиотеки (например, "какие фильмы этого жанра есть на диске?").

  Резюме для разработки
  При добавлении нового функционала:
   1. Не обращайтесь к GoogleGenerativeAI напрямую, используйте UnifiedChatModel из core/ai/unified_chat.py.
   2. Используйте инструменты (tools) для взаимодействия с базой или другими сервисами, а не просите модель "вычислить" данные.
   3. Системные промпты должны находиться в .ai_instructions/prompts/.