"""CLI точка входа для запуска поиска по истории файлов Windows через RAG."""
import argparse
import json
import sys
import time
from apps.windows.file_history_ai_search.collector import WindowsFileHistoryCollector
from apps.windows.file_history_ai_search.rag_service import FileHistoryRAGService
from apps.windows.file_history_ai_search.scheduler import FileHistoryScheduler


def main() -> None:
    """Точка входа CLI модуля file_history_ai_search."""
    parser = argparse.ArgumentParser(
        description="File History AI Search — Поиск и RAG-индексация истории файлов Windows OS"
    )
    subparsers = parser.add_subparsers(dest="command", help="Команды модуля")

    # Команда scan
    subparsers.add_parser("scan", help="Сканирование доступных источников истории файлов Windows")

    # Команда index
    subparsers.add_parser("index", help="Сбор истории и построение/обновление RAG-индекса")

    # Команда search
    search_parser = subparsers.add_parser("search", help="Быстрый семантический поиск по истории файлов")
    search_parser.add_argument("query", type=str, help="Текст поискового запроса")
    search_parser.add_argument("--top-k", type=int, default=5, help="Количество результатов (default: 5)")
    search_parser.add_argument("--source", type=str, default=None, help="Фильтр по источнику")

    # Команда status
    subparsers.add_parser("status", help="Получение состояния RAG-индекса")

    # Команда daemon
    daemon_parser = subparsers.add_parser("daemon", help="Запуск фонового планировщика обновления RAG")
    daemon_parser.add_argument("--interval", type=int, default=15, help="Интервал автообновления в минутах")

    args = parser.parse_args()

    collector = WindowsFileHistoryCollector()
    rag_service = FileHistoryRAGService()

    if args.command == "scan":
        items = collector.collect_all()
        print(f"Собрано {len(items)} элементов истории файлов Windows:\n")
        for item in items[:15]:
            print(f"[{item.source_type}] {item.file_name} ({item.timestamp})")
            print(f"  Путь: {item.file_path}")
            if item.content_preview:
                print(f"  Превью: {item.content_preview[:80]}...")
            print("-" * 50)
        if len(items) > 15:
            print(f"... и еще {len(items) - 15} элементов.")

    elif args.command == "index":
        print("Запуск сканирования и векторного индексирования RAG...")
        items = collector.collect_all()
        count = rag_service.index_items(items)
        print(f"Успешно проиндексировано {count} документов истории файлов!")

    elif args.command == "search":
        print(f"Поиск по RAG-индексу: '{args.query}'...")
        res = rag_service.search(query=args.query, top_k=args.top_k, source_type=args.source)
        print(f"\nНайдено совпадений: {res.total_found} (за {res.execution_time_ms} мс):\n")
        for i, item in enumerate(res.results, 1):
            print(f"{i}. {item.file_name} (Релевантность: {item.score})")
            print(f"   Источник: {item.source_type} | Время: {item.timestamp}")
            print(f"   Путь: {item.file_path}")
            print(f"   Отрывок: {item.snippet}")
            print("=" * 60)

    elif args.command == "status":
        status = rag_service.get_status()
        print(json.dumps(status.model_dump(), ensure_ascii=False, indent=2))

    elif args.command == "daemon":
        scheduler = FileHistoryScheduler(collector=collector, rag_service=rag_service, interval_minutes=args.interval)
        print(f"Запуск планировщика обновления RAG каждые {args.interval} минут. Для выхода нажмите Ctrl+C...")
        scheduler.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nОстановка планировщика...")
            scheduler.stop()
            print("Планировщик остановлен.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
