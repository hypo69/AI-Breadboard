# -*- coding: utf-8 -*-
import imaplib
import email
import csv
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup
from email.header import decode_header

# Конфигурация
CONFIG_FILE = Path("src/secrets/mailboxes.json")
PROCESSED_FILE = Path("data/kazarinov/orders/processed_orders.json")
CSV_FILE = Path("data/kazarinov/orders/morlevi_orders.csv")

def get_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["kazarinov"]

def get_processed_ids():
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_processed_ids(ids):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, indent=4)

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    order_num = None
    date = None
    total = None
    
    # Поиск номера заказа и даты
    h1 = soup.find('h1')
    if h1:
        order_num = h1.text.replace('מספר הזמנה:', '').strip()
        
    h3 = soup.find('h3')
    if h3:
        date = h3.text.replace('תאריך הזמנה:', '').strip()
        
    # Поиск суммы (наивная реализация, зависит от структуры HTML)
    # Ищем текст "סה\"כ לפני הנחה" или похожее
    total_tag = soup.find(text=lambda x: x and "סה\"כ" in x)
    if total_tag:
        # Это требует уточнения структуры для поиска конкретной суммы
        # Сейчас для примера берем текст родителя
        total = total_tag.find_next().text.strip()
        
    return {"order_num": order_num, "date": date, "total": total}

def main():
    cfg = get_config()
    processed = get_processed_ids()
    
    m = imaplib.IMAP4_SSL(cfg["imap_host"], cfg["imap_port"])
    m.login(cfg["username"], cfg["password"])
    m.select("INBOX")
    
    typ, data = m.search(None, 'FROM', 'info@morlevi.co.il')
    ids = data[0].split()
    
    new_orders = []
    
    for i in ids:
        msg_id = i.decode()
        if msg_id in processed:
            continue
            
        typ, msg_data = m.fetch(i, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        
        # Фильтр по теме
        subject = ""
        for part, encoding in decode_header(msg.get('Subject', '')):
            if isinstance(part, bytes):
                subject += part.decode(encoding or 'utf-8', 'ignore')
            else:
                subject += part
        
        if 'תודה לך על הזמנתך' not in subject:
            continue
            
        # Парсинг тела
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                body = part.get_payload(decode=True).decode('utf-8', 'ignore')
                order_data = parse_html(body)
                order_data["id"] = msg_id
                new_orders.append(order_data)
                processed.add(msg_id)
                break
    
    # Сохранение в CSV
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, "a", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "order_num", "date", "total"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_orders)
        
    save_processed_ids(processed)
    print(f"Обработано {len(new_orders)} новых заказов.")

if __name__ == "__main__":
    main()
