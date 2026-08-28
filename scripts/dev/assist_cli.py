## \file scripts/dev/assist_cli.py
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интерактивный CLI-ассистент управления проектом (assist)
# =============================================================================
# Описание:
#   Предоставляет удобный терминальный интерфейс для управления жизненным циклом
#   серверов, проверки статуса, мониторинга провайдеров ИИ, просмотра логов
#   и настройки конфигурации:
#   - assist start [run|unicorn|light|foundry]
#   - assist stop [server|foundry|all]
#   - assist restart
#   - assist status
#   - assist providers
#   - assist logs [lines]
#   - assist config [show|get|set]
#   - assist test
#   - assist install-profile
#
# File: scripts/dev/assist_cli.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import header
from header import __root__
from dotenv import load_dotenv

# Настройка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(__root__ / ".env")

# ANSI цвета для красивого терминального вывода
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"
C_MAGENTA = "\033[95m"


def _get_venv_python() -> str:
    """Возвращает путь к интерпретатору Python в виртуальном окружении venv."""
    venv_py = __root__ / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def _get_config() -> dict:
    """Загружает config.json."""
    cfg_path = __root__ / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"{C_RED}Ошибка чтения config.json: {e}{C_RESET}")
        return {}


def _get_occupied_port_pids(port: int) -> list[int]:
    """Возвращает список PID процессов, слушающих заданный порт."""
    pids = []
    if sys.platform.startswith("win"):
        try:
            out = subprocess.check_output(f"netstat -aon", shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore")
            for line in out.splitlines():
                if f":{port} " in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if parts and parts[-1].isdigit():
                        pid = int(parts[-1])
                        if pid > 0 and pid not in pids:
                            pids.append(pid)
        except Exception:
            pass
    return pids


def cmd_start(args: argparse.Namespace) -> int:
    """Запускает сервисы проекта."""
    target = getattr(args, "service", "run") or "run"
    target = target.lower()

    script_map = {
        "run": "run.ps1",
        "all": "run.ps1",
        "unicorn": "Run-Unicorn.ps1",
        "uvicorn": "Run-Unicorn.ps1",
        "light": "Run-LightServer.ps1",
        "foundry": "Run-Foundry.ps1",
    }

    script_name = script_map.get(target)
    if not script_name:
        print(f"{C_RED}❌ Неизвестная цель запуска: '{target}'{C_RESET}")
        print(f"{C_GRAY}Доступные цели: run (по умолчанию), unicorn, light, foundry, all{C_RESET}")
        return 1

    script_path = __root__ / script_name
    if not script_path.exists():
        script_path = __root__ / "launchers" / script_name
    if not script_path.exists():
        print(f"{C_RED}❌ Скрипт не найден: {script_path}{C_RESET}")
        return 1

    print(f"{C_CYAN}🚀 Запуск: {script_name}...{C_RESET}")
    if script_name == "Run-Foundry.ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path), "-Action", "start"]
    else:
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]

    return subprocess.call(cmd, cwd=str(__root__))


def cmd_stop(args: argparse.Namespace) -> int:
    """Останавливает сервер и сопутствующие процессы."""
    target = getattr(args, "service", "all") or "all"
    target = target.lower()

    cfg = _get_config()
    server_cfg = cfg.get("server", {})
    port = int(server_cfg.get("port", 3000))

    stopped_any = False

    if target in ("server", "all", "unicorn", "uvicorn", "light"):
        pids = _get_occupied_port_pids(port)
        if pids:
            print(f"{C_YELLOW}⏹ Остановка FastAPI сервера на порту {port} (PID: {pids})...{C_RESET}")
            for pid in pids:
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                    print(f"  {C_GREEN}✔ Завершен процесс PID {pid}{C_RESET}")
                    stopped_any = True
                except Exception as e:
                    print(f"  {C_RED}✖ Не удалось завершить PID {pid}: {e}{C_RESET}")
        else:
            print(f"{C_GRAY}Порт {port} свободен (FastAPI сервер не запущен){C_RESET}")

    if target in ("foundry", "all"):
        foundry_script = __root__ / "launchers" / "Run-Foundry.ps1"
        if not foundry_script.exists():
            foundry_script = __root__ / "Run-Foundry.ps1"
        if foundry_script.exists():
            print(f"{C_YELLOW}⏹ Остановка службы Foundry...{C_RESET}")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(foundry_script), "-Action", "stop"], cwd=str(__root__))
            stopped_any = True

    if not stopped_any and not pids:
        print(f"{C_GREEN}Все сервисы уже остановлены.{C_RESET}")
    return 0


def cmd_restart(args: argparse.Namespace) -> int:
    """Перезапускает сервер."""
    print(f"{C_CYAN}🔄 Перезапуск сервисов...{C_RESET}")
    cmd_stop(args)
    return cmd_start(args)


def cmd_status(args: argparse.Namespace) -> int:
    """Проверяет текущий статус сервера, портов и служб."""
    cfg = _get_config()
    server_cfg = cfg.get("server", {})
    port = int(server_cfg.get("port", 3000))
    use_ssl = bool(server_cfg.get("use_ssl", False))
    mode = str(server_cfg.get("mode", "DEV"))
    reload_on = bool(server_cfg.get("reload", True))

    proto = "https" if use_ssl else "http"
    local_url = f"{proto}://localhost:{port}/"

    print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║             СТАТУС AI ASSISTANT СИСТЕМЫ                       ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════╝{C_RESET}\n")

    # Проверка порта 3000
    pids = _get_occupied_port_pids(port)
    if pids:
        print(f"  {C_BOLD}FastAPI Сервер:{C_RESET}     {C_GREEN}● РАБОТАЕТ{C_RESET}")
        print(f"  {C_BOLD}URL:{C_RESET}                {C_CYAN}{local_url}{C_RESET}")
        print(f"  {C_BOLD}PID процессов:{C_RESET}      {', '.join(str(p) for p in pids)}")
    else:
        print(f"  {C_BOLD}FastAPI Сервер:{C_RESET}     {C_RED}○ ОСТАНОВЛЕН{C_RESET}")
        print(f"  {C_BOLD}Ожидаемый порт:{C_RESET}     {port}")

    print(f"  {C_BOLD}Режим / SSL:{C_RESET}        {mode} | SSL: {'ВКЛ' if use_ssl else 'ВЫКЛ'} | Autoreload: {'ВКЛ' if reload_on else 'ВЫКЛ'}")

    # Проверка Foundry
    ai_cfg = cfg.get("ai", {})
    use_foundry = bool(ai_cfg.get("use_foundry", False))
    foundry_url = str(ai_cfg.get("foundry_base_url", "http://localhost:54837"))
    foundry_pids = []
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq foundry.exe"', shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore")
        for line in out.splitlines():
            if "foundry.exe" in line.lower():
                parts = line.strip().split()
                if len(parts) > 1 and parts[1].isdigit():
                    foundry_pids.append(int(parts[1]))
    except Exception:
        pass

    if foundry_pids:
        print(f"  {C_BOLD}AI Foundry:{C_RESET}         {C_GREEN}● РАБОТАЕТ{C_RESET} (PID: {foundry_pids}, URL: {foundry_url})")
    elif use_foundry:
        print(f"  {C_BOLD}AI Foundry:{C_RESET}         {C_YELLOW}○ ВКЛЮЧЕН В CONFIG, НО НЕ ЗАПУЩЕН{C_RESET}")
    else:
        print(f"  {C_BOLD}AI Foundry:{C_RESET}         {C_GRAY}○ ОТКЛЮЧЕН В CONFIG{C_RESET}")

    # API Ключи Gemini
    key_names_env = os.getenv("GEMINI_API_KEY_NAMES", "")
    key_count = len([k for k in key_names_env.split(",") if k.strip()])
    print(f"  {C_BOLD}Gemini API Keys:{C_RESET}    {C_GREEN}{key_count} настроено в пуле ротации{C_RESET}")
    print("")
    return 0


def cmd_providers(args: argparse.Namespace) -> int:
    """Выводит детальный список всех настроенных провайдеров ИИ и их моделей."""
    cfg = _get_config()
    ai_cfg = cfg.get("ai", {})

    print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║                     РЕЕСТР ПРОВАЙДЕРОВ И МОДЕЛЕЙ ИИ                                   ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{C_RESET}\n")

    # 1. Google Gemini Cloud API
    key_names_env = os.getenv("GEMINI_API_KEY_NAMES", "")
    keys = [k.strip() for k in key_names_env.split(",") if k.strip()]
    has_gemini = len(keys) > 0
    print(f"{C_BOLD}{C_GREEN}1. Google Gemini API (Прямой Cloud API){C_RESET}")
    print(f"   Статус:          {'✅ Активен' if has_gemini else '❌ Нет ключей в .env'}")
    print(f"   Пул ключей:      {len(keys)} шт. ({', '.join(keys) if keys else 'пусто'})")
    print(f"   Дефолтная модель: gemini-2.5-flash / gemini-3.7-flash")
    print("")

    # 2. Gemini CLI
    use_gemini_cli = bool(ai_cfg.get("use_gemini_cli", True))
    gemini_cli_model = str(ai_cfg.get("gemini_cli_model_id", "gemini-3.1-flash-lite"))
    print(f"{C_BOLD}{C_GREEN}2. Gemini CLI (Терминальный агент){C_RESET}")
    print(f"   Статус:          {'✅ Включен' if use_gemini_cli else '○ Отключен'}")
    print(f"   Модель:          {gemini_cli_model}")
    print("")

    # 3. Antigravity AGY
    use_agy = bool(ai_cfg.get("use_agy", False))
    agy_model = str(ai_cfg.get("agy_model_id", "agy-flash"))
    has_agy_key = bool(os.getenv("AGY_API_KEY"))
    print(f"{C_BOLD}{C_GREEN}3. Google Antigravity (AGY Platform){C_RESET}")
    print(f"   Статус:          {'✅ Включен' if use_agy else '○ Отключен'}")
    print(f"   Модель:          {agy_model}")
    print(f"   API Key:         {'✅ Настроен' if has_agy_key else '○ Не задан'}")
    print("")

    # 4. Microsoft AI Foundry
    use_foundry = bool(ai_cfg.get("use_foundry", False))
    foundry_model = str(ai_cfg.get("foundry_model_id", "qwen2.5-1.5b"))
    foundry_url = str(ai_cfg.get("foundry_base_url", "http://localhost:54837"))
    print(f"{C_BOLD}{C_GREEN}4. Microsoft AI Foundry (Локальная служба LLM){C_RESET}")
    print(f"   Статус:          {'✅ Включен' if use_foundry else '○ Отключен'}")
    print(f"   Модель:          {foundry_model}")
    print(f"   Endpoint:        {foundry_url}")
    print("")

    # 5. Ollama
    use_ollama = bool(ai_cfg.get("use_ollama", False))
    ollama_model = str(ai_cfg.get("ollama_model_id", "llama3.1"))
    ollama_url = str(ai_cfg.get("ollama_base_url", "http://localhost:11434"))
    print(f"{C_BOLD}{C_GREEN}5. Ollama Local{C_RESET}")
    print(f"   Статус:          {'✅ Включен' if use_ollama else '○ Отключен'}")
    print(f"   Модель:          {ollama_model}")
    print(f"   Endpoint:        {ollama_url}")
    print("")

    # 6. HuggingFace Local
    hf_cfg = cfg.get("huggingface", {})
    hf_enabled = bool(hf_cfg.get("enabled", False))
    hf_model = str(hf_cfg.get("default_model", "Qwen/Qwen2.5-0.5B-Instruct"))
    print(f"{C_BOLD}{C_GREEN}6. HuggingFace (Local Transformers){C_RESET}")
    print(f"   Статус:          {'✅ Включен' if hf_enabled else '○ Отключен'}")
    print(f"   Модель:          {hf_model}")
    print("")

    # 7. ONNX DirectML
    onnx_cfg = cfg.get("onnx", {})
    onnx_enabled = bool(onnx_cfg.get("enabled", False))
    onnx_ep = str(onnx_cfg.get("execution_provider", "DirectMLExecutionProvider"))
    print(f"{C_BOLD}{C_GREEN}7. ONNX Runtime (DirectML / GPU / NPU){C_RESET}")
    print(f"   Статус:          {'✅ Включен' if onnx_enabled else '○ Отключен'}")
    print(f"   Execution Prov:  {onnx_ep}")
    print("")

    # 8. OpenAI Compatible Providers
    openai_cfg = cfg.get("openai_compat", {}).get("providers", {})
    if openai_cfg:
        print(f"{C_BOLD}{C_GREEN}8. OpenAI-Compatible Провайдеры (DeepSeek, LMStudio, OpenAI...){C_RESET}")
        for p_name, p_info in openai_cfg.items():
            base = p_info.get("base_url", "")
            models = ", ".join(p_info.get("models", [])) or "авто"
            print(f"   • {C_BOLD}{p_name}{C_RESET}: {base} (модели: {models})")
        print("")

    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    """Отображает последние строки логов."""
    lines_count = getattr(args, "lines", 40) or 40
    log_name = getattr(args, "name", "fastapi") or "fastapi"

    logs_dir = __root__ / "logs"
    if not logs_dir.exists():
        print(f"{C_YELLOW}Каталог logs/ пока пуст.{C_RESET}")
        return 0

    # Поиск нужного лог-файла
    target_file = None
    if log_name == "fastapi":
        target_file = logs_dir / "fastapi.log"
    elif log_name == "info":
        target_file = logs_dir / "info.log"
    elif log_name == "error" or log_name == "errors":
        target_file = logs_dir / "errors.log"
    elif log_name in ("uvicorn", "server"):
        # Самый свежий uvicorn_*.log
        uv_files = sorted(logs_dir.glob("uvicorn_*.log"), key=os.path.getmtime, reverse=True)
        if uv_files:
            target_file = uv_files[0]

    if not target_file or not target_file.exists():
        # Резервный выбор: info.log или fastapi.log
        for cand in ("fastapi.log", "info.log", "errors.log"):
            if (logs_dir / cand).exists():
                target_file = logs_dir / cand
                break

    if not target_file or not target_file.exists():
        print(f"{C_YELLOW}Лог-файл '{log_name}' не найден в {logs_dir}.{C_RESET}")
        return 0

    print(f"\n{C_CYAN}📄 Последние {lines_count} строк из: {target_file.name}{C_RESET}\n" + "-" * 70)
    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            for line in all_lines[-int(lines_count):]:
                print(line.rstrip())
    except Exception as e:
        print(f"{C_RED}Ошибка чтения файла логов: {e}{C_RESET}")
    print("-" * 70 + "\n")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Просмотр и изменение config.json."""
    sub = getattr(args, "subcommand", "show") or "show"
    cfg_path = __root__ / "config.json"
    cfg = _get_config()

    if sub == "show":
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return 0

    if sub == "get":
        key = getattr(args, "key", "")
        if not key:
            print(f"{C_RED}Укажите ключ (например: server.port или ai.use_foundry){C_RESET}")
            return 1
        parts = key.split(".")
        val = cfg
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, {})
            else:
                val = None
                break
        print(f"{key} = {json.dumps(val, ensure_ascii=False)}")
        return 0

    if sub == "set":
        key = getattr(args, "key", "")
        value = getattr(args, "value", "")
        if not key or value == "":
            print(f"{C_RED}Использование: assist config set <section.key> <value>{C_RESET}")
            return 1

        # Попытка разобрать тип значения
        parsed_val = value
        if value.lower() in ("true", "1", "yes"):
            parsed_val = True
        elif value.lower() in ("false", "0", "no"):
            parsed_val = False
        elif value.isdigit():
            parsed_val = int(value)

        parts = key.split(".")
        curr = cfg
        for p in parts[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        curr[parts[-1]] = parsed_val

        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        print(f"{C_GREEN}✔ Обновлено: {key} = {parsed_val}{C_RESET}")
        return 0

    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Запускает набор тестов."""
    print(f"{C_CYAN}🧪 Запуск тестов проекта pytest...{C_RESET}")
    venv_py = _get_venv_python()
    cmd = [venv_py, "-m", "pytest", "tests/"]
    extra = getattr(args, "rest", [])
    if extra:
        cmd.extend(extra)
    return subprocess.call(cmd, cwd=str(__root__))


def cmd_install_profile(args: argparse.Namespace) -> int:
    """Добавляет глобальную функцию `assist` в PowerShell профиль пользователя."""
    if not sys.platform.startswith("win"):
        print("Команда предназначена для Windows PowerShell.")
        return 0

    try:
        profile_path = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Write-Output $PROFILE"],
            text=True
        ).strip()
    except Exception as e:
        print(f"{C_RED}Не удалось определить путь к $PROFILE: {e}{C_RESET}")
        return 1

    profile_file = Path(profile_path)
    profile_file.parent.mkdir(parents=True, exist_ok=True)

    assist_ps1 = __root__ / "assist.ps1"
    snippet = f"""
# ==========================================
# AI ASSISTANT CLI ALIAS
# ==========================================
function assist {{
    & "{assist_ps1}" @args
}}
"""
    existing_content = ""
    if profile_file.exists():
        existing_content = profile_file.read_text(encoding="utf-8")

    if "function assist" in existing_content:
        print(f"{C_YELLOW}Функция 'assist' уже присутствует в $PROFILE:{C_RESET}\n  {profile_file}")
        return 0

    with open(profile_file, "a", encoding="utf-8") as f:
        f.write(snippet)

    print(f"{C_GREEN}✅ Функция 'assist' успешно зарегистрирована в вашем PowerShell $PROFILE:{C_RESET}")
    print(f"   {profile_file}")
    print(f"{C_CYAN}Теперь вы можете вводить 'assist start', 'assist status', 'assist providers' в любом терминале!{C_RESET}")
    return 0


def main() -> int:
    """Точка входа CLI assist."""
    parser = argparse.ArgumentParser(
        prog="assist",
        description="Терминальный ассистент управления проектом AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  assist start             # запуск сервера (run.ps1)
  assist start foundry     # запуск только AI Foundry
  assist stop              # остановка всех процессов сервера
  assist restart           # перезапуск сервера
  assist status            # статус сервера, портов и моделей
  assist providers         # подробный список провайдеров и моделей ИИ
  assist logs 50           # последние 50 строк лога
  assist config show       # просмотр config.json
  assist test              # запуск pytest
  assist install-profile   # зарегистрировать команду 'assist' глобально в PowerShell
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # start
    p_start = subparsers.add_parser("start", help="Запустить сервисы (run / unicorn / light / foundry)")
    p_start.add_argument("service", nargs="?", default="run", help="Сервис: run, unicorn, light, foundry, all")

    # stop
    p_stop = subparsers.add_parser("stop", help="Остановить сервер и процессы")
    p_stop.add_argument("service", nargs="?", default="all", help="Сервис: server, foundry, all")

    # restart
    p_restart = subparsers.add_parser("restart", help="Перезапустить сервер")
    p_restart.add_argument("service", nargs="?", default="run", help="Сервис: run, unicorn, light, foundry, all")

    # status
    subparsers.add_parser("status", help="Проверить статус сервера, портов и служб")

    # providers
    subparsers.add_parser("providers", help="Показать список и статус всех провайдеров ИИ")
    subparsers.add_parser("models", help="Алиас для assist providers")

    # logs
    p_logs = subparsers.add_parser("logs", help="Просмотр последних строк логов")
    p_logs.add_argument("lines", nargs="?", type=int, default=40, help="Количество строк (по умолчанию 40)")
    p_logs.add_argument("--name", "-n", default="fastapi", help="Имя лога: fastapi, info, error, uvicorn")

    # config
    p_cfg = subparsers.add_parser("config", help="Просмотр и изменение config.json")
    p_cfg.add_argument("subcommand", nargs="?", default="show", choices=["show", "get", "set"])
    p_cfg.add_argument("key", nargs="?", default="")
    p_cfg.add_argument("value", nargs="?", default="")

    # test
    p_test = subparsers.add_parser("test", help="Запуск тестов")
    p_test.add_argument("rest", nargs=argparse.REMAINDER, help="Дополнительные аргументы pytest")

    # install-profile
    subparsers.add_parser("install-profile", help="Зарегистрировать 'assist' в PowerShell $PROFILE")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    dispatch = {
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "providers": cmd_providers,
        "models": cmd_providers,
        "logs": cmd_logs,
        "config": cmd_config,
        "test": cmd_test,
        "install-profile": cmd_install_profile,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
