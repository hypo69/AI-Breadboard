# Каталог системных операций Accounts & Identity Windows

## Общие сведения
Каталог содержит полный реестр из ~180 операций операционной системы Windows по управлению субъектами безопасности (Principals), учетными записями, группами, правами LSA, токенами доступа, сессиями и профилями.

### Категории риска (Risk Levels)
- 🟢 **SAFE**: Чтение данных, диагностика, аудит без изменения состояния.
- 🟡 **ADMIN**: Административные изменения (требуют прав администратора / UAC elevation).
- 🔴 **DANGEROUS**: Высокорисковые операции (удаление учетных записей/групп, сброс паролей, отключение доступа).
- ⚫ **ADVANCED**: Низкоуровневые API ядра, извлечение системных маркеров (требуют `LocalSystem` / `SE_TCB_NAME`).

---

## 1. Identity / Текущий пользователь (12 операций)
| № | Операция | Windows Механизм | Win32 API / CLI | Уровень риска |
|---|---|---|---|---|
| 1 | Получить текущего пользователя | GetUserNameEx / whoami | `GetUserNameExW` / `whoami` | 🟢 SAFE |
| 2 | Получить DOMAIN\User | GetUserNameEx | `GetUserNameExW(NameSamCompatible)` | 🟢 SAFE |
| 3 | Получить UPN | GetUserNameEx / whoami | `whoami /upn` | 🟢 SAFE |
| 4 | Получить FQDN identity | GetUserNameEx / whoami | `whoami /fqdn` | 🟢 SAFE |
| 5 | Получить SID текущего пользователя | Access Token / whoami | `GetTokenInformation(TokenUser)` | 🟢 SAFE |
| 6 | Получить Logon ID | Token / WTS | `whoami /logonid` | 🟢 SAFE |
| 7 | Получить группы текущего пользователя | Token | `whoami /groups` | 🟢 SAFE |
| 8 | Получить privileges | Token | `whoami /priv` | 🟢 SAFE |
| 9 | Получить claims | Token | `whoami /claims` | 🟢 SAFE |
| 10 | Получить полный access token | GetTokenInformation | `whoami /all` | 🟢 SAFE |
| 11 | Проверить членство в группе | CheckTokenMembership | `CheckTokenMembership` | 🟢 SAFE |
| 12 | Определить integrity level | Token Mandatory Label | `GetTokenInformation(TokenIntegrityLevel)` | 🟢 SAFE |

---

## 2. Local Users / Учетные записи (20 операций)
| № | Операция | Windows Механизм | Win32 API / PowerShell | Уровень риска |
|---|---|---|---|---|
| 13 | Список пользователей | NetUserEnum | `Get-LocalUser` / `NetUserEnum` | 🟢 SAFE |
| 14 | Получить пользователя | NetUserGetInfo | `NetUserGetInfo(USER_INFO_3)` | 🟢 SAFE |
| 15 | Получить пользователя через LocalAccounts | LocalAccounts | `Get-LocalUser` | 🟢 SAFE |
| 16 | Получить SID пользователя | LookupAccountName | `LookupAccountNameW` | 🟢 SAFE |
| 17 | Получить имя по SID | LookupAccountSid | `LookupAccountSidW` | 🟢 SAFE |
| 18 | Создать пользователя | NetUserAdd / New-LocalUser | `New-LocalUser` | 🟡 ADMIN |
| 19 | Удалить пользователя | NetUserDel / Remove-LocalUser | `Remove-LocalUser` | 🔴 DANGEROUS |
| 20 | Изменить пользователя | NetUserSetInfo | `Set-LocalUser` | 🟡 ADMIN |
| 21 | Переименовать пользователя | Rename-LocalUser | `Rename-LocalUser` | 🟡 ADMIN |
| 22 | Включить пользователя | Enable-LocalUser | `Enable-LocalUser` | 🟡 ADMIN |
| 23 | Отключить пользователя | Disable-LocalUser | `Disable-LocalUser` | 🔴 DANGEROUS |
| 24 | Изменить Full Name | NetUserSetInfo | `Set-LocalUser -FullName` | 🟡 ADMIN |
| 25 | Изменить Description | NetUserSetInfo | `Set-LocalUser -Description` | 🟡 ADMIN |
| 26 | Изменить account expiration | NetUserSetInfo | `Set-LocalUser -AccountExpires` | 🟡 ADMIN |
| 27 | Получить account expiration | NetUserGetInfo | `(Get-LocalUser).AccountExpires` | 🟢 SAFE |
| 28 | Запретить изменение пароля | NetUserSetInfo | `Set-LocalUser -UserMayChangePassword $false` | 🟡 ADMIN |
| 29 | Password never expires | NetUserSetInfo | `Set-LocalUser -PasswordNeverExpires $true` | 🟡 ADMIN |
| 30 | Password required | NetUserSetInfo | `net user` | 🟡 ADMIN |
| 31 | Получить last logon | NetUserGetInfo | `USER_INFO_2` | 🟢 SAFE |
| 32 | Получить logon restrictions | NetUserGetInfo | `USER_INFO_2` | 🟢 SAFE |

---

## 3. Password / Authentication (14 операций)
| № | Операция | Windows Механизм | Win32 API / CLI | Уровень риска |
|---|---|---|---|---|
| 33 | Проверить password required | LocalAccounts / NetAPI | `Get-LocalUser` | 🟢 SAFE |
| 34 | Проверить password expired | NetAPI | `USER_INFO_3` | 🟢 SAFE |
| 35 | Проверить password never expires | NetAPI | `Get-LocalUser` | 🟢 SAFE |
| 36 | Проверить user may change password | NetAPI | `Get-LocalUser` | 🟢 SAFE |
| 37 | Получить password age | NetAPI | `USER_INFO_3` | 🟢 SAFE |
| 38 | Получить password minimum age | NetUserModalsGet | `net accounts` | 🟢 SAFE |
| 39 | Получить maximum password age | NetUserModalsGet | `net accounts` | 🟢 SAFE |
| 40 | Получить minimum password length | NetUserModalsGet | `net accounts` | 🟢 SAFE |
| 41 | Получить password history length | NetUserModalsGet | `net accounts` | 🟢 SAFE |
| 42 | Изменить собственный пароль | NetUserChangePassword | `NetUserChangePassword` | 🟡 ADMIN |
| 43 | Сбросить пароль администратора | NetUserSetInfo | `Set-LocalUser -Password` | 🔴 DANGEROUS |
| 44 | Получить password policy | NetUserModalsGet | `NetUserModalsGet` | 🟢 SAFE |
| 45 | Изменить password policy | NetUserModalsSet | `NetUserModalsSet` | 🔴 DANGEROUS |
| 46 | Проверить account lockout policy | NetUserModalsGet | `USER_MODALS_INFO_3` | 🟢 SAFE |

---

## 4. Logon Restrictions (8 операций)
| № | Операция | Windows Механизм | Win32 API / CLI | Уровень риска |
|---|---|---|---|---|
| 47 | Получить разрешённые часы входа | NetAPI | `USER_INFO_2 (logon_hours)` | 🟢 SAFE |
| 48 | Установить часы входа | NetUserSetInfo | `net user /times` | 🟡 ADMIN |
| 49 | Получить разрешённые workstation | NetAPI | `USER_INFO_2 (workstations)` | 🟢 SAFE |
| 50 | Установить workstation restrictions | NetAPI | `net user /workstations` | 🟡 ADMIN |
| 51 | Получить account expiration | NetAPI | `Get-LocalUser` | 🟢 SAFE |
| 52 | Установить expiration | NetAPI | `net user /expires` | 🟡 ADMIN |
| 53 | Проверить account locked | NetAPI / Events | `UF_LOCKOUT` | 🟢 SAFE |
| 54 | Проверить account disabled | NetAPI | `UF_ACCOUNTDISABLE` | 🟢 SAFE |

---

## 5. Local Groups & Граф членства (18 операций)
| № | Операция | Windows Механизм | Win32 API / PowerShell | Уровень риска |
|---|---|---|---|---|
| 55 | Список локальных групп | NetLocalGroupEnum | `Get-LocalGroup` | 🟢 SAFE |
| 56 | Получить группу | NetLocalGroupGetInfo | `Get-LocalGroup -Name` | 🟢 SAFE |
| 57 | Получить SID группы | LookupAccountName | `LookupAccountNameW` | 🟢 SAFE |
| 58 | Получить членов группы | NetLocalGroupGetMembers | `Get-LocalGroupMember` | 🟢 SAFE |
| 59 | Создать группу | NetLocalGroupAdd | `New-LocalGroup` | 🟡 ADMIN |
| 60 | Изменить группу | NetLocalGroupSetInfo | `Set-LocalGroup` | 🟡 ADMIN |
| 61 | Переименовать группу | Rename-LocalGroup | `Rename-LocalGroup` | 🟡 ADMIN |
| 62 | Удалить группу | NetLocalGroupDel | `Remove-LocalGroup` | 🔴 DANGEROUS |
| 63 | Добавить пользователя | NetLocalGroupAddMembers | `Add-LocalGroupMember` | 🟡 ADMIN |
| 64 | Удалить пользователя | NetLocalGroupDelMembers | `Remove-LocalGroupMember` | 🔴 DANGEROUS |
| 65 | Проверить membership | Get-LocalGroupMember | `Get-LocalGroupMember` | 🟢 SAFE |
| 66 | Получить группы пользователя | NetUserGetLocalGroups | `net user` | 🟢 SAFE |
| 67 | Получить global groups пользователя | NetUserGetGroups | `net user` | 🟢 SAFE |
| 68 | Добавить global group | NetAPI | `NetGroupAdd` | 🟡 ADMIN |
| 69 | Удалить global group | NetAPI | `NetGroupDel` | 🔴 DANGEROUS |
| 70 | Enumerate nested membership | NetAPI / AD | Рекурсивный обход | 🟢 SAFE |
| 71 | Построить group graph | Собственный анализ | `IdentityGraphEngine` | 🟢 SAFE |
| 72 | Найти путь User → Administrators | Собственный анализ | Поиск пути в графе | 🟢 SAFE |

---

## 6. Built-in & Well-Known Accounts (10 операций)
| № | Операция | Назначение | Уровень риска |
|---|---|---|---|
| 73 | Определить built-in account | Проверка RID 500/501/503/504 | 🟢 SAFE |
| 74 | Определить Well-Known SID | Проверка по базе известных SID | 🟢 SAFE |
| 75 | Проверить Administrator | Диагностика встроенного администратора (RID 500) | 🟢 SAFE |
| 76 | Проверить Guest | Диагностика гостевой учетной записи (RID 501) | 🟢 SAFE |
| 77 | Проверить DefaultAccount | Проверка системного аккаунта (RID 503) | 🟢 SAFE |
| 78 | Проверить WDAGUtilityAccount | Проверка Application Guard (RID 504) | 🟢 SAFE |
| 79 | Проверить SYSTEM | Проверка псевдо-аккаунта S-1-5-18 | 🟢 SAFE |
| 80 | Проверить LOCAL SERVICE | Проверка системного контекста S-1-5-19 | 🟢 SAFE |
| 81 | Проверить NETWORK SERVICE | Проверка сетевого контекста S-1-5-20 | 🟢 SAFE |
| 82 | Проверить наличие неизвестных principals | Аудит аномальных и скрытых субъектов | 🟢 SAFE |

---

## 7. SID / Principal Resolution (14 операций)
| № | Операция | API / Механизм | Уровень риска |
|---|---|---|---|
| 83 | Name → SID | `LookupAccountNameW` | 🟢 SAFE |
| 84 | SID → Name | `LookupAccountSidW` | 🟢 SAFE |
| 85 | SID → domain | `LookupAccountSidW` | 🟢 SAFE |
| 86 | SID → account type | `SID_NAME_USE` | 🟢 SAFE |
| 87 | Проверить валидность SID | `IsValidSid` | 🟢 SAFE |
| 88 | Создать SID | `AllocateAndInitializeSid` | 🟢 SAFE |
| 89 | Сравнить SID | `EqualSid` | 🟢 SAFE |
| 90 | Получить SID string | `ConvertSidToStringSidW` | 🟢 SAFE |
| 91 | SID string → SID | `ConvertStringSidToSidW` | 🟢 SAFE |
| 92 | Определить Well-Known SID | `CreateWellKnownSid` | 🟢 SAFE |
| 93 | Определить orphaned SID | `LookupAccountSidW` (ошибка разрешения) | 🟢 SAFE |
| 94 | Найти ACL references | Сканирование Security Descriptors файловой системы | 🟢 SAFE |
| 95 | Найти Registry references | Поиск в `ProfileList` и ACL веток реестра | 🟢 SAFE |
| 96 | Найти Service references | Поиск в `Win32_Service` / SCM | 🟢 SAFE |

---

## 8. User Rights / LSA (15 операций)
| № | Операция | Win32 API / Утилита | Уровень риска |
|---|---|---|---|
| 97 | Список rights пользователя | `LsaEnumerateAccountRights` | 🟢 SAFE |
| 98 | Добавить right | `LsaAddAccountRights` | 🔴 DANGEROUS |
| 99 | Удалить right | `LsaRemoveAccountRights` | 🔴 DANGEROUS |
| 100 | Найти accounts с right | `LsaEnumerateAccountsWithUserRight` | 🟢 SAFE |
| 101 | Открыть LSA Policy | `LsaOpenPolicy` | 🟢 SAFE |
| 102 | Получить policy information | `LsaQueryInformationPolicy` | 🟢 SAFE |
| 103 | Определить SeServiceLogonRight | Аудит права входа как служба | 🟢 SAFE |
| 104 | Определить SeRemoteInteractiveLogonRight | Аудит права удаленного входа по RDP | 🟢 SAFE |
| 105 | Определить SeBackupPrivilege | Аудит права создания бэкапа в обход ACL | 🟢 SAFE |
| 106 | Определить SeRestorePrivilege | Аудит права восстановления файлов | 🟢 SAFE |
| 107 | Определить SeDebugPrivilege | Аудит привилегии отладки процессов | 🟢 SAFE |
| 108 | Определить SeTakeOwnershipPrivilege | Аудит права овладения объектами | 🟢 SAFE |
| 109 | Определить SeImpersonatePrivilege | Аудит права олицетворения клиентов | 🟢 SAFE |
| 110 | Построить effective-rights report | Сводный отчет прав с учетом групп | 🟢 SAFE |
| 111 | Найти accounts с опасными rights | Выявление рискованных конфигураций | 🟢 SAFE |

---

## 9. Access Tokens / Досье PID (15 операций)
| № | Операция | Win32 API / Механизм | Уровень риска |
|---|---|---|---|
| 112 | Open process token | `OpenProcessToken` | 🟢 SAFE |
| 113 | Получить User SID | `GetTokenInformation(TokenUser)` | 🟢 SAFE |
| 114 | Получить group SIDs | `GetTokenInformation(TokenGroups)` | 🟢 SAFE |
| 115 | Получить privileges | `GetTokenInformation(TokenPrivileges)` | 🟢 SAFE |
| 116 | Получить token type | `GetTokenInformation(TokenType)` | 🟢 SAFE |
| 117 | Получить impersonation level | `TokenImpersonationLevel` | 🟢 SAFE |
| 118 | Получить integrity level | `TokenIntegrityLevel` | 🟢 SAFE |
| 119 | Получить elevation | `TokenElevation` (UAC Elevated YES/NO) | 🟢 SAFE |
| 120 | Получить linked elevated token | `TokenLinkedToken` | 🟢 SAFE |
| 121 | Получить session ID | `TokenSessionId` | 🟢 SAFE |
| 122 | Получить logon SID | `TokenLogonSid` | 🟢 SAFE |
| 123 | Получить token groups | `TokenGroupsAndPrivileges` | 🟢 SAFE |
| 124 | Проверить privilege | `PrivilegeCheck` | 🟢 SAFE |
| 125 | Проверить membership | `CheckTokenMembership` | 🟢 SAFE |
| 126 | Сопоставить process → account | `explain_pid` (полная цепочка контекста) | 🟢 SAFE |

---

## 10. Sessions & Logon (15 операций)
| № | Операция | API / Механизм | Уровень риска |
|---|---|---|---|
| 127 | Список sessions | `WTSEnumerateSessionsW` | 🟢 SAFE |
| 128 | Получить session ID | `ProcessIdToSessionId` | 🟢 SAFE |
| 129 | Session username | `WTSQuerySessionInformationW(WTSUserName)` | 🟢 SAFE |
| 130 | Session domain | `WTSQuerySessionInformationW(WTSDomainName)` | 🟢 SAFE |
| 131 | Session state | `WTSQuerySessionInformationW(WTSConnectState)` | 🟢 SAFE |
| 132 | Client name | `WTSClientName` | 🟢 SAFE |
| 133 | Client address | `WTSClientAddress` | 🟢 SAFE |
| 134 | Logon time | `WTSLogonTime` | 🟢 SAFE |
| 135 | Idle time | `WTSIdleTime` | 🟢 SAFE |
| 136 | Session type | `WTSWinStationName` | 🟢 SAFE |
| 137 | Console session | `WTSGetActiveConsoleSessionId` | 🟢 SAFE |
| 138 | RDP session | Анализ протокола сессии | 🟢 SAFE |
| 139 | Disconnect session | `WTSDisconnectSession` | 🔴 DANGEROUS |
| 140 | Logoff session | `WTSLogoffSession` | 🔴 DANGEROUS |
| 141 | Получить user token session | `WTSQueryUserToken` | ⚫ ADVANCED |

---

## 11. User Profiles (13 операций)
| № | Операция | API / Механизм | Уровень риска |
|---|---|---|---|
| 142 | Получить Profiles root | `GetProfilesDirectoryW` (`C:\Users`) | 🟢 SAFE |
| 143 | Получить Default profile | `GetDefaultUserProfileDirectoryW` | 🟢 SAFE |
| 144 | Получить All Users profile | `GetAllUsersProfileDirectoryW` (`ProgramData`) | 🟢 SAFE |
| 145 | Получить user profile path | Реестр `ProfileImagePath` | 🟢 SAFE |
| 146 | Определить profile type | `GetProfileType` | 🟢 SAFE |
| 147 | Создать profile | `CreateProfileW` | 🟡 ADMIN |
| 148 | Загрузить profile | `LoadUserProfileW` / `Reg Load` | 🟡 ADMIN |
| 149 | Выгрузить profile | `UnloadUserProfileW` / `Reg Unload` | 🟡 ADMIN |
| 150 | Удалить profile | `DeleteProfileW` | 🔴 DANGEROUS |
| 151 | Найти profile registry hive | Проверка файла `NTUSER.DAT` | 🟢 SAFE |
| 152 | Проверить profile state | Реестр `State` flags | 🟢 SAFE |
| 153 | Найти orphaned profiles | Сопоставление папок и живых SID | 🟢 SAFE |
| 154 | Найти account без profile | Сопоставление пользователей и `ProfileList` | 🟢 SAFE |

---

## 12. Domain & Entra ID Identity (12 операций)
| № | Операция | Механизм / API | Уровень риска |
|---|---|---|---|
| 155 | Определить domain join | `DsRoleGetPrimaryDomainInformation` | 🟢 SAFE |
| 156 | Получить domain name | `DsRole` | 🟢 SAFE |
| 157 | Получить DNS domain | `DsRole` / IPGlobalProperties | 🟢 SAFE |
| 158 | Получить forest | `DsRole` | 🟢 SAFE |
| 159 | Получить domain GUID | `DsRole` | 🟢 SAFE |
| 160 | Определить machine role | `DsRole(MachineRole)` | 🟢 SAFE |
| 161 | Определить Workgroup | `Win32_ComputerSystem.Workgroup` | 🟢 SAFE |
| 162 | Domain user → SID | `LookupAccountNameW` | 🟢 SAFE |
| 163 | SID → domain user | `LookupAccountSidW` | 🟢 SAFE |
| 164 | UPN → identity | `TranslateNameW` | 🟢 SAFE |
| 165 | Проверить Entra/AAD join state | `dsregcmd /status` | 🟢 SAFE |
| 166 | Получить computer identity | `GetComputerObjectNameW` | 🟢 SAFE |

---

## 13. Windows Audit Security Events (15 операций)
| № | Событие | Event ID | Описание |
|---|---|---|---|
| 167 | User created | 4720 | Создана учетная запись пользователя |
| 168 | User enabled | 4722 | Учетная запись пользователя включена |
| 169 | Password change attempt | 4723 | Попытка самостоятельной смены пароля |
| 170 | Password reset | 4724 | Принудительный сброс пароля администратором |
| 171 | User disabled | 4725 | Учетная запись пользователя отключена |
| 172 | User deleted | 4726 | Учетная запись пользователя удалена |
| 173 | Local group created | 4731 | Создана локальная группа безопасности |
| 174 | Member added to local group | 4732 | Пользователь добавлен в локальную группу |
| 175 | Member removed from local group | 4733 | Пользователь исключен из локальной группы |
| 176 | Local group deleted | 4734 | Локальная группа безопасности удалена |
| 177 | Local group changed | 4735 | Изменены параметры локальной группы |
| 178 | User changed | 4738 | Изменены атрибуты пользователя |
| 179 | Account locked | 4740 | Учетная запись заблокирована из-за неверных паролей |
| 180 | Successful logon | 4624 | Успешный вход в систему |
| 181 | Failed logon | 4625 | Неудачная попытка входа в систему |
