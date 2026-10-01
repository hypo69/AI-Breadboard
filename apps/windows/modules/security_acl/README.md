# 🔐 Windows Security, ACL & Encryption Manager

Модуль управления списками контроля доступа (ACL, `icacls.exe`), шифрованием дисков BitLocker (`manage-bde.exe`), политиками аудита (`auditpol.exe`) и EFS (`cipher.exe`).

---

## 🚀 Возможности
- Инспекция списков контроля доступа ACL для файлов и директорий
- Проверка статуса шифрования BitLocker, типа алгоритма и привязанных протекторов (TPM, PIN, Recovery Password)
- Поддержка SafeOps режима Dry-Run при изменении ACL прав

---

## 📡 REST API Эндпоинты (`/api/security-acl`)
- `GET /api/security-acl/report` — сводный отчет безопасности и шифрования
- `GET /api/security-acl/bitlocker` — статус шифрования дисков
- `GET /api/security-acl/acl?path=C:\path` — чтение прав ACL для объекта
- `POST /api/security-acl/acl/modify` — изменение или симуляция прав ACL

---

## 🖥️ Использование через CLI
```powershell
# Запуск TUI дашборда
py -m apps.windows.modules.security_acl

# Запуск REST сервера
py -m apps.windows.modules.security_acl --mode server --port 8127
```
