# 🚀 Запуск сервисов и PowerShell Launchers

**Статус:** ✅ Reference  
**Версия:** 1.0  
**Платформа:** Windows PowerShell  
**Последнее обновление:** сентябрь 2026

---

## 1. Встроенные Launchers

### Местоположение

Все launcher скрипты находятся в `launchers/` директории.

### Основные Launchers

| Launcher | Назначение |
|----------|-----------|
| `Run-Server.ps1` | Запуск FastAPI сервера |
| `Run-Tests.ps1` | Запуск тестов |
| `Run-Dev.ps1` | Запуск в режиме разработки (с hot reload) |
| `Run-Worker.ps1` | Запуск фоновых рабочих процессов |

### Запуск Launcher'а

```powershell
# Запустить сервер
.\launchers\Run-Server.ps1

# Запустить тесты
.\launchers\Run-Tests.ps1

# Запустить dev режим
.\launchers\Run-Dev.ps1
```

---

## 2. Запуск с параметрами

```powershell
# Запуск на конкретном порту
.\launchers\Run-Server.ps1 -Port 8001

# Запуск с конкретной конфигурацией
.\launchers\Run-Server.ps1 -Config production

# Запуск с логированием
.\launchers\Run-Server.ps1 -LogLevel DEBUG
```

---

## 3. Создание нового Launcher'а

### Шаблон Launcher'а

```powershell
# launchers/Run-MyService.ps1

<#
.SYNOPSIS
    Start MyService
.DESCRIPTION
    Start MyService with configuration and error handling
.PARAMETER Port
    Server port (default: 8000)
#>

param(
    [int]$Port = 8000
)

# Check if virtual environment exists
if (-not (Test-Path venv)) {
    Write-Error "Virtual environment not found. Run: python -m venv venv"
    exit 1
}

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start service
Write-Host "Starting MyService on port $Port..."
python -m apps.my_service --port $Port

# Cleanup on exit
deactivate
```

### Использование Launcher'а

```powershell
# Запустить новый launcher
.\launchers\Run-MyService.ps1 -Port 8001
```

---

## 4. Управление несколькими сервисами

### Запуск нескольких сервисов

```powershell
# Запуск сервера в отдельном процессе
Start-Process powershell -ArgumentList "-NoExit", ".\launchers\Run-Server.ps1"

# Запуск worker'а в отдельном процессе
Start-Process powershell -ArgumentList "-NoExit", ".\launchers\Run-Worker.ps1"
```

### Остановка сервисов

```powershell
# Остановить все Python процессы
Stop-Process -Name python -Force

# Или более аккуратно
Get-Process python | Where-Object {$_.CommandLine -match "main.py"} | Stop-Process -Confirm
```

---

## 5. Проверка состояния сервисов

```powershell
# Проверить, запущен ли сервер
$response = curl.exe http://localhost:8000/api/version
if ($response) {
    Write-Host "✓ Server is running"
} else {
    Write-Host "✗ Server is not responding"
}
```

---

## 📚 Дополнительно

- [`guides/INSTALLATION.md`](INSTALLATION.md) — Установка проекта
- [`guides/CLI_TOOLS.md`](CLI_TOOLS.md) — Использование CLI инструментов

**Последнее обновление:** сентябрь 2026
