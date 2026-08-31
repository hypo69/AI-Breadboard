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


# Директория для хранения состояния выбранных провайдера/модели
_STATE_DIR = __root__ / ".assist_state"
_PROVIDER_FILE = _STATE_DIR / "provider.json"
_MODEL_FILE = _STATE_DIR / "model.json"


def _ensure_state_dir() -> None:
    """Создает директорию состояния если её нет."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)


def _get_selected_provider() -> dict:
    """Возвращает текущий выбранный провайдер."""
    if not _PROVIDER_FILE.exists():
        return {}
    try:
        with open(_PROVIDER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _set_selected_provider(provider_name: str) -> None:
    """Сохраняет выбранный провайдер."""
    _ensure_state_dir()
    with open(_PROVIDER_FILE, "w", encoding="utf-8") as f:
        json.dump({"provider": provider_name}, f, ensure_ascii=False, indent=2)


def _get_selected_model() -> dict:
    """Возвращает текущую выбранную модель."""
    if not _MODEL_FILE.exists():
        return {}
    try:
        with open(_MODEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _set_selected_model(model_name: str, provider: str = "") -> None:
    """Сохраняет выбранную модель."""
    _ensure_state_dir()
    data = {"model": model_name}
    if provider:
        data["provider"] = provider
    with open(_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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


def _auto_start_server() -> bool:
    """Проверяет и при необходимости запускает сервер."""
    # Проверка через переменную окружения
    auto_env = os.getenv("AUTO_START_ASSIST_CLI", "").lower()
    if auto_env in ("false", "0", "no", ""):
        return False
    
    cfg = _get_config()
    auto_start = cfg.get("server", {}).get("auto_start_assist_cli", False)
    
    if not auto_start:
        return False
    
    # Проверяем, запущен ли сервер
    port = int(cfg.get("server", {}).get("port", 8000))
    pids = _get_occupied_port_pids(port)
    
    if pids:
        # Сервер уже запущен
        return False
    
    # Запускаем сервер через run.ps1
    run_script = __root__ / "run.ps1"
    if not run_script.exists():
        print(f"{C_YELLOW}⚠️  run.ps1 не найден, пропускаем автозапуск{C_RESET}")
        return False
    
    print(f"{C_CYAN}🚀 Автозапуск сервера через run.ps1...{C_RESET}")
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(run_script)],
            cwd=str(__root__),
            timeout=5  # Запуск в фоновом режиме, timeout для проверки
        )
        print(f"{C_GREEN}✔ Сервер запускается в фоновом режиме{C_RESET}")
        return True
    except subprocess.TimeoutExpired:
        # Это нормально, запуск продолжится в фоне
        print(f"{C_GREEN}✔ Сервер запускается в фоновом режиме{C_RESET}")
        return True
    except Exception as e:
        print(f"{C_RED}✗ Ошибка автозапуска: {e}{C_RESET}")
        return False


def cmd_status(args: argparse.Namespace) -> int:
    """Проверяет текущий статус сервера, портов и служб."""
    cfg = _get_config()
    server_cfg = cfg.get("server", {})
    port = int(server_cfg.get("port", 8000))
    use_ssl = bool(server_cfg.get("use_ssl", False))
    mode = str(server_cfg.get("mode", "DEV"))
    reload_on = bool(server_cfg.get("reload", True))

    proto = "https" if use_ssl else "http"
    local_url = f"{proto}://localhost:{port}/"

    print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║             СТАТУС AI ASSISTANT СИСТЕМЫ                       ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════╝{C_RESET}\n")

    # Автозапуск если сервер не запущен и включён переключатель
    _auto_start_server()
    
    # Проверка порта
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


# ============================================================================
# НОВЫЕ КОМАНДЫ ДЛЯ РАБОТЫ С ПРОВАЙДЕРАМИ И МОДЕЛЯМИ
# ============================================================================

def cmd_list_providers(args: argparse.Namespace) -> int:
    """Выводит список доступных провайдеров ИИ."""
    cfg = _get_config()
    ai_cfg = cfg.get("ai", {})
    key_names_env = os.getenv("GEMINI_API_KEY_NAMES", "")
    keys = [k.strip() for k in key_names_env.split(",") if k.strip()]
    has_gemini = len(keys) > 0

    selected = _get_selected_provider()
    selected_provider = selected.get("provider", "")

    print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║                    ДОСТУПНЫЕ ПРОВАЙДЕРЫ ИИ                         ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════╝{C_RESET}\n")

    providers = [
        ("gemini", "Google Gemini API", has_gemini),
        ("gemini_cli", "Gemini CLI", bool(ai_cfg.get("use_gemini_cli", True))),
        ("agy", "Google Antigravity (AGY)", bool(ai_cfg.get("use_agy", False)) and bool(os.getenv("AGY_API_KEY"))),
        ("foundry", "Microsoft AI Foundry", bool(ai_cfg.get("use_foundry", False))),
        ("ollama", "Ollama Local", bool(ai_cfg.get("use_ollama", False))),
        ("hf", "HuggingFace Local", bool(cfg.get("huggingface", {}).get("enabled", False))),
        ("onnx", "ONNX Runtime (DirectML)", bool(cfg.get("onnx", {}).get("enabled", False))),
        ("openai", "OpenAI Compatible", bool(cfg.get("openai_compat", {}).get("providers", {}))),
    ]

    for i, (name, desc, available) in enumerate(providers, 1):
        status = f"{C_GREEN}✓ Активен{C_RESET}" if available else f"{C_GRAY}○ Отключен{C_RESET}"
        marker = " ▶ " if name == selected_provider else "   "
        print(f"{marker}{i}. {C_BOLD}{name}{C_RESET}: {desc}")
        print(f"     Статус: {status}")

    print(f"\n{C_GRAY}Текущий провайдер: {C_BOLD}{selected_provider or 'не выбран'}{C_RESET}")
    print(f"\n{C_GRAY}Используйте: {C_CYAN}assist select provider <имя>{C_RESET} для выбора провайдера")
    return 0


def cmd_select_provider(args: argparse.Namespace) -> int:
    """Выбирает провайдера ИИ."""
    provider = getattr(args, "name", "")
    if not provider:
        print(f"{C_RED}Укажите имя провайдера. Доступные: gemini, gemini_cli, agy, foundry, ollama, hf, onnx, openai{C_RESET}")
        return 1

    valid_providers = ["gemini", "gemini_cli", "agy", "foundry", "ollama", "hf", "onnx", "openai"]
    provider_lower = provider.lower()

    if provider_lower not in valid_providers:
        print(f"{C_RED}Неизвестный провайдер: {provider}{C_RESET}")
        print(f"Доступные провайдеры: {', '.join(valid_providers)}")
        return 1

    _set_selected_provider(provider_lower)
    print(f"{C_GREEN}✓ Провайдер '{provider_lower}' выбран{C_RESET}")

    # Предложим выбрать модель
    print(f"\n{C_CYAN}Доступные модели для {provider_lower}:{C_RESET}")
    print(f"{C_GRAY}Используйте: assist list models{C_RESET}")
    return 0


def cmd_list_models(args: argparse.Namespace) -> int:
    """Выводит список моделей для выбранного провайдера или всех."""
    cfg = _get_config()
    ai_cfg = cfg.get("ai", {})
    selected = _get_selected_provider()
    selected_provider = selected.get("provider", "")
    selected_model = _get_selected_model().get("model", "")

    print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║                        СПИСОК МОДЕЛЕЙ                            ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════╝{C_RESET}\n")

    all_models = {}

    # Gemini
    all_models["gemini"] = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    # Gemini CLI
    cli_model = ai_cfg.get("gemini_cli_model_id", "gemini-3.1-flash-lite")
    all_models["gemini_cli"] = [cli_model, "gemini-2.5-flash", "gemini-3.1-pro-preview"]

    # AGY
    all_models["agy"] = [ai_cfg.get("agy_model_id", "agy-flash"), "agy-gemini-3.5-flash-lite"]

    # Foundry
    all_models["foundry"] = [ai_cfg.get("foundry_model_id", "qwen2.5-1.5b-instruct-generic-cpu:4")]

    # Ollama
    all_models["ollama"] = [ai_cfg.get("ollama_model_id", "llama3.1"), "qwen2.5:7b", "mistral"]

    # HuggingFace
    hf_cfg = cfg.get("huggingface", {})
    all_models["hf"] = [hf_cfg.get("default_model", "Qwen/Qwen2.5-0.5B-Instruct")]

    # ONNX
    all_models["onnx"] = ["qwen2.5-0.5b", "llama3-1b"]

    # OpenAI Compatible
    openai_cfg = cfg.get("openai_compat", {}).get("providers", {})
    if openai_cfg:
        for prov_name, prov_data in openai_cfg.items():
            models = prov_data.get("models", [])
            if models:
                all_models[prov_name] = models
            # Добавляем дефолтные для openai/deepseek
            if prov_name == "openai":
                all_models[prov_name] = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            elif prov_name == "deepseek":
                all_models[prov_name] = ["deepseek-chat", "deepseek-reasoner"]

    if selected_provider:
        if selected_provider in all_models:
            print(f"{C_BOLD}Провайдер: {selected_provider}{C_RESET}\n")
            for model in all_models[selected_provider]:
                marker = " ▶ " if model == selected_model else "   "
                print(f"{marker}{model}")
        else:
            print(f"{C_YELLOW}Нет информации о моделях для прова��дера: {selected_provider}{C_RESET}")
    else:
        print(f"{C_YELLOW}Провайдер не выбран. Сначала выберите провайдера:{C_RESET}")
        print(f"{C_GRAY}assist select provider <имя>{C_RESET}\n")
        print("Или используйте 'assist providers' для просмотра всех провайдеров\n")

    if selected_model:
        print(f"{C_GRAY}Текущая модель: {C_BOLD}{selected_model}{C_RESET}")
    return 0


def cmd_select_model(args: argparse.Namespace) -> int:
    """Выбирает модель для работы."""
    model = getattr(args, "name", "")
    if not model:
        print(f"{C_RED}Укажите имя модели. Сначала выберите провайдер: assist list models{C_RESET}")
        return 1

    # СНАЧАЛА получаем текущий выбранный провайдер
    provider = _get_selected_provider().get("provider", "")
    
    # Затем пытаемся уточнить по префиксу модели (только если есть явный префикс с ":")
    model_lower = model.lower()
    
    # Явные префиксы с двоеточием имеют приоритет
    if ":" in model:
        if model.startswith("gemini_cli:") or model.startswith("gemini-cli-"):
            provider = "gemini_cli"
        elif model.startswith("gemini:"):
            provider = "gemini"
        elif model.startswith("agy"):
            provider = "agy"
        elif model.startswith("foundry:"):
            provider = "foundry"
        elif model.startswith("ollama:"):
            provider = "ollama"
        elif model.startswith("hf:") or model.startswith("hf::"):
            provider = "hf"
        elif model.startswith("onnx:") or model.startswith("onnx::"):
            provider = "onnx"

    if not provider:
        print(f"{C_YELLOW}Провайдер не определен. Сначала выберите провайдера:{C_RESET}")
        print(f"{C_GRAY}assist select provider <имя>{C_RESET}")
        return 1

    _set_selected_model(model, provider)
    print(f"{C_GREEN}✓ Модель '{model}' выбрана для провайдера '{provider}'{C_RESET}")
    print(f"\n{C_CYAN}Теперь можете отправить запрос:{C_RESET}")
    print(f"{C_GRAY}assist model ask \"ваш вопрос\"{C_RESET}")
    return 0


def cmd_model_ask(args: argparse.Namespace) -> int:
    """Отправляет запрос к выбранной модели."""
    message = getattr(args, "message", "")
    if not message:
        print(f"{C_RED}Укажите сообщение для модели{C_RESET}")
        print(f"{C_GRAY}Пример: assist model ask \"Привет, как дела?\"{C_RESET}")
        return 1

    model_data = _get_selected_model()
    provider_data = _get_selected_provider()

    selected_model = model_data.get("model", "")
    selected_provider = model_data.get("provider", "") or provider_data.get("provider", "")

    if not selected_model and not selected_provider:
        print(f"{C_YELLOW}Модель не выбрана. Сначала выберите провайдер и модель:{C_RESET}")
        print(f"{C_GRAY}assist list providers")
        print(f"assist select provider <имя>")
        print(f"assist list models")
        print(f"assist select model <имя>{C_RESET}")
        return 1

    # Формируем полное имя модели с префиксом провайдера
    full_model_name = f"{selected_provider}:{selected_model}" if selected_provider else selected_model

    print(f"\n{C_CYAN}→ Провайдер: {selected_provider}{C_RESET}")
    print(f"{C_CYAN}→ Модель: {selected_model}{C_RESET}")
    print(f"{C_CYAN}→ Запрос: {message}{C_RESET}\n")
    print(f"{C_BOLD}{C_YELLOW}Ответ:{C_RESET}\n")

    # Загружаем системный промпт если есть
    system_prompt = ""
    prompt_file = _STATE_DIR / "system_prompt.txt"
    if prompt_file.exists():
        system_prompt = prompt_file.read_text(encoding="utf-8").strip()

    try:
        from core.fastapi.router_chat import get_chat_model
        import asyncio

        model = get_chat_model(full_model_name, system_instruction=system_prompt)

        async def run_chat():
            result = await model.chat(message)
            print(result)

        asyncio.run(run_chat())

    except ImportError as e:
        print(f"{C_RED}Ошибка импорта модулей: {e}{C_RESET}")
        print(f"{C_YELLOW}Убедитесь что проект установлен и все зависимости доступны{C_RESET}")
        return 1
    except Exception as e:
        print(f"{C_RED}Ошибка при обращении к модели: {e}{C_RESET}")
        return 1

    return 0


# ============================================================================
# КОМАНДЫ ДЛЯ РАБОТЫ С СИСТЕМНЫМИ ПРОМПТАМИ
# ============================================================================

def cmd_create_prompt(args: argparse.Namespace) -> int:
    """Создает новый системный промпт."""
    _ensure_state_dir()
    prompt_file = _STATE_DIR / "system_prompt.txt"

    # Проверяем, передан ли текст через аргумент
    prompt_text = getattr(args, "text", "") or ""

    if prompt_file.exists() and not prompt_text:
        print(f"{C_YELLOW}Системный промпт уже существует.{C_RESET}")
        print(f"{C_GRAY}Используйте: assist edit-prompt для редактирования{C_RESET}")
        print(f"Или удалите файл: {prompt_file}")
        return 1

    if prompt_text:
        # Используем переданный текст
        prompt_file.write_text(prompt_text, encoding="utf-8")
        print(f"\n{C_GREEN}✓ Системный промпт сохранен{C_RESET}")
        print(f"{C_GRAY}Файл: {prompt_file}{C_RESET}")
        return 0

    # Интерактивный ввод промпта
    print(f"\n{C_CYAN}Создание системного промпта{C_RESET}")
    print(f"{C_GRAY}Введите текст системного промпта (нажмите Enter для завершения ввода):{C_RESET}")
    print(f"{C_GRAY}Для отмены введите пустую строку или нажмите Ctrl+C{C_RESET}\n")

    try:
        lines = []
        while True:
            line = input()
            if line.strip() == "" and lines:
                break
            lines.append(line)
    except (KeyboardInterrupt, EOFError):
        print(f"\n{C_YELLOW}Создание промпта отменено.{C_RESET}")
        return 0

    if not lines:
        print(f"{C_YELLOW}Промпт пустой, не сохранен.{C_RESET}")
        return 0

    prompt_text = "\n".join(lines)
    prompt_file.write_text(prompt_text, encoding="utf-8")

    print(f"\n{C_GREEN}✓ Системный промпт сохранен{C_RESET}")
    print(f"{C_GRAY}Файл: {prompt_file}{C_RESET}")
    return 0


def cmd_edit_prompt(args: argparse.Namespace) -> int:
    """Редактирует существующий системный промпт."""
    _ensure_state_dir()
    prompt_file = _STATE_DIR / "system_prompt.txt"

    mode = getattr(args, "mode", "edit")

    if mode == "view":
        if not prompt_file.exists():
            print(f"{C_YELLOW}Системный промпт не существует. Создайте его:{C_RESET}")
            print(f"{C_GRAY}assist create-prompt{C_RESET}")
            return 1
        content = prompt_file.read_text(encoding="utf-8")
        print(f"\n{C_CYAN}Текущий системный промпт:{C_RESET}\n")
        print(content)
        return 0

    if mode == "delete":
        if not prompt_file.exists():
            print(f"{C_YELLOW}Системный промпт не существует.{C_RESET}")
            return 1
        prompt_file.unlink()
        print(f"{C_GREEN}✓ Системный промпт удален{C_RESET}")
        return 0

    # Редактирование (по умолчанию)
    if not prompt_file.exists():
        print(f"{C_YELLOW}Системный промпт не существует. Сначала создайте его:{C_RESET}")
        print(f"{C_GRAY}assist create-prompt{C_RESET}")
        return 1

    current = prompt_file.read_text(encoding="utf-8")

    print(f"\n{C_CYAN}Редактирование системного промпта{C_RESET}")
    print(f"{C_GRAY}Текущий текст:{C_RESET}\n")
    print(current)
    print(f"\n{C_GRAY}Введите новый текст (пустая строка = оставить без изменений):{C_RESET}")

    try:
        new_lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            new_lines.append(line)
    except (KeyboardInterrupt, EOFError):
        print(f"\n{C_YELLOW}Редактирование отменено.{C_RESET}")
        return 0

    if new_lines:
        new_text = "\n".join(new_lines)
        prompt_file.write_text(new_text, encoding="utf-8")
        print(f"\n{C_GREEN}✓ Системный промпт обновлен{C_RESET}")
    else:
        print(f"\n{C_GRAY}Промпт оставлен без изменений.{C_RESET}")

    return 0


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ
# ============================================================================

def cmd_current(args: argparse.Namespace) -> int:
    """Показывает текущие настройки (выбранный провайдер и модель)."""
    provider = _get_selected_provider()
    model = _get_selected_model()

    print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║                    ТЕКУЩИЕ НАСТРОЙКИ                             ║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════╝{C_RESET}\n")

    print(f"  {C_BOLD}Провайдер:{C_RESET}  {provider.get('provider', 'не выбран') or C_YELLOW + 'не выбран' + C_RESET}")
    print(f"  {C_BOLD}Модель:{C_RESET}    {model.get('model', 'не выбрана') or C_YELLOW + 'не выбрана' + C_RESET}")

    # Проверим системный промпт
    prompt_file = _STATE_DIR / "system_prompt.txt"
    if prompt_file.exists():
        prompt_content = prompt_file.read_text(encoding="utf-8")
        preview = prompt_content[:100] + "..." if len(prompt_content) > 100 else prompt_content
        print(f"\n  {C_BOLD}Системный промпт:{C_RESET} {C_GREEN}установлен{C_RESET}")
        print(f"  {C_GRAY}   → {preview}{C_RESET}")
    else:
        print(f"\n  {C_BOLD}Системный промпт:{C_RESET} {C_GRAY}не установлен{C_RESET}")

    print(f"\n{C_GRAY}Изменить настройки:")
    print(f"  assist select provider <имя>")
    print(f"  assist select model <имя>")
    print(f"  assist create-prompt / assist edit-prompt{C_RESET}\n")
    return 0


def cmd_shell(args: argparse.Namespace) -> int:
    """Открывает интерактивную оболочку Python с загруженными модулями проекта."""
    print(f"{C_CYAN}Запуск интерактивной оболочки Python...{C_RESET}")
    print(f"{C_GRAY}Доступны модули: core, header (как __root__){C_RESET}")
    print(f"{C_GRAY}Для выхода введите exit(){C_RESET}\n")

    venv_py = _get_venv_python()
    cmd = [venv_py, "-i", "-c", f"""
import sys
sys.path.insert(0, r'{__root__}')
from header import __root__
from core.fastapi.router_chat import get_chat_model
print('Доступны: __root__, get_chat_model')
print('Пример: model = get_chat_model(\"gemini:gemini-2.5-flash\")')
"""]
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
  assist status            # статус сервера, портов и моделей (автозапуск если включён)
  assist providers         # подробный список провайдеров и моделей ИИ
  assist logs 50           # последние 50 строк лога
  assist config show       # просмотр config.json
  assist test              # запуск pytest
  assist install-profile   # зарегистрировать команду 'assist' глобально в PowerShell

Управление провайдерами и моделями:
  assist list providers    # показать доступных провайдеров
  assist select provider <name>    # выбрать провайдера (gemini, gemini_cli, agy, foundry, ollama, hf, onnx, openai)
  assist list models       # показать модели выбранного провайдера
  assist select model <name>       # выбрать модель
  assist model ask "msg"   # отправить запрос к модели
  assist current           # показать текущие настройки

Работа с системными промптами:
  assist create-prompt     # создать системный промпт
  assist edit-prompt       # редактировать системный промпт
  assist edit-prompt view  # посмотреть текущий промпт
  assist edit-prompt delete # удалить промпт

Дополнительно:
  assist shell             # открыть интерактивную оболочку Python

Настройка автозапуска:
  В config.json установите:
  "server": {
    "auto_start_assist_cli": true
  }
  При включении сервер будет запускаться автоматически при вызове assist без параметров или assist status
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

    # --- НОВЫЕ КОМАНДЫ ---
    # list providers
    p_list_providers = subparsers.add_parser("list", help="Список (providers/models)")
    p_list_providers.add_argument("subcommand", nargs="?", default="", choices=["providers", "models"])

    # select provider
    p_select = subparsers.add_parser("select", help="Выбрать провайдер или модель")
    p_select.add_argument("target", choices=["provider", "model"], help="Что выбрать")
    p_select.add_argument("name", help="Имя провайдера или модели")

    # model ask
    p_model = subparsers.add_parser("model", help="Работа с моделью")
    p_model_sub = p_model.add_subparsers(dest="model_command", help="Команды модели")
    p_model_ask = p_model_sub.add_parser("ask", help="Отправить запрос модели")
    p_model_ask.add_argument("message", nargs="?", default="", help="Сообщение для модели")

    # create-prompt
    p_create_prompt = subparsers.add_parser("create-prompt", help="Создать системный промпт")
    p_create_prompt.add_argument("--text", "-t", default="", help="Текст промпта (можно передать сразу)")

    # edit-prompt
    p_edit_prompt = subparsers.add_parser("edit-prompt", help="Редактировать системный промпт")
    p_edit_prompt.add_argument("mode", nargs="?", default="edit", choices=["edit", "view", "delete"])

    # current - показать текущие настройки
    subparsers.add_parser("current", help="Показать текущие настройки (провайдер, модель)")

    # shell - интерактивная оболочка
    subparsers.add_parser("shell", help="Открыть интерактивную оболочку Python")

    args = parser.parse_args()

    if not args.command:
        # При вызове без параметров показываем справку, но перед этим проверяем автозапуск
        _auto_start_server()
        parser.print_help()
        return 0

    # Обработка составных команд
    if args.command == "list":
        if args.subcommand == "providers":
            return cmd_list_providers(args)
        elif args.subcommand == "models":
            return cmd_list_models(args)
        else:
            # По умолчанию показываем список провайдеров
            return cmd_list_providers(args)

    if args.command == "select":
        if args.target == "provider":
            return cmd_select_provider(args)
        elif args.target == "model":
            return cmd_select_model(args)

    if args.command == "model":
        if args.model_command == "ask":
            return cmd_model_ask(args)

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
        # Новые команды
        "list": lambda a: cmd_list_providers(a) if getattr(a, 'subcommand', '') == 'providers' else cmd_list_models(a),
        "select": lambda a: cmd_select_provider(a) if getattr(a, 'target', '') == 'provider' else cmd_select_model(a),
        "model": cmd_model_ask,
        "create-prompt": cmd_create_prompt,
        "edit-prompt": cmd_edit_prompt,
        "current": cmd_current,
        "shell": cmd_shell,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
