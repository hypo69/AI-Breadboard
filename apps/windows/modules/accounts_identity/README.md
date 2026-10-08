# Accounts & Identity Windows (AI Breadboard)

## Описание модуля
Модуль **Accounts & Identity** представляет собой полноценную OS-level подсистему для операционной системы Windows, реализующую архитектуру **Windows Identity Graph**. В отличие от простых CLI-оболочек над `net user`, данный модуль использует фундаментальный принцип: **SID — первичный идентификатор безопасности, а имя (onela, Administrators) — строковое представление**.

## Архитектура: 10 подсистем
1. **01 Identity (Текущий субъект)**: Определение токена, UPN, FQDN, Logon ID, групп, привилегий, Claims и Mandatory Integrity Level.
2. **02 Users (Пользователи)**: Инвентаризация, создание, редактирование, блокировка/включение, атрибуты и ограничения SAM/AD.
3. **03 Groups (Группы)**: Локальные и доменные группы, вложенное членство (nested membership), граф связей и цепочки пути `User -> Administrators`.
4. **04 SID (Разрешение SID)**: Трансляция Name <-> SID, определение Well-Known SIDs (SYSTEM, LOCAL SERVICE, RID 500), выявление осиротевших (orphaned) SID.
5. **05 Authentication (Политики паролей)**: Глубина истории, минимальная/максимальная длительность, пороги блокировки аккаунтов (lockout policy).
6. **06 Rights (LSA права)**: Назначение и аудит прав Local Security Authority (`SeServiceLogonRight`, `SeRemoteInteractiveLogonRight`, `SeDebugPrivilege` и др.).
7. **07 Tokens (Маркеры процессов)**: Инспекция PID, привязка процесса к токену, целостности (Integrity), UAC Elevation и сессии.
8. **08 Sessions (Сессии WTS)**: Консольные и RDP сеансы, состояние, активность, отключение и завершение.
9. **09 Profiles (Профили)**: Каталоги `C:\Users`, сопоставление с веткой реестра `ProfileList`, проверка `NTUSER.DAT` и осиротевших профилей.
10. **10 Audit (Журнал безопасности)**: Корреляция событий безопасности (Event ID 4720, 4722, 4724, 4726, 4732, 4740, 4624, 4625).

## Единый объект Principal
Объединяет все аспекты жизненного цикла субъекта:
```
Principal
├── SID: S-1-5-21-...
├── Name: onela
├── Domain: WORKGROUP
├── Type: User
├── Source: SAM
├── Elevated/Admin: YES (🟢)
├── Account State: Enabled, Password Expires: Never
├── Groups: Users, Administrators [ADMIN]
├── LSA Rights: SeChangeNotifyPrivilege, SeShutdownPrivilege
├── Profile: C:\Users\onela
├── Active Sessions: 1 (Console)
└── Running Processes: 24
```

## Досье безопасности процесса (`explain-pid`)
Связывает процесс с контекстом прав и учетной записи:
```
PID 12345
│
├── Process: python.exe
├── Parent: powershell.exe
│
├── Account
│   ├── DELL-VOSTRO\onela
│   └── SID: S-1-5-21-...
│
├── Groups
│   ├── Users
│   └── Administrators
│
├── Integrity: High
├── Elevated: YES
│
├── Privileges
│   ├── SeChangeNotifyPrivilege
│   ├── SeShutdownPrivilege
│   └── SeDebugPrivilege
│
└── Session
    ├── Console
    └── Session ID: 1
```

## Использование через Python API
```python
from apps.windows.modules.accounts_identity import get_accounts_identity_service

service = get_accounts_identity_service()

# Разрешение субъекта
principal = service.explain("onela")

# Кто является администратором
admins = service.who_is_admin()

# Кто может входить через RDP
rdp_users = service.who_can_rdp()

# Инспекция процесса
pid_info = service.explain_pid(1234)

# Построение Identity Graph
graph = service.get_identity_graph()
```

## REST API
Роутер подключен по префиксу `/api/windows/identity`:
- `GET /api/windows/identity/catalog` — каталог всех ~180 операций
- `GET /api/windows/identity/current` — текущий контекст токена
- `GET /api/windows/identity/users` — список пользователей
- `GET /api/windows/identity/groups` — список групп
- `GET /api/windows/identity/who-is-admin` — перечень администраторов
- `GET /api/windows/identity/explain-pid/{pid}` — исследование PID
- `GET /api/windows/identity/graph` — полный граф связей
