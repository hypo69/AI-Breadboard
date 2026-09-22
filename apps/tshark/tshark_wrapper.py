# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: TShark binary detection and process execution wrapper
# =============================================================================
# Description:
#   Provides asynchronous wrapper around TShark CLI for discovering network
#   interfaces, reading PCAP files, and executing live packet capture sessions.
#
# Examples:
#   >>> from src.network.tshark_wrapper import TSharkWrapper
#   >>> wrapper = TSharkWrapper()
#   >>> ifaces = wrapper.list_interfaces()
#
# File: tshark_wrapper.py
# Project: ai-breadboard
# Package: src.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""TShark binary detection and async execution wrapper."""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Any, Union

from logger import logger
from .models import NetworkInterface, PacketSummary, CaptureFilter


class TSharkWrapper:
    """Wrapper class managing interaction with TShark executable."""

    COMMON_WINDOWS_PATHS: List[str] = [
        r"C:\Program Files\Wireshark\tshark.exe",
        r"C:\Program Files (x86)\Wireshark\tshark.exe",
    ]

    def __init__(self, tshark_path: str = "") -> None:
        """Initialize TShark wrapper instance.

        Args:
            tshark_path (str): Explicit path to tshark.exe binary.
        """
        self.tshark_path: str = self._resolve_tshark_path(tshark_path)

    def _resolve_tshark_path(self, explicit_path: str = "") -> str:
        """Resolve valid tshark binary path from system.

        Args:
            explicit_path (str): Custom provided binary path.

        Returns:
            str: Resolved executable path or empty string if not found.
        """
        if explicit_path and Path(explicit_path).is_file():
            return explicit_path

        # Check system PATH
        found_path = shutil.which("tshark")
        if found_path:
            return found_path

        # Check standard Windows installation directories
        for candidate in self.COMMON_WINDOWS_PATHS:
            if Path(candidate).is_file():
                return candidate

        return ""

    def is_available(self) -> bool:
        """Check whether TShark executable is present and ready.

        Returns:
            bool: True if binary exists, False otherwise.
        """
        return bool(self.tshark_path and Path(self.tshark_path).is_file())

    def list_interfaces(self) -> List[NetworkInterface]:
        """Query available capture network interfaces using 'tshark -D'.

        Returns:
            List[NetworkInterface]: List of discovered network interfaces.
        """
        if not self.is_available():
            logger.warning("TShark executable is not available on this host.")
            return []

        try:
            result = subprocess.run(
                [self.tshark_path, "-D"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                err_msg = result.stderr.strip()
                if "Unable to load Npcap" in err_msg or "wpcap.dll" in err_msg:
                    logger.warning(
                        "TShark requires Npcap driver for live capture, but Npcap (wpcap.dll) is not installed. "
                        "Live capture is disabled until Npcap is installed: https://npcap.com/"
                    )
                else:
                    logger.error(f"Failed to list interfaces with TShark: {err_msg}")
                return []

            interfaces: List[NetworkInterface] = []
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                # Example: "1. \Device\NPF_{...} (Ethernet)" or "1. eth0"
                parts = line.split(".", 1)
                if len(parts) == 2:
                    idx = parts[0].strip()
                    desc = parts[1].strip()
                    name = desc
                    if "(" in desc and desc.endswith(")"):
                        name_part = desc.split("(")[-1].rstrip(")")
                        if name_part:
                            name = name_part
                    interfaces.append(NetworkInterface(id=idx, name=name, description=desc))
            return interfaces
        except Exception as ex:
            logger.error("Error executing TShark interface discovery", exc_info=True)
            return []

    def parse_json_packet(self, raw_pkt: Dict[str, Any]) -> PacketSummary:
        """Transform raw TShark JSON packet dictionary into standardized PacketSummary.

        Args:
            raw_pkt (Dict[str, Any]): Raw JSON packet structure from TShark.

        Returns:
            PacketSummary: Normalized packet structure.
        """
        layers = raw_pkt.get("_source", {}).get("layers", {})
        
        frame_layer = layers.get("frame", {})
        ip_layer = layers.get("ip", {})
        ipv6_layer = layers.get("ipv6", {})
        eth_layer = layers.get("eth", {})
        
        # Frame information
        frame_num = int(frame_layer.get("frame.number", 0) or 0)
        timestamp = frame_layer.get("frame.time", "")
        frame_len = int(frame_layer.get("frame.len", 0) or 0)
        
        # Source and Destination addresses
        src_ip = ip_layer.get("ip.src", "") or ipv6_layer.get("ipv6.src", "") or eth_layer.get("eth.src", "unknown")
        dst_ip = ip_layer.get("ip.dst", "") or ipv6_layer.get("ipv6.dst", "") or eth_layer.get("eth.dst", "unknown")
        
        # Determine top layer protocol
        protocol = "UNKNOWN"
        layer_keys = list(layers.keys())
        if layer_keys:
            # Filter out non-payload lower protocols
            non_top = {"frame", "eth", "raw"}
            candidates = [k.upper() for k in layer_keys if k not in non_top]
            protocol = candidates[-1] if candidates else layer_keys[-1].upper()

        info_text = f"{protocol} {src_ip} -> {dst_ip} Len={frame_len}"

        return PacketSummary(
            number=frame_num,
            timestamp=timestamp,
            source_ip=src_ip,
            destination_ip=dst_ip,
            protocol=protocol,
            length=frame_len,
            info=info_text,
            raw_layers=layers,
        )

    def read_pcap(
        self,
        pcap_path: Union[str, Path],
        display_filter: str = "",
        max_packets: int = 0,
    ) -> List[PacketSummary]:
        """Read and parse packets from an existing .pcap / .pcapng file.

        Args:
            pcap_path (Union[str, Path]): Path to PCAP file.
            display_filter (str): Wireshark display filter string.
            max_packets (int): Maximum number of packets to return.

        Returns:
            List[PacketSummary]: Decoded packet summaries list.
        """
        if not self.is_available():
            logger.error("Cannot read PCAP: TShark executable is not found.")
            return []

        path_obj = Path(pcap_path)
        if not path_obj.is_file():
            logger.error(f"PCAP file not found: {pcap_path}")
            return []

        cmd: List[str] = [
            self.tshark_path,
            "-r", str(path_obj.resolve()),
            "-T", "json",
        ]

        if display_filter:
            cmd.extend(["-Y", display_filter])

        if max_packets > 0:
            cmd.extend(["-c", str(max_packets)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                logger.error(f"TShark failed reading PCAP: {result.stderr}")
                return []

            if not result.stdout.strip():
                return []

            data = json.loads(result.stdout)
            if not isinstance(data, list):
                return []

            return [self.parse_json_packet(pkt) for pkt in data]
        except Exception as ex:
            logger.error("Failed to parse PCAP with TShark", exc_info=True)
            return []

    async def live_capture_stream(
        self,
        config: CaptureFilter,
    ) -> AsyncGenerator[PacketSummary, None]:
        """Stream live network packets asynchronously using TShark line/ek json output.

        Args:
            config (CaptureFilter): Capture filter settings.

        Yields:
            PacketSummary: Stream of captured and parsed packet summaries.
        """
        if not self.is_available():
            logger.error("Live capture failed: TShark executable not found.")
            return

        cmd: List[str] = [
            self.tshark_path,
            "-i", str(config.interface),
            "-T", "ek",
            "-l",
        ]

        if config.capture_filter:
            cmd.extend(["-f", config.capture_filter])

        if config.display_filter:
            cmd.extend(["-Y", config.display_filter])

        if config.packet_count > 0:
            cmd.extend(["-c", str(config.packet_count)])

        if config.duration_seconds > 0:
            cmd.extend(["-a", f"duration:{config.duration_seconds}"])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            pkt_count = 0
            while True:
                if not process.stdout:
                    break
                line = await process.stdout.readline()
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str or line_str.startswith('{"index":'):
                    continue

                try:
                    raw_doc = json.loads(line_str)
                    layers = raw_doc.get("layers", {})
                    if not layers:
                        continue
                    summary = self.parse_json_packet({"_source": {"layers": layers}})
                    pkt_count += 1
                    summary.number = pkt_count
                    yield summary
                except Exception:
                    continue

            await process.wait()
        except Exception as ex:
            logger.error("Live capture stream error encountered", exc_info=True)
