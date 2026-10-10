# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Cli Commands - Agents
# =============================================================================
# Description:
#   Команды управления и запуска AI-агентов платформы AI Breadboard из каталога .agents.
#
# Usage Examples:
#   CLI:
#     py manage_tools.py agents list
#     py manage_tools.py agents run --name windows_controller_agent --query "Проверь диски"
#
# File: agents.py
# Project: ai-breadboard
# Package: scripts.cli.commands
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 08:32:00
# =============================================================================

from __future__ import annotations
"""Команды управления и запуска AI-агентов (agents)."""

import argparse
import asyncio
import json
from header import __root__
from src.ai.agents import AGENT_REGISTRY
from src.ai.agents.loader import list_available_agents, load_agent_from_manifest


def register_agents_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды agents."""
    agents_parser = subparsers.add_parser('agents', help='Autonomous AI agents management and execution')
    agents_subparsers = agents_parser.add_subparsers(dest='subcommand', help='Subcommands')
    agents_subparsers.add_parser('list', help='List available AI agents')
    agents_run = agents_subparsers.add_parser('run', help='Execute an AI agent')
    agents_run.add_argument('--name', required=True, help='Agent name, ID or manifest (e.g. windows_controller_agent, travel_agent, system_logs_agent)')
    agents_run.add_argument('--query', default='', help='Query or task for the agent')


def run_agents_command(args: argparse.Namespace) -> int:
    """Управление и запуск автономных AI-агентов."""
    sub = getattr(args, 'subcommand', None)

    if sub == 'list':
        manifest_agents = list_available_agents()
        if manifest_agents:
            print('\n=== ДЕКЛАРАТИВНЫЕ АГЕНТЫ (.agents/) ===')
            for a in manifest_agents:
                a_id = a.get('id', '')
                name = a.get('name', a_id)
                desc = a.get('description', '')
                model = a.get('model', 'gemini')
                tools_cnt = len(a.get('tools', []))
                print(f"  • {a_id}: {name}")
                print(f"    Модель: {model} | Инструментов: {tools_cnt} | Описание: {desc}")
                print()

        print('=== ЗАРЕГИСТРИРОВАННЫЕ КЛАССЫ (AGENT_REGISTRY) ===')
        for agent_name, agent_cls in sorted(AGENT_REGISTRY.items()):
            doc = (agent_cls.__doc__ or '').strip().split('\n')[0]
            print(f'  • {agent_name}: {doc}')
        print('==================================================\n')
        return 0

    if sub == 'run':
        name = getattr(args, 'name', '')
        query = getattr(args, 'query', '')
        if not name:
            print('Error: не указано имя агента (--name)')
            return 1

        print(f"[+] Поиск и инициализация агента '{name}'...")
        try:
            agent_instance = load_agent_from_manifest(name)
        except Exception as e:
            # Fallback к поиску по классам AGENT_REGISTRY
            target_cls = None
            for reg_name, cls in AGENT_REGISTRY.items():
                if reg_name.lower() == name.lower() or reg_name.lower().replace('agent', '') == name.lower().replace('agent', ''):
                    target_cls = cls
                    break
            if target_cls:
                agent_instance = target_cls()
            else:
                print(f"[ERROR] Не удалось загрузить агента '{name}': {e}")
                return 1

        print(f"[+] Запуск агента '{type(agent_instance).__name__}' с задачей: '{query}'...")
        try:
            if hasattr(agent_instance, 'search'):
                if asyncio.iscoroutinefunction(agent_instance.search):
                    result = asyncio.run(agent_instance.search(query))
                else:
                    result = agent_instance.search(query)
                print(f"\n[РЕЗУЛЬТАТ]:\n{json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else result}\n")
                return 0
            elif hasattr(agent_instance, 'run'):
                result = agent_instance.run(query)
                print(f"\n[РЕЗУЛЬТАТ]:\n{result}\n")
                return 0
            elif hasattr(agent_instance, 'execute'):
                result = agent_instance.execute(query)
                print(f"\n[РЕЗУЛЬТАТ]:\n{result}\n")
                return 0
            else:
                print(f"[OK] Агент '{type(agent_instance).__name__}' успешно инициализирован.")
                return 0
        except Exception as e:
            print(f"[ERROR] Ошибка выполнения задачи агентом: {e}")
            return 1

    print(f'Error: неизвестная подкоманда agents: {sub}')
    return 1
