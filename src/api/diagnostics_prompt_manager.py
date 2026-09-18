# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Diagnostics Prompt Manager
# =============================================================================
# Description:
#   Менеджер шаблонов промптов и системных инструкций для различных типов таблиц
#   системы (ПО, процессы, службы, задачи, сеть, реестр, пользователи, сайты, RAG, диски).
#   Обеспечивает загрузку, сохранение, сброс к значениям по умолчанию и форматирование.
#
# Examples:
#   >>> from src.api.diagnostics_prompt_manager import prompt_manager
#   >>> tmpl = prompt_manager.get_template("software")
#   >>> formatted_prompt = tmpl.format_prompt(title="Google Chrome", subtitle="Google LLC", metadata={}, raw_data="")
#
# File: diagnostics_prompt_manager.py
# Project: ai-breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер шаблонов промптов для аудита и объяснения таблиц."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.logger import logger

PROMPTS_DIR = Path("prompts/diagnostics")

DEFAULT_PROMPTS: Dict[str, Dict[str, Any]] = {
    "software": {
        "table_type": "software",
        "name": "Аудит установленного ПО",
        "description": "Промпт для анализа установленного программного обеспечения, проверки издателя и оценки рисков.",
        "system_instruction": "Ты — ведущий системный инженер и эксперт по безопасности программного обеспечения Windows. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный экспертный аудит установленного программного обеспечения:

Имя программы / Заголовок: {title}
Издатель / Вторичный заголовок: {subtitle}
Метаданные записи:
{metadata}
Исполняемый файл / Путь установки / Данные: {raw_data}

Верни СТРОГО JSON со следующей схемой (без markdown-разметки и без обратных кавычек):
{{
  "summary": "Краткое и понятное описание назначения программы на русском языке (что это, зачем нужно, кто разработчик)",
  "developer": "Разработчик или вендор ПО",
  "category": "Категория программного обеспечения",
  "security_verdict": "Оценка безопасности, легитимности, репутации и рисков",
  "performance_impact": "Влияние на дисковое пространство, автозапуск и фоновые процессы",
  "recommendation": "Практическая рекомендация: оставить, удалить, обновить или проверить",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "process": {
        "table_type": "process",
        "name": "Аудит процессов Windows",
        "description": "Промпт для анализа запущенных процессов, потребления ресурсов и обнаружения вредоносной активности.",
        "system_instruction": "Ты — эксперт по внутреннему устройству Windows (Windows Internals) и оптимизации производительности. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный экспертный аудит запущенного процесса Windows:

Имя процесса / Заголовок: {title}
Контекст выполнения / PID / Пользователь: {subtitle}
Метрики производительности и метаданные:
{metadata}
Командная строка запуска / Исполняемый путь: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Краткое описание назначения процесса (системный сервис ядра, пользовательское приложение, фоновый агент)",
  "developer": "Вендор / Разработчик (Microsoft Corporation или сторонний автор)",
  "category": "Системный процесс / Фоновая служба / Пользовательское приложение",
  "security_verdict": "Оценка легитимности процесса, пути запуска (%TEMP%, AppData, System32) и рисков",
  "performance_impact": "Оценка потребления CPU, памяти (RAM) и дискового ввода-вывода",
  "recommendation": "Рекомендация: завершить, оставить активным, ограничить приоритет или проверить на вирусы",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "service": {
        "table_type": "service",
        "name": "Аудит системных служб",
        "description": "Промпт для анализа служб Windows (Services), типов запуска и зависимостей.",
        "system_instruction": "Ты — системный администратор и эксперт по Windows Services. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный экспертный аудит службы Windows:

Имя службы / Заголовок: {title}
Отображаемое имя / Описание: {subtitle}
Параметры запуска и метаданные:
{metadata}
Бинарный путь / Исполняемый файл службы: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Назначение и роль службы в операционной системе Windows",
  "developer": "Разработчик службы (Microsoft / сторонний разработчик)",
  "category": "Фоновая служба Windows",
  "security_verdict": "Оценка безопасности исполняемого пути, учетной записи службы (LocalSystem, NetworkService) и прав",
  "performance_impact": "Влияние службы на время загрузки системы и потребление ресурсов",
  "recommendation": "Рекомендация: Auto (автозапуск), Manual (вручную), Disabled (отключить) или оставить",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "task": {
        "table_type": "task",
        "name": "Аудит задач планировщика",
        "description": "Промпт для анализа запланированных задач Windows Task Scheduler и их триггеров.",
        "system_instruction": "Ты — эксперт по администрированию Windows и анализу планировщика задач. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи экспертный аудит запланированной задачи Windows Task Scheduler:

Имя задачи: {title}
Путь в дереве задач / Описание: {subtitle}
Триггеры и метаданные:
{metadata}
Действие / Запускаемая команда: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Назначение задачи и контекст ее выполнения по расписанию",
  "developer": "Microsoft / Разработчик приложения",
  "category": "Задача планировщика (Task Scheduler)",
  "security_verdict": "Оценка легитимности триггера и команды (защита от механизмов закрепления Persistence)",
  "performance_impact": "Периодичность и нагрузка при срабатывании триггера",
  "recommendation": "Рекомендация по оптимизации или отключению задачи",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "network": {
        "table_type": "network",
        "name": "Аудит сетевых соединений и трафика",
        "description": "Промпт для анализа сетевых сокетов, удаленных IP-адресов, протоколов и портов.",
        "system_instruction": "Ты — сетевой архитектор и специалист по информационной безопасности (Network Security). Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный аудит сетевого соединения / пакета трафика:

Заголовок / Протокол: {title}
Соединение / Узлы (Local -> Remote): {subtitle}
Атрибуты соединения / Метрики:
{metadata}
Сырые данные сокета / Пакет / Процесс: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Характеристика сетевого соединения (внутреннее IPC, публичный веб-ресурс, облачный сервис, DNS)",
  "developer": "Сетевой стек / Владелец удаленного хоста (ASN/ISP)",
  "category": "Сетевое соединение",
  "security_verdict": "Оценка доверия к удаленному IP/порту, уровень шифрования (TLS/Cleartext) и потенциальные угрозы",
  "performance_impact": "Использование полосы пропускания и нагрузка на сокеты",
  "recommendation": "Рекомендация: разрешить, проверить процесс-владелец или заблокировать брандмауэром",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "registry": {
        "table_type": "registry",
        "name": "Аудит параметров системного реестра",
        "description": "Промпт для анализа ключей и значений реестра Windows (Windows Registry).",
        "system_instruction": "Ты — ведущий эксперт по Windows Registry и конфигурации системы. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи экспертный анализ параметра реестра Windows:

Имя параметра: {title}
Ветка реестра (Key Path): {subtitle}
Тип данных и метаданные:
{metadata}
Значение параметра: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Назначение параметра реестра и за какую функцию операционной системы/приложения он отвечает",
  "developer": "Microsoft Windows Registry",
  "category": "Параметр системного реестра",
  "security_verdict": "Влияние значения на политики безопасности (UAC, политики групп, сетевой доступ)",
  "performance_impact": "Влияние параметра на стабильность и скорость работы ОС",
  "recommendation": "Рекомендация по изменению или сохранению текущего значения (с указанием мер предосторожности)",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "user": {
        "table_type": "user",
        "name": "Аудит учетных записей и прав",
        "description": "Промпт для анализа пользователей, групп безопасности и привилегий Windows/Active Directory.",
        "system_instruction": "Ты — аудитор безопасности и администратор Active Directory / Windows SAM. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи аудит учетной записи / группы безопасности:

Имя пользователя / Группы: {title}
SID / Роль / Домен: {subtitle}
Метаданные и статус (активен, заблокирован, группы):
{metadata}
Дополнительные атрибуты / Права: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Описание типа учетной записи (локальный администратор, системная учетная запись, стандартный пользователь)",
  "developer": "Security Accounts Manager (SAM) / Active Directory",
  "category": "Учетная запись / Группа безопасности",
  "security_verdict": "Оценка привилегий (Least Privilege principle), рисков компрометации и срока действия пароля",
  "performance_impact": "Минимальное — обработка сессий входа",
  "recommendation": "Рекомендация по аудиту прав, блокировке неактивных записей или ротации учетных данных",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "website": {
        "table_type": "website",
        "name": "Аудит доступности и качества веб-сайтов",
        "description": "Промпт для анализа страниц сайта, HTTP статусов, задержек и SEO/аналитики.",
        "system_instruction": "Ты — Site Reliability Engineer (SRE) и эксперт по веб-производительности. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный аудит веб-страницы / ресурса:

URL / Путь ресурса: {title}
Полный адрес / Хост: {subtitle}
Метрики доступности, HTTP статус, задержка и аналитика:
{metadata}
Сырые данные ответа / Ошибки: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Анализ состояния веб-ресурса (доступность, код ответа, производительность)",
  "developer": "Веб-сервер / CDN / Хостинг-провайдер",
  "category": "Веб-сервис / Мониторинг",
  "security_verdict": "Оценка безопасности (HTTPS, SSL, заголовки безопасности)",
  "performance_impact": "Оценка времени отклика (Latency/TTFB) и нагрузки на сервер",
  "recommendation": "Рекомендация: нормальная работа, оптимизация кэширования, устранение 4xx/5xx ошибок",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "rag_doc": {
        "table_type": "rag_doc",
        "name": "Аудит документов базы знаний RAG",
        "description": "Промпт для анализа документов, чанков и векторных эмбеддингов базы знаний.",
        "system_instruction": "Ты — AI Data Engineer и архитектор RAG (Retrieval-Augmented Generation) систем. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи экспертный анализ документа базы знаний RAG:

Имя документа / Источник: {title}
Путь / Категория: {subtitle}
Метрики индексации, количество чанков, размер и статус:
{metadata}
Фрагмент текста / Сырые данные: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Описание содержания документа и его роли в базе знаний RAG",
  "developer": "RAG Knowledge Store",
  "category": "Документ базы знаний",
  "security_verdict": "Проверка отсутствия утечек конфиденциальных данных и секретов в индексируемом документе",
  "performance_impact": "Влияние на размер векторного индекса и качество семантического поиска",
  "recommendation": "Рекомендация: актуален, требует переиндексации, оптимизации чанкования или дополнения",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "disk": {
        "table_type": "disk",
        "name": "Аудит дисков и накопителей",
        "description": "Промпт для анализа свободного пространства дисков, файловых систем и состояния хранилищ.",
        "system_instruction": "Ты — системный архитектор и специалист по дисковым подсистемам Windows. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи аудит дискового накопителя / тома:

Том / Буква диска: {title}
Тип файловой системы / Название тома: {subtitle}
Метрики заполненности (Free / Total / %):
{metadata}
Дополнительные данные: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Состояние и назначение дискового тома (системный, рабочий, архивный)",
  "developer": "Storage Controller / Windows Volume Manager",
  "category": "Дисковый накопитель",
  "security_verdict": "Проверка целостности файловой системы и доступности тома",
  "performance_impact": "Оценка дефицита свободного места и влияния на swap/виртуальную память",
  "recommendation": "Рекомендация: очистка временных файлов, дефрагментация или расширение тома",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "startup": {
        "table_type": "startup",
        "name": "Аудит автозагрузки программ",
        "description": "Промпт для анализа элементов автозапуска Windows (Registry Run, Startup Folder, Services).",
        "system_instruction": "Ты — специалист по оптимизации Windows и анализу автозагрузки ПО. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный аудит элемента автозагрузки Windows:

Имя программы / Запись: {title}
Издатель / Расположение ключа: {subtitle}
Метаданные записи:
{metadata}
Команда запуска / Исполняемый файл: {raw_data}

Верни СТРОГО JSON со следующей схемой:
{{
  "summary": "Назначение программы и обоснованность ее автоматического запуска при старте системы",
  "developer": "Издатель программы",
  "category": "Элемент автозагрузки",
  "security_verdict": "Оценка легитимности расположения автозапуска и доверия к исполняемому файлу",
  "performance_impact": "Влияние на время старта операционной системы и фоновое потребление RAM",
  "recommendation": "Рекомендация: оставить в автозагрузке, отключить или удалить",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["title", "subtitle", "metadata", "raw_data"]
    },
    "generic": {
        "table_type": "generic",
        "name": "Универсальный аудит сущности",
        "description": "Базовый шаблон для любых таблиц и структурированных сущностей системы.",
        "system_instruction": "Ты — ведущий системный инженер, эксперт по безопасности Windows и SRE-архитектор. Отвечай строго в формате чистого JSON.",
        "prompt_template": """Проведи детальный экспертный аудит и объясни сущность из интерфейса системы:

Тип таблицы/сущности: {table_type}
Имя / Заголовок: {title}
Подзаголовок / Контекст: {subtitle}
Метаданные записи:
{metadata}
Сырые данные / Команда / Путь: {raw_data}

Верни СТРОГО JSON со следующей схемой (без markdown-разметки):
{{
  "summary": "Краткое и четкое описание сущности на русском языке (что это, зачем нужно, кто создал)",
  "developer": "Разработчик, вендор или системный компонент",
  "category": "Категория сущности",
  "security_verdict": "Оценка безопасности, легитимности, рисков и доверия",
  "performance_impact": "Влияние на ресурсы (RAM, CPU, диск, сеть, время отклика)",
  "recommendation": "Практическая рекомендация: что делать с элементом (оставить, оптимизировать, отключить, обновить, проверить)",
  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]
}}""",
        "variables": ["table_type", "title", "subtitle", "metadata", "raw_data"]
    }
}


class DiagnosticPromptTemplate(BaseModel):
    """Модель шаблона промпта для типа таблицы."""
    table_type: str = Field(description="Уникальный идентификатор типа таблицы")
    name: str = Field(description="Человекочитаемое название")
    description: str = Field(default="", description="Описание назначения промпта")
    system_instruction: str = Field(description="Системная инструкция для LLM")
    prompt_template: str = Field(description="Шаблон текста промпта с переменными {title}, {subtitle}, {metadata}, {raw_data}")
    variables: List[str] = Field(default_factory=lambda: ["title", "subtitle", "metadata", "raw_data"], description="Доступные переменные шаблона")
    is_customized: bool = Field(default=False, description="Признак пользовательской модификации")

    def format_prompt(self, title: str, subtitle: str, metadata: Dict[str, Any], raw_data: str) -> str:
        """Форматирует промпт подставляя фактические значения полей."""
        meta_str = "\n".join([f"- {k}: {v}" for k, v in metadata.items()]) if metadata else "- Нет дополнительных метаданных"
        try:
            return self.prompt_template.format(
                table_type=self.table_type,
                title=title or "Не указано",
                subtitle=subtitle or "Нет",
                metadata=meta_str,
                raw_data=raw_data or "Нет"
            )
        except Exception as e:
            logger.warning(f"Ошибка при подстановке переменных в промпт '{self.table_type}': {e}. Применен базовый формат.")
            return f"{self.prompt_template}\n\n[Контекст: {title} | {subtitle} | {raw_data}]"


class DiagnosticsPromptManager:
    """Управляет жизненным циклом и сохранением шаблонов промптов для таблиц."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or PROMPTS_DIR
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Создает каталог хранения промптов если он отсутствует."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Не удалось создать каталог промптов {self.storage_dir}: {e}")

    def _get_file_path(self, table_type: str) -> Path:
        """Возвращает путь к файлу шаблона промпта."""
        safe_type = "".join(c for c in table_type if c.isalnum() or c in ("_", "-")).lower()
        return self.storage_dir / f"{safe_type}.json"

    def get_template(self, table_type: str) -> DiagnosticPromptTemplate:
        """Возвращает шаблон промпта для указанного типа таблицы.

        Если сохранен пользовательский файл JSON в prompts/diagnostics/, загружает его.
        Иначе возвращает стандартный шаблон по умолчанию.
        """
        key = table_type.lower()
        file_path = self._get_file_path(key)

        if file_path.is_file():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                return DiagnosticPromptTemplate(
                    table_type=data.get("table_type", key),
                    name=data.get("name", DEFAULT_PROMPTS.get(key, {}).get("name", key.capitalize())),
                    description=data.get("description", ""),
                    system_instruction=data.get("system_instruction", ""),
                    prompt_template=data.get("prompt_template", ""),
                    variables=data.get("variables", ["title", "subtitle", "metadata", "raw_data"]),
                    is_customized=True
                )
            except Exception as e:
                logger.warning(f"Не удалось загрузить кастомный промпт из {file_path}: {e}")

        # Возврат значения по умолчанию
        if key in DEFAULT_PROMPTS:
            raw_def = DEFAULT_PROMPTS[key]
            return DiagnosticPromptTemplate(
                table_type=raw_def["table_type"],
                name=raw_def["name"],
                description=raw_def["description"],
                system_instruction=raw_def["system_instruction"],
                prompt_template=raw_def["prompt_template"],
                variables=raw_def["variables"],
                is_customized=False
            )

        # Fallback к generic
        raw_generic = DEFAULT_PROMPTS["generic"]
        return DiagnosticPromptTemplate(
            table_type=key,
            name=f"Аудит {key}",
            description=f"Шаблон аудита для типа {key}",
            system_instruction=raw_generic["system_instruction"],
            prompt_template=raw_generic["prompt_template"],
            variables=raw_generic["variables"],
            is_customized=False
        )

    def list_templates(self) -> List[DiagnosticPromptTemplate]:
        """Возвращает список всех доступных шаблонов промптов."""
        all_keys = list(DEFAULT_PROMPTS.keys())
        
        # Также проверяем файлы в каталоге, которых нет в DEFAULT_PROMPTS
        if self.storage_dir.is_dir():
            for p in self.storage_dir.glob("*.json"):
                stem = p.stem.lower()
                if stem not in all_keys:
                    all_keys.append(stem)

        return [self.get_template(k) for k in all_keys]

    def save_template(
        self,
        table_type: str,
        system_instruction: str,
        prompt_template: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> DiagnosticPromptTemplate:
        """Сохраняет пользовательский шаблон промпта в файл."""
        key = table_type.lower()
        file_path = self._get_file_path(key)
        
        default_info = DEFAULT_PROMPTS.get(key, {})
        final_name = name or default_info.get("name", key.capitalize())
        final_desc = description if description is not None else default_info.get("description", "")
        variables = default_info.get("variables", ["title", "subtitle", "metadata", "raw_data"])

        payload = {
            "table_type": key,
            "name": final_name,
            "description": final_desc,
            "system_instruction": system_instruction,
            "prompt_template": prompt_template,
            "variables": variables
        }

        self._ensure_storage()
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Сохранен пользовательский шаблон промпта для '{key}' в {file_path}")

        return DiagnosticPromptTemplate(
            table_type=key,
            name=final_name,
            description=final_desc,
            system_instruction=system_instruction,
            prompt_template=prompt_template,
            variables=variables,
            is_customized=True
        )

    def reset_template(self, table_type: str) -> DiagnosticPromptTemplate:
        """Сбрасывает шаблон промпта к дефолтному состоянию, удаляя файл кастомизации."""
        key = table_type.lower()
        file_path = self._get_file_path(key)
        if file_path.is_file():
            try:
                file_path.unlink()
                logger.info(f"Сброшен шаблон промпта для '{key}' (удален {file_path})")
            except Exception as e:
                logger.error(f"Не удалось удалить файл шаблона {file_path}: {e}")

        return self.get_template(key)


# Глобальный синглтон-экземпляр
prompt_manager = DiagnosticsPromptManager()

__all__ = [
    "DiagnosticPromptTemplate",
    "DiagnosticsPromptManager",
    "prompt_manager",
    "DEFAULT_PROMPTS"
]
