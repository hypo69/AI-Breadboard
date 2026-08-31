# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cross-platform utility functions
# =============================================================================
# Description:
#   Utilities for cross-platform operations including port management,
#   process handling, environment variable manipulation, and command execution.
#
# File: utils.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Cross-platform utility functions for system operations."""

import os
import sys
import socket
import subprocess
from pathlib import Path
from typing import Tuple, Optional, List

def find_available_port(host: str = "127.0.0.1", start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find an available port.
    
    Args:
        host: IP address to bind to.
        start_port: Starting port number.
        max_attempts: Maximum number of attempts.
    
    Returns:
        An available port number.
    
    Raises:
        RuntimeError: If no available ports found.
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
    """Check if port is open (process listening).
    
    Args:
        port: Port number to check.
        host: IP address to connect to.
    
    Returns:
        True if port is open, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def get_process_on_port(port: int) -> Optional[Tuple[int, str]]:
    """Get process ID and name listening on port.
    
    Args:
        port: Port number.
    
    Returns:
        Tuple (PID, process_name) or None if no process found.
    """
    try:
        if sys.platform == "win32":
            # Windows: netstat
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
            # Linux/macOS: lsof
            try:
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
                # lsof not available
                return (None, "unknown")
    
    except Exception as e:
        print(f"Error getting process on port {port}: {e}")
    
    return None

def get_process_name(pid: int) -> str:
    """Get process name by PID.
    
    Args:
        pid: Process ID.
    
    Returns:
        Process name or 'unknown'.
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
    """Terminate process.
    
    Args:
        pid: Process ID.
        force: Use SIGKILL (Unix) or /F flag (Windows).
    
    Returns:
        True if successful, False otherwise.
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

def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    check: bool = False,
    shell: bool = False
) -> subprocess.CompletedProcess:
    """Run command cross-platform.
    
    Args:
        cmd: Command and arguments list.
        cwd: Working directory.
        env: Environment variables.
        check: Raise error if return code != 0.
        shell: Use shell.
    
    Returns:
        CompletedProcess result.
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
    """Find command path (cross-platform which/where).
    
    Args:
        command: Command name to find.
    
    Returns:
        Path to command or None if not found.
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
