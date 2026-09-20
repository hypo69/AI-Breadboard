import json
import os
from pathlib import Path

skills_dir = Path(".skills")
status_file = skills_dir / "test_status.json"

if not status_file.exists():
    status_data = {"skills": {}}
    for skill in [d.name for d in skills_dir.iterdir() if d.is_dir()]:
        status_data["skills"][skill] = {"status": "pending", "last_run": None}
    
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=4, ensure_ascii=False)
    print(f"Файл статуса тестов создан: {status_file}")
else:
    print("Файл статуса тестов уже существует.")
