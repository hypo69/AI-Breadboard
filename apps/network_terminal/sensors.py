# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Terminal Sensors Module (Windows Native)
# =============================================================================
# Description:
#   Network monitoring sensors using ONLY Windows native tools (PowerShell, IP Helper API).
#   No TShark or external packet capture tools - only OS-native network monitoring.
#
# File: sensors.py
# Project: ai-breadboard
# Package: apps.network_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Network monitoring sensors for telemetry integration using Windows native tools."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from typing import List, Optional

from src.logger import logger
from apps.common.csv_logger import AppCsvLogger
from apps.windows.telemetry.models import HardwareSensor


class NetworkTerminalSensor:
    """Network monitoring sensor using Windows native tools only."""

    def __init__(self) -> None:
        """Initialize network sensor with CSV logging."""
        self._csv_logger = AppCsvLogger("network_terminal")
        self._last_net_io = None
        self._last_time = time.time()

    def get_network_sensors(self) -> List[HardwareSensor]:
        """Collect network interface metrics as sensors using Windows native tools.

        Returns:
            List[HardwareSensor]: Network interface telemetry as sensors.
        """
        sensors: List[HardwareSensor] = []
        
        try:
            import psutil
            
            # Get network I/O counters using psutil (Windows native wrapper)
            current_net_io = psutil.net_io_counters(pernic=True)
            now = time.time()
            elapsed = max(now - self._last_time, 0.1)
            
            if current_net_io and self._last_net_io:
                for name, current in current_net_io.items():
                    if name in self._last_net_io:
                        prev = self._last_net_io[name]
                        
                        # Calculate rates
                        bytes_sent_rate = max(0.0, (current.bytes_sent - prev.bytes_sent) / elapsed)
                        bytes_recv_rate = max(0.0, (current.bytes_recv - prev.bytes_recv) / elapsed)
                        packets_sent_rate = max(0.0, (current.packets_sent - prev.packets_sent) / elapsed)
                        packets_recv_rate = max(0.0, (current.packets_recv - prev.packets_recv) / elapsed)
                        
                        # Create sensors for each interface
                        sensors.append(HardwareSensor(
                            sensor_id=f"net_{name}_bytes_sent",
                            name=f"Network {name} Bytes Sent",
                            category="network",
                            value=round(bytes_sent_rate, 2),
                            unit="B/s",
                        ))
                        
                        sensors.append(HardwareSensor(
                            sensor_id=f"net_{name}_bytes_recv",
                            name=f"Network {name} Bytes Received",
                            category="network",
                            value=round(bytes_recv_rate, 2),
                            unit="B/s",
                        ))
                        
                        sensors.append(HardwareSensor(
                            sensor_id=f"net_{name}_packets_sent",
                            name=f"Network {name} Packets Sent",
                            category="network",
                            value=round(packets_sent_rate, 2),
                            unit="pkt/s",
                        ))
                        
                        sensors.append(HardwareSensor(
                            sensor_id=f"net_{name}_packets_recv",
                            name=f"Network {name} Packets Received",
                            category="network",
                            value=round(packets_recv_rate, 2),
                            unit="pkt/s",
                        ))
            
            self._last_net_io = current_net_io
            self._last_time = now
            
        except Exception as ex:
            logger.debug(f"Network sensor probe failed: {ex}")
        
        return sensors

    def get_listening_ports_native(self) -> List[dict]:
        """Get listening ports using Windows native PowerShell cmdlets.

        Returns:
            List[dict]: List of listening ports with process info.
        """
        ports = []
        try:
            # Use PowerShell Get-NetTCPConnection (Windows native)
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess | ConvertTo-Json -Compress"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    try:
                        pid = item.get("OwningProcess", 0)
                        proc_name = None
                        if pid and pid > 4:
                            try:
                                import psutil
                                proc = psutil.Process(pid)
                                proc_name = proc.name()
                            except Exception:
                                pass
                        
                        ports.append({
                            "port": item.get("LocalPort"),
                            "ip": item.get("LocalAddress", "0.0.0.0"),
                            "pid": pid,
                            "process": proc_name,
                        })
                    except Exception:
                        continue
                        
        except Exception as ex:
            logger.debug(f"Failed to get listening ports via PowerShell: {ex}")
        
        return ports

    def get_active_connections_native(self) -> List[dict]:
        """Get active connections using Windows native PowerShell cmdlets.

        Returns:
            List[dict]: List of active connections.
        """
        connections = []
        try:
            # Use PowerShell Get-NetTCPConnection for established connections
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess | ConvertTo-Json -Compress"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    try:
                        connections.append({
                            "local": f"{item.get('LocalAddress', '0.0.0.0')}:{item.get('LocalPort', 0)}",
                            "remote": f"{item.get('RemoteAddress', '0.0.0.0')}:{item.get('RemotePort', 0)}",
                            "pid": item.get("OwningProcess"),
                        })
                    except Exception:
                        continue
                        
        except Exception as ex:
            logger.debug(f"Failed to get active connections via PowerShell: {ex}")
        
        return connections

    def get_network_adapters_native(self) -> List[dict]:
        """Get network adapters using Windows native PowerShell cmdlets.

        Returns:
            List[dict]: List of network adapters with status.
        """
        adapters = []
        try:
            # Use PowerShell Get-NetAdapter
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, LinkSpeed, MacAddress | ConvertTo-Json -Compress"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    try:
                        adapters.append({
                            "name": item.get("Name"),
                            "description": item.get("InterfaceDescription"),
                            "status": item.get("Status"),
                            "speed_mbps": self._parse_speed(item.get("LinkSpeed")),
                            "mac": item.get("MacAddress"),
                        })
                    except Exception:
                        continue
                        
        except Exception as ex:
            logger.debug(f"Failed to get network adapters via PowerShell: {ex}")
        
        return adapters

    def _parse_speed(self, speed_str: Optional[str]) -> int:
        """Parse link speed string to Mbps integer.

        Args:
            speed_str: Speed string from PowerShell (e.g., "1 Gbps", "100 Mbps")

        Returns:
            int: Speed in Mbps
        """
        if not speed_str:
            return 0
        try:
            speed_str = speed_str.lower()
            if "gbps" in speed_str:
                return int(float(speed_str.replace("gbps", "").strip()) * 1000)
            elif "mbps" in speed_str:
                return int(float(speed_str.replace("mbps", "").strip()))
            elif "kbps" in speed_str:
                return int(float(speed_str.replace("kbps", "").strip()) / 1000)
            return 0
        except Exception:
            return 0

    def log_network_metrics(self, interface: str, bytes_sent: float, bytes_recv: float, 
                           packets_sent: float, packets_recv: float) -> None:
        """Log network metrics to CSV.

        Args:
            interface: Network interface name.
            bytes_sent: Bytes sent per second.
            bytes_recv: Bytes received per second.
            packets_sent: Packets sent per second.
            packets_recv: Packets received per second.
        """
        try:
            self._csv_logger.log_poll(
                poll_type="network_metrics",
                metric_name=f"{interface}_bytes_sent",
                value=round(bytes_sent, 2),
                unit="B/s",
                status="OK",
                details={"interface": interface},
                filename="network_terminal_sensors.csv",
            )
            
            self._csv_logger.log_poll(
                poll_type="network_metrics",
                metric_name=f"{interface}_bytes_recv",
                value=round(bytes_recv, 2),
                unit="B/s",
                status="OK",
                details={"interface": interface},
                filename="network_terminal_sensors.csv",
            )
            
            self._csv_logger.log_poll(
                poll_type="network_metrics",
                metric_name=f"{interface}_packets_sent",
                value=round(packets_sent, 2),
                unit="pkt/s",
                status="OK",
                details={"interface": interface},
                filename="network_terminal_sensors.csv",
            )
            
            self._csv_logger.log_poll(
                poll_type="network_metrics",
                metric_name=f"{interface}_packets_recv",
                value=round(packets_recv, 2),
                unit="pkt/s",
                status="OK",
                details={"interface": interface},
                filename="network_terminal_sensors.csv",
            )
            
        except Exception as ex:
            logger.error(f"Failed to log network metrics: {ex}")


def get_network_sensors() -> List[HardwareSensor]:
    """Convenience function to get network sensors.

    Returns:
        List[HardwareSensor]: Network interface telemetry as sensors.
    """
    sensor = NetworkTerminalSensor()
    return sensor.get_network_sensors()
