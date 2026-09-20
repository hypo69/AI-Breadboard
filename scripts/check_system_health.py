import requests
import json
import datetime
from pathlib import Path

# URL сервера из контекста
SERVER_URL = "https://localhost:8000"

def check_health():
    print(f"Проверка состояния системы на {SERVER_URL}...")
    try:
        # Пытаемся получить доступ к корню или специфическому эндпоинту состояния
        # Используем verify=False, так как это локальный сервер с самоподписанным сертификатом
        response = requests.get(f"{SERVER_URL}/", verify=False, timeout=5)
        
        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "server_url": SERVER_URL,
            "status_code": response.status_code,
            "healthy": response.status_code == 200
        }
        
        print(f"Результат: статус {response.status_code}, здорова: {status['healthy']}")
        return status
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения к серверу: {e}")
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "server_url": SERVER_URL,
            "error": str(e),
            "healthy": False
        }

if __name__ == "__main__":
    report = check_health()
    
    # Сохраняем отчет
    report_file = Path("logs/health_report.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    print(f"Отчет сохранен в {report_file}")
