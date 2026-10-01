# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Network
# =============================================================================
# Description:
#   Команды захвата сетевого трафика и анализа TShark (network).
#
# Usage Examples:
#   Python API:
#     from scripts.cli.commands.network import register_network_parser
#
#     res = register_network_parser()
#
# File: network.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

from __future__ import annotations
"""Команды захвата сетевого трафика и анализа TShark (network)."""

import argparse


def register_network_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды network."""
    network_parser = subparsers.add_parser('network', help='Network traffic capture and TShark analysis')
    network_subparsers = network_parser.add_subparsers(dest='subcommand', help='Subcommands')
    network_subparsers.add_parser('status', help='Check TShark binary status')
    network_subparsers.add_parser('interfaces', help='List available network interfaces')
    network_devices = network_subparsers.add_parser('devices', help='List discovered devices on local network')
    network_devices.add_argument('--scan', '-s', action='store_true', help='Trigger active ARP/SSDP scan')
    network_devices.add_argument('--subnet', help='Target subnet CIDR (e.g. 192.168.1.0/24)')
    network_analyze = network_subparsers.add_parser('analyze', help='Analyze PCAP file')
    network_analyze.add_argument('--file', '-f', required=True, help='Path to .pcap or .pcapng file')
    network_analyze.add_argument('--filter', '-Y', default='', help='Wireshark display filter')


def run_network_command(args: argparse.Namespace) -> int:
    """Анализ PCAP трафика и проверка доступности TShark."""
    from apps.tshark import TSharkWrapper, TrafficAnalyzer
    sub = args.subcommand
    wrapper = TSharkWrapper()
    if sub == 'status':
        print(f'TShark Available: {wrapper.is_available()}')
        print(f"TShark Binary Path: {wrapper.tshark_path or 'Not Found'}")
        return 0
    if sub == 'interfaces':
        if not wrapper.is_available():
            print('Error: TShark is not available on this host.')
            return 1
        ifaces = wrapper.list_interfaces()
        print('\n--- NETWORK CAPTURE INTERFACES ---')
        for iface in ifaces:
            print(f'[{iface.id}] {iface.name} - {iface.description}')
        print('----------------------------------\n')
        return 0
    if sub == 'devices':
        from apps.windows.network.lan_scanner import WindowsLanScanner
        scanner = WindowsLanScanner()
        full_scan = bool(getattr(args, 'scan', False))
        subnet = getattr(args, 'subnet', None)
        print(f"[*] {'Сканирование' if full_scan else 'Чтение кеша'} устройств локальной сети{' в ' + subnet if subnet else ''}...")
        devices = scanner.discover_devices(full_scan=full_scan, subnet_cidr=subnet)
        print(f'\nНайдено {len(devices)} устройств в локальной сети:')
        print(f"{'IP Адрес':<18} {'MAC Адрес':<19} {'Производитель':<20} {'Имя хоста':<22} {'Статус'}")
        print('-' * 95)
        for d in devices:
            tag = ' [ШЛЮЗ]' if d.is_gateway else ' [ЛОКАЛЬНЫЙ]' if d.is_local else ''
            vendor_str = (d.vendor or 'Неизвестно')[:19]
            hostname_str = (d.hostname or '-')[:21]
            mac_str = d.mac or '-'
            print(f"{d.ip:<18} {mac_str:<19} {vendor_str:<20} {hostname_str:<22} {d.state}{tag}")
        print('-' * 95 + '\n')
        return 0
    if sub == 'analyze':
        pcap_file = getattr(args, 'file', '')
        if not pcap_file:
            print('Error: --file argument is required for PCAP analysis.')
            return 1
        if not wrapper.is_available():
            print('Error: TShark is not available on this host.')
            return 1
        packets = wrapper.read_pcap(pcap_file, display_filter=getattr(args, 'filter', '') or '')
        analyzer = TrafficAnalyzer()
        stats = analyzer.compute_stats(packets)
        heuristics = analyzer.detect_heuristics(packets)
        print('\n--- PCAP TRAFFIC REPORT ---')
        print(f'Total Packets: {stats.total_packets}')
        print(f'Total Volume: {stats.total_bytes} bytes')
        print(f'Protocol Distribution: {stats.protocol_distribution}')
        print(f'Top Sources: {stats.top_sources}')
        print(f'Top Destinations: {stats.top_destinations}')
        if heuristics:
            print('\nWarnings / Heuristics:')
            for h in heuristics:
                print(f'  [!] {h}')
        print('---------------------------\n')
        return 0
    print(f'Unknown network subcommand: {sub}')
    return 1
