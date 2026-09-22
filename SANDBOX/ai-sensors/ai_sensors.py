# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Sensors - Centralized Telemetry Aggregator
# =============================================================================
# Description:
#   Autonomous application for collecting telemetry from all /apps/ modules
#   (hardware, file events, processes, network) with JSON logging and
#   incremental writes.
#
# File: ai_sensors.py
# Project: ai-breadboard
# Package: SANDBOX.ai-sensors
# Author: Kiro AI
# Copyright: © 2026 hypo69
# =============================================================================

"""Centralized telemetry aggregator for AI-Breadboard SANDBOX."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import logger


class TelemetryAggregator:
    """Centralized aggregator for all telemetry data from /apps/ modules."""

    def __init__(
        self,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the telemetry aggregator.

        Args:
            config: Configuration dictionary with interval, file limits, etc.
        """
        self.config = config
        self.interval = config.get("interval_seconds", 5.0)
        self.max_file_size_mb = config.get("max_file_size_mb", 100)
        self.max_measurements = config.get("max_measurements", None)
        self.watch_directories = config.get("watch_directories", ["C:\\Users\\"])
        self.log_filename = config.get("log_filename", "ai_sensors_polls.json")
        self.collect_serial_numbers = config.get("collect_serial_numbers", True)
        self.collect_hardware_inventory = config.get("collect_hardware_inventory", True)
        self.collect_file_events = config.get("collect_file_events", True)

        # State tracking
        self._running = False
        self._stop_event = threading.Event()
        self._last_values: Dict[str, Any] = {}
        self._measurements_count = 0
        self._start_time: Optional[float] = None
        self._last_poll_time: Optional[float] = None

        # Telemetry sources
        self._collector = None
        self._lhm_service = None
        self._watchers: Dict[str, Any] = {}
        self._telemetry_service = None

        # Logger configuration
        self._log_dir = Path(os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or Path.home() / ".config") / "AI-Breadboard" / "apps" / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._current_log_file = self._log_dir / self.log_filename

        # Initialize telemetry sources
        self._init_telemetry_sources()

    def _init_telemetry_sources(self) -> None:
        """Initialize all telemetry source modules."""
        try:
            from apps.windows.hardware.hardware_monitor import HardwareMonitor
            self._collector = HardwareMonitor()
            logger.success("HardwareMonitor initialized")
        except Exception as ex:
            logger.warning(f"Failed to initialize HardwareMonitor: {ex}")

        try:
            from apps.windows.telemetry.service import TelemetryLoggerService
            self._telemetry_service = TelemetryLoggerService.get_instance()
            logger.success("TelemetryLoggerService initialized")
        except Exception as ex:
            logger.warning(f"Failed to initialize TelemetryLoggerService: {ex}")

        # Initialize LHM service (LibreHardwareMonitor Web API)
        try:
            from apps.librehardwaremonitor.core.lhm_service import LhmService, DEFAULT_ENDPOINT
            self._lhm_service = LhmService(endpoint_url=DEFAULT_ENDPOINT)
            if self._lhm_service.is_running():
                logger.success("LHM Web API initialized")
            else:
                logger.warning("LHM Web API not running - will try to use HardwareMonitor fallback")
        except Exception as ex:
            logger.warning(f"Failed to initialize LHM service: {ex}")

        # Initialize DirectoryWatchers for each configured directory
        if self.collect_file_events:
            for watch_dir in self.watch_directories:
                if os.path.isdir(watch_dir):
                    try:
                        from apps.windows_sysadmin.src.directory_watcher import DirectoryWatcher
                        watcher = DirectoryWatcher(watch_dir=watch_dir, max_history=500)
                        self._watchers[watch_dir] = watcher
                        watcher.start()
                        logger.success(f"DirectoryWatcher started for: {watch_dir}")
                    except Exception as ex:
                        logger.warning(f"Failed to initialize DirectoryWatcher for {watch_dir}: {ex}")

    def collect_hardware_snapshot(self) -> Dict[str, Any]:
        """Collect complete hardware snapshot using HardwareMonitor.

        Returns:
            Dict[str, Any]: Full hardware telemetry snapshot.
        """
        if not self._collector:
            return {}

        try:
            snapshot = self._collector.get_snapshot()
            result = snapshot.to_dict()

            # Add serial numbers if enabled
            if self.collect_serial_numbers:
                result["serial_numbers"] = self.collect_serial_numbers_data()

            return result
        except Exception as ex:
            logger.warning(f"Failed to collect hardware snapshot: {ex}")
            return {}

    def collect_serial_numbers_data(self) -> Dict[str, Any]:
        """Collect serial numbers from all devices.

        Returns:
            Dict[str, Any]: Serial numbers for disks, memory, and other devices.
        """
        serials: Dict[str, Any] = {}

        try:
            from apps.windows.hardware.smartctl_probe import SmartProber
            prober = SmartProber()
            drives = prober.scan_drives()
            serials["disks"] = [
                {
                    "device": d.device,
                    "model": d.model,
                    "serial": d.serial,
                    "capacity_gb": d.capacity_gb,
                }
                for d in drives
            ]
        except Exception as ex:
            logger.debug(f"Failed to collect disk serial numbers: {ex}")

        try:
            import wmi
            w = wmi.WMI()
            memory = w.Win32_PhysicalMemory()
            serials["memory"] = [
                {
                    "bank": str(m.BankLabel or "DIMM"),
                    "capacity_gb": round(int(m.Capacity or 0) / (1024**3), 1),
                    "speed_mhz": int(m.Speed or 3200),
                    "serial": str(m.SerialNumber or "N/A").strip(),
                }
                for m in memory
            ]
        except Exception as ex:
            logger.debug(f"Failed to collect memory serial numbers: {ex}")

        return serials

    def collect_lhm_sensors(self) -> Dict[str, Any]:
        """Collect sensors from LibreHardwareMonitor Web API.

        Returns:
            Dict[str, Any]: LHM sensor data if available, empty dict otherwise.
        """
        if not self._lhm_service or not self._lhm_service.is_running():
            return {}

        try:
            sensors = self._lhm_service.get_flattened_sensors()
            summary = self._lhm_service.get_system_summary()

            return {
                "lhm_available": True,
                "sensors": sensors,
                "summary": summary,
                "sensors_count": len(sensors) if sensors else 0,
            }
        except Exception as ex:
            logger.debug(f"Failed to collect LHM sensors: {ex}")
            return {}

    def collect_file_events(self) -> List[Dict[str, Any]]:
        """Collect recent file system events from all watchers.

        Returns:
            List[Dict[str, Any]]: Recent file events.
        """
        all_events: List[Dict[str, Any]] = []

        for watch_dir, watcher in self._watchers.items():
            try:
                events = watcher.get_recent_events(limit=100)
                for event in events:
                    event_dict = {
                        "timestamp": event.timestamp,
                        "action": event.action,
                        "path": event.path,
                        "watch_dir": watch_dir,
                        "source": "DirectoryWatcher",
                    }
                    all_events.append(event_dict)
            except Exception as ex:
                logger.debug(f"Failed to collect file events from {watch_dir}: {ex}")

        return all_events

    def _has_value_changed(self, key: str, new_value: Any) -> bool:
        """Check if value has changed since last poll.

        Args:
            key: Unique key for the value.
            new_value: New value to compare.

        Returns:
            bool: True if value changed or this is first poll.
        """
        prev_value = self._last_values.get(key)

        def to_hashable(val: Any) -> Any:
            if isinstance(val, dict):
                return tuple(sorted((k, to_hashable(v)) for k, v in val.items()))
            elif isinstance(val, (list, set)):
                return tuple(to_hashable(v) for v in val)
            return val

        prev_hashable = to_hashable(prev_value) if prev_value is not None else None
        new_hashable = to_hashable(new_value)

        changed = prev_hashable != new_hashable
        self._last_values[key] = new_value
        return changed

    def write_json_row(self, data: Dict[str, Any]) -> Path:
        """Write telemetry data to JSON file.

        Args:
            data: Telemetry data to write.

        Returns:
            Path: Path to the written file.
        """
        self.rotate_file_if_needed()

        # Format data for writing
        write_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measurement_number": self._measurements_count + 1,
            **data,
        }

        try:
            with open(self._current_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(write_data, ensure_ascii=False) + "\n")
            logger.debug(f"Written measurement #{self._measurements_count + 1}")
            return self._current_log_file
        except Exception as ex:
            logger.error(f"Failed to write JSON log: {ex}")
            return Path("")

    def rotate_file_if_needed(self) -> None:
        """Rotate log file if size exceeds max_file_size_mb."""
        try:
            if self._current_log_file.exists():
                size_mb = self._current_log_file.stat().st_size / (1024 * 1024)
                if size_mb >= self.max_file_size_mb:
                    # Rotate file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    rotated_name = self._current_log_file.stem + f"_{timestamp}.json"
                    rotated_path = self._current_log_file.parent / rotated_name

                    self._current_log_file.rename(rotated_path)
                    logger.info(f"Rotated log file: {self._current_log_file.name} -> {rotated_name}")

                    # Create new empty file
                    self._current_log_file.touch(exist_ok=True)
        except Exception as ex:
            logger.warning(f"Failed to rotate log file: {ex}")

    def poll_once(self) -> bool:
        """Perform single telemetry poll.

        Returns:
            bool: True if data was written, False otherwise.
        """
        try:
            self._measurements_count += 1
            self._last_poll_time = time.time()

            telemetry_data: Dict[str, Any] = {}

            # Collect hardware snapshot (HardwareMonitor)
            if self.collect_hardware_inventory and self._collector:
                hardware = self.collect_hardware_snapshot()
                if hardware:
                    telemetry_data["hardware"] = hardware

            # Collect LHM sensors (LibreHardwareMonitor Web API)
            if self.collect_hardware_inventory and self._lhm_service:
                lhm_data = self.collect_lhm_sensors()
                if lhm_data and lhm_data.get("lhm_available"):
                    telemetry_data["lhm_sensors"] = lhm_data

            # Collect file events
            if self.collect_file_events and self._watchers:
                file_events = self.collect_file_events()
                if file_events:
                    telemetry_data["file_events"] = file_events

            # Check if anything changed
            telemetry_hash = str(telemetry_data)
            if self._has_value_changed("telemetry", telemetry_hash) or not telemetry_data:
                if telemetry_data:
                    self.write_json_row(telemetry_data)
                    return True
                else:
                    logger.debug("No telemetry data collected")
            else:
                logger.debug("No changes detected, skipping write")

            # Check max measurements limit
            if self.max_measurements and self._measurements_count >= self.max_measurements:
                logger.info(f"Reached max measurements ({self.max_measurements}), stopping")
                self.stop()
                return True

            return False
        except Exception as ex:
            logger.error(f"Error during poll: {ex}")
            return False

    def start(self) -> bool:
        """Start background telemetry collection.

        Returns:
            bool: True if started successfully.
        """
        if self._running:
            logger.warning("Telemetry aggregator already running")
            return False

        self._running = True
        self._stop_event.clear()
        self._start_time = time.time()
        self._measurements_count = 0

        logger.info(f"Telemetry aggregator started (interval: {self.interval}s)")
        logger.info(f"Watch directories: {self.watch_directories}")
        logger.info(f"Log file: {self._current_log_file}")

        # Start worker thread
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="TelemetryAggregator")
        self._thread.start()

        return True

    def stop(self) -> bool:
        """Stop background telemetry collection.

        Returns:
            bool: True if stopped successfully.
        """
        if not self._running:
            return False

        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        self._thread = None

        logger.info(f"Telemetry aggregator stopped. Total measurements: {self._measurements_count}")
        return True

    def _worker_loop(self) -> None:
        """Background worker loop for periodic telemetry collection."""
        while not self._stop_event.is_set():
            poll_start = time.time()

            try:
                self.poll_once()
            except Exception as ex:
                logger.error(f"Error in worker loop: {ex}")

            # Calculate sleep time to maintain precise interval
            elapsed = time.time() - poll_start
            sleep_time = max(0.01, self.interval - elapsed)

            if self._stop_event.wait(timeout=sleep_time):
                break

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the telemetry aggregator.

        Returns:
            Dict[str, Any]: Status information.
        """
        uptime = round(time.time() - self._start_time, 1) if self._start_time and self._running else 0.0

        return {
            "running": self._running,
            "measurements_count": self._measurements_count,
            "uptime_seconds": uptime,
            "interval_seconds": self.interval,
            "max_file_size_mb": self.max_file_size_mb,
            "watch_directories_count": len(self._watchers),
            "log_file": str(self._current_log_file),
        }


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to config file (optional).

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    if config_path is None:
        # Default config path (parent directory of this script)
        script_dir = Path(__file__).parent
        config_path = script_dir / "config.json"

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {
            "interval_seconds": 5.0,
            "max_file_size_mb": 100,
            "max_measurements": None,
            "watch_directories": ["C:\\Users\\"],
            "log_filename": "ai_sensors_polls.json",
            "collect_serial_numbers": True,
            "collect_hardware_inventory": True,
            "collect_file_events": True,
        }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as ex:
        logger.error(f"Failed to load config from {config_path}: {ex}")
        return {}


def main() -> None:
    """Main entry point for ai-sensors application."""
    # Load configuration
    config = load_config()

    # Create aggregator
    aggregator = TelemetryAggregator(config)

    # Start collection
    aggregator.start()

    # Wait for stop signal (Ctrl+C)
    try:
        while aggregator._running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        aggregator.stop()


if __name__ == "__main__":
    main()
