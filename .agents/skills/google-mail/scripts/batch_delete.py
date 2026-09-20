# -*- coding: utf-8 -*-
import argparse
import sys
from pathlib import Path

# Добавляем корень проекта в путь
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from gmail_manager import GmailManager

def batch_delete(query: str, account: str = None):
    """Поиск и удаление писем по запросу."""
    manager = GmailManager(account_name=account)
    if not manager.service:
        print("❌ Ошибка инициализации Gmail.")
        return

    print(f"🔍 Поиск писем для удаления: '{query}'...")
    # Получаем только ID, чтобы ускорить процесс
    results = manager.service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    
    if not messages:
        print("✅ Писем для удаления не найдено.")
        return

    print(f"⚠️ Найдено писем: {len(messages)}. Начинаю удаление...")
    
    for msg in messages:
        msg_id = msg['id']
        if manager.delete_message(msg_id):
            print(f"✅ Удалено: {msg_id}")
        else:
            print(f"❌ Ошибка удаления: {msg_id}")
            
    print("🏁 Пакетное удаление завершено.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gmail Batch Delete Script")
    parser.add_argument("--query", "-q", required=True, help="Поисковый запрос для выбора писем")
    parser.add_argument("--account", "-a", default=None, help="Имя аккаунта")
    
    args = parser.parse_args()
    batch_delete(args.query, args.account)
