# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: TShark Network Packet Sensors Module
# =============================================================================
# Description:
#   Network packet capture sensors using TShark (Wireshark CLI engine).
#   Provides real-time packet metrics, protocol distributions, and anomaly indicators.
#
# File: sensors.py
# Project: ai-breadboard
# Package: apps.tshark
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""TShark network packet sensors for telemetry integration."""

from __future__ import annotations

import time
from typing import List, Optional, Any

from src.logger import logger
from apps.common.csv_logger import AppCsvLogger
from apps.windows.telemetry.models import HardwareSensor


class TSharkPacketSensor:
    """Network packet sensor using TShark for real-time capture metrics."""

    def __init__(self) -> None:
        """Initialize TShark packet sensor with CSV logging."""
        self._csv_logger = AppCsvLogger("tshark")
        self._last_net_io = None
        self._last_time = time.time()
        self._packet_count = 0
        self._byte_count = 0

    def get_packet_sensors(self, packets: List[Any] = None) -> List[HardwareSensor]:
        """Collect network packet metrics as sensors.

        Args:
            packets: Optional list of captured packets (PacketSummary objects).

        Returns:
            List[HardwareSensor]: Network packet telemetry as sensors.
        """
        sensors: List[HardwareSensor] = []
        
        try:
            if packets:
                # Calculate metrics from provided packets
                total_packets = len(packets)
                total_bytes = sum(p.length for p in packets)
                
                # Protocol distribution sensors
                protocol_counts: dict[str, int] = {}
                for p in packets:
                    proto = p.protocol.upper()
                    protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
                
                # Create sensors for each protocol
                for proto, count in protocol_counts.items():
                    sensors.append(HardwareSensor(
                        sensor_id=f"pkt_proto_{proto}",
                        name=f"Packet Protocol {proto}",
                        category="network_packet",
                        value=count,
                        unit="pkts",
                    ))
                
                # Total packet sensors
                sensors.append(HardwareSensor(
                    sensor_id="pkt_total",
                    name="Total Packets Captured",
                    category="network_packet",
                    value=total_packets,
                    unit="pkts",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id="pkt_bytes_total",
                    name="Total Bytes Captured",
                    category="network_packet",
                    value=total_bytes,
                    unit="B",
                ))
                
                # Average packet size
                if total_packets > 0:
                    avg_size = total_bytes / total_packets
                    sensors.append(HardwareSensor(
                        sensor_id="pkt_avg_size",
                        name="Average Packet Size",
                        category="network_packet",
                        value=round(avg_size, 2),
                        unit="B",
                    ))
                
                # Packet rate (if we have timing info)
                now = time.time()
                elapsed = max(now - self._last_time, 0.1)
                packet_rate = total_packets / elapsed
                
                sensors.append(HardwareSensor(
                    sensor_id="pkt_rate",
                    name="Packet Capture Rate",
                    category="network_packet",
                    value=round(packet_rate, 2),
                    unit="pkt/s",
                ))
                
                self._last_time = now
                self._packet_count = total_packets
                self._byte_count = total_bytes
            else:
                # Fallback sensors when no packets available
                sensors.append(HardwareSensor(
                    sensor_id="pkt_total",
                    name="Total Packets Captured",
                    category="network_packet",
                    value=self._packet_count,
                    unit="pkts",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id="pkt_bytes_total",
                    name="Total Bytes Captured",
                    category="network_packet",
                    value=self._byte_count,
                    unit="B",
                ))
                
                sensors.append(HardwareSensor(
                    sensor_id="pkt_rate",
                    name="Packet Capture Rate",
                    category="network_packet",
                    value=0.0,
                    unit="pkt/s",
                ))
            
        except Exception as ex:
            logger.debug(f"TShark packet sensor probe failed: {ex}")
        
        return sensors

    def get_capture_status_sensors(self, wrapper_available: bool = False, 
                                   interface: str = "", is_capturing: bool = False) -> List[HardwareSensor]:
        """Get sensors for TShark capture session status.

        Args:
            wrapper_available: Whether TShark binary is available.
            interface: Current capture interface.
            is_capturing: Whether capture is active.

        Returns:
            List[HardwareSensor]: Capture status sensors.
        """
        sensors: List[HardwareSensor] = []
        
        # TShark availability sensor
        sensors.append(HardwareSensor(
            sensor_id="tshark_available",
            name="TShark Binary Available",
            category="network_capture",
            value=1.0 if wrapper_available else 0.0,
            unit="status",
        ))
        
        # Capture interface sensor
        sensors.append(HardwareSensor(
            sensor_id="capture_interface",
            name="Capture Interface",
            category="network_capture",
            value=1.0 if interface else 0.0,
            unit="interface",
        ))
        
        # Capture active sensor
        sensors.append(HardwareSensor(
            sensor_id="capture_active",
            name="Capture Active",
            category="network_capture",
            value=1.0 if is_capturing else 0.0,
            unit="status",
        ))
        
        return sensors

    def log_packet_metrics(self, interface: str, packet_count: int, byte_count: int,
                          packet_rate: float, protocol_dist: dict[str, int]) -> None:
        """Log packet metrics to CSV.

        Args:
            interface: Network interface name.
            packet_count: Total packets captured.
            byte_count: Total bytes captured.
            packet_rate: Packets per second.
            protocol_dist: Protocol distribution dictionary.
        """
        try:
            self._csv_logger.log_poll(
                poll_type="packet_metrics",
                metric_name=f"{interface}_packet_count",
                value=packet_count,
                unit="pkts",
                status="OK",
                details={"interface": interface},
                filename="tshark_packet_sensors.csv",
            )
            
            self._csv_logger.log_poll(
                poll_type="packet_metrics",
                metric_name=f"{interface}_byte_count",
                value=byte_count,
                unit="B",
                status="OK",
                details={"interface": interface},
                filename="tshark_packet_sensors.csv",
            )
            
            self._csv_logger.log_poll(
                poll_type="packet_metrics",
                metric_name=f"{interface}_packet_rate",
                value=round(packet_rate, 2),
                unit="pkt/s",
                status="OK",
                details={"interface": interface},
                filename="tshark_packet_sensors.csv",
            )
            
            # Log protocol distribution as separate metrics
            for proto, count in protocol_dist.items():
                self._csv_logger.log_poll(
                    poll_type="packet_metrics",
                    metric_name=f"{interface}_proto_{proto.lower()}",
                    value=count,
                    unit="pkts",
                    status="OK",
                    details={"interface": interface, "protocol": proto},
                    filename="tshark_packet_sensors.csv",
                )
            
        except Exception as ex:
            logger.error(f"Failed to log packet metrics: {ex}")


def get_tshark_sensors(packets: List[Any] = None, wrapper_available: bool = False,
                      interface: str = "", is_capturing: bool = False) -> List[HardwareSensor]:
    """Convenience function to get TShark packet sensors.

    Args:
        packets: Optional list of captured packets.
        wrapper_available: Whether TShark binary is available.
        interface: Current capture interface.
        is_capturing: Whether capture is active.

    Returns:
        List[HardwareSensor]: TShark packet telemetry as sensors.
    """
    sensor = TSharkPacketSensor()
    sensors = sensor.get_packet_sensors(packets)
    sensors.extend(sensor.get_capture_status_sensors(wrapper_available, interface, is_capturing))
    return sensors
