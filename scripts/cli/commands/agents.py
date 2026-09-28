# -*- coding: utf-8 -*-
"""Команды управления и запуска AI-агентов (agents)."""
from __future__ import annotations

import argparse
import json
from header import __root__
from src.ai.agents import AGENT_REGISTRY


def register_agents_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды agents."""
    agents_parser = subparsers.add_parser('agents', help='Autonomous AI agents management and execution')
    agents_subparsers = agents_parser.add_subparsers(dest='subcommand', help='Subcommands')
    agents_subparsers.add_parser('list', help='List available AI agents')
    agents_run = agents_subparsers.add_parser('run', help='Execute an AI agent')
    agents_run.add_argument('--name', required=True, help='Agent name or class (e.g. travel, system_logs, MediaSearchAgent)')
    agents_run.add_argument('--query', default='', help='Query or task for the agent')


def run_agents_command(args: argparse.Namespace) -> int:
    """Управление и запуск автономных AI-агентов."""
    sub = getattr(args, 'subcommand', None)

    if sub == 'list':
        print('\n--- ДОСТУПНЫЕ АГЕНТЫ (AGENT_REGISTRY) ---')
        for agent_name, agent_cls in sorted(AGENT_REGISTRY.items()):
            doc = (agent_cls.__doc__ or '').strip().split('\n')[0]
            print(f'  • {agent_name}: {doc}')

        agents_dir = __root__ / 'src' / 'ai' / 'agents'
        json_agents = list(agents_dir.glob('*_agent.json'))
        if json_agents:
            print('\n--- МАНИФЕСТЫ АГЕНТОВ (JSON) ---')
            for jf in json_agents:
                try:
                    data = json.loads(jf.read_text(encoding='utf-8'))
                    name = data.get('name', jf.stem)
                    desc = data.get('description', '')
                    print(f'  • {jf.stem}: {name} - {desc}')
                except Exception:
                    print(f'  • {jf.stem}')
        print('-----------------------------------------\n')
        return 0

    if sub == 'run':
        name = getattr(args, 'name', '')
        query = getattr(args, 'query', '')
        if not name:
            print('Error: не указано имя агента (--name)')
            return 1

        target_cls = None
        for reg_name, cls in AGENT_REGISTRY.items():
            if reg_name.lower() == name.lower() or reg_name.lower().replace('agent', '') == name.lower().replace('agent', ''):
                target_cls = cls
                break

        if target_cls:
            print(f"[+] Запуск агента '{target_cls.__name__}' с запросом: '{query}'...")
            try:
                agent_instance = target_cls()
                if hasattr(agent_instance, 'run'):
                    result = agent_instance.run(query)
                    print(f"\n[РЕЗУЛЬТАТ]:\n{result}\n")
                    return 0
                elif hasattr(agent_instance, 'execute'):
                    result = agent_instance.execute(query)
                    print(f"\n[РЕЗУЛЬТАТ]:\n{result}\n")
                    return 0
                else:
                    print(f"[OK] Агент '{target_cls.__name__}' успешно инициализирован.")
                    return 0
            except Exception as e:
                print(f"[ERROR] Ошибка выполнения агента: {e}")
                return 1

        print(f"Error: агент '{name}' не найден в реестре AGENT_REGISTRY")
        return 1

    print(f'Error: неизвестная подкоманда agents: {sub}')
    return 1
