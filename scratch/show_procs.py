# -*- coding: utf-8 -*-
from apps.windows.telemetry.storage import TelemetryStorage

def main():
    storage = TelemetryStorage.get_instance()
    procs = storage.get_latest_processes(limit=15)
    print(f"=== СОСТОЯНИЕ ЗАПУЩЕННЫХ ПРОЦЕССОВ ИЗ SQL ({storage.db_path}) ===")
    print(f"{'PID':<8} {'Имя процесса':<25} {'CPU %':<10} {'Память (МБ)':<15} {'Потоки':<8} {'Пользователь'}")
    print("-" * 85)
    for p in procs:
        pid = p.get("pid", 0)
        name = p.get("name", "unknown")
        cpu = p.get("cpu_percent", 0.0)
        mem = p.get("memory_mb", 0.0)
        threads = p.get("num_threads", 0)
        user = p.get("username", "-") or "-"
        print(f"{pid:<8} {name:<25} {cpu:<10.1f} {mem:<15.1f} {threads:<8} {user}")

if __name__ == "__main__":
    main()
