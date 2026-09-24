# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network models and schema definitions
# =============================================================================
# Description:
#   Pydantic schema definitions for network packets, capture session parameters,
#   network interfaces, traffic analytics, and AI anomaly detection models.
#
# Examples:
#   >>> from src.network.models import NetworkInterface, PacketSummary
#   >>> iface = NetworkInterface(id="1", name="Ethernet")
#
# File: models.py
# Project: ai-breadboard
# Package: src.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Data models for network capture, traffic summary, and security analytics."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NetworkInterface(BaseModel):
    """Network capture interface information representation."""

    id: str = Field(..., description="Interface index or identifier")
    name: str = Field(..., description="Interface human-readable name or device ID")
    description: str = Field(default="", description="Optional interface description")


class CaptureFilter(BaseModel):
    """Capture filter parameters and constraints."""

    interface: str = Field(default="1", description="Interface ID or name")
    capture_filter: str = Field(default="", description="Capture filter (pcap syntax e.g. 'tcp port 443')")
    display_filter: str = Field(default="", description="Display filter (wireshark syntax e.g. 'http.request')")
    packet_count: int = Field(default=0, description="Max packets to capture (0 for infinite)")
    duration_seconds: int = Field(default=0, description="Duration in seconds (0 for infinite)")


class PacketSummary(BaseModel):
    """Summary of decoded packet details."""

    number: int = Field(default=0, description="Packet index number")
    packet_number: int = Field(default=0, description="Alias for packet index number")
    timestamp: str = Field(default="", description="Capture timestamp")
    source_ip: str = Field(default="", description="Source IP address or MAC")
    source: str = Field(default="", description="Alias for source IP")
    source_port: int | str = Field(default="", description="Source port")
    destination_ip: str = Field(default="", description="Destination IP address or MAC")
    destination: str = Field(default="", description="Alias for destination IP")
    destination_port: int | str = Field(default="", description="Destination port")
    protocol: str = Field(default="", description="Highest layer protocol (e.g. TCP, HTTP, DNS)")
    length: int = Field(default=0, description="Packet length in bytes")
    info: str = Field(default="", description="Summary information text")
    raw_layers: Dict[str, Any] = Field(default_factory=dict, description="Parsed layer fields dictionary")

    def model_post_init(self, __context: Any) -> None:
        """Синхронизация полей-алиасов после инициализации."""
        if not self.packet_number and self.number:
            self.packet_number = self.number
        elif not self.number and self.packet_number:
            self.number = self.packet_number

        if not self.source and self.source_ip:
            self.source = self.source_ip
        elif not self.source_ip and self.source:
            self.source_ip = self.source

        if not self.destination and self.destination_ip:
            self.destination = self.destination_ip
        elif not self.destination_ip and self.destination:
            self.destination_ip = self.destination


class TrafficStats(BaseModel):
    """Aggregated traffic statistics."""

    total_packets: int = Field(default=0, description="Total analyzed packets count")
    total_bytes: int = Field(default=0, description="Total analyzed bytes")
    protocol_distribution: Dict[str, int] = Field(default_factory=dict, description="Packet count per protocol")
    top_sources: Dict[str, int] = Field(default_factory=dict, description="Top source IP talkers")
    top_destinations: Dict[str, int] = Field(default_factory=dict, description="Top destination IP talkers")
    top_ports: Dict[str, int] = Field(default_factory=dict, description="Top active ports")


class AnomalyReport(BaseModel):
    """AI and heuristic security anomaly evaluation result."""

    threat_level: str = Field(default="low", description="Threat level: low, medium, high, critical")
    summary: str = Field(default="", description="High level analysis explanation")
    findings: List[str] = Field(default_factory=list, description="List of suspicious activities or warnings")
    recommended_actions: List[str] = Field(default_factory=list, description="Remediation steps")
