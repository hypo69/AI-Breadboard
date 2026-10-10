# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Diagnostics Prompt Manager
# =============================================================================
# Description:
#   Менеджер шаблонов промптов и системных инструкций для аудита и объяснения таблиц.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.diagnostics_prompt_manager import DiagnosticPromptTemplate, prompt_manager
#
#     tmpl = prompt_manager.get_template('user_account')
#     prompt = tmpl.format_prompt(title='Admin', subtitle='SID: S-1-5-21...', metadata={}, raw_data='')
#     print(tmpl.system_instruction)
#
# File: diagnostics_prompt_manager.py
# Project: ai-breadboard
# Package: apps.windows.api
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 12:41:00
# =============================================================================

from __future__ import annotations
"""Менеджер шаблонов промптов и системных инструкций для аудита и объяснения таблиц."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from logger import logger

PROMPTS_DIR = Path('prompts/diagnostics')

DEFAULT_PROMPTS: Dict[str, Dict[str, Any]] = {
    'cpu': {
        'table_type': 'cpu',
        'name': 'Аудит спецификаций и состояния процессора (CPU)',
        'description': 'Промпт для экспертного анализа микроархитектуры CPU, сокета, частотного потенциала, кэш-памяти, энергоэффективности и аппаратных уязвимостей.',
        'system_instruction': 'Ты — ведущий системный архитектор, эксперт по микроархитектуре CPU (x86_64/ARM), аппаратным инструкциям и оптимизации производительности железа. Отвечай строго в формате чистого JSON.',
        'prompt_template': 'Проведи детальный экспертный аудит и анализ процессора (CPU):\n\nМодель процессора / Заголовок: {title}\nВендор / Сокет / Конфигурация: {subtitle}\nСпецификации и метаданные:\n{metadata}\nСырые параметры телеметрии / Инвентарь: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Подробное резюме о процессоре: микроархитектура, технологический процесс, сегмент применения и общая производительность",\n  "developer": "Вендор процессора (Intel / AMD / ARM / Apple)",\n  "category": "Центральный процессор (CPU)",\n  "security_verdict": "Аппаратная безопасность: аппаратные уязвимости (Spectre/Meltdown/Downfall) и статус их изоляции/патчей",\n  "performance_impact": "Производительность: однопоточный/многопоточный потенциал, эффективность кэш-памяти L2/L3, тепловыделение (TDP)",\n  "recommendation": "Рекомендации по охлаждению, профилям питания (Power Plan), разгону/андервольтингу и сценариям нагрузок",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'gpu': {
        'table_type': 'gpu',
        'name': 'Аудит спецификаций и состояния видеокарты (GPU)',
        'description': 'Промпт для экспертного анализа видеокарты (GPU), видеопамяти VRAM, архитектуры, TDP, частотного потенциала, температурного режима и драйверов.',
        'system_instruction': 'Ты — ведущий системный архитектор и специалист по аппаратной графике (GPU, DirectX, Vulkan, CUDA, OpenCL). Отвечай строго в формате чистого JSON.',
        'prompt_template': 'Проведи детальный экспертный аудит и анализ видеокарты (GPU):\n\nМодель видеокарты / Заголовок: {title}\nВендор / Шина / Интерфейс: {subtitle}\nСпецификации и метаданные:\n{metadata}\nСырые параметры телеметрии / Сенсоры: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Подробное резюме о видеокарте: архитектура, поколение, сегмент применения, возможности вычислений/рендеринга",\n  "developer": "Вендор GPU (NVIDIA / AMD / Intel)",\n  "category": "Графический ускоритель (GPU)",\n  "security_verdict": "Статус драйверов, безопасность прошивки (VBIOS), наличие критических багов или уязвимостей в драйверах",\n  "performance_impact": "Производительность: объем и пропускная способность VRAM, TDP/энергопотребление, термический запас и троттлинг",\n  "recommendation": "Рекомендации по актуализации драйверов, профилям охлаждения, настройкам электропитания и разгону/андервольтингу",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'software': {
        'table_type': 'software',
        'name': 'Аудит установленного ПО',
        'description': 'Промпт для детального анализа установленного программного обеспечения, издателя, открытости исходного кода и репутации.',
        'system_instruction': 'Ты — ведущий системный инженер и эксперт по безопасности программного обеспечения Windows. Используй поиск в интернете (Web Grounding) для точной идентификации программы, разработчика, официального сайта и назначения. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи детальный экспертный аудит установленного программного обеспечения с проверкой фактов в интернете:\n\nИмя программы / Заголовок: {title}\nИздатель / Вторичный заголовок: {subtitle}\nМетаданные записи:\n{metadata}\nИсполняемый файл / Путь установки / Данные: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Исчерпывающее и понятное описание назначения программы (что это за софт, какие ключевые функции выполняет, открытый или проприетарный код, официальный проект/сайт, зачем установлен)",\n  "developer": "Точный разработчик, компания, вендор или сообщество (например: Microsoft Corporation, LibreHardwareMonitor Team, VideoLAN)",\n  "category": "Категория программного обеспечения (Системная утилита, Офисный пакет, Разработка, Медиаплеер и т.д.)",\n  "security_verdict": "Оценка безопасности: репутация, легитимность, цифровая подпись, права доступа и потенциальные риски",\n  "performance_impact": "Влияние на ресурсы: дисковое пространство, службы автообновления, фоновые агенты",\n  "recommendation": "Практическая рекомендация: оставить, обновить, удалить или настроить параметры",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2", "Рекомендованное действие 3"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'process': {
        'table_type': 'process',
        'name': 'Аудит процессов Windows',
        'description': 'Промпт для глубокого анализа запущенных процессов, низкоуровневых драйверов режима ядра, назначения утилиты и безопасности.',
        'system_instruction': 'Ты — ведущий эксперт по внутреннему устройству Windows (Windows Internals), аналитик информационной безопасности и системный архитектор. Используй данные из интернета (Web Grounding) для точной идентификации программы, репозитория, разработчика, открытого исходного кода и драйверов ядра. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи детальный экспертный аудит запущенного процесса Windows с поиском актуальной информации в интернете:\n\nИмя процесса / Заголовок: {title}\nКонтекст выполнения / PID / Пользователь: {subtitle}\nМетрики производительности и метаданные:\n{metadata}\nКомандная строка запуска / Исполняемый путь: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Подробное и понятное описание программы и процесса (что это за утилита/сервис, какие задачи решает, открытый/закрытый исходный код, репозиторий GitHub/сайт, зачем запущен этот процесс в системе)",\n  "developer": "Точный вендор / Разработчик / Сообщество (например: LibreHardwareMonitor Team, Microsoft Corporation, Google LLC, Valve)",\n  "category": "Категория (Системный мониторинг / Аппаратная утилита / Пользовательское приложение / Служба ядра)",\n  "security_verdict": "Глубокая оценка безопасности: легитимность, цифровая подпись, использование драйверов режима ядра (Ring 0 / WinRing0 / InpOut32), типичные каталоги запуска и риски подмены",\n  "performance_impact": "Влияние на ресурсы: нагрузка на процессор (CPU), видеокарту (GPU), оперативную память (RAM), интервал опроса сенсоров и энергопотребление",\n  "recommendation": "Практическая рекомендация эксперта: стоит ли оставлять активным, запускать от администратора, настроить автозапуск или проверить цифровую подпись",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2", "Рекомендованное действие 3"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'file_event': {
        'table_type': 'file_event',
        'name': 'Аудит файловых событий WinAPI',
        'description': 'Промпт для анализа событий изменения файловой системы (ReadDirectoryChangesW) и процессов-инициаторов.',
        'system_instruction': 'Ты — эксперт по цифровой криминалистике Windows (Forensics) и анализу файловой активности. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи аудит файлового события Windows:\n\nСобытие / Заголовок: {title}\nПуть / Время: {subtitle}\nМетаданные события:\n{metadata}\nСырые данные WinAPI: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Характеристика операции файловой системы (создание, изменение, удаление, переименование) и контекст процесса",\n  "developer": "Процесс-инициатор / Файловая система NTFS/ReFS",\n  "category": "Файловая активность (File Activity)",\n  "security_verdict": "Оценка безопасности: легитимная запись приложения, временные файлы или подозрительная массовая модификация/удаление",\n  "performance_impact": "Влияние дисковых операций на ресурс накопителя (IOPS, Wear Level)",\n  "recommendation": "Рекомендация по безопасности и мониторингу каталога",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'service': {
        'table_type': 'service',
        'name': 'Аудит системных служб Windows',
        'description': 'Промпт для анализа системных служб (Services), типа запуска, учетной записи и безопасности.',
        'system_instruction': 'Ты — ведущий системный архитектор и специалист по безопасности служб Windows. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи аудит службы Windows:\n\nИмя службы / Заголовок: {title}\nОтображаемое имя / Статус: {subtitle}\nМетаданные службы:\n{metadata}\nПараметры запуска / Двоичный путь: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Назначение службы и ее роль в ОС",\n  "developer": "Разработчик / Издатель",\n  "category": "Служба Windows (Windows Service)",\n  "security_verdict": "Оценка безопасности: учетная запись выполнения (LocalSystem, NetworkService) и риски",\n  "performance_impact": "Влияние на время загрузки и фоновые ресурсы",\n  "recommendation": "Рекомендации по типу запуска (Авто/Вручную/Отключено)",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'network': {
        'table_type': 'network',
        'name': 'Аудит сетевых соединений и адаптеров',
        'description': 'Промпт для анализа сетевых интерфейсов, открытых портов, удаленных IP и безопасности соединений.',
        'system_instruction': 'Ты — сетевой инженер и эксперт по сетевой безопасности Windows. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи аудит сетевого соединения / интерфейса:\n\nИнтерфейс / Соединение: {title}\nЛокальный / Удаленный адрес: {subtitle}\nМетаданные сети:\n{metadata}\nСырые параметры / Статистика: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Характеристика соединения и назначение порта/протокола",\n  "developer": "Процесс-владелец сокета / Сетевой стек",\n  "category": "Сетевая активность (Network)",\n  "security_verdict": "Оценка безопасности: легитимность удаленного хоста, шифрование и открытые порты",\n  "performance_impact": "Пропускная способность и задержки",\n  "recommendation": "Рекомендации по настройке брандмауэра и безопасности",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'user_account': {
        'table_type': 'user_account',
        'name': 'Аудит учетных записей Windows (Users & Principals)',
        'description': 'Промпт для экспертного анализа учетных записей пользователей, групп безопасности, SID/RID, прав администратора и встроенных системных аккаунтов.',
        'system_instruction': 'Ты — ведущий системный администратор и эксперт по безопасности Active Directory и локальной безопасности Windows (SAM, LSA, SID, UAC, SpecialAccounts). Используй поиск в интернете (Web Grounding) для точной идентификации назначения аккаунта (например DefaultAccount / System Managed Account для UWP, WDAGUtilityAccount, Guest, Administrator). Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи детальный экспертный аудит учетной записи Windows с онлайн-исследованием:\n\nИмя аккаунта / Заголовок: {title}\nПодзаголовок / SID: {subtitle}\nМетаданные учетной записи:\n{metadata}\nСырые параметры / Конфигурация: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Исчерпывающее описание учетной записи (что это за аккаунт, встроенный ли он в Windows, кем и для каких задач используется, например System Managed Account для UWP/AppContainer, гостевой доступ, локальный админ и т.д.)",\n  "developer": "Принадлежность аккаунта (Операционная система Windows / Microsoft / Локальный пользователь / Домен Active Directory)",\n  "category": "Категория (Встроенная системная учетная запись / Локальный администратор / Пользовательская запись / Сервисный аккаунт)",\n  "security_verdict": "Оценка безопасности: привилегии (Admin/Standard), статус активности (Enabled/Disabled), требования к паролю и риски несанкционированного доступа",\n  "performance_impact": "Фоновые процессы, потребление оперативной памяти и размер локального профиля на диске",\n  "recommendation": "Практическая рекомендация по управлению учетной записью (оставить как есть, отключить, ограничить права, сменить пароль)",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'security_event': {
        'table_type': 'security_event',
        'name': 'Аудит событий безопасности Windows (Security Log)',
        'description': 'Промпт для анализа событий аудита безопасности (Event ID), аутентификации, входов в систему и действий с правами.',
        'system_instruction': 'Ты — эксперт по анализу журналов безопасности Windows (Security Event Log, Windows Defender, Logon Types, Kerberos/NTLM, Audit Policies). Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи экспертный аудит события безопасности Windows:\n\nСобытие / Event ID: {title}\nКонтекст / Время: {subtitle}\nМетаданные события:\n{metadata}\nСырые данные аудита / Описание: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Подробное объяснение события безопасности: что произошло, какой механизм Windows задействован",\n  "developer": "Подсистема безопасности Windows (LSA, Kerberos, SAM, Defender, UAC)",\n  "category": "Событие безопасности (Security Audit Event)",\n  "security_verdict": "Оценка легитимности: штатное системное действие, успешная аутентификация или подозрительная активность / аномалия",\n  "performance_impact": "Влияние на журнал аудита и политику логирования",\n  "recommendation": "Рекомендации системному администратору по реагированию",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'task': {
        'table_type': 'task',
        'name': 'Аудит задач планировщика Windows (Task Scheduler)',
        'description': 'Промпт для анализа запланированных заданий Windows, триггеров запуска, исполняемых модулей и привилегий.',
        'system_instruction': 'Ты — ведущий системный администратор и эксперт по безопасности задач Windows (Task Scheduler, COM Handlers, Scheduled Tasks). Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи детальный аудит задачи планировщика Windows:\n\nИмя задачи / Заголовок: {title}\nПуть / Автор / Статус: {subtitle}\nМетаданные задачи:\n{metadata}\nДействие / Командная строка: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Назначение задачи планировщика и ее роль в системе",\n  "developer": "Издатель / Разработчик задачи",\n  "category": "Запланированная задача (Scheduled Task)",\n  "security_verdict": "Оценка безопасности: легитимность исполняемого пути, контекст запуска (SYSTEM/User) и риски персистентности",\n  "performance_impact": "Влияние на фоновые ресурсы и частоту запуска",\n  "recommendation": "Рекомендация по управлению задачей (включить/отключить/изменить триггеры)",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'registry': {
        'table_type': 'registry',
        'name': 'Аудит параметров системного реестра Windows',
        'description': 'Промпт для анализа ключей реестра, политик, параметров конфигурации и твиков безопасности.',
        'system_instruction': 'Ты — ведущий эксперт по реестру Windows (HKLM, HKCU, HKCR, Group Policies) и твикам оптимизации. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи экспертный анализ параметра или ветки реестра Windows:\n\nПараметр реестра / Ключ: {title}\nВетка / Тип значения: {subtitle}\nМетаданные записи:\n{metadata}\nЗначение параметра / Данные: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Назначение и функционал данного параметра реестра",\n  "developer": "Подсистема Windows / Приложение",\n  "category": "Реестр Windows (Registry Setting)",\n  "security_verdict": "Влияние на безопасность: стандартное значение, системная политика или критический твик безопасности",\n  "performance_impact": "Влияние на производительность и поведение системы",\n  "recommendation": "Рекомендации по настройке или сбросу значения",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'disk': {
        'table_type': 'disk',
        'name': 'Аудит дисков и томов (Storage & Drives)',
        'description': 'Промпт для анализа дисковых накопителей, файловых систем, разделов, SMART телеметрии и износа.',
        'system_instruction': 'Ты — системный архитектор и специалист по дисковым подсистемам Windows, файловым системам (NTFS, ReFS) и здоровью накопителей (NVMe/SSD/HDD, SMART). Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи экспертный аудит диска или накопителя:\n\nМодель накопителя / Буква: {title}\nТип носителя / Раздел: {subtitle}\nМетаданные диска:\n{metadata}\nСырые данные / Сенсоры / SMART: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Характеристика накопителя, интерфейс подключения и назначение тома",\n  "developer": "Производитель накопителя",\n  "category": "Дисковая подсистема (Storage)",\n  "security_verdict": "Оценка надежности, шифрования BitLocker и рисков сбоя",\n  "performance_impact": "Скоростные характеристики, свободное место и износ (Wear Level)",\n  "recommendation": "Рекомендации по обслуживанию, резервному копированию и дефрагментации/TRIM",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'startup': {
        'table_type': 'startup',
        'name': 'Аудит автозагрузки Windows (Startup & Autoruns)',
        'description': 'Промпт для анализа программ и модулей, запускающихся при старте системы.',
        'system_instruction': 'Ты — эксперт по оптимизации Windows и анализу автозагрузки (Run keys, Startup folder, Task Scheduler autoruns). Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи аудит элемента автозагрузки:\n\nИмя элемента: {title}\nМестоположение / Источник: {subtitle}\nМетаданные элемента:\n{metadata}\nКомандная строка: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Назначение приложения в автозагрузке",\n  "developer": "Разработчик / Издатель",\n  "category": "Автозагрузка (Startup)",\n  "security_verdict": "Оценка безопасности: легитимность, цифровая подпись, необходимость автозапуска",\n  "performance_impact": "Влияние на скорость загрузки ОС и оперативную память",\n  "recommendation": "Рекомендация: оставить в автозапуске, отложить или отключить",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'website': {
        'table_type': 'website',
        'name': 'Аудит веб-ресурсов и мониторинга сайтов',
        'description': 'Промпт для анализа веб-сайтов, трафика, аналитики GA4/GSC и доступности.',
        'system_instruction': 'Ты — эксперт по веб-аналитике, SEO и мониторингу веб-сервисов (GA4, GSC, Web Performance). Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи аудит веб-ресурса / страницы:\n\nURL / Домен: {title}\nМетрика / Статус: {subtitle}\nМетаданные сайта:\n{metadata}\nСырые параметры аналитики: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Обзор веб-ресурса и его ключевых метрик",\n  "developer": "Владелец / Платформа",\n  "category": "Веб-ресурс (Web Intelligence)",\n  "security_verdict": "Оценка доступности, SSL сертификата и надежности",\n  "performance_impact": "Показатели трафика, конверсии и индексации",\n  "recommendation": "Рекомендации по оптимизации и мониторингу",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'rag_doc': {
        'table_type': 'rag_doc',
        'name': 'Аудит документов базы знаний RAG',
        'description': 'Промпт для анализа документов, чанков и релевантности векторной базы знаний.',
        'system_instruction': 'Ты — специалист по информационному поиску, эмбеддингам и архитектуре RAG. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи анализ документа базы знаний RAG:\n\nИмя документа / Заголовок: {title}\nФормат / Размер: {subtitle}\nМетаданные документа:\n{metadata}\nСодержимое / Чанк: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Краткое содержание и тематика документа",\n  "developer": "Источник документа",\n  "category": "База знаний RAG",\n  "security_verdict": "Оценка актуальности и конфиденциальности данных",\n  "performance_impact": "Качество индексации и векторного поиска",\n  "recommendation": "Рекомендации по обновлению или категоризации",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
    'generic': {
        'table_type': 'generic',
        'name': 'Базовый аудит записи',
        'description': 'Стандартный промпт для общего системного аудита и анализа записей.',
        'system_instruction': 'Ты — ведущий системный архитектор и аналитик. Отвечай строго в формате чистого JSON на русском языке.',
        'prompt_template': 'Проведи детальный экспертный аудит записи:\n\nЗаголовок: {title}\nПодзаголовок / Контекст: {subtitle}\nМетаданные записи:\n{metadata}\nСырые данные: {raw_data}\n\nВерни СТРОГО JSON со следующей схемой:\n{{\n  "summary": "Подробное резюме о записи",\n  "developer": "Разработчик / Источник",\n  "category": "Категория",\n  "security_verdict": "Оценка безопасности и рисков",\n  "performance_impact": "Влияние на производительность и ресурсы",\n  "recommendation": "Рекомендации",\n  "action_steps": ["Рекомендованное действие 1", "Рекомендованное действие 2"]\n}}',
        'variables': ['title', 'subtitle', 'metadata', 'raw_data']
    },
}


class DiagnosticPromptTemplate(BaseModel):
    """Модель шаблона промпта для типа таблицы."""
    table_type: str = Field(description='Уникальный идентификатор типа таблицы')
    name: str = Field(description='Человекочитаемое название')
    description: str = Field(default='', description='Описание назначения промпта')
    system_instruction: str = Field(description='Системная инструкция для LLM')
    prompt_template: str = Field(description='Шаблон текста промпта с переменными {title}, {subtitle}, {metadata}, {raw_data}')
    variables: List[str] = Field(default_factory=lambda: ['title', 'subtitle', 'metadata', 'raw_data'], description='Доступные переменные шаблона')
    is_customized: bool = Field(default=False, description='Признак пользовательской модификации')

    def format_prompt(self, title: str, subtitle: str, metadata: Dict[str, Any], raw_data: str) -> str:
        """Форматирует промпт подставляя фактические значения полей."""
        meta_str = '\n'.join([f'- {k}: {v}' for k, v in metadata.items()]) if metadata else '- Нет дополнительных метаданных'
        try:
            return self.prompt_template.format(
                table_type=self.table_type,
                title=title or 'Не указано',
                subtitle=subtitle or 'Нет',
                metadata=meta_str,
                raw_data=raw_data or 'Нет'
            )
        except Exception as e:
            logger.warning(f"Ошибка при подстановке переменных в промпт '{self.table_type}': {e}. Применен базовый формат.")
            return f'{self.prompt_template}\n\n[Контекст: {title} | {subtitle} | {raw_data}]'


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
            logger.error(f'Не удалось создать каталог промптов {self.storage_dir}: {e}')

    def _get_file_path(self, table_type: str) -> Path:
        """Возвращает путь к файлу шаблона промпта."""
        safe_type = ''.join((c for c in table_type if c.isalnum() or c in ('_', '-'))).lower()
        return self.storage_dir / f'{safe_type}.json'

    def normalize_table_type(self, table_type: str) -> str:
        """Нормализует тип таблицы с учетом алиасов."""
        key = table_type.lower().strip()
        aliases = {
            'user': 'user_account',
            'users': 'user_account',
            'account': 'user_account',
            'accounts': 'user_account',
            'security': 'security_event',
            'event': 'security_event',
            'events': 'security_event',
            'tasks': 'task',
            'services': 'service',
            'processes': 'process',
            'disks': 'disk',
            'apps': 'software',
            'app': 'software',
            'autorun': 'startup',
            'autoruns': 'startup',
        }
        return aliases.get(key, key)

    def get_template(self, table_type: str) -> DiagnosticPromptTemplate:
        """Возвращает шаблон промпта для указанного типа таблицы.

        Если сохранен пользовательский файл JSON в prompts/diagnostics/, загружает его.
        Иначе возвращает стандартный шаблон по умолчанию.
        """
        key = self.normalize_table_type(table_type)

        file_path = self._get_file_path(key)
        if file_path.is_file():
            try:
                data = json.loads(file_path.read_text(encoding='utf-8'))
                return DiagnosticPromptTemplate(
                    table_type=data.get('table_type', key),
                    name=data.get('name', DEFAULT_PROMPTS.get(key, {}).get('name', key.capitalize())),
                    description=data.get('description', ''),
                    system_instruction=data.get('system_instruction', ''),
                    prompt_template=data.get('prompt_template', ''),
                    variables=data.get('variables', ['title', 'subtitle', 'metadata', 'raw_data']),
                    is_customized=True
                )
            except Exception as e:
                logger.warning(f'Не удалось загрузить кастомный промпт из {file_path}: {e}')

        if key in DEFAULT_PROMPTS:
            raw_def = DEFAULT_PROMPTS[key]
            return DiagnosticPromptTemplate(
                table_type=raw_def['table_type'],
                name=raw_def['name'],
                description=raw_def['description'],
                system_instruction=raw_def['system_instruction'],
                prompt_template=raw_def['prompt_template'],
                variables=raw_def['variables'],
                is_customized=False
            )

        raw_generic = DEFAULT_PROMPTS['generic']
        return DiagnosticPromptTemplate(
            table_type=key,
            name=f'Аудит {key}',
            description=f'Шаблон аудита для типа {key}',
            system_instruction=raw_generic['system_instruction'],
            prompt_template=raw_generic['prompt_template'],
            variables=raw_generic['variables'],
            is_customized=False
        )

    def list_templates(self) -> List[DiagnosticPromptTemplate]:
        """Возвращает список всех доступных шаблонов промптов."""
        all_keys = list(DEFAULT_PROMPTS.keys())
        if self.storage_dir.is_dir():
            for p in self.storage_dir.glob('*.json'):
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
        key = self.normalize_table_type(table_type)
        file_path = self._get_file_path(key)
        default_info = DEFAULT_PROMPTS.get(key, {})
        final_name = name or default_info.get('name', key.capitalize())
        final_desc = description if description is not None else default_info.get('description', '')
        variables = default_info.get('variables', ['title', 'subtitle', 'metadata', 'raw_data'])
        payload = {
            'table_type': key,
            'name': final_name,
            'description': final_desc,
            'system_instruction': system_instruction,
            'prompt_template': prompt_template,
            'variables': variables
        }
        self._ensure_storage()
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
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
        key = self.normalize_table_type(table_type)
        file_path = self._get_file_path(key)
        if file_path.is_file():
            try:
                file_path.unlink()
                logger.info(f"Сброшен шаблон промпта для '{key}' (удален {file_path})")
            except Exception as e:
                logger.error(f'Не удалось удалить файл шаблона {file_path}: {e}')
        return self.get_template(key)


prompt_manager = DiagnosticsPromptManager()

__all__ = ['DiagnosticPromptTemplate', 'DiagnosticsPromptManager', 'prompt_manager', 'DEFAULT_PROMPTS']
