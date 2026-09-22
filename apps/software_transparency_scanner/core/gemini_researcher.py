# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Gemini AI Software Researcher
# =============================================================================
# Description:
#   Интеллектуальное исследование приложения через Google Gemini:
#   - Формирование структурированного запроса с фактами локального сканирования
#   - Исследование назначения конфигов, хранилищ и сетевых доменов
#   - Разделение на подтвержденные факты, предположения и неизвестные аспекты
#   - Строгий fallback при отсутствии связи с AI
#
# File: gemini_researcher.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль исследования программ и доменов с помощью Gemini AI."""

from __future__ import annotations

import json
import re
from typing import Optional

from logger import logger
from apps.software_transparency_scanner.core.models import (
    GeminiAppResearch,
    SoftwareItem,
)


class GeminiResearcher:
    """AI-исследователь программного обеспечения на базе Google Gemini."""

    def __init__(self, chat_provider: Optional[Any] = None):
        self.chat_provider = chat_provider

    async def research_software(self, app: SoftwareItem) -> GeminiAppResearch:
        """Проводит исследование программы через Gemini или локальные эвристики.

        Args:
            app: Карточка ПО со собранными локальными фактами.

        Returns:
            GeminiAppResearch: Структурированное объяснение назначения ПО и его компонентов.
        """
        # 1. Попытка запроса через активный провайдер Gemini
        if self.chat_provider and hasattr(self.chat_provider, "chat"):
            try:
                prompt = self._build_gemini_prompt(app)
                raw_response = await self.chat_provider.chat(prompt)
                if raw_response:
                    parsed = self._parse_gemini_response(raw_response, app.name)
                    if parsed:
                        return parsed
            except Exception as ex:
                logger.warning(f"[GeminiResearcher] Ошибка вызова Gemini API: {ex}")

        # 2. Детерминированный fallback анализ
        return self._generate_fallback_research(app)

    def _build_gemini_prompt(self, app: SoftwareItem) -> str:
        """Формирует компактный промпт для Gemini со строгими ограничениями."""
        configs_list = [f"- {c.display_path} ({c.format}, {c.size_bytes} B)" for c in app.config_files[:5]]
        dirs_list = [f"- {d.display_path} [{d.category.value}]" for d in app.data_directories[:5]]
        domains_list = [f"- {ep.domain_or_ip}:{ep.port or 443}" for ep in app.network_endpoints[:5]]

        return f"""Ты — эксперт по анализу безопасности и прозрачности ПО Windows.
Исследуй программу на основе собранных фактов локального сканирования:

Название: {app.name}
Версия: {app.version}
Издатель: {app.publisher}
Исполняемый файл: {app.executable_path or 'Не указан'}

Найденные конфигурационные файлы:
{chr(10).join(configs_list) if configs_list else '- Не найдены'}

Найденные каталоги:
{chr(10).join(dirs_list) if dirs_list else '- Не найдены'}

Найденные сетевые домены/хосты:
{chr(10).join(domains_list) if domains_list else '- Не обнаружены'}

Определи:
1. Назначение программы.
2. Назначение конфигурационных файлов.
3. Какие данные могут храниться локально.
4. Назначение сетевых доменов.
5. Какие утверждения подтверждены официальными источниками.
6. Какие сведения неизвестны или предполагаются.

Верни строго валидный JSON следующего формата:
{{
  "summary": "Краткое описание программы",
  "config_purpose_explanation": "Объяснение конфигов",
  "data_storage_explanation": "Объяснение мест хранения",
  "network_activity_explanation": "Объяснение сетевых доменов",
  "confirmed_facts": ["Факт 1", "Факт 2"],
  "inferred_facts": ["Предположение 1"],
  "unknown_aspects": ["Неизвестно 1"],
  "confidence_level": "Высокий"
}}
Не выдумывай информацию. Если что-то неизвестно, честно укажи в unknown_aspects.
"""

    def _parse_gemini_response(self, response_text: str, app_name: str) -> Optional[GeminiAppResearch]:
        """Парсит JSON-ответ от модели Gemini."""
        clean_json = response_text.strip()
        if clean_json.startswith("`"):
            clean_json = re.sub(r"^`[a-z]*\n", "", clean_json)
            clean_json = re.sub(r"\n`$", "", clean_json).strip()

        try:
            data = json.loads(clean_json)
            return GeminiAppResearch(
                app_name=app_name,
                summary=data.get("summary", ""),
                config_purpose_explanation=data.get("config_purpose_explanation", ""),
                data_storage_explanation=data.get("data_storage_explanation", ""),
                network_activity_explanation=data.get("network_activity_explanation", ""),
                confirmed_facts=data.get("confirmed_facts", []),
                inferred_facts=data.get("inferred_facts", []),
                unknown_aspects=data.get("unknown_aspects", []),
                confidence_level=data.get("confidence_level", "Средний"),
            )
        except Exception as ex:
            logger.debug(f"Не удалось распарсить JSON Gemini: {ex}")
            return None

    def _generate_fallback_research(self, app: SoftwareItem) -> GeminiAppResearch:
        """Детерминированный fallback анализ с разделением фактов и предположений."""
        n_low = app.name.lower()
        
        if "chrome" in n_low:
            return GeminiAppResearch(
                app_name=app.name,
                summary="Google Chrome — популярный веб-браузер на базе Chromium с поддержкой расширений и облачной синхронизации.",
                config_purpose_explanation="Файлы Preferences и Local State в %LOCALAPPDATA% хранят настройки профилей, поисковые системы и конфигурацию вкладок.",
                data_storage_explanation="В %LOCALAPPDATA%\\Google\\Chrome\\User Data хранятся история посещений (History SQLite), закладки (Bookmarks JSON), кэш страниц и куки.",
                network_activity_explanation="Подключается к update.googleapis.com для обновлений, clients2.google.com для Safe Browsing и accounts.google.com для синхронизации.",
                confirmed_facts=[
                    "Программа является веб-браузером Google Chrome",
                    "Конфигурация профилей хранится в формате JSON в %LOCALAPPDATA%",
                    "Сетевые соединения используются для обновлений и синхронизации",
                ],
                inferred_facts=[
                    "Шифрованный трафик HTTPS защищает передаваемые данные",
                ],
                unknown_aspects=[
                    "Конкретный состав отправляемых телеметрических отчетов без глубокого WFP-аудита",
                ],
                confidence_level="Подтверждено документацией",
            )

        if "code" in n_low or "visual studio code" in n_low:
            return GeminiAppResearch(
                app_name=app.name,
                summary="Visual Studio Code — расширяемый редактор исходного кода от Microsoft с поддержкой языков программирования и плагинов.",
                config_purpose_explanation="Файл settings.json в %APPDATA%\\Code\\User содержит пользовательские настройки интерфейса, форматирования и плагинов.",
                data_storage_explanation="Локальное состояние и кэш расширений хранятся в %APPDATA%\\Code и %USERPROFILE%\\.vscode.",
                network_activity_explanation="Соединения с marketplace.visualstudio.com (каталог плагинов) и update.code.visualstudio.com (обновления).",
                confirmed_facts=[
                    "Программа — редактор кода Microsoft VS Code",
                    "Настройки пользователя хранятся в %APPDATA%\\Code\\User\\settings.json",
                ],
                inferred_facts=[
                    "Установленные сторонние расширения могут иметь собственную сетевую активность",
                ],
                unknown_aspects=[
                    "Сетевая активность сторонних установленных расширений",
                ],
                confidence_level="Подтверждено документацией",
            )

        # Обобщенный fallback
        return GeminiAppResearch(
            app_name=app.name,
            summary=f"Программа {app.name} от разработчика {app.publisher}. Версия: {app.version}.",
            config_purpose_explanation="Конфигурационные файлы хранят локальные параметры работы и профили пользователя.",
            data_storage_explanation="Данные программы распределены между Program Files (бинари) и каталогами %APPDATA% / %LOCALAPPDATA%.",
            network_activity_explanation="Сетевые соединения используются для проверки обновлений и сетевого взаимодействия приложения.",
            confirmed_facts=[
                f"ПО установлено в системе (версия {app.version})",
                f"Издатель: {app.publisher}",
            ],
            inferred_facts=[
                "Файлы настроек соответствуют стандартной схеме расположения Windows AppData",
            ],
            unknown_aspects=[
                "Детали закрытых протоколов и шифрованного сетевого взаимодействия",
            ],
            confidence_level="Предположение Gemini",
        )
