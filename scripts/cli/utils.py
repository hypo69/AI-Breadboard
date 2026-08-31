# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Утилиты для кроссплатформенной работы.
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: utils.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Утилиты для кроссплатформенной работы.
"""

import os
import sys
import socket
import subprocess
from pathlib import Path
from typing import Tuple, Optional, List

def find_available_port(host: str = "127.0.0.1", start_port: int = 8000, max_attempts: int = 100) -> int:
    """
    Найти доступный порт.
    
    Args:
        host: IP адрес
        start_port: Начальный порт
        max_attempts: Максимум попыток
    
    Returns:
        Доступный порт
    
    Raises:
        RuntimeError: Если нет доступных портов
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                s.listen(1)
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")

def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """
    Проверить, открыт ли порт.
    
    Args:
        port: Номер порта
        host: IP адрес
    
    Returns:
        True если порт открыт (процесс слушает), False иначе
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def get_process_on_port(port: int) -> Optional[Tuple[int, str]]:
    """
    Получить PID и имя процесса, слушающего на порте.
    
    Args:
        port: Номер порта
    
    Returns:
        Tuple (PID, имя_процесса) или None если процесса нет
    """
    try:
        if sys.platform == "win32":
            # Windows: netstat -aon
            output = subprocess.run(
                ["netstat", "-aon"],
                capture_output=True,
                text=True,
                check=False
            ).stdout
            
            for line in output.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid_str = parts[-1]
                        try:
                            pid = int(pid_str)
                            proc_name = get_process_name(pid)
                            return (pid, proc_name)
                        except (ValueError, Exception):
                            pass
        
        else:
            # Linux/macOS: lsof или netstat
            try:
                # Пробуем lsof (более надежный)
                output = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True,
                    text=True,
                    check=False
                ).stdout
                
                for line in output.split("\n")[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            proc_name = parts[0]
                            pid_str = parts[1]
                            try:
                                pid = int(pid_str)
                                return (pid, proc_name)
                            except ValueError:
                                pass
            except FileNotFoundError:
                # lsof не установлен, пробуем netstat
                output = subprocess.run(
                    ["netstat", "-tuln"],
                    capture_output=True,
                    text=True,
                    check=False
                ).stdout
                
                for line in output.split("\n"):
                    if f":{port}" in line:
                        return (None, "unknown")
    
    except Exception as e:
        print(f"Error getting process on port {port}: {e}")
    
    return None

def get_process_name(pid: int) -> str:
    """
    Получить имя процесса по PID.
    
    Args:
        pid: Процесс ID
    
    Returns:
        Имя процесса или 'unknown'
    """
    try:
        if sys.platform == "win32":
            output = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                check=False
            ).stdout
            
            for line in output.split("\n"):
                if str(pid) in line:
                    parts = line.split()
                    if parts:
                        return parts[0]
        
        else:
            output = subprocess.run(
                ["ps", "-p", str(pid), "-o", "comm="],
                capture_output=True,
                text=True,
                check=False
            ).stdout
            
            name = output.strip()
            if name:
                return name
    
    except Exception:
        pass
    
    return "unknown"

def kill_process(pid: int, force: bool = False) -> bool:
    """
    Завершить процесс.
    
    Args:
        pid: Процесс ID
        force: Использовать SIGKILL (Linux) или /F (Windows)
    
    Returns:
        True если successfully, False иначе
    """
    try:
        if sys.platform == "win32":
            cmd = ["taskkill", "/PID", str(pid)]
            if force:
                cmd.append("/F")
            
            result = subprocess.run(cmd, capture_output=True, check=False)
            return result.returncode == 0
        
        else:
            import signal
            signal_type = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, signal_type)
            return True
    
    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False

def ensure_in_path(binary_path: Path) -> bool:
    """
    Убедиться, что бинарник находится в PATH.
    
    Args:
        binary_path: Путь до бинарника
    
    Returns:
        True если в PATH или добавлен, False если Error
    """
    bin_dir = binary_path.parent
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    
    if str(bin_dir) not in path_dirs:
        if sys.platform == "win32":
            # Windows: добавить в реестр
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    access=winreg.KEY_SET_VALUE
                )
                current_path = winreg.QueryValueEx(key, "PATH")[0]
                new_path = f"{current_path}{os.pathsep}{bin_dir}"
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                winreg.CloseKey(key)
                return True
            except Exception as e:
                print(f"Error adding to PATH: {e}")
                return False
        
        else:
            # Linux/macOS: добавить в ~/.bashrc, ~/.zshrc
            shells = [Path.home() / ".bashrc", Path.home() / ".zshrc"]
            
            for shell_rc in shells:
                if shell_rc.exists():
                    content = shell_rc.read_text()
                    export_line = f'export PATH="{bin_dir}:$PATH"'
                    
                    if export_line not in content:
                        with open(shell_rc, "a") as f:
                            f.write(f"\n# Added by AI-Breadboard installer\n{export_line}\n")
            
            return True
    
    return True

def add_to_env_var(var_name: str, value: str, prepend: bool = True) -> bool:
    """
    Добавить значение к переменной окружения.
    
    Args:
        var_name: Имя переменной
        value: Значение
        prepend: Добавить в начало (True) или конец (False)
    
    Returns:
        True если successfully
    """
    try:
        current = os.environ.get(var_name, "")
        
        if not current:
            new_value = value
        elif prepend:
            new_value = f"{value}{os.pathsep}{current}"
        else:
            new_value = f"{current}{os.pathsep}{value}"
        
        if sys.platform == "win32":
            # Windows: реестр
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    access=winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, var_name, 0, winreg.REG_EXPAND_SZ, new_value)
                winreg.CloseKey(key)
                return True
            except Exception:
                return False
        
        else:
            # Linux/macOS: ~/.bashrc, ~/.zshrc
            shells = [Path.home() / ".bashrc", Path.home() / ".zshrc"]
            
            for shell_rc in shells:
                if shell_rc.exists():
                    content = shell_rc.read_text()
                    export_line = f'export {var_name}="{new_value}"'
                    
                    if export_line not in content:
                        with open(shell_rc, "a") as f:
                            f.write(f"\n# {var_name} added by AI-Breadboard\n{export_line}\n")
            
            return True
    
    except Exception as e:
        print(f"Error adding to {var_name}: {e}")
        return False

def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    check: bool = False,
    shell: bool = False
) -> subprocess.CompletedProcess:
    """
    Запустить команду кроссплатформенно.
    
    Args:
        cmd: Команда и аргументы
        cwd: Рабочая директория
        env: Переменные окружения
        check: Вызвать ошибку если return code != 0
        shell: Использовать shell
    
    Returns:
        CompletedProcess
    """
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=full_env,
        shell=shell,
        check=check
    )

def which(command: str) -> Optional[Path]:
    """
    Найти путь до команды (кроссплатформенный which/where).
    
    Args:
        command: Имя команды
    
    Returns:
        Путь до команды или None
    """
    try:
        result = subprocess.run(
            ["where" if sys.platform == "win32" else "which", command],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            path_str = result.stdout.strip().split("\n")[0]
            return Path(path_str)
    
    except Exception:
        pass
    
    return None
