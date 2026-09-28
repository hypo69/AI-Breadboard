# -*- coding: utf-8 -*-
"""Команды управления RAG-индексацией (rag)."""
from __future__ import annotations

import argparse
from header import __root__


def register_rag_parser(subparsers: argparse._SubParsersAction) -> None:
    """Регистрация аргументов команды rag."""
    rag_parser = subparsers.add_parser('rag', help='RAG index management')
    rag_subparsers = rag_parser.add_subparsers(dest='subcommand', help='Subcommands')
    rag_rebuild = rag_subparsers.add_parser('rebuild', help='Full rebuild of RAG index')
    rag_rebuild.add_argument('rest', nargs=argparse.REMAINDER, help='Rebuild options')
    rag_subparsers.add_parser('reindex', help='Reindex knowledge base')
    rag_subparsers.add_parser('validate', help='Validate knowledge base files')
    rag_subparsers.add_parser('status', help='Check RAG index status')
    rag_subparsers.add_parser('tc-status', help='Check Test Computer (TC) Q&A RAG status')
    rag_tc_export = rag_subparsers.add_parser('tc-export', help='Export TC Q&A dataset for fine-tuning')
    rag_tc_export.add_argument('rest', nargs=argparse.REMAINDER, help='Format (alpaca, sharegpt, gemini)')


def run_rag_command(args: argparse.Namespace) -> int:
    """Операции над векторным индексом RAG."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])
    if sub == 'rebuild':
        try:
            from src.rag import build_rules_index
            index_path, docs_path = build_rules_index(*extra)
            print(f'RAG index rebuilt successfully: {index_path}, {docs_path}')
            return 0
        except TypeError:
            from src.rag import build_rules_index
            index_path, docs_path = build_rules_index()
            print(f'RAG index rebuilt successfully: {index_path}, {docs_path}')
            return 0
        except Exception as e:
            print(f'Error rebuilding RAG: {e}')
            return 1
    if sub == 'status':
        try:
            idx_file = __root__ / 'tmp' / 'rag' / 'rules.index'
            print(f"Core RAG status: {('Ready' if idx_file.exists() else 'Not built')}")
            return 0
        except Exception as e:
            print(f'Error checking RAG status: {e}')
            return 1
    if sub == 'tc-status':
        try:
            from src.ai.gemini.approved_responses_store import list_responses, get_store_dir
            responses = list_responses()
            store_dir = get_store_dir()
            print(f'TC Approved Responses Directory: {store_dir}')
            print(f'Total Approved TC Q&A items: {len(responses)}')
            return 0
        except Exception as e:
            print(f'Error checking TC RAG status: {e}')
            return 1
    if sub == 'tc-export':
        try:
            from src.ai.gemini.approved_responses_store import export_tuning_dataset
            fmt = 'alpaca'
            if extra and len(extra) > 0:
                fmt = extra[0]
            out_file = __root__ / 'data' / 'tc' / 'datasets' / f'tc_qa_{fmt}.jsonl'
            count = export_tuning_dataset(out_file, fmt=fmt)
            print(f'Exported {count} TC Q&A items to {out_file} (format: {fmt})')
            return 0
        except Exception as e:
            print(f'Error exporting TC dataset: {e}')
            return 1
    print(f'Unknown rag subcommand: {sub}')
    return 1
