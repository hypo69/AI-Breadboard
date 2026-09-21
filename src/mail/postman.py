# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SKILLS_ROOT = Path("C:/Users/onela/AppData/Local/AI-Breadboard/.skills")
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))

# Директория называется google-mail (с дефисом), 
# поэтому импорт должен быть динамическим или через структуру, учитывающую дефис.
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gmail_manager", 
    _SKILLS_ROOT / "google-mail" / "scripts" / "gmail_manager.py"
)
gmail_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gmail_mod)
GmailManager = gmail_mod.GmailManager

class Postman:
    """Универсальный почтовый диспетчер."""

    def __init__(self, config_path: str = "src/secrets/mailboxes.json") -> None:
        self.config_path = Path(config_path)
        self.mailboxes = self._load_mailboxes()

    def _load_mailboxes(self) -> Dict[str, Any]:
        """Загрузка конфигурации ящиков."""
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_mailbox_by_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        """Поиск ящика по алиасу."""
        for name, cfg in self.mailboxes.items():
            if alias in cfg.get("aliases", []):
                return cfg
        return None

    def search_messages(self, alias: str, query: str = "is:unread", limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск сообщений через выбранный ящик."""
        mailbox = self.get_mailbox_by_alias(alias)
        if not mailbox:
            print(f"❌ Ящик с алиасом '{alias}' не найден.")
            return []
        
        if "gmail" in mailbox.get("imap_host", "").lower():
            # Делегирование в GmailManager
            manager = GmailManager(account_name=mailbox.get("username"))
            return manager.search_messages(query=query, max_results=limit)
        
        print(f"⚠️ Поиск для типа ящика {mailbox.get('imap_host')} пока не реализован.")
        return []

    def send_email(self, alias: str, to: str, subject: str, body: str) -> bool:
        """Отправка письма через выбранный ящик."""
        mailbox = self.get_mailbox_by_alias(alias)
        if not mailbox:
            print(f"❌ Ящик с алиасом '{alias}' не найден.")
            return False
        
        # Логика делегирования будет добавлена позже
        print(f"🚀 Отправка письма через {mailbox.get('username')}...")
        return True

if __name__ == "__main__":
    postman = Postman()
    print("Postman инициализирован.")
