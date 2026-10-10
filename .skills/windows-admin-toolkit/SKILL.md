---
name: windows-admin-toolkit
description: Windows System Administration toolkit for AD, local users, SSH/WinRM remoting and security management
description_i18n:
  en: Windows System Administration toolkit for AD, local users, SSH/WinRM remoting and security management
  ru: Инструментарий системного администратора Windows: AD, локальные пользователи, SSH/WinRM сессии и безопасность
---

# 🛠️ Навык: Windows Admin Toolkit (SysAdmin & Remoting Engine)

## 🎯 Назначение
Навык `windows-admin-toolkit` обеспечивает полномочия системного администрирования операционной системы Windows через модуль `apps/windows/sdk/modules/sysadmin`, подсистемы `accounts_identity`, `security_acl` и удалённые протоколы (OpenSSH / WinRM / PowerShell Remoting).

---

## 🏗️ Архитектура подсистем администрирования (`apps/windows/sdk`)

- **`sysadmin`** (`apps/windows/sdk/modules/sysadmin`):
  - `user_collector.py`: Аудит активных сессий, учетных записей и привилегий.
  - `directory_watcher.py`: Мониторинг изменений критических каталогов в реальном времени.
  - `file_auditor.py`: Аудит прав доступа, целостности и изменений файлов.
  - `watcher_telemetry.py`: Телеметрия файловой активности и попыток несанкционированного доступа.
- **`accounts_identity`** (`apps/windows/sdk/modules/accounts_identity`):
  - Управление локальными пользователями (`LocalUser`), группами (`LocalGroup`), статус блокировки/паролей.
  - Разрешение SID ↔ Имя пользователя, проверка членства в `Administrators`.
  - Active Directory (AD) операции: опрос контроллеров домена, аудит учетных записей домена.
- **`security_acl`** (`apps/windows/sdk/modules/security_acl`):
  - Дескрипторы безопасности SDDL, списки управления доступом DACL / SACL.
  - Автоматизация `icacls`, аудит наследования прав и владения объектами.
- **SSH & WinRM Remoting**:
  - Настройка `sshd` демона и авторизованных ключей `authorized_keys`.
  - Запуск удаленных команд через SSH (`ssh`, `scp`, `sftp`) и WinRM (`Invoke-Command`, `Enter-PSSession`).

---

## ⚡ Полномочия и сценарии выполнения

1. **Управление пользователями и сессиями**:
   - Создание, модификация, отключение и аудит локальных пользователей.
   - Завершение зависших пользовательских сессий (`logoff`, `quser`, `qwinsta`).
2. **Удаленное администрирование (SSH / WinRM)**:
   - Автоматический подъем OpenSSH Server при необходимости удаленного доступа.
   - Исполнение административных команд на удаленных узлах через SSH или WinRM.
3. **Аудит безопасности и событий**:
   - Аудит событий входа (Logon/Logoff Event ID 4624, 4625, 4672).
   - Выявление попыток подбора паролей и аномальной активности в `Security.evtx`.
4. **Контроль файловых прав (ACL)**:
   - Рекурсивный аудит и назначение прав доступа на папки и общие ресурсы.

---

## 🐍 Примеры использования через SDK

```python
from apps.windows.sdk import windows_sdk

# Аудит пользователей и сессий
sysadmin = windows_sdk.modules.sysadmin if hasattr(windows_sdk.modules, 'sysadmin') else None
users = windows_sdk.core.process_audit.get_active_sessions()

# Включение OpenSSH Server
windows_sdk.features.enable_feature("OpenSSH.Server~~~~0.0.1.0")
windows_sdk.modules.services.start_service("sshd")
```
