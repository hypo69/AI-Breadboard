import json
import sys
from dataclasses import dataclass
from pathlib import Path
from src.utils.printer import pprint as print
_PROMPTS_ROOT: Path = Path(__file__).resolve().parent.parent / 'prompts'
_RAG_DIR: Path = Path(__file__).resolve().parent.parent / 'tmp' / 'rag'
_INDEX_PATH: Path = _RAG_DIR / 'rules.index'
_DOCUMENTS_PATH: Path = _RAG_DIR / 'documents.json'
_MODEL_NAME: str = 'sentence-transformers/all-MiniLM-L6-v2'
_CORE_MODULES: list[str] = ['core/identity.md', 'core/categories.md']
_CHAT_MODULES: list[str] = ['chat/chat_rules.md', 'narrator/narrator_style.md']
_NARRATOR_MODULES: list[str] = ['narrator/tts_rules.md', 'narrator/narrator_style.md']
_EXAMPLE_MODULE: str = 'examples/series_example.json'
_SCHEMA_MODULE: str = 'core/output_schema.json'
_ALWAYS_INCLUDE: list[str] = ['identity.md', 'categories.md']

def _read_file(relative_path: str) -> str:
    """
    Прочитать файл из директории prompts.

    Args:
        relative_path (str): Путь относительно _PROMPTS_ROOT.

    Returns:
        str: Содержимое файла.
    """
    full_path: Path = _PROMPTS_ROOT / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f'Prompt module not found: {full_path}')
    return full_path.read_text(encoding='utf-8')

def _load_modules(module_paths: list[str]) -> str:
    """
    Загрузить и соединить несколько модулей подсказок.

    Args:
        module_paths (list[str]): Список относительных путей к модулям.

    Returns:
        str: Объединённое содержимое всех модулей.
    """
    parts: list[str] = [_read_file(p).strip() for p in module_paths]
    return '\n\n---\n\n'.join(parts)

def _load_schema_block() -> str:
    """
    Загрузить JSON‑схему и обернуть в markdown‑блок.

    Returns:
        str: Схема в виде markdown‑блока.
    """
    raw: str = _read_file(_SCHEMA_MODULE)
    parsed: dict = json.loads(raw)
    formatted: str = json.dumps(parsed, ensure_ascii=False, indent=2)
    return f'## JSON Response Schema\n\n```json\n{formatted}\n```'

def _load_example_block() -> str:
    """
    Загрузить пример JSON и обернуть в markdown‑блок.

    Returns:
        str: Пример в виде markdown‑блока.
    """
    raw: str = _read_file(_EXAMPLE_MODULE)
    parsed: dict = json.loads(raw)
    formatted: str = json.dumps(parsed, ensure_ascii=False, indent=2)
    return f'## Example Filled Response (Series)\n\n```json\n{formatted}\n```'
from src.rag.rules_rag import RulesRAG, RulesSearchResult
SearchResult = RulesSearchResult

def load_chat_prompt(query: str='Create media description for chat') -> str:
    """
    Сформировать системный промпт для Chat‑агента через FAISS‑поиск.

    Args:
        query (str): Запрос для выбора релевантных модулей.

    Returns:
        str: Готовый системный промпт (~5‑8\u202fК символов).
    """
    rag: RulesRAG = RulesRAG()
    context: str = rag.build_context(query, top_k=4)
    return context

def load_narrator_prompt(query: str='Prepare text for voice narrator TTS') -> str:
    """
    Сформировать системный промпт для Narrator‑агента через FAISS‑поиск.

    Args:
        query (str): Запрос для выбора релевантных модулей.

    Returns:
        str: Готовый системный промпт (~5‑8\u202fК символов).
    """
    rag: RulesRAG = RulesRAG()
    context: str = rag.build_context(query, top_k=4)
    return context

def load_chat_prompt_static() -> str:
    """
    Сборка полного промпта для Chat‑агента без FAISS‑поиска.

    Returns:
        str: Полный промпт (~20\u202fК символов).
    """
    sections: list[str] = [_load_modules(_CORE_MODULES), _load_schema_block(), _load_modules(_CHAT_MODULES), _load_example_block()]
    return '\n\n---\n\n'.join(sections)

def load_narrator_prompt_static() -> str:
    """
    Сборка полного промпта для Narrator‑агента без FAISS‑поиска.

    Returns:
        str: Полный промпт (~20\u202fК символов).
    """
    sections: list[str] = [_load_modules(_CORE_MODULES), _load_schema_block(), _load_modules(_NARRATOR_MODULES), _load_example_block()]
    return '\n\n---\n\n'.join(sections)
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('=== Static Mode ===')
    chat_s: str = load_chat_prompt_static()
    narrator_s: str = load_narrator_prompt_static()
    print(f'Chat (static):     {len(chat_s):>6} characters  |  {len(chat_s.split()):>5} words')
    print(f'Narrator (static): {len(narrator_s):>6} characters  |  {len(narrator_s.split()):>5} words')
    print()
    if not INDEX_PATH.exists():
        print('FAISS index not found. Run: python rag/build_rules_index.py')
        sys.exit(0)
    print('=== RAG Mode ===')
    rag: RulesRAG = RulesRAG()
    test_queries: list[str] = ['Series description', 'Rules for TTS narrator', 'Media categories action spies']
    for q in test_queries:
        results = rag.search(q, top_k=3)
        files: list[str] = [r.file for r in results]
        print(f"  '{q}' → {files}")
    print()
    chat_r: str = load_chat_prompt('Series description')
    narrator_r: str = load_narrator_prompt('Text for narrator')
    print(f'Chat (RAG):        {len(chat_r):>6} characters  |  {len(chat_r.split()):>5} words')
    print(f'Narrator (RAG):    {len(narrator_r):>6} characters  |  {len(narrator_r.split()):>5} words')
    reduction: float = (1 - len(chat_r) / len(chat_s)) * 100
    print(f'\nPrompt compression: {reduction:.0f}%')