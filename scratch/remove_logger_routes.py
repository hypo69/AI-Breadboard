import re
from pathlib import Path

target_file = Path(r"c:\Users\onela\AppData\Local\AI-Breadboard\src\api\router_system.py")
content = target_file.read_text(encoding="utf-8")

# Удаляем эндпоинты /logger/start, /logger/stop, /logger/status
pattern = r"\s*# =+\s*# Посекундный логгер телеметрии \(CSV\)\s*# =+.*?async def get_telemetry_logger_status\(\) -> Dict\[str, Any\]:\s*\"\"\"[^\"]*\"\"\"\s*return telemetry_service\.get_status\(\)\n"

new_content = re.sub(pattern, "\n\n", content, flags=re.DOTALL)

if new_content != content:
    target_file.write_text(new_content, encoding="utf-8")
    print("Успешно удалено!")
else:
    print("Совпадение не найдено, проверяем шаблоны...")
