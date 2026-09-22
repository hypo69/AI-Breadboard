# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cloudflared Monitor State and Diagnostics Engine
# =============================================================================
# Description:
#   Core engine for monitoring Cloudflare Tunnel (cloudflared) daemon, parsing
#   tunnel logs, probing public hostnames, collecting process telemetry, and
#   evaluating heuristic / AI health diagnostics.
#
# File: state.py
# Project: ai-breadboard
# Package: apps.cloudflared_monitor.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Cloudflared process supervision, log parsing, endpoint probing, and diagnostics."""

from __future__ import annotations

import csv
import datetime
import io
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore
    PSUTIL_AVAILABLE = False

from logger import logger


@dataclass
class CloudflaredProcessInfo:
    """Process metrics and state for the cloudflared daemon."""

    is_running: bool = False
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    num_threads: int = 0
    uptime_seconds: float = 0.0
    start_time: Optional[str] = None
    exe_path: Optional[str] = None
    cmdline: List[str] = field(default_factory=list)


@dataclass
class CloudflaredLogEntry:
    """Structured log record parsed from cloudflared.log."""

    timestamp: str
    level: str  # 'INFO', 'WARN', 'ERROR', 'DEBUG', etc.
    message: str
    connection_id: Optional[str] = None
    raw: str = ""


@dataclass
class EndpointHealth:
    """Status and response metrics for the public tunnel endpoint."""

    url: str = "https://kino.davidka.net"
    is_reachable: bool = False
    status_code: Optional[int] = None
    response_time_ms: float = 0.0
    last_checked: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CloudflaredAnomaly:
    """Identified issue or anomaly in tunnel operation."""

    title: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'


@dataclass
class CloudflaredDiagnosticReport:
    """Diagnostic health assessment report."""

    health_score: int
    status: str  # 'HEALTHY', 'DEGRADED', 'OFFLINE', 'CRITICAL'
    summary: str
    anomalies: List[CloudflaredAnomaly] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evaluated_at: str = ""


class CloudflaredState:
    """State manager and telemetry collector for Cloudflare Tunnel monitoring."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        public_url: str = "https://kino.davidka.net",
        log_file_rel: str = "logs/cloudflared.log",
        max_log_entries: int = 200,
    ) -> None:
        """Initialize Cloudflared state.

        Args:
            project_root: Path to workspace root directory.
            public_url: Public hostname endpoint to probe.
            log_file_rel: Relative or absolute path to cloudflared.log.
            max_log_entries: Maximum number of log lines to keep in memory.
        """
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent.parent
        self.public_url = public_url
        self.log_file = (
            Path(log_file_rel)
            if Path(log_file_rel).is_absolute()
            else self.project_root / log_file_rel
        )
        self.max_log_entries = max_log_entries

        self.process: CloudflaredProcessInfo = CloudflaredProcessInfo()
        self.endpoint: EndpointHealth = EndpointHealth(url=public_url)
        self.logs: List[CloudflaredLogEntry] = []
        self.report: Optional[CloudflaredDiagnosticReport] = None
        self.has_token: bool = False
        self.token_preview: str = ""
        self.exe_path: Optional[str] = None

        self.total_errors_in_log: int = 0
        self.total_warnings_in_log: int = 0
        self.active_connections_count: int = 0
        self.last_refreshed: str = ""

    def find_executable(self) -> Optional[str]:
        """Locate cloudflared.exe across common project and system paths.

        Returns:
            Optional[str]: Path to cloudflared executable if located, else None.
        """
        candidates = [
            r"C:\Users\onela\AppData\Local\bin\cloudflared.exe",
            str(self.project_root / "cloudflared.exe"),
            str(self.project_root / "bin" / "cloudflared.exe"),
        ]
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            candidates.append(str(Path(local_app_data) / "bin" / "cloudflared.exe"))

        for cand in candidates:
            if cand and Path(cand).exists():
                self.exe_path = cand
                return cand

        which_path = shutil.which("cloudflared.exe") or shutil.which("cloudflared")
        if which_path:
            self.exe_path = which_path
            return which_path

        self.exe_path = None
        return None

    def check_token(self) -> bool:
        """Inspect .env file for CLOUDFLARE_TUNNEL_TOKEN presence.

        Returns:
            bool: True if token is present and valid.
        """
        env_file = self.project_root / ".env"
        token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "")

        if not token and env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "CLOUDFLARE_TUNNEL_TOKEN":
                            token = v.strip().strip("'\"")
                            break
            except Exception as e:
                logger.warning(f"Error reading .env for cloudflared token: {e}")

        if token:
            self.has_token = True
            if len(token) > 10:
                self.token_preview = f"{token[:4]}...{token[-4:]}"
            else:
                self.token_preview = "***"
            return True

        self.has_token = False
        self.token_preview = "Missing"
        return False

    def inspect_process(self) -> CloudflaredProcessInfo:
        """Query host processes for running cloudflared instances.

        Returns:
            CloudflaredProcessInfo: Populated process telemetry.
        """
        if PSUTIL_AVAILABLE and psutil is not None:
            matched_proc: Optional[psutil.Process] = None

            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
                try:
                    pname = (proc.info.get("name") or "").lower()
                    if "cloudflared" in pname:
                        matched_proc = proc
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            if matched_proc:
                try:
                    with matched_proc.oneshot():
                        pid = matched_proc.pid
                        cpu = matched_proc.cpu_percent(interval=0.0)
                        mem_info = matched_proc.memory_info()
                        mem_mb = round(mem_info.rss / (1024 * 1024), 2)
                        mem_pct = round(matched_proc.memory_percent(), 2)
                        threads = matched_proc.num_threads()
                        ctime = matched_proc.create_time()
                        uptime = max(0.0, time.time() - ctime)
                        start_str = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S")
                        exe = matched_proc.exe() if hasattr(matched_proc, "exe") else self.exe_path
                        cmdline = matched_proc.cmdline()

                        self.process = CloudflaredProcessInfo(
                            is_running=True,
                            pid=pid,
                            cpu_percent=cpu,
                            memory_mb=mem_mb,
                            memory_percent=mem_pct,
                            num_threads=threads,
                            uptime_seconds=uptime,
                            start_time=start_str,
                            exe_path=exe,
                            cmdline=cmdline,
                        )
                        return self.process
                except Exception as e:
                    logger.debug(f"Failed to inspect cloudflared process via psutil: {e}")

        # Fallback for Windows host using tasklist
        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    ["tasklist", "/FO", "CSV", "/NH", "/FI", "IMAGENAME eq cloudflared*"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and "cloudflared" in res.stdout.lower():
                    reader = csv.reader(io.StringIO(res.stdout))
                    for row in reader:
                        if row and "cloudflared" in row[0].lower():
                            try:
                                pid = int(row[1])
                                mem_str = row[4].replace(" K", "").replace(",", "").replace(".", "").strip()
                                mem_mb = round(float(mem_str) / 1024.0, 2)
                            except Exception:
                                pid = 0
                                mem_mb = 0.0

                            self.process = CloudflaredProcessInfo(
                                is_running=True,
                                pid=pid,
                                memory_mb=mem_mb,
                                exe_path=self.exe_path,
                            )
                            return self.process
            except Exception as e:
                logger.debug(f"Failed to inspect cloudflared process via tasklist: {e}")

        self.process = CloudflaredProcessInfo(is_running=False)
        return self.process

    def parse_log_line(self, line: str) -> Optional[CloudflaredLogEntry]:
        """Parse a single line from cloudflared.log.

        Args:
            line: Raw log line.

        Returns:
            Optional[CloudflaredLogEntry]: Parsed entry or None.
        """
        line = line.strip()
        if not line:
            return None

        # Format 0: JSON format (e.g. {"level":"error","time":"2026-09-13T03:09:23Z","message":"..."})
        if line.startswith("{") and line.endswith("}"):
            try:
                import json
                data = json.loads(line)
                if isinstance(data, dict):
                    raw_lvl = str(data.get("level", "info")).upper()
                    if raw_lvl in ("ERR", "ERROR"):
                        level = "ERROR"
                    elif raw_lvl in ("WRN", "WARN", "WARNING"):
                        level = "WARN"
                    elif raw_lvl in ("DBG", "DEBUG"):
                        level = "DEBUG"
                    else:
                        level = "INFO"

                    timestamp = str(data.get("time") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    msg_text = str(data.get("message") or data.get("msg") or data.get("error") or line)
                    if data.get("error") and data.get("error") != msg_text:
                        msg_text = f"{msg_text}: {data.get('error')}"
                    conn_id = str(data.get("connIndex")) if "connIndex" in data else str(data.get("connection", "")) or None

                    return CloudflaredLogEntry(
                        timestamp=timestamp,
                        level=level,
                        message=msg_text,
                        connection_id=conn_id,
                        raw=line,
                    )
            except Exception:
                pass

        # Format 1: 2026-09-13T03:40:00Z ERR message connIndex=0
        # Format 2: 2026/09/13 03:40:00 [ERR] message
        # Format 3: timestamp level=info msg="..."
        level = "INFO"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = line
        conn_id = None

        iso_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^ ]*)\s+([A-Z]{3,5})\s+(.*)$", line)
        if iso_match:
            timestamp = iso_match.group(1)
            raw_lvl = iso_match.group(2).upper()
            message = iso_match.group(3)
            if raw_lvl in ("ERR", "ERROR"):
                level = "ERROR"
            elif raw_lvl in ("WRN", "WARN", "WARNING"):
                level = "WARN"
            elif raw_lvl in ("INF", "INFO"):
                level = "INFO"
            elif raw_lvl in ("DBG", "DEBUG"):
                level = "DEBUG"
            else:
                level = raw_lvl
        elif " ERR " in line or "[ERR]" in line or "level=error" in line:
            level = "ERROR"
        elif " WRN " in line or "[WRN]" in line or "level=warn" in line:
            level = "WARN"
        elif " INF " in line or "[INF]" in line or "level=info" in line:
            level = "INFO"

        conn_id = None
        conn_idx_match = re.search(r"connIndex=(\d+)", line, re.IGNORECASE)
        if conn_idx_match:
            conn_id = conn_idx_match.group(1)
        else:
            conn_guid_match = re.search(r"connection[ =]([a-f0-9\-]+)", line, re.IGNORECASE)
            if conn_guid_match:
                conn_id = conn_guid_match.group(1)

        return CloudflaredLogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            connection_id=conn_id,
            raw=line,
        )

    def tail_logs(self, limit: int = 100) -> List[CloudflaredLogEntry]:
        """Read and parse the latest entries from cloudflared.log.

        Args:
            limit: Maximum entries to return.

        Returns:
            List[CloudflaredLogEntry]: Parsed log entries (latest first).
        """
        if not self.log_file.exists():
            self.logs = []
            self.total_errors_in_log = 0
            self.total_warnings_in_log = 0
            self.active_connections_count = 0
            return []

        try:
            with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning(f"Error reading {self.log_file}: {e}")
            return []

        parsed: List[CloudflaredLogEntry] = []
        errors = 0
        warnings = 0
        active_connections = set()

        # Parse recent slice
        recent_lines = lines[-min(len(lines), self.max_log_entries):]
        for l in recent_lines:
            entry = self.parse_log_line(l)
            if entry:
                parsed.append(entry)
                if entry.level == "ERROR":
                    errors += 1
                elif entry.level == "WARN":
                    warnings += 1
                if "Registered tunnel connection" in entry.message or "Connection" in entry.message:
                    if entry.connection_id:
                        active_connections.add(entry.connection_id)

        self.total_errors_in_log = errors
        self.total_warnings_in_log = warnings
        self.active_connections_count = max(len(active_connections), 1 if self.process.is_running else 0)
        self.logs = list(reversed(parsed))[:limit]
        return self.logs

    def probe_endpoint(self, timeout: float = 3.0) -> EndpointHealth:
        """Perform HTTP health probe against the public tunnel URL.

        Args:
            timeout: Timeout in seconds for HTTP GET probe.

        Returns:
            EndpointHealth: Connectivity and latency measurement.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.public_url:
            self.endpoint = EndpointHealth(
                url=self.public_url,
                is_reachable=False,
                last_checked=now_str,
                error_message="No public URL configured",
            )
            return self.endpoint

        start_time = time.perf_counter()
        req = urllib.request.Request(
            self.public_url,
            headers={"User-Agent": "AI-Breadboard-CloudflaredMonitor/1.0"},
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
                self.endpoint = EndpointHealth(
                    url=self.public_url,
                    is_reachable=True,
                    status_code=response.status,
                    response_time_ms=elapsed_ms,
                    last_checked=now_str,
                    error_message=None,
                )
        except urllib.error.HTTPError as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
            # HTTP 401, 403, 404 still means tunnel reached origin/edge
            self.endpoint = EndpointHealth(
                url=self.public_url,
                is_reachable=True,
                status_code=e.code,
                response_time_ms=elapsed_ms,
                last_checked=now_str,
                error_message=f"HTTP {e.code}: {e.reason}",
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
            self.endpoint = EndpointHealth(
                url=self.public_url,
                is_reachable=False,
                status_code=None,
                response_time_ms=elapsed_ms,
                last_checked=now_str,
                error_message=str(e),
            )

        return self.endpoint

    def evaluate_diagnostics(self) -> CloudflaredDiagnosticReport:
        """Evaluate heuristics and calculate health score for the tunnel.

        Returns:
            CloudflaredDiagnosticReport: Diagnostic score and recommendations.
        """
        score = 100
        anomalies: List[CloudflaredAnomaly] = []
        recs: List[str] = []

        # 1. Check Executable
        if not self.exe_path:
            score -= 40
            anomalies.append(
                CloudflaredAnomaly(
                    title="Executable Not Found",
                    description="cloudflared.exe was not detected in AppData or PATH.",
                    severity="high",
                )
            )
            recs.append("Install cloudflared using .\\install.ps1 or place in AppData\\Local\\bin.")

        # 2. Check Token
        if not self.has_token:
            score -= 40
            anomalies.append(
                CloudflaredAnomaly(
                    title="Missing Cloudflare Token",
                    description="CLOUDFLARE_TUNNEL_TOKEN is not defined in .env or environment.",
                    severity="critical",
                )
            )
            recs.append("Set CLOUDFLARE_TUNNEL_TOKEN in your .env file.")

        # 3. Check Process Status
        if not self.process.is_running:
            score -= 50
            anomalies.append(
                CloudflaredAnomaly(
                    title="Tunnel Process Inactive",
                    description="cloudflared daemon process is currently not running.",
                    severity="critical",
                )
            )
            recs.append("Launch tunnel via '.\\launchers\\Run-Cloudflared.ps1' or API /start endpoint.")
        else:
            if self.process.cpu_percent > 80:
                score -= 15
                anomalies.append(
                    CloudflaredAnomaly(
                        title="High CPU Usage",
                        description=f"cloudflared CPU consumption is {self.process.cpu_percent}%.",
                        severity="medium",
                    )
                )
                recs.append("Investigate high traffic load or potential infinite proxy loops.")

        # 4. Check Public Endpoint Reachability
        if self.endpoint.is_reachable:
            if self.endpoint.response_time_ms > 1500:
                score -= 10
                anomalies.append(
                    CloudflaredAnomaly(
                        title="High Latency to Public Host",
                        description=f"Public probe latency is {self.endpoint.response_time_ms} ms.",
                        severity="low",
                    )
                )
                recs.append("Check host network bandwidth and Cloudflare edge route health.")
        else:
            if self.process.is_running:
                score -= 25
                anomalies.append(
                    CloudflaredAnomaly(
                        title="Public Host Unreachable",
                        description=f"Failed to reach {self.public_url}: {self.endpoint.error_message}",
                        severity="high",
                    )
                )
                recs.append("Ensure local backend service (FastAPI on :8000) is running and bound properly.")

        # 5. Check Log Errors
        if self.total_errors_in_log > 10:
            score -= 20
            anomalies.append(
                CloudflaredAnomaly(
                    title="Elevated Error Rate in Logs",
                    description=f"{self.total_errors_in_log} errors recorded in recent log buffer.",
                    severity="high",
                )
            )
            recs.append("Review log messages for origin connection resets or authentication failures.")
        elif self.total_errors_in_log > 0:
            score -= 5

        health_score = max(0, min(100, score))
        if health_score >= 85:
            status = "HEALTHY"
        elif health_score >= 50:
            status = "DEGRADED"
        elif self.process.is_running:
            status = "CRITICAL"
        else:
            status = "OFFLINE"

        summary = (
            f"Tunnel Status: {status} (Score: {health_score}/100). "
            f"{len(anomalies)} anomalies identified. "
            f"Active process: {'YES (PID ' + str(self.process.pid) + ')' if self.process.is_running else 'NO'}."
        )

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.report = CloudflaredDiagnosticReport(
            health_score=health_score,
            status=status,
            summary=summary,
            anomalies=anomalies,
            recommendations=recs,
            evaluated_at=now_str,
        )
        return self.report

    def refresh(self, probe_network: bool = True) -> None:
        """Perform full state refresh cycle.

        Args:
            probe_network: Whether to execute network probe against public URL.
        """
        self.find_executable()
        self.check_token()
        self.inspect_process()
        self.tail_logs()
        if probe_network:
            self.probe_endpoint()
        self.evaluate_diagnostics()
        self.last_refreshed = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def start_tunnel(self) -> Tuple[bool, str]:
        """Launch cloudflared tunnel process via PowerShell launcher or direct binary.

        Returns:
            Tuple[bool, str]: (Success, status message).
        """
        if self.process.is_running:
            return True, f"Cloudflared already running with PID {self.process.pid}"

        launcher_ps = self.project_root / "launchers" / "Run-Cloudflared.ps1"
        if launcher_ps.exists():
            try:
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(launcher_ps),
                    ],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                time.sleep(1.0)
                self.inspect_process()
                return True, "Cloudflared start requested via launcher script"
            except Exception as e:
                logger.error(f"Failed to trigger Run-Cloudflared.ps1: {e}")
                return False, f"Failed to run launcher: {e}"

        exe = self.find_executable()
        if not exe:
            return False, "cloudflared.exe not found on host"

        if not self.has_token:
            return False, "CLOUDFLARE_TUNNEL_TOKEN missing in .env"

        token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "")
        log_path = str(self.log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.Popen(
                [
                    exe,
                    "--no-autoupdate",
                    "--loglevel",
                    "error",
                    "--logfile",
                    log_path,
                    "tunnel",
                    "run",
                    "--token",
                    token,
                ],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            time.sleep(1.0)
            self.inspect_process()
            return True, "Cloudflared launched directly"
        except Exception as e:
            logger.error(f"Failed to start cloudflared directly: {e}")
            return False, f"Start failed: {e}"

    def stop_tunnel(self) -> Tuple[bool, str]:
        """Terminate all running cloudflared.exe processes.

        Returns:
            Tuple[bool, str]: (Success, status message).
        """
        stopped = 0
        if PSUTIL_AVAILABLE and psutil is not None:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pname = (proc.info.get("name") or "").lower()
                    if "cloudflared" in pname:
                        proc.terminate()
                        stopped += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        elif sys.platform == "win32":
            try:
                subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True)
                stopped = 1
            except Exception:
                pass

        time.sleep(0.5)
        self.inspect_process()
        if stopped > 0:
            return True, f"Stopped {stopped} cloudflared process(es)"
        return True, "No active cloudflared processes found to stop"

    def restart_tunnel(self) -> Tuple[bool, str]:
        """Stop and restart cloudflared tunnel.

        Returns:
            Tuple[bool, str]: (Success, status message).
        """
        self.stop_tunnel()
        time.sleep(1.0)
        return self.start_tunnel()
