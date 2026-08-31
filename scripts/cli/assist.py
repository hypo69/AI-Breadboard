# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Кроссплатформенный CLI ассистент для управления пр
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: assist.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Кроссплатформенный CLI ассистент для управления проектом AI Breadboard.

Портировано со старого assist.ps1 для работы на Windows, Linux и macOS.

Использование:
    assist start [service]          # Запустить сервис (run, unicorn, light, foundry)
    assist stop [service]           # Остановить сервис (server, foundry, all)
    assist restart                  # Перезапустить
    assist status                   # Показать status
    assist providers                # List провайдеров ИИ
    assist logs [lines]             # Показать логи
    assist config [show|get|set]    # Работа с config.json
    assist test                     # Запустить тесты
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Добавляем root в PYTHONPATH для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cli.paths import init_paths, get_paths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import (
    find_available_port,
    is_port_open,
    get_process_on_port,
    kill_process,
    ensure_in_path,
    run_command,
    which
)

# ANSI цвета для терминала
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"
C_MAGENTA = "\033[95m"

class AssistCLI:
    """Главный CLI class для управления AI-Breadboard"""
    
    def __init__(self):
        self.paths = init_paths()
        self.config_mgr = get_config_manager()
        self._state_dir = self.paths.data_dir / "assist_state"
        self._ensure_state_dir()
    
    def _ensure_state_dir(self) -> None:
        """Creates директорию состояния"""
        self._state_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_state_file(self, name: str) -> Path:
        """Получить путь до файла состояния"""
        return self._state_dir / f"{name}.json"
    
    def _load_state(self, name: str) -> dict:
        """Загрузить state из файла"""
        state_file = self._get_state_file(name)
        if not state_file.exists():
            return {}
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_state(self, name: str, data: dict) -> None:
        """Сохранить state в файл"""
        self._ensure_state_dir()
        state_file = self._get_state_file(name)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def cmd_start(self, service: str = "run") -> int:
        """Запустить сервис"""
        service = service.lower()
        
        # Маппинг сервисов на скрипты
        script_map = {
            "run": "launchers/run.py",
            "all": "launchers/run.py",
            "unicorn": "launchers/run_unicorn.py",
            "uvicorn": "launchers/run_unicorn.py",
            "light": "launchers/run_light_server.py",
            "foundry": "launchers/run_foundry.py",
        }
        
        script_name = script_map.get(service)
        if not script_name:
            print(f"{C_RED}❌ Неизвестный сервис: '{service}'{C_RESET}")
            print(f"{C_GRAY}Доступные сервисы: run, unicorn, light, foundry, all{C_RESET}")
            return 1
        
        script_path = self.paths.project_root / script_name
        
        if not script_path.exists():
            print(f"{C_RED}❌ Скрипт не найден: {script_path}{C_RESET}")
            return 1
        
        print(f"{C_CYAN}🚀 Запуск: {script_name}...{C_RESET}")
        
        # Запустить скрипт
        try:
            python_exe = str(self.paths.venv_python) if self.paths.venv_python.exists() else sys.executable
            result = subprocess.run(
                [python_exe, str(script_path)],
                cwd=str(self.paths.project_root),
                check=False
            )
            return result.returncode
        except Exception as e:
            print(f"{C_RED}❌ Error запуска: {e}{C_RESET}")
            return 1
    
    def cmd_stop(self, service: str = "all") -> int:
        """Остановить сервис"""
        service = service.lower()
        
        config = self.config_mgr.load_config()
        server_cfg = config.get("server", {})
        port = int(server_cfg.get("port", 8000))
        
        stopped_any = False
        
        if service in ("server", "all", "unicorn", "uvicorn", "light"):
            proc_info = get_process_on_port(port)
            if proc_info:
                pid, proc_name = proc_info
                print(f"{C_YELLOW}⏹ Остановка сервера на порту {port} (PID: {pid}, {proc_name})...{C_RESET}")
                if kill_process(pid, force=True):
                    print(f"  {C_GREEN}✔ Процесс завершен{C_RESET}")
                    stopped_any = True
                else:
                    print(f"  {C_RED}✖ Не удалось завершить процесс{C_RESET}")
            else:
                print(f"{C_GRAY}Порт {port} свободен (сервер не запущен){C_RESET}")
        
        if service in ("foundry", "all"):
            print(f"{C_YELLOW}⏹ Остановка Foundry...{C_RESET}")
            # TODO: Реализовать остановку Foundry
            stopped_any = True
        
        if not stopped_any:
            print(f"{C_GREEN}Все сервисы уже остановлены.{C_RESET}")
        
        return 0
    
    def cmd_restart(self) -> int:
        """Перезапустить сервисы"""
        print(f"{C_CYAN}🔄 Перезапуск сервисов...{C_RESET}")
        self.cmd_stop()
        return self.cmd_start()
    
    def cmd_status(self) -> int:
        """Показать status"""
        config = self.config_mgr.load_config()
        server_cfg = config.get("server", {})
        port = int(server_cfg.get("port", 8000))
        use_ssl = bool(server_cfg.get("use_ssl", False))
        mode = str(server_cfg.get("mode", "DEV"))
        reload_on = bool(server_cfg.get("reload", True))
        
        proto = "https" if use_ssl else "http"
        local_url = f"{proto}://localhost:{port}/"
        
        print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════╗{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}║             СТАТУС AI ASSISTANT СИСТЕМЫ                       ║{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════╝{C_RESET}\n")
        
        # Check FastAPI сервера
        proc_info = get_process_on_port(port)
        if proc_info:
            pid, proc_name = proc_info
            print(f"  {C_BOLD}FastAPI Сервер:{C_RESET}     {C_GREEN}● РАБОТАЕТ{C_RESET}")
            print(f"  {C_BOLD}URL:{C_RESET}                {C_CYAN}{local_url}{C_RESET}")
            print(f"  {C_BOLD}PID процесса:{C_RESET}       {pid} ({proc_name})")
        else:
            print(f"  {C_BOLD}FastAPI Сервер:{C_RESET}     {C_RED}○ ОСТАНОВЛЕН{C_RESET}")
            print(f"  {C_BOLD}Ожидаемый порт:{C_RESET}     {port}")
        
        print(f"  {C_BOLD}Режим / SSL:{C_RESET}        {mode} | SSL: {'ВКЛ' if use_ssl else 'ВЫКЛ'} | Autoreload: {'ВКЛ' if reload_on else 'ВЫКЛ'}")
        
        # AI Foundry
        ai_cfg = config.get("ai", {})
        use_foundry = bool(ai_cfg.get("use_foundry", False))
        foundry_url = str(ai_cfg.get("foundry_base_url", "http://localhost:54837"))
        
        if use_foundry:
            print(f"  {C_BOLD}AI Foundry:{C_RESET}         {C_YELLOW}○ ВКЛЮЧЕН В CONFIG (внешний сервис){C_RESET}")
            print(f"  {C_BOLD}URL:{C_RESET}                {foundry_url}")
        else:
            print(f"  {C_BOLD}AI Foundry:{C_RESET}         {C_GRAY}○ ОТКЛЮЧЕН В CONFIG{C_RESET}")
        
        # Gemini API Keys
        gemini_keys = os.getenv("GEMINI_API_KEY_NAMES", "")
        key_count = len([k for k in gemini_keys.split(",") if k.strip()])
        print(f"  {C_BOLD}Gemini API Keys:{C_RESET}    {C_GREEN}{key_count} в пуле ротации{C_RESET}")
        
        print()
        return 0
    
    def cmd_providers(self) -> int:
        """Показать list провайдеров"""
        config = self.config_mgr.load_config()
        ai_cfg = config.get("ai", {})
        
        print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════╗{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}║                     РЕЕСТР ПРОВАЙДЕРОВ И МОДЕЛЕЙ ИИ                                   ║{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{C_RESET}\n")
        
        # 1. Google Gemini API
        gemini_keys = os.getenv("GEMINI_API_KEY_NAMES", "")
        keys = [k.strip() for k in gemini_keys.split(",") if k.strip()]
        has_gemini = len(keys) > 0
        print(f"{C_BOLD}{C_GREEN}1. Google Gemini API (Cloud API){C_RESET}")
        print(f"   Status:          {'✅ Активен' if has_gemini else '❌ Нет ключей'}")
        print(f"   Пул ключей:      {len(keys)} шт. ({', '.join(keys) if keys else 'пусто'})")
        print(f"   Дефолтная модель: gemini-2.5-flash / gemini-3.1-flash-lite")
        print()
        
        # 2. Gemini CLI
        use_gemini_cli = bool(ai_cfg.get("use_gemini_cli", True))
        gemini_cli_model = str(ai_cfg.get("gemini_cli_model_id", "gemini-3.1-flash-lite"))
        print(f"{C_BOLD}{C_GREEN}2. Gemini CLI (Терминальный агент){C_RESET}")
        print(f"   Status:          {'✅ Включен' if use_gemini_cli else '○ Отключен'}")
        print(f"   Модель:          {gemini_cli_model}")
        print()
        
        # 3. Microsoft AI Foundry
        use_foundry = bool(ai_cfg.get("use_foundry", False))
        foundry_model = str(ai_cfg.get("foundry_model_id", "qwen2.5-1.5b"))
        foundry_url = str(ai_cfg.get("foundry_base_url", "http://localhost:54837"))
        print(f"{C_BOLD}{C_GREEN}3. Microsoft AI Foundry (Локальная LLM){C_RESET}")
        print(f"   Status:          {'✅ Включен' if use_foundry else '○ Отключен'}")
        print(f"   Модель:          {foundry_model}")
        print(f"   Endpoint:        {foundry_url}")
        print()
        
        # 4. Ollama
        use_ollama = bool(ai_cfg.get("use_ollama", False))
        ollama_model = str(ai_cfg.get("ollama_model_id", "llama3.1"))
        ollama_url = str(ai_cfg.get("ollama_base_url", "http://localhost:11434"))
        print(f"{C_BOLD}{C_GREEN}4. Ollama Local{C_RESET}")
        print(f"   Status:          {'✅ Включен' if use_ollama else '○ Отключен'}")
        print(f"   Модель:          {ollama_model}")
        print(f"   Endpoint:        {ollama_url}")
        print()
        
        # 5. OpenAI Compatible
        openai_cfg = config.get("openai_compat", {}).get("providers", {})
        if openai_cfg:
            print(f"{C_BOLD}{C_GREEN}5. OpenAI-Compatible Провайдеры{C_RESET}")
            for p_name, p_info in openai_cfg.items():
                base = p_info.get("base_url", "")
                models = ", ".join(p_info.get("models", [])) or "авто"
                print(f"   • {C_BOLD}{p_name}{C_RESET}: {base}")
                print(f"     Модели: {models}")
            print()
        
        return 0
    
    def cmd_logs(self, lines: int = 40, name: str = "fastapi") -> int:
        """Показать логи"""
        logs_dir = self.paths.project_root / "logs"
        if not logs_dir.exists():
            print(f"{C_YELLOW}Каталог logs/ пока пуст.{C_RESET}")
            return 0
        
        # Поиск лог-файла
        target_file = None
        if name == "fastapi":
            target_file = logs_dir / "fastapi.log"
        elif name == "info":
            target_file = logs_dir / "info.log"
        elif name == "error" or name == "errors":
            target_file = logs_dir / "errors.log"
        
        if not target_file or not target_file.exists():
            # Найти первый доступный лог
            for cand in ["fastapi.log", "info.log", "errors.log"]:
                if (logs_dir / cand).exists():
                    target_file = logs_dir / cand
                    break
        
        if not target_file or not target_file.exists():
            print(f"{C_YELLOW}Лог-файл не найден в {logs_dir}{C_RESET}")
            return 0
        
        print(f"\n{C_CYAN}📄 Последние {lines} строк: {target_file.name}{C_RESET}\n" + "-" * 70)
        try:
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                for line in all_lines[-int(lines):]:
                    print(line.rstrip())
        except Exception as e:
            print(f"{C_RED}Error чтения логов: {e}{C_RESET}")
        print("-" * 70 + "\n")
        return 0
    
    def cmd_config(self, subcommand: str = "show", key: str = "", value: str = "") -> int:
        """Работа с config.json"""
        config = self.config_mgr.load_config()
        
        if subcommand == "show":
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return 0
        
        if subcommand == "get":
            if not key:
                print(f"{C_RED}Укажите ключ (например: server.port){C_RESET}")
                return 1
            
            parts = key.split(".")
            val = config
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p, {})
                else:
                    val = None
                    break
            print(f"{key} = {json.dumps(val, ensure_ascii=False)}")
            return 0
        
        if subcommand == "set":
            if not key or value == "":
                print(f"{C_RED}Использование: assist config set <key> <value>{C_RESET}")
                return 1
            
            # Парсим значение
            parsed_val = value
            if value.lower() in ("true", "1", "yes"):
                parsed_val = True
            elif value.lower() in ("false", "0", "no"):
                parsed_val = False
            elif value.isdigit():
                parsed_val = int(value)
            
            # Устанавливаем значение
            parts = key.split(".")
            curr = config
            for p in parts[:-1]:
                if p not in curr or not isinstance(curr[p], dict):
                    curr[p] = {}
                curr = curr[p]
            curr[parts[-1]] = parsed_val
            
            # Сохраняем
            if self.config_mgr.save_config(config):
                print(f"{C_GREEN}✔ Обновлено: {key} = {parsed_val}{C_RESET}")
                return 0
            else:
                print(f"{C_RED}✗ Error сохранения конфигурации{C_RESET}")
                return 1
        
        return 0
    
    def cmd_test(self) -> int:
        """Запустить тесты"""
        print(f"{C_CYAN}🧪 Запуск тестов pytest...{C_RESET}")
        venv_python = str(self.paths.venv_python)
        result = subprocess.run(
            [venv_python, "-m", "pytest", "tests/"],
            cwd=str(self.paths.project_root),
            check=False
        )
        return result.returncode

def main():
    """Главная function"""
    parser = argparse.ArgumentParser(
        description="CLI ассистент для управления AI-Breadboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  assist start                  # Запустить основной сервер
  assist start unicorn          # Запустить FastAPI через uvicorn
  assist stop                   # Остановить все сервисы
  assist status                 # Показать status
  assist providers              # List провайдеров ИИ
  assist logs 50                # Последние 50 строк логов
  assist config get server.port # Получить значение
  assist config set server.port 8080  # Установить значение
  assist test                   # Запустить тесты
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Команда")
    
    # start
    start_parser = subparsers.add_parser("start", help="Запустить сервис")
    start_parser.add_argument("service", nargs="?", default="run", help="Сервис (run, unicorn, light, foundry)")
    
    # stop
    stop_parser = subparsers.add_parser("stop", help="Остановить сервис")
    stop_parser.add_argument("service", nargs="?", default="all", help="Сервис (server, foundry, all)")
    
    # restart
    subparsers.add_parser("restart", help="Перезапустить")
    
    # status
    subparsers.add_parser("status", help="Показать status")
    
    # providers
    subparsers.add_parser("providers", help="List провайдеров")
    
    # logs
    logs_parser = subparsers.add_parser("logs", help="Показать логи")
    logs_parser.add_argument("lines", nargs="?", type=int, default=40, help="Количество строк")
    logs_parser.add_argument("-n", "--name", default="fastapi", help="Имя лога (fastapi, info, error)")
    
    # config
    config_parser = subparsers.add_parser("config", help="Работа с config.json")
    config_parser.add_argument("subcommand", nargs="?", default="show", help="Субкоманда (show, get, set)")
    config_parser.add_argument("key", nargs="?", default="", help="Ключ")
    config_parser.add_argument("value", nargs="?", default="", help="Значение")
    
    # test
    subparsers.add_parser("test", help="Запустить тесты")
    
    args = parser.parse_args()
    
    # Если команда не указана, показать справку
    if not args.command:
        parser.print_help()
        return 0
    
    cli = AssistCLI()
    
    # Выполнить команду
    if args.command == "start":
        return cli.cmd_start(args.service)
    elif args.command == "stop":
        return cli.cmd_stop(args.service)
    elif args.command == "restart":
        return cli.cmd_restart()
    elif args.command == "status":
        return cli.cmd_status()
    elif args.command == "providers":
        return cli.cmd_providers()
    elif args.command == "logs":
        return cli.cmd_logs(args.lines, args.name)
    elif args.command == "config":
        return cli.cmd_config(args.subcommand, args.key, args.value)
    elif args.command == "test":
        return cli.cmd_test()
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
