# -*- coding: utf-8 -*-
from apps.windows.telemetry.storage import TelemetryStorage

def main():
    storage = TelemetryStorage.get_instance()
    with storage._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s1.hardware_name, s1.sensor_name, s1.value, s1.unit, s1.timestamp
            FROM sensor_polls s1
            INNER JOIN (
                SELECT sensor_id, MAX(id) as max_id
                FROM sensor_polls
                WHERE sensor_category = 'Temperatures'
                GROUP BY sensor_id
            ) s2 ON s1.id = s2.max_id
            ORDER BY s1.hardware_name, s1.sensor_name;
        """)
        rows = cursor.fetchall()
        print(f"=== ТЕМПЕРАТУРНЫЕ ДАТЧИКИ ИЗ SQL ({storage.db_path}) ===")
        print(f"{'Оборудование':<25} {'Датчик':<25} {'Значение':<10} {'Ед.':<8} {'Время'}")
        print("-" * 80)
        for r in rows:
            hw = r["hardware_name"] or "System"
            sname = r["sensor_name"] or "Unknown"
            val = r["value"]
            unit = r["unit"] or "°C"
            ts = r["timestamp"]
            print(f"{hw:<25} {sname:<25} {val:<10.1f} {unit:<8} {ts}")

if __name__ == "__main__":
    main()
