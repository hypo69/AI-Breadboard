"""CLI-проверка локального хранилища корпоративных знаний."""

import argparse

from apps.enterprise_knowledge.engine import EnterpriseKnowledgeEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Knowledge Platform")
    parser.add_argument("query", nargs="?", help="Запрос к локальному индексу")
    args = parser.parse_args()
    if args.query:
        print(EnterpriseKnowledgeEngine().query(args.query))
    else:
        print("Enterprise Knowledge Platform готова к ingestion")


if __name__ == "__main__":
    main()