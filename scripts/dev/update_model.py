import sqlite3
import sys

try:
    conn = sqlite3.connect('C:/ai-breadboard/src/user_manager/users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE user_settings SET model = 'gemini-2.0-flash'")
    conn.commit()
    print(f"Updated {cursor.rowcount} rows in users.db")
    conn.close()
except Exception as e:
    print(e)
    sys.exit(1)
