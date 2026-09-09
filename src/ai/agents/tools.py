# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Search for current information on the internet
# =============================================================================
# Description:
#   Набор нативных LangChain-инструментов для AI-агентов.
#
# File: langchain_tools.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict

try:
    from langchain_core.tools import tool
except ImportError:
    class DummyTool:
        def __init__(self, func):
            self.func = func
            self.__name__ = getattr(func, '__name__', 'DummyTool')
            self.__doc__ = getattr(func, '__doc__', '')

        def invoke(self, input_data=None, **kwargs):
            if isinstance(input_data, dict):
                return self.func(**input_data)
            elif input_data is not None:
                return self.func(input_data, **kwargs)
            return self.func(**kwargs)

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    def tool(func=None, *args, **kwargs):
        if func is not None:
            return DummyTool(func)
        return lambda f: DummyTool(f)

from src.logger import logger
from header import __root__

@tool
async def web_search(query: str) -> str:
    """Поиск актуальной информации в интернете через поисковые адаптеры.

    Args:
        query: Поисковый запрос.
    """
    try:
        from src.fastapi.router_chat import get_chat_model
        model = get_chat_model()
        response = await model.ask(f"Найди в интернете актуальную информацию по запросу: {query}")
        return response
    except Exception as e:
        logger.error(f"[langchain_tools] Error веб-поиска: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
async def rag_search(query: str, top_k: int = 5) -> str:
    """Семантический поиск по локальной базе знаний и документам.

    Args:
        query: Запрос для семантического поиска.
        top_k: Максимальное количество фрагментов.
    """
    try:
        from src.rag.rag_manager import rag_manager
        results = await rag_manager.search(query=query, limit=top_k)
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[langchain_tools] Error RAG-поиска: {e}")
        return json.dumps([], ensure_ascii=False)

@tool
def python_eval(code: str) -> str:
    """Безопасное выполнение простых математических и строковых выражений Python.

    Args:
        code: Выражение или фрагмент кода для вычисления.
    """
    try:
        allowed_globals = {"__builtins__": {"abs": abs, "min": min, "max": max, "sum": sum, "round": round, "len": len}}
        result = eval(code, allowed_globals, {})
        return str(result)
    except Exception as e:
        return f"Error вычисления: {e}"

@tool
def file_read(file_path: str) -> str:
    """Чтение содержимого текстового файла проекта.

    Args:
        file_path: Относительный или абсолютный путь к файлу.
    """
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = __root__ / p
        if not p.exists() or not p.is_file():
            return f"Файл не найден: {file_path}"
        return p.read_text(encoding="utf-8", errors="replace")[:10000]
    except Exception as e:
        return f"Error чтения файла: {e}"

@tool
async def flight_search(
    origin: str,
    destination: str,
    date: str,
    return_date: str = "",
    passengers: int = 1,
    travel_class: str = "economy",
) -> str:
    """Поиск авиабилетов и рейсов через поисковые адаптеры и агрегаторы.

    Args:
        origin: Город или IATA-код отправления (напр. 'TLV', 'Тель-Авив', 'MOW').
        destination: Город или IATA-код назначения (напр. 'CDG', 'Париж', 'BER').
        date: Дата вылета (напр. '2026-10-15' или '15 октября 2026').
        return_date: Дата обратного рейса (опционально).
        passengers: Количество пассажиров (по умолчанию 1).
        travel_class: Класс обслуживания ('economy', 'premium_economy', 'business', 'first').
    """
    try:
        from src.fastapi.router_chat import get_chat_model
        
        # Build search query
        query_parts = [
            f"Найди актуальные авиабилеты и рейсы из {origin} в {destination} на дату {date}"
        ]
        if return_date:
            query_parts.append(f"обратно {return_date}")
        query_parts.append(f"пассажиров: {passengers}, класс: {travel_class}.")
        query_parts.append(
            "Укажи авиакомпании, прямые рейсы или пересадки, время вылета/прилета, цены и ссылки на бронирование."
        )
        full_query = " ".join(query_parts)

        model = get_chat_model()
        response = await model.ask(full_query)
        
        # Construct helpful direct aggregator links
        import urllib.parse
        encoded_origin = urllib.parse.quote(origin)
        encoded_dest = urllib.parse.quote(destination)
        google_flights_url = f"https://www.google.com/travel/flights?q=Flights%20to%20{encoded_dest}%20from%20{encoded_origin}%20on%20{urllib.parse.quote(date)}"
        aviasales_url = f"https://www.aviasales.ru/search/{origin}{date}{destination}"
        skyscanner_url = f"https://www.skyscanner.com/transport/flights/{encoded_origin}/{encoded_dest}/{urllib.parse.quote(date)}"

        links_block = (
            f"\n\nПолезные прямые ссылки для бронирования:\n"
            f"- [Google Flights]({google_flights_url})\n"
            f"- [Aviasales]({aviasales_url})\n"
            f"- [Skyscanner]({skyscanner_url})"
        )

        return f"{response}\n{links_block}"
    except Exception as e:
        logger.error(f"[langchain_tools] Error поиска авиабилетов: {e}")
        return json.dumps({
            "error": f"Flight search failed: {str(e)}",
            "origin": origin,
            "destination": destination,
            "date": date
        }, ensure_ascii=False)

@tool
def flight_price_calculator(
    base_price: float,
    currency: str = "USD",
    baggage_fee: float = 0.0,
    passengers: int = 1,
    tax_rate: float = 0.0,
    discount_percent: float = 0.0,
) -> str:
    """Точный расчет полной стоимости перелета с учетом багажа, налогов, скидок и количества пассажиров.

    Args:
        base_price: Базовый тариф за 1 билет.
        currency: Валюта расчета (USD, EUR, RUB, ILS).
        baggage_fee: Дополнительная плата за багаж на человека.
        passengers: Количество пассажиров.
        tax_rate: Процент аэропортовых и сервисных сборов (напр. 5.0 для 5%).
        discount_percent: Скидка или промокод в процентах (напр. 10.0 для 10%).
    """
    try:
        subtotal_per_person = float(base_price) + float(baggage_fee)
        taxes_per_person = subtotal_per_person * (float(tax_rate) / 100.0)
        total_per_person = subtotal_per_person + taxes_per_person
        
        discount_amount = total_per_person * (float(discount_percent) / 100.0)
        final_per_person = total_per_person - discount_amount
        total_all_passengers = final_per_person * int(passengers)

        breakdown = {
            "currency": currency,
            "passengers_count": passengers,
            "base_price_per_passenger": base_price,
            "baggage_fee_per_passenger": baggage_fee,
            "tax_amount_per_passenger": round(taxes_per_person, 2),
            "discount_per_passenger": round(discount_amount, 2),
            "final_per_passenger": round(final_per_person, 2),
            "total_overall": round(total_all_passengers, 2)
        }
        return json.dumps(breakdown, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error расчета цены: {e}"

# --- Google Workspace Tools (Gmail, Drive, Sheets, Docs) ---

def _get_google_workspace_managers():
    """Dynamically import Google Workspace managers from skill scripts."""
    scripts_dir = __root__ / ".agents" / "skills" / "google-workspace" / "scripts"
    import sys
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from gmail_manager import GmailManager
        from gdrive_manager import GDriveManager
        from gsheets_manager import GSheetsManager
        return GmailManager, GDriveManager, GSheetsManager
    except Exception as e:
        logger.error(f"[google_workspace_tools] Failed to import managers: {e}")
        return None, None, None

@tool
def gmail_search(query: str = "is:unread", limit: int = 10, account_name: str = "") -> str:
    """Поиск и получение списка писем в Gmail по запросу (например: 'is:unread', 'from:boss', 'subject:report').

    Args:
        query: Строка поискового фильтра Gmail.
        limit: Максимальное количество писем (по умолчанию 10).
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        GmailManager, _, _ = _get_google_workspace_managers()
        if not GmailManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GmailManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        messages = manager.search_messages(query=query, max_results=limit)
        return json.dumps(messages, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gmail_search: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gmail_create_draft(to: str, subject: str, body: str, account_name: str = "") -> str:
    """Создание черновика электронного письма в Gmail.

    Args:
        to: Email адрес получателя.
        subject: Тема письма.
        body: Текст сообщения.
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        GmailManager, _, _ = _get_google_workspace_managers()
        if not GmailManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GmailManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        draft = manager.create_draft(to=to, subject=subject, body_text=body)
        if draft:
            return json.dumps({"status": "ok", "draft_id": draft.get("id"), "message": f"Draft created for {to}"}, ensure_ascii=False)
        return json.dumps({"error": "Failed to create draft"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gmail_create_draft: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gdrive_list_files(query: str = "", limit: int = 10, account_name: str = "") -> str:
    """Поиск и получение списка файлов и папок на Google Диске (например: "name contains 'Report'", "trashed = false").

    Args:
        query: Строка поискового запроса Google Drive API (опционально).
        limit: Максимальное количество файлов (по умолчанию 10).
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        _, GDriveManager, _ = _get_google_workspace_managers()
        if not GDriveManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GDriveManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        files = manager.list_files(query=query if query else None, page_size=limit)
        return json.dumps(files, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gdrive_list_files: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gdrive_download_file(file_id: str, mime_type: str = "", dest_path: str = "data/downloads/document", account_name: str = "") -> str:
    """Выгрузка файла с Google Диска или экспорт документа Google Docs / Sheets в локальный файл.

    Args:
        file_id: Идентификатор файла в Google Drive.
        mime_type: MIME-тип файла (напр. 'application/vnd.google-apps.document').
        dest_path: Локальный путь для сохранения файла.
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        _, GDriveManager, _ = _get_google_workspace_managers()
        if not GDriveManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GDriveManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        target_path = Path(dest_path)
        if not target_path.is_absolute():
            target_path = __root__ / target_path
        success = manager.download_or_export_file(file_id=file_id, mime_type=mime_type, dest_path=target_path)
        if success:
            return json.dumps({"status": "ok", "saved_path": str(target_path)}, ensure_ascii=False)
        return json.dumps({"error": f"Failed to download file {file_id}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gdrive_download_file: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gsheets_info(spreadsheet_id: str, account_name: str = "") -> str:
    """Получение структуры и списка листов Google Таблицы по её ID.

    Args:
        spreadsheet_id: Идентификатор Google Таблицы из URL.
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        _, _, GSheetsManager = _get_google_workspace_managers()
        if not GSheetsManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GSheetsManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        info = manager.get_spreadsheet_info(spreadsheet_id)
        if info:
            return json.dumps(info, ensure_ascii=False, indent=2)
        return json.dumps({"error": f"Failed to get info for spreadsheet {spreadsheet_id}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gsheets_info: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gsheets_read(spreadsheet_id: str, range_name: str = "A1:Z50", account_name: str = "") -> str:
    """Чтение значений ячеек из Google Таблицы в указанном диапазоне (например: 'Sheet1!A1:D20').

    Args:
        spreadsheet_id: Идентификатор Google Таблицы.
        range_name: Диапазон ячеек в нотации A1 (по умолчанию 'A1:Z50').
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        _, _, GSheetsManager = _get_google_workspace_managers()
        if not GSheetsManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GSheetsManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        rows = manager.read_range(spreadsheet_id=spreadsheet_id, range_name=range_name)
        return json.dumps({"range": range_name, "rows": rows}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gsheets_read: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gsheets_search(spreadsheet_id: str, query: str, range_name: str = "A1:Z500", account_name: str = "") -> str:
    """Поиск строк в Google Таблице по текстовому запросу.

    Args:
        spreadsheet_id: Идентификатор Google Таблицы.
        query: Текст для поиска.
        range_name: Диапазон поиска (по умолчанию 'A1:Z500').
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        _, _, GSheetsManager = _get_google_workspace_managers()
        if not GSheetsManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GSheetsManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        matches = manager.search(spreadsheet_id=spreadsheet_id, query=query, range_name=range_name)
        return json.dumps({"query": query, "matches": matches}, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gsheets_search: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def gsheets_append(spreadsheet_id: str, range_name: str, values_json: str, account_name: str = "") -> str:
    """Добавление новой строки данных в Google Таблицу.

    Args:
        spreadsheet_id: Идентификатор Google Таблицы.
        range_name: Диапазон/лист для добавления (например: 'Sheet1!A1').
        values_json: JSON-массив значений ячеек (например: '["Значение 1", "Значение 2", 123]').
        account_name: Имя аккаунта в пуле src/secrets/google_accounts.json (опционально).
    """
    try:
        _, _, GSheetsManager = _get_google_workspace_managers()
        if not GSheetsManager:
            return json.dumps({"error": "Google Workspace manager is not available"}, ensure_ascii=False)
        manager = GSheetsManager(account_name=account_name or None)
        if not manager.service:
            return json.dumps({
                "error": f"Google Workspace authentication failed for account '{account_name or 'default'}'. Please configure credentials in src/secrets/."
            }, ensure_ascii=False)
        parsed_values = json.loads(values_json)
        if not isinstance(parsed_values, list):
            return json.dumps({"error": "values_json must be a JSON array"}, ensure_ascii=False)
        if parsed_values and not isinstance(parsed_values[0], list):
            parsed_values = [parsed_values]
        res = manager.append_rows(spreadsheet_id=spreadsheet_id, range_name=range_name, values=parsed_values)
        if res:
            return json.dumps({"status": "ok", "updated_range": res.get("updates", {}).get("updatedRange")}, ensure_ascii=False)
        return json.dumps({"error": "Failed to append rows"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[google_workspace_tools] Error in gsheets_append: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# --- Заглушки для обратной совместимости ---

@tool
async def search_torrents(query: str) -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps([], ensure_ascii=False)

@tool
async def get_movie_metadata(title: str) -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps({}, ensure_ascii=False)

@tool
def get_streaming_sources(title: str) -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps({}, ensure_ascii=False)

@tool
def build_player_url(url: str, provider: str = "") -> str:
    """Устаревший инструмент (артефакт удален)."""
    return json.dumps({}, ensure_ascii=False)

@tool
async def add_torrent_download(url: str, source: str = "", title: str = "") -> str:
    """Устаревший инструмент (артефакт удален)."""
    return "Функциональность торрентов удалена."
