# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Accounts & Identity Catalog
# =============================================================================
# Description:
#   Полный официальный реестр ~180 операций OS-level каталога
#   Accounts & Identity Windows с категоризацией рисков (SAFE/ADMIN/DANGEROUS/ADVANCED).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.accounts_identity.catalog import get_full_catalog
#
#     ops = get_full_catalog()
#
# File: catalog.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.accounts_identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:48:00
# =============================================================================

"""Каталог системных операций Accounts & Identity Windows."""

from __future__ import annotations

from typing import List, Dict, Optional
from apps.windows.sdk.modules.accounts_identity.models import OperationCatalogItem, RiskLevel

_OPERATIONS: List[OperationCatalogItem] = [
    # 1. Identity / текущий пользователь (12)
    OperationCatalogItem(
        id=1, name_ru="Получить текущего пользователя", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="GetUserNameEx / whoami", win32_api="GetUserNameExW", ps_or_cli="whoami",
        description_ru="Возвращает имя текущего авторизованного пользователя."
    ),
    OperationCatalogItem(
        id=2, name_ru="Получить DOMAIN\\User", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="GetUserNameEx / whoami", win32_api="GetUserNameExW(NameSamCompatible)", ps_or_cli="whoami",
        description_ru="Возвращает составной идентификатор Домен\\Пользователь."
    ),
    OperationCatalogItem(
        id=3, name_ru="Получить UPN", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="GetUserNameEx / whoami", win32_api="GetUserNameExW(NameUserPrincipal)", ps_or_cli="whoami /upn",
        description_ru="Возвращает User Principal Name (пользователь@домен)."
    ),
    OperationCatalogItem(
        id=4, name_ru="Получить FQDN identity", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="GetUserNameEx / whoami", win32_api="GetUserNameExW(NameFullyQualifiedDN)", ps_or_cli="whoami /fqdn",
        description_ru="Возвращает полное доменное имя субъекта в Active Directory."
    ),
    OperationCatalogItem(
        id=5, name_ru="Получить SID текущего пользователя", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="Access Token / whoami", win32_api="GetTokenInformation(TokenUser)", ps_or_cli="whoami /user",
        description_ru="Извлекает строковый SID владельца текущего процесса."
    ),
    OperationCatalogItem(
        id=6, name_ru="Получить Logon ID", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="Token / WTS", win32_api="GetTokenInformation(TokenStatistics)", ps_or_cli="whoami /logonid",
        description_ru="Возвращает LUID сеанса входа текущего процесса."
    ),
    OperationCatalogItem(
        id=7, name_ru="Получить группы текущего пользователя", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenGroups)", ps_or_cli="whoami /groups",
        description_ru="Возвращает список SID и имен групп из токена доступа."
    ),
    OperationCatalogItem(
        id=8, name_ru="Получить privileges", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenPrivileges)", ps_or_cli="whoami /priv",
        description_ru="Перечисляет все привилегии процесса (включенные и отключенные)."
    ),
    OperationCatalogItem(
        id=9, name_ru="Получить claims", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenUserClaimAttributes)", ps_or_cli="whoami /claims",
        description_ru="Возвращает утверждения безопасности (Security Claims) токена."
    ),
    OperationCatalogItem(
        id=10, name_ru="Получить полный access token", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="GetTokenInformation", win32_api="GetTokenInformation", ps_or_cli="whoami /all",
        description_ru="Формирует полный слепок параметров маркера доступа."
    ),
    OperationCatalogItem(
        id=11, name_ru="Проверить членство в группе", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="CheckTokenMembership", win32_api="CheckTokenMembership", ps_or_cli="[Security.Principal.WindowsPrincipal]",
        description_ru="Проверяет наличие указанного SID среди эффективных групп токена."
    ),
    OperationCatalogItem(
        id=12, name_ru="Определить integrity level", subsystem_id="01_identity",
        subsystem_name_ru="Текущий пользователь и контекст", risk_level=RiskLevel.SAFE,
        mechanism="Token Integrity", win32_api="GetTokenInformation(TokenIntegrityLevel)", ps_or_cli="whoami /groups (Mandatory Label)",
        description_ru="Определяет уровень целостности MIC (Low/Medium/High/System)."
    ),

    # 2. Local Users (20)
    OperationCatalogItem(
        id=13, name_ru="Список пользователей", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="NetUserEnum", win32_api="NetUserEnum", ps_or_cli="Get-LocalUser",
        description_ru="Возвращает перечень всех локальных учетных записей SAM."
    ),
    OperationCatalogItem(
        id=14, name_ru="Получить пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="NetUserGetInfo", win32_api="NetUserGetInfo(USER_INFO_3)", ps_or_cli="Get-LocalUser -Name ...",
        description_ru="Извлекает полные параметры учетной записи через NetAPI."
    ),
    OperationCatalogItem(
        id=15, name_ru="Получить пользователя через LocalAccounts", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="LocalAccounts", win32_api="NetUserGetInfo", ps_or_cli="Get-LocalUser",
        description_ru="Получение параметров учетной записи через PowerShell модуль."
    ),
    OperationCatalogItem(
        id=16, name_ru="Получить SID пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountName", win32_api="LookupAccountNameW", ps_or_cli="(Get-LocalUser ...).SID",
        description_ru="Транслирует имя учетной записи в строковый SID."
    ),
    OperationCatalogItem(
        id=17, name_ru="Получить имя по SID", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountSid", win32_api="LookupAccountSidW", ps_or_cli="LookupAccountSid",
        description_ru="Транслирует SID в имя учетной записи и домен."
    ),
    OperationCatalogItem(
        id=18, name_ru="Создать пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserAdd / New-LocalUser", win32_api="NetUserAdd", ps_or_cli="New-LocalUser",
        description_ru="Создает новую локальную учетную запись в SAM."
    ),
    OperationCatalogItem(
        id=19, name_ru="Удалить пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.DANGEROUS,
        mechanism="NetUserDel / Remove-LocalUser", win32_api="NetUserDel", ps_or_cli="Remove-LocalUser",
        description_ru="Безвозвратно удаляет локальную учетную запись."
    ),
    OperationCatalogItem(
        id=20, name_ru="Изменить пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo", ps_or_cli="Set-LocalUser",
        description_ru="Обновляет комплексные свойства учетной записи."
    ),
    OperationCatalogItem(
        id=21, name_ru="Переименовать пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="Rename-LocalUser", win32_api="NetUserSetInfo(USER_INFO_0)", ps_or_cli="Rename-LocalUser",
        description_ru="Изменяет имя локальной учетной записи без смены SID."
    ),
    OperationCatalogItem(
        id=22, name_ru="Включить пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="Enable-LocalUser", win32_api="NetUserSetInfo(flags UF_ACCOUNTDISABLE off)", ps_or_cli="Enable-LocalUser",
        description_ru="Снимает флаг блокировки и активирует учетную запись."
    ),
    OperationCatalogItem(
        id=23, name_ru="Отключить пользователя", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.DANGEROUS,
        mechanism="Disable-LocalUser", win32_api="NetUserSetInfo(flags UF_ACCOUNTDISABLE on)", ps_or_cli="Disable-LocalUser",
        description_ru="Блокирует возможность интерактивного входа пользователя."
    ),
    OperationCatalogItem(
        id=24, name_ru="Изменить Full Name", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(USER_INFO_1011)", ps_or_cli="Set-LocalUser -FullName",
        description_ru="Устанавливает отображаемое полное имя пользователя."
    ),
    OperationCatalogItem(
        id=25, name_ru="Изменить Description", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(USER_INFO_1007)", ps_or_cli="Set-LocalUser -Description",
        description_ru="Обновляет комментарий к учетной записи."
    ),
    OperationCatalogItem(
        id=26, name_ru="Изменить account expiration", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(USER_INFO_1017)", ps_or_cli="Set-LocalUser -AccountExpires",
        description_ru="Устанавливает дату и время истечения срока действия аккаунта."
    ),
    OperationCatalogItem(
        id=27, name_ru="Получить account expiration", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="NetUserGetInfo", win32_api="NetUserGetInfo", ps_or_cli="(Get-LocalUser ...).AccountExpires",
        description_ru="Возвращает дату истечения срока действия аккаунта."
    ),
    OperationCatalogItem(
        id=28, name_ru="Запретить изменение пароля", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(UF_PASSWD_CANT_CHANGE)", ps_or_cli="Set-LocalUser -UserMayChangePassword $false",
        description_ru="Запрещает пользователю самостоятельно менять свой пароль."
    ),
    OperationCatalogItem(
        id=29, name_ru="Password never expires", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(UF_DONT_EXPIRE_PASSWD)", ps_or_cli="Set-LocalUser -PasswordNeverExpires $true",
        description_ru="Отключает принудительное периодическое истечение пароля."
    ),
    OperationCatalogItem(
        id=30, name_ru="Password required", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(UF_PASSWD_NOTREQD)", ps_or_cli="net user ...",
        description_ru="Управляет обязательностью наличия пароля для аккаунта."
    ),
    OperationCatalogItem(
        id=31, name_ru="Получить last logon", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="NetUserGetInfo", win32_api="NetUserGetInfo(USER_INFO_2)", ps_or_cli="net user ...",
        description_ru="Возвращает timestamp последнего успешного входа в систему."
    ),
    OperationCatalogItem(
        id=32, name_ru="Получить logon restrictions", subsystem_id="02_users",
        subsystem_name_ru="Локальные и доменные пользователи", risk_level=RiskLevel.SAFE,
        mechanism="NetUserGetInfo", win32_api="NetUserGetInfo(USER_INFO_2)", ps_or_cli="net user ...",
        description_ru="Возвращает ограничения по рабочим станциям и расписанию входа."
    ),

    # 3. Password / Authentication (14)
    OperationCatalogItem(
        id=33, name_ru="Проверить password required", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="LocalAccounts / NetAPI", win32_api="NetUserGetInfo", ps_or_cli="Get-LocalUser",
        description_ru="Проверяет наличие флага обязательности пароля."
    ),
    OperationCatalogItem(
        id=34, name_ru="Проверить password expired", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo(USER_INFO_3)", ps_or_cli="Get-LocalUser",
        description_ru="Проверяет, истек ли срок действия пароля."
    ),
    OperationCatalogItem(
        id=35, name_ru="Проверить password never expires", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo", ps_or_cli="(Get-LocalUser ...).PasswordNeverExpires",
        description_ru="Проверяет наличие бессрочного действия пароля."
    ),
    OperationCatalogItem(
        id=36, name_ru="Проверить user may change password", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo", ps_or_cli="(Get-LocalUser ...).UserMayChangePassword",
        description_ru="Проверяет право пользователя на смену пароля."
    ),
    OperationCatalogItem(
        id=37, name_ru="Получить password age", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo(usri3_password_age)", ps_or_cli="Get-LocalUser",
        description_ru="Возвращает возраст текущего пароля в днях/секундах."
    ),
    OperationCatalogItem(
        id=38, name_ru="Получить password minimum age", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetUserModalsGet", win32_api="NetUserModalsGet(USER_MODALS_INFO_0)", ps_or_cli="net accounts",
        description_ru="Возвращает минимальный срок действия пароля перед сменой."
    ),
    OperationCatalogItem(
        id=39, name_ru="Получить maximum password age", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetUserModalsGet", win32_api="NetUserModalsGet(USER_MODALS_INFO_0)", ps_or_cli="net accounts",
        description_ru="Возвращает максимальный срок действия пароля политики."
    ),
    OperationCatalogItem(
        id=40, name_ru="Получить minimum password length", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetUserModalsGet", win32_api="NetUserModalsGet(USER_MODALS_INFO_0)", ps_or_cli="net accounts",
        description_ru="Возвращает минимально допустимую длину пароля."
    ),
    OperationCatalogItem(
        id=41, name_ru="Получить password history length", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetUserModalsGet", win32_api="NetUserModalsGet(USER_MODALS_INFO_0)", ps_or_cli="net accounts",
        description_ru="Возвращает глубину неповторяемости истории паролей."
    ),
    OperationCatalogItem(
        id=42, name_ru="Изменить собственный пароль", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserChangePassword", win32_api="NetUserChangePassword", ps_or_cli="net user ... *",
        description_ru="Изменяет пароль пользователя с проверкой старого значения."
    ),
    OperationCatalogItem(
        id=43, name_ru="Сбросить пароль администратора", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.DANGEROUS,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(USER_INFO_1003)", ps_or_cli="Set-LocalUser -Password",
        description_ru="Административный принудительный сброс пароля без старого значения."
    ),
    OperationCatalogItem(
        id=44, name_ru="Получить password policy", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetUserModalsGet", win32_api="NetUserModalsGet", ps_or_cli="net accounts",
        description_ru="Считывает сводную политику безопасности паролей системы."
    ),
    OperationCatalogItem(
        id=45, name_ru="Изменить password policy", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.DANGEROUS,
        mechanism="NetUserModalsSet", win32_api="NetUserModalsSet", ps_or_cli="net accounts /...",
        description_ru="Устанавливает параметры глобальной политики паролей."
    ),
    OperationCatalogItem(
        id=46, name_ru="Проверить account lockout policy", subsystem_id="03_auth",
        subsystem_name_ru="Пароли и аутентификация", risk_level=RiskLevel.SAFE,
        mechanism="NetUserModalsGet", win32_api="NetUserModalsGet(USER_MODALS_INFO_3)", ps_or_cli="net accounts",
        description_ru="Считывает порог и длительность блокировки при неверном вводе пароля."
    ),

    # 4. Logon restrictions (8)
    OperationCatalogItem(
        id=47, name_ru="Получить разрешённые часы входа", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo(usri2_logon_hours)", ps_or_cli="net user ...",
        description_ru="Считывает битовую маску разрешенных часов авторизации."
    ),
    OperationCatalogItem(
        id=48, name_ru="Установить часы входа", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.ADMIN,
        mechanism="NetUserSetInfo", win32_api="NetUserSetInfo(USER_INFO_2)", ps_or_cli="net user ... /times:...",
        description_ru="Конфигурирует расписание допустимого входа пользователя."
    ),
    OperationCatalogItem(
        id=49, name_ru="Получить разрешённые workstation", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo(usri2_workstations)", ps_or_cli="net user ...",
        description_ru="Возвращает список имен рабочих станций, с которых разрешен вход."
    ),
    OperationCatalogItem(
        id=50, name_ru="Установить workstation restrictions", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.ADMIN,
        mechanism="NetAPI", win32_api="NetUserSetInfo", ps_or_cli="net user ... /workstations:...",
        description_ru="Ограничивает перечень компьютеров для авторизации."
    ),
    OperationCatalogItem(
        id=51, name_ru="Получить account expiration", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo", ps_or_cli="Get-LocalUser",
        description_ru="Считывает дату истечения учетной записи."
    ),
    OperationCatalogItem(
        id=52, name_ru="Установить expiration", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.ADMIN,
        mechanism="NetAPI", win32_api="NetUserSetInfo", ps_or_cli="net user ... /expires:...",
        description_ru="Назначает дату деактивации аккаунта."
    ),
    OperationCatalogItem(
        id=53, name_ru="Проверить account locked", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI / Security Events", win32_api="NetUserGetInfo(UF_LOCKOUT)", ps_or_cli="net user ...",
        description_ru="Диагностирует состояние блокировки из-за неверных паролей."
    ),
    OperationCatalogItem(
        id=54, name_ru="Проверить account disabled", subsystem_id="04_logon_restrictions",
        subsystem_name_ru="Ограничения входа", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI", win32_api="NetUserGetInfo(UF_ACCOUNTDISABLE)", ps_or_cli="Get-LocalUser",
        description_ru="Проверяет, отключен ли аккаунт администратором."
    ),

    # 5. Local Groups (18)
    OperationCatalogItem(
        id=55, name_ru="Список локальных групп", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="NetLocalGroupEnum", win32_api="NetLocalGroupEnum", ps_or_cli="Get-LocalGroup",
        description_ru="Перечисляет все локальные группы безопасности."
    ),
    OperationCatalogItem(
        id=56, name_ru="Получить группу", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="NetLocalGroupGetInfo", win32_api="NetLocalGroupGetInfo", ps_or_cli="Get-LocalGroup -Name ...",
        description_ru="Возвращает свойства локальной группы."
    ),
    OperationCatalogItem(
        id=57, name_ru="Получить SID группы", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountName", win32_api="LookupAccountNameW", ps_or_cli="(Get-LocalGroup ...).SID",
        description_ru="Определяет строковый SID указанной группы."
    ),
    OperationCatalogItem(
        id=58, name_ru="Получить членов группы", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="NetLocalGroupGetMembers", win32_api="NetLocalGroupGetMembers", ps_or_cli="Get-LocalGroupMember",
        description_ru="Возвращает прямой список пользователей и вложенных групп."
    ),
    OperationCatalogItem(
        id=59, name_ru="Создать группу", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.ADMIN,
        mechanism="NetLocalGroupAdd", win32_api="NetLocalGroupAdd", ps_or_cli="New-LocalGroup",
        description_ru="Создает новую локальную группу безопасности."
    ),
    OperationCatalogItem(
        id=60, name_ru="Изменить группу", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.ADMIN,
        mechanism="NetLocalGroupSetInfo", win32_api="NetLocalGroupSetInfo", ps_or_cli="Set-LocalGroup",
        description_ru="Обновляет описание локальной группы."
    ),
    OperationCatalogItem(
        id=61, name_ru="Переименовать группу", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.ADMIN,
        mechanism="Rename-LocalGroup", win32_api="NetLocalGroupSetInfo", ps_or_cli="Rename-LocalGroup",
        description_ru="Переименовывает локальную группу."
    ),
    OperationCatalogItem(
        id=62, name_ru="Удалить группу", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.DANGEROUS,
        mechanism="NetLocalGroupDel", win32_api="NetLocalGroupDel", ps_or_cli="Remove-LocalGroup",
        description_ru="Удаляет локальную группу безопасности."
    ),
    OperationCatalogItem(
        id=63, name_ru="Добавить пользователя", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.ADMIN,
        mechanism="NetLocalGroupAddMembers", win32_api="NetLocalGroupAddMembers", ps_or_cli="Add-LocalGroupMember",
        description_ru="Включает пользователя или субъект в состав группы."
    ),
    OperationCatalogItem(
        id=64, name_ru="Удалить пользователя", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.DANGEROUS,
        mechanism="NetLocalGroupDelMembers", win32_api="NetLocalGroupDelMembers", ps_or_cli="Remove-LocalGroupMember",
        description_ru="Исключает пользователя из состава группы."
    ),
    OperationCatalogItem(
        id=65, name_ru="Проверить membership", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="Get-LocalGroupMember", win32_api="NetLocalGroupGetMembers", ps_or_cli="Get-LocalGroupMember",
        description_ru="Проверяет, состоит ли субъект в конкретной группе."
    ),
    OperationCatalogItem(
        id=66, name_ru="Получить группы пользователя", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="NetUserGetLocalGroups", win32_api="NetUserGetLocalGroups", ps_or_cli="net user ...",
        description_ru="Возвращает локальные группы, в которых состоит пользователь."
    ),
    OperationCatalogItem(
        id=67, name_ru="Получить global groups пользователя", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="NetUserGetGroups", win32_api="NetUserGetGroups", ps_or_cli="net user ...",
        description_ru="Возвращает глобальные доменные группы пользователя."
    ),
    OperationCatalogItem(
        id=68, name_ru="Добавить global group", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.ADMIN,
        mechanism="NetAPI", win32_api="NetGroupAdd", ps_or_cli="New-ADGroup / net group",
        description_ru="Создает глобальную доменную группу."
    ),
    OperationCatalogItem(
        id=69, name_ru="Удалить global group", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.DANGEROUS,
        mechanism="NetAPI", win32_api="NetGroupDel", ps_or_cli="Remove-ADGroup / net group",
        description_ru="Удаляет глобальную доменную группу."
    ),
    OperationCatalogItem(
        id=70, name_ru="Enumerate nested membership", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="NetAPI / AD", win32_api="Recursive Member Enum", ps_or_cli="Recursive expansion",
        description_ru="Рекурсивно разворачивает дерево всех вложенных групп."
    ),
    OperationCatalogItem(
        id=71, name_ru="Построить group graph", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="Собственный анализ", win32_api="Graph Construction Engine", ps_or_cli="Identity Graph",
        description_ru="Строит ориентированный граф связей пользователей и групп."
    ),
    OperationCatalogItem(
        id=72, name_ru="Найти путь User → Administrators", subsystem_id="05_groups",
        subsystem_name_ru="Группы безопасности и граф членства", risk_level=RiskLevel.SAFE,
        mechanism="Собственный анализ", win32_api="Shortest Path Search", ps_or_cli="Path to Admin",
        description_ru="Ищет цепочку вложенных групп от пользователя к группе Администраторов."
    ),

    # 6. Built-in / well-known accounts (10)
    OperationCatalogItem(
        id=73, name_ru="Определить built-in account", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="RID / Well-Known DB", win32_api="CheckWellKnownSid", ps_or_cli="RID 500/501 check",
        description_ru="Определяет, является ли аккаунт штатным встроенным объектом Windows."
    ),
    OperationCatalogItem(
        id=74, name_ru="Определить Well-Known SID", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="CreateWellKnownSid", win32_api="CreateWellKnownSid", ps_or_cli="Well-known SIDs DB",
        description_ru="Сопоставляет SID со стандартными известными субъектами (NT AUTHORITY, SYSTEM и др.)."
    ),
    OperationCatalogItem(
        id=75, name_ru="Проверить Administrator", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="RID 500 Check", win32_api="LookupAccountName", ps_or_cli="Get-LocalUser -SID '*-500'",
        description_ru="Проверяет состояние встроенного суперадминистратора (RID 500)."
    ),
    OperationCatalogItem(
        id=76, name_ru="Проверить Guest", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="RID 501 Check", win32_api="LookupAccountName", ps_or_cli="Get-LocalUser -SID '*-501'",
        description_ru="Проверяет состояние гостевой учетной записи (RID 501)."
    ),
    OperationCatalogItem(
        id=77, name_ru="Проверить DefaultAccount", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="RID 503 Check", win32_api="LookupAccountName", ps_or_cli="Get-LocalUser -SID '*-503'",
        description_ru="Проверяет встроенную системную учетную запись DefaultAccount."
    ),
    OperationCatalogItem(
        id=78, name_ru="Проверить WDAGUtilityAccount", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="RID 504 Check", win32_api="LookupAccountName", ps_or_cli="Get-LocalUser -SID '*-504'",
        description_ru="Проверяет учетную запись Windows Defender Application Guard."
    ),
    OperationCatalogItem(
        id=79, name_ru="Проверить SYSTEM", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="S-1-5-18", win32_api="LookupAccountSid", ps_or_cli="NT AUTHORITY\\SYSTEM",
        description_ru="Проверяет параметры псевдо-аккаунта локальной системы."
    ),
    OperationCatalogItem(
        id=80, name_ru="Проверить LOCAL SERVICE", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="S-1-5-19", win32_api="LookupAccountSid", ps_or_cli="NT AUTHORITY\\LOCAL SERVICE",
        description_ru="Проверяет системный контекст Local Service с минимальными правами."
    ),
    OperationCatalogItem(
        id=81, name_ru="Проверить NETWORK SERVICE", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="S-1-5-20", win32_api="LookupAccountSid", ps_or_cli="NT AUTHORITY\\NETWORK SERVICE",
        description_ru="Проверяет системный контекст Network Service для сетевых служб."
    ),
    OperationCatalogItem(
        id=82, name_ru="Проверить наличие неизвестных principals", subsystem_id="06_builtin",
        subsystem_name_ru="Встроенные и системные учетные записи", risk_level=RiskLevel.SAFE,
        mechanism="Anomalous Principal Audit", win32_api="Audit Registry & SAM", ps_or_cli="Principal Audit",
        description_ru="Выявляет аномальные или скрытые учетные записи в системе."
    ),

    # 7. SID / Principal Resolution (14)
    OperationCatalogItem(
        id=83, name_ru="Name → SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountName", win32_api="LookupAccountNameW", ps_or_cli="[NTAccount].Translate([SecurityIdentifier])",
        description_ru="Преобразует имя учетной записи в строковый SID."
    ),
    OperationCatalogItem(
        id=84, name_ru="SID → Name", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountSid", win32_api="LookupAccountSidW", ps_or_cli="[SecurityIdentifier].Translate([NTAccount])",
        description_ru="Преобразует SID в имя пользователя или группы."
    ),
    OperationCatalogItem(
        id=85, name_ru="SID → domain", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountSid", win32_api="LookupAccountSidW", ps_or_cli="LookupAccountSid",
        description_ru="Определяет домен или имя хоста, выпустившего данный SID."
    ),
    OperationCatalogItem(
        id=86, name_ru="SID → account type", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="SID_NAME_USE", win32_api="LookupAccountSidW(peUse)", ps_or_cli="SidTypeEnum",
        description_ru="Определяет тип сущности (User, Group, Domain, Alias, WellKnownGroup, Computer)."
    ),
    OperationCatalogItem(
        id=87, name_ru="Проверить валидность SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="IsValidSid", win32_api="IsValidSid", ps_or_cli="[SecurityIdentifier]::new()",
        description_ru="Валидирует структуру и контрольную сумму бинарного SID."
    ),
    OperationCatalogItem(
        id=88, name_ru="Создать SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="AllocateAndInitializeSid", win32_api="AllocateAndInitializeSid", ps_or_cli="New-Object SecurityIdentifier",
        description_ru="Конструирует SID по указанному Authority и субавторитетам."
    ),
    OperationCatalogItem(
        id=89, name_ru="Сравнить SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="EqualSid", win32_api="EqualSid", ps_or_cli="sid1 -eq sid2",
        description_ru="Побайтово сравнивает два дескриптора SID."
    ),
    OperationCatalogItem(
        id=90, name_ru="Получить SID string", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="ConvertSidToStringSid", win32_api="ConvertSidToStringSidW", ps_or_cli="$sid.Value",
        description_ru="Конвертирует бинарный SID в стандартную строку S-1-5-..."
    ),
    OperationCatalogItem(
        id=91, name_ru="SID string → SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="ConvertStringSidToSid", win32_api="ConvertStringSidToSidW", ps_or_cli="[SecurityIdentifier]::new($str)",
        description_ru="Конвертирует строковое представление SID в структуру памяти."
    ),
    OperationCatalogItem(
        id=92, name_ru="Определить Well-Known SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="CreateWellKnownSid", win32_api="CreateWellKnownSid", ps_or_cli="Well-known database",
        description_ru="Определяет тип стандартного SID (Everyone, Authenticated Users и др.)."
    ),
    OperationCatalogItem(
        id=93, name_ru="Определить orphaned SID", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="Resolution Failure", win32_api="LookupAccountSidW fail check", ps_or_cli="Unresolved SID detection",
        description_ru="Выявляет осиротевшие SID удаленных учетных записей."
    ),
    OperationCatalogItem(
        id=94, name_ru="Найти ACL references", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="Security Descriptor", win32_api="GetSecurityInfo / ACL scan", ps_or_cli="Get-Acl scan",
        description_ru="Ищет ссылки на указанный SID в дескрипторах безопасности файловой системы."
    ),
    OperationCatalogItem(
        id=95, name_ru="Найти Registry references", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="ACL Enumeration", win32_api="RegGetKeySecurity", ps_or_cli="Registry ACL scan",
        description_ru="Ищет ссылки на указанный SID в правах доступа к разделам реестра."
    ),
    OperationCatalogItem(
        id=96, name_ru="Найти Service references", subsystem_id="07_sid",
        subsystem_name_ru="Разрешение SID и аудит осиротевших ссылок", risk_level=RiskLevel.SAFE,
        mechanism="SCM / Security Descriptor", win32_api="QueryServiceObjectSecurity", ps_or_cli="Service ACL scan",
        description_ru="Ищет службы, запускаемые от имени указанного аккаунта или защищенные его SID."
    ),

    # 8. User Rights / LSA (15)
    OperationCatalogItem(
        id=97, name_ru="Список rights пользователя", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LsaEnumerateAccountRights", win32_api="LsaEnumerateAccountRights", ps_or_cli="secedit /export / ntrights",
        description_ru="Возвращает список назначенных LSA-прав для указанного SID."
    ),
    OperationCatalogItem(
        id=98, name_ru="Добавить right", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.DANGEROUS,
        mechanism="LsaAddAccountRights", win32_api="LsaAddAccountRights", ps_or_cli="ntrights +r ...",
        description_ru="Назначает LSA-право или привилегию указанному субъекту."
    ),
    OperationCatalogItem(
        id=99, name_ru="Удалить right", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.DANGEROUS,
        mechanism="LsaRemoveAccountRights", win32_api="LsaRemoveAccountRights", ps_or_cli="ntrights -r ...",
        description_ru="Отозвать LSA-право или привилегию у субъекта."
    ),
    OperationCatalogItem(
        id=100, name_ru="Найти accounts с right", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LsaEnumerateAccountsWithUserRight", win32_api="LsaEnumerateAccountsWithUserRight", ps_or_cli="LSA query",
        description_ru="Находит все учетные записи и группы, обладающие указанным правом."
    ),
    OperationCatalogItem(
        id=101, name_ru="Открыть LSA Policy", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LsaOpenPolicy", win32_api="LsaOpenPolicy", ps_or_cli="LsaOpenPolicy Handle",
        description_ru="Открывает дескриптор локальной политики безопасности LSA."
    ),
    OperationCatalogItem(
        id=102, name_ru="Получить policy information", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LsaQueryInformationPolicy", win32_api="LsaQueryInformationPolicy", ps_or_cli="LSA Policy Info",
        description_ru="Считывает глобальные параметры политики LSA (аудит, домен, квоты)."
    ),
    OperationCatalogItem(
        id=103, name_ru="Определить SeServiceLogonRight", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeServiceLogonRight')", ps_or_cli="Service Logon check",
        description_ru="Находит учетные записи с правом входа в качестве службы."
    ),
    OperationCatalogItem(
        id=104, name_ru="Определить SeRemoteInteractiveLogonRight", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeRemoteInteractiveLogonRight')", ps_or_cli="RDP Logon check",
        description_ru="Находит учетные записи с правом удаленного входа через RDP."
    ),
    OperationCatalogItem(
        id=105, name_ru="Определить SeBackupPrivilege", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeBackupPrivilege')", ps_or_cli="Backup Privilege check",
        description_ru="Находит учетные записи с правом обхода проверок чтения для бэкапа."
    ),
    OperationCatalogItem(
        id=106, name_ru="Определить SeRestorePrivilege", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeRestorePrivilege')", ps_or_cli="Restore Privilege check",
        description_ru="Находит учетные записи с правом восстановления файлов с подменой ACL."
    ),
    OperationCatalogItem(
        id=107, name_ru="Определить SeDebugPrivilege", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeDebugPrivilege')", ps_or_cli="Debug Privilege check",
        description_ru="Находит субъектов с привилегией отладки любых системных процессов."
    ),
    OperationCatalogItem(
        id=108, name_ru="Определить SeTakeOwnershipPrivilege", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeTakeOwnershipPrivilege')", ps_or_cli="Ownership Privilege check",
        description_ru="Находит субъектов с правом захвата владения любыми объектами."
    ),
    OperationCatalogItem(
        id=109, name_ru="Определить SeImpersonatePrivilege", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA", win32_api="LsaEnumerateAccountsWithUserRight('SeImpersonatePrivilege')", ps_or_cli="Impersonate check",
        description_ru="Находит субъектов с правом олицетворения клиентов (критично для безопасности)."
    ),
    OperationCatalogItem(
        id=110, name_ru="Построить effective-rights report", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="LSA + Groups", win32_api="Effective Rights Engine", ps_or_cli="Effective Rights Analysis",
        description_ru="Строит сводный отчет эффективных прав субъекта с учетом всех групп."
    ),
    OperationCatalogItem(
        id=111, name_ru="Найти accounts с опасными rights", subsystem_id="08_lsa_rights",
        subsystem_name_ru="LSA привилегии и права пользователей", risk_level=RiskLevel.SAFE,
        mechanism="Собственный анализ", win32_api="Risk Analyzer", ps_or_cli="Security Posture Check",
        description_ru="Выявляет нестандартные учетные записи с высокорисковыми привилегиями."
    ),

    # 9. Access Tokens (15)
    OperationCatalogItem(
        id=112, name_ru="Open process token", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="OpenProcessToken", win32_api="OpenProcessToken", ps_or_cli="Process Token Handle",
        description_ru="Открывает дескриптор маркера доступа указанного процесса по PID."
    ),
    OperationCatalogItem(
        id=113, name_ru="Получить User SID", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="GetTokenInformation", win32_api="GetTokenInformation(TokenUser)", ps_or_cli="whoami /user",
        description_ru="Извлекает SID владельца процесса из маркера доступа."
    ),
    OperationCatalogItem(
        id=114, name_ru="Получить group SIDs", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="GetTokenInformation", win32_api="GetTokenInformation(TokenGroups)", ps_or_cli="whoami /groups",
        description_ru="Извлекает перечень SID групп маркера доступа."
    ),
    OperationCatalogItem(
        id=115, name_ru="Получить privileges", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="GetTokenInformation", win32_api="GetTokenInformation(TokenPrivileges)", ps_or_cli="whoami /priv",
        description_ru="Извлекает привилегии и их состояние (Enabled/Disabled) для процесса."
    ),
    OperationCatalogItem(
        id=116, name_ru="Получить token type", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="GetTokenInformation", win32_api="GetTokenInformation(TokenType)", ps_or_cli="Token Type",
        description_ru="Определяет тип токена (Primary или Impersonation)."
    ),
    OperationCatalogItem(
        id=117, name_ru="Получить impersonation level", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenImpersonationLevel)", ps_or_cli="Impersonation Level",
        description_ru="Определяет уровень олицетворения токена."
    ),
    OperationCatalogItem(
        id=118, name_ru="Получить integrity level", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenIntegrityLevel)", ps_or_cli="whoami /groups (Mandatory Label)",
        description_ru="Определяет Mandatory Integrity Level процесса (Low/Medium/High/System)."
    ),
    OperationCatalogItem(
        id=119, name_ru="Получить elevation", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenElevation)", ps_or_cli="IsElevated Check",
        description_ru="Проверяет, работает ли процесс с повышенными привилегиями (UAC Elevated)."
    ),
    OperationCatalogItem(
        id=120, name_ru="Получить linked elevated token", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenLinkedToken)", ps_or_cli="Linked Token Query",
        description_ru="Получает связанный повышенный маркер в режиме фильтрованного UAC."
    ),
    OperationCatalogItem(
        id=121, name_ru="Получить session ID", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenSessionId)", ps_or_cli="Process Session ID",
        description_ru="Определяет идентификатор сессии WTS, к которой привязан процесс."
    ),
    OperationCatalogItem(
        id=122, name_ru="Получить logon SID", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenLogonSid)", ps_or_cli="Logon SID",
        description_ru="Извлекает уникальный SID сеанса входа маркера."
    ),
    OperationCatalogItem(
        id=123, name_ru="Получить token groups", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token", win32_api="GetTokenInformation(TokenGroupsAndPrivileges)", ps_or_cli="whoami /groups",
        description_ru="Извлекает полный набор групп и атрибутов токена."
    ),
    OperationCatalogItem(
        id=124, name_ru="Проверить privilege", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="PrivilegeCheck", win32_api="PrivilegeCheck", ps_or_cli="Privilege Check",
        description_ru="Проверяет наличие активной привилегии в маркере."
    ),
    OperationCatalogItem(
        id=125, name_ru="Проверить membership", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="CheckTokenMembership", win32_api="CheckTokenMembership", ps_or_cli="CheckTokenMembership",
        description_ru="Проверяет действительное членство маркера в указанной группе."
    ),
    OperationCatalogItem(
        id=126, name_ru="Сопоставить process → account", subsystem_id="09_tokens",
        subsystem_name_ru="Маркеры доступа процессов и потоков", risk_level=RiskLevel.SAFE,
        mechanism="Token + SID", win32_api="PID Security Resolution Engine", ps_or_cli="explain-pid",
        description_ru="Разрешает PID процесса в полное досье субъекта безопасности."
    ),

    # 10. Sessions / Logon (15)
    OperationCatalogItem(
        id=127, name_ru="Список sessions", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTSEnumerateSessions", win32_api="WTSEnumerateSessionsW", ps_or_cli="qwinsta / query session",
        description_ru="Перечисляет все терминальные и консольные сессии входа."
    ),
    OperationCatalogItem(
        id=128, name_ru="Получить session ID", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="ProcessIdToSessionId", ps_or_cli="qwinsta",
        description_ru="Определяет Session ID для текущего или заданного процесса."
    ),
    OperationCatalogItem(
        id=129, name_ru="Session username", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTSQuerySessionInformation", win32_api="WTSQuerySessionInformationW(WTSUserName)", ps_or_cli="query user",
        description_ru="Извлекает имя пользователя сессии WTS."
    ),
    OperationCatalogItem(
        id=130, name_ru="Session domain", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSQuerySessionInformationW(WTSDomainName)", ps_or_cli="query user",
        description_ru="Извлекает домен пользователя сессии WTS."
    ),
    OperationCatalogItem(
        id=131, name_ru="Session state", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSQuerySessionInformationW(WTSConnectState)", ps_or_cli="qwinsta",
        description_ru="Определяет состояние сессии (Active, Disconnected, Listen, Idle)."
    ),
    OperationCatalogItem(
        id=132, name_ru="Client name", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSQuerySessionInformationW(WTSClientName)", ps_or_cli="RDP Client Name",
        description_ru="Возвращает имя клиентского устройства удаленной сессии RDP."
    ),
    OperationCatalogItem(
        id=133, name_ru="Client address", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSQuerySessionInformationW(WTSClientAddress)", ps_or_cli="RDP Client IP",
        description_ru="Возвращает IP-адрес входящего подключения RDP-сессии."
    ),
    OperationCatalogItem(
        id=134, name_ru="Logon time", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS / Event Log", win32_api="WTSQuerySessionInformationW(WTSLogonTime)", ps_or_cli="qwinsta / Event 4624",
        description_ru="Возвращает точное время авторизации сессии."
    ),
    OperationCatalogItem(
        id=135, name_ru="Idle time", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSQuerySessionInformationW(WTSIdleTime)", ps_or_cli="qwinsta Idle Time",
        description_ru="Возвращает время бездействия сессии."
    ),
    OperationCatalogItem(
        id=136, name_ru="Session type", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSQuerySessionInformationW(WTSWinStationName)", ps_or_cli="Console vs RDP",
        description_ru="Определяет тип терминальной станции (Console, RDP-Tcp, Services)."
    ),
    OperationCatalogItem(
        id=137, name_ru="Console session", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTSGetActiveConsoleSessionId", ps_or_cli="Console ID",
        description_ru="Определяет ID сессии, подключенной к физическому монитору/клавиатуре."
    ),
    OperationCatalogItem(
        id=138, name_ru="RDP session", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.SAFE,
        mechanism="WTS", win32_api="WTS Protocol Query", ps_or_cli="RDP Session detector",
        description_ru="Идентифицирует входящие RDP подключения."
    ),
    OperationCatalogItem(
        id=139, name_ru="Disconnect session", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.DANGEROUS,
        mechanism="WTSDisconnectSession", win32_api="WTSDisconnectSession", ps_or_cli="tsdiscon <id>",
        description_ru="Разрывает сетевое соединение сессии без завершения процессов."
    ),
    OperationCatalogItem(
        id=140, name_ru="Logoff session", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.DANGEROUS,
        mechanism="WTSLogoffSession", win32_api="WTSLogoffSession", ps_or_cli="logoff <id>",
        description_ru="Принудительно завершает сеанс пользователя и все его процессы."
    ),
    OperationCatalogItem(
        id=141, name_ru="Получить user token session", subsystem_id="10_sessions",
        subsystem_name_ru="Сессии входа и службы удаленных рабочих столов", risk_level=RiskLevel.ADVANCED,
        mechanism="WTSQueryUserToken", win32_api="WTSQueryUserToken", ps_or_cli="System Token Query",
        description_ru="Извлекает первичный токен сессии (требует LocalSystem + SE_TCB_NAME)."
    ),

    # 11. User Profiles (13)
    OperationCatalogItem(
        id=142, name_ru="Получить Profiles root", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="GetProfilesDirectory", win32_api="GetProfilesDirectoryW", ps_or_cli="Registry ProfileList / ProfilesDirectory",
        description_ru="Возвращает корневую директорию профилей (обычно C:\\Users)."
    ),
    OperationCatalogItem(
        id=143, name_ru="Получить Default profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="GetDefaultUserProfileDirectory", win32_api="GetDefaultUserProfileDirectoryW", ps_or_cli="Default Profile Dir",
        description_ru="Возвращает путь к эталонному профилю по умолчанию (C:\\Users\\Default)."
    ),
    OperationCatalogItem(
        id=144, name_ru="Получить All Users profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="GetAllUsersProfileDirectory", win32_api="GetAllUsersProfileDirectoryW", ps_or_cli="ProgramData Dir",
        description_ru="Возвращает путь к общему профилю всех пользователей (C:\\ProgramData)."
    ),
    OperationCatalogItem(
        id=145, name_ru="Получить user profile path", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="GetUserProfileDirectory", win32_api="GetUserProfileDirectoryW", ps_or_cli="Registry ProfileImagePath",
        description_ru="Считывает физический путь к папке профиля конкретного SID."
    ),
    OperationCatalogItem(
        id=146, name_ru="Определить profile type", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="GetProfileType", win32_api="GetProfileType", ps_or_cli="Registry Profile Flags",
        description_ru="Определяет тип профиля (Local, Roaming, Mandatory, Temporary)."
    ),
    OperationCatalogItem(
        id=147, name_ru="Создать profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.ADMIN,
        mechanism="CreateProfile", win32_api="CreateProfileW", ps_or_cli="Profile Creation Engine",
        description_ru="Инициализирует структуру каталога и реестра для нового профиля."
    ),
    OperationCatalogItem(
        id=148, name_ru="Загрузить profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.ADMIN,
        mechanism="LoadUserProfile", win32_api="LoadUserProfileW", ps_or_cli="Reg Load NTUSER.DAT",
        description_ru="Монтирует файл NTUSER.DAT в раздел реестра HKEY_USERS\\<SID>."
    ),
    OperationCatalogItem(
        id=149, name_ru="Выгрузить profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.ADMIN,
        mechanism="UnloadUserProfile", win32_api="UnloadUserProfileW", ps_or_cli="Reg Unload",
        description_ru="Демонтирует куст реестра пользователя при выходе."
    ),
    OperationCatalogItem(
        id=150, name_ru="Удалить profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.DANGEROUS,
        mechanism="DeleteProfile", win32_api="DeleteProfileW", ps_or_cli="Remove-CimInstance Win32_UserProfile",
        description_ru="Удаляет профиль пользователя, файлы и запись в ProfileList."
    ),
    OperationCatalogItem(
        id=151, name_ru="Найти profile registry hive", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="NTUSER.DAT", win32_api="File & Registry Scan", ps_or_cli="NTUSER.DAT inspection",
        description_ru="Проверяет наличие и целостность файла NTUSER.DAT в профиле."
    ),
    OperationCatalogItem(
        id=152, name_ru="Проверить profile state", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="Registry", win32_api="RegQueryValueEx(State)", ps_or_cli="Registry ProfileList State",
        description_ru="Считывает битовые флаги состояния профиля из реестра."
    ),
    OperationCatalogItem(
        id=153, name_ru="Найти orphaned profiles", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="Registry + Filesystem", win32_api="Orphan Profile Analyzer", ps_or_cli="Orphaned Profile Scan",
        description_ru="Выявляет папки профилей и записи в реестре без живых аккаунтов."
    ),
    OperationCatalogItem(
        id=154, name_ru="Найти account без profile", subsystem_id="11_profiles",
        subsystem_name_ru="Профили пользователей и кусты реестра", risk_level=RiskLevel.SAFE,
        mechanism="Account + Profile DB", win32_api="Profile Matching Engine", ps_or_cli="Accounts Without Profile",
        description_ru="Выявляет учетные записи, для которых не создан профиль."
    ),

    # 12. Domain / Entra / Directory identity (12)
    OperationCatalogItem(
        id=155, name_ru="Определить domain join", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRoleGetPrimaryDomainInformation", win32_api="DsRoleGetPrimaryDomainInformation", ps_or_cli="(Get-CimInstance Win32_ComputerSystem).PartOfDomain",
        description_ru="Определяет, присоединен ли компьютер к Active Directory или Entra ID."
    ),
    OperationCatalogItem(
        id=156, name_ru="Получить domain name", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRole", win32_api="DsRoleGetPrimaryDomainInformation", ps_or_cli="(Get-CimInstance Win32_ComputerSystem).Domain",
        description_ru="Возвращает имя домена NetBIOS."
    ),
    OperationCatalogItem(
        id=157, name_ru="Получить DNS domain", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRole", win32_api="DsRoleGetPrimaryDomainInformation", ps_or_cli="[System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().DomainName",
        description_ru="Возвращает полное DNS-имя домена."
    ),
    OperationCatalogItem(
        id=158, name_ru="Получить forest", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRole", win32_api="DsRoleGetPrimaryDomainInformation", ps_or_cli="Active Directory Forest Info",
        description_ru="Возвращает имя леса Active Directory."
    ),
    OperationCatalogItem(
        id=159, name_ru="Получить domain GUID", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRole", win32_api="DsRoleGetPrimaryDomainInformation", ps_or_cli="Domain GUID",
        description_ru="Возвращает GUID домена."
    ),
    OperationCatalogItem(
        id=160, name_ru="Определить machine role", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRole", win32_api="DsRoleGetPrimaryDomainInformation(MachineRole)", ps_or_cli="Win32_ComputerSystem DomainRole",
        description_ru="Определяет роль компьютера (Workstation, Server, Domain Controller)."
    ),
    OperationCatalogItem(
        id=161, name_ru="Определить Workgroup", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="DsRole", win32_api="DsRoleGetPrimaryDomainInformation", ps_or_cli="(Get-CimInstance Win32_ComputerSystem).Workgroup",
        description_ru="Возвращает имя рабочей группы при отсутствии домена."
    ),
    OperationCatalogItem(
        id=162, name_ru="Domain user → SID", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountName", win32_api="LookupAccountNameW(domain user)", ps_or_cli="LookupAccountName",
        description_ru="Разрешает доменного пользователя в Active Directory SID."
    ),
    OperationCatalogItem(
        id=163, name_ru="SID → domain user", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="LookupAccountSid", win32_api="LookupAccountSidW(domain sid)", ps_or_cli="LookupAccountSid",
        description_ru="Разрешает доменный SID в имя доменного аккаунта."
    ),
    OperationCatalogItem(
        id=164, name_ru="UPN → identity", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="Directory APIs", win32_api="TranslateNameW", ps_or_cli="UPN Resolution",
        description_ru="Разрешает UPN в SAM-совместимое имя учетной записи."
    ),
    OperationCatalogItem(
        id=165, name_ru="Проверить Entra/AAD join state", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="OS Identity State", win32_api="NetGetAadJoinInformation", ps_or_cli="dsregcmd /status",
        description_ru="Проверяет статус подключения к Azure Active Directory / Entra ID."
    ),
    OperationCatalogItem(
        id=166, name_ru="Получить computer identity", subsystem_id="12_domain",
        subsystem_name_ru="Доменная и Entra/Active Directory идентификация", risk_level=RiskLevel.SAFE,
        mechanism="GetComputerObjectName", win32_api="GetComputerObjectNameW", ps_or_cli="Computer Identity Query",
        description_ru="Возвращает идентификатор компьютера в каталоге безопасности."
    ),

    # 13. Windows Audit Events (15)
    OperationCatalogItem(
        id=167, name_ru="Событие 4720: User created", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4720)", win32_api="EvtQuery / Get-WinEvent", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4720}",
        description_ru="Аудит создания учетной записи пользователя."
    ),
    OperationCatalogItem(
        id=168, name_ru="Событие 4722: User enabled", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4722)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4722}",
        description_ru="Аудит включения учетной записи пользователя."
    ),
    OperationCatalogItem(
        id=169, name_ru="Событие 4723: Password change attempt", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4723)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4723}",
        description_ru="Аудит попытки изменения пароля пользователем."
    ),
    OperationCatalogItem(
        id=170, name_ru="Событие 4724: Password reset", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4724)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4724}",
        description_ru="Аудит принудительного сброса пароля администратором."
    ),
    OperationCatalogItem(
        id=171, name_ru="Событие 4725: User disabled", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4725)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4725}",
        description_ru="Аудит отключения учетной записи пользователя."
    ),
    OperationCatalogItem(
        id=172, name_ru="Событие 4726: User deleted", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4726)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4726}",
        description_ru="Аудит удаления учетной записи пользователя."
    ),
    OperationCatalogItem(
        id=173, name_ru="Событие 4731: Local group created", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4731)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4731}",
        description_ru="Аудит создания локальной группы безопасности."
    ),
    OperationCatalogItem(
        id=174, name_ru="Событие 4732: Member added to local group", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4732)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4732}",
        description_ru="Аудит добавления участника в локальную группу."
    ),
    OperationCatalogItem(
        id=175, name_ru="Событие 4733: Member removed from local group", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4733)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4733}",
        description_ru="Аудит исключения участника из локальной группы."
    ),
    OperationCatalogItem(
        id=176, name_ru="Событие 4734: Local group deleted", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4734)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4734}",
        description_ru="Аудит удаления локальной группы безопасности."
    ),
    OperationCatalogItem(
        id=177, name_ru="Событие 4735: Local group changed", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4735)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4735}",
        description_ru="Аудит модификации параметров локальной группы."
    ),
    OperationCatalogItem(
        id=178, name_ru="Событие 4738: User changed", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4738)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4738}",
        description_ru="Аудит изменения атрибутов учетной записи пользователя."
    ),
    OperationCatalogItem(
        id=179, name_ru="Событие 4740: Account locked", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4740)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4740}",
        description_ru="Аудит блокировки аккаунта из-за превышения числа неверных паролей."
    ),
    OperationCatalogItem(
        id=180, name_ru="Событие 4624: Successful logon", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4624)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624}",
        description_ru="Аудит успешного входа пользователя в систему."
    ),
    OperationCatalogItem(
        id=181, name_ru="Событие 4625: Failed logon", subsystem_id="13_audit",
        subsystem_name_ru="Аудит событий безопасности Windows", risk_level=RiskLevel.SAFE,
        mechanism="Security Event Log (4625)", win32_api="EvtQuery", ps_or_cli="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625}",
        description_ru="Аудит неудачной попытки входа в систему."
    ),
]


def get_full_catalog() -> List[OperationCatalogItem]:
    """
    Возвращает полный каталог всех операций Accounts & Identity.

    Returns:
        Список элементов OperationCatalogItem.
    """
    return list(_OPERATIONS)


def get_operation_by_id(op_id: int) -> Optional[OperationCatalogItem]:
    """
    Поиск операции по уникальному идентификатору.

    Args:
        op_id: Идентификатор операции (1-181).

    Returns:
        OperationCatalogItem или None.
    """
    for op in _OPERATIONS:
        if op.id == op_id:
            return op
    return None


def get_operations_by_subsystem(subsystem_id: str) -> List[OperationCatalogItem]:
    """
    Фильтрация операций по идентификатору подсистемы.

    Args:
        subsystem_id: ID подсистемы (например '01_identity', '02_users').

    Returns:
        Список операций данной подсистемы.
    """
    return [op for op in _OPERATIONS if op.subsystem_id == subsystem_id]


def get_operations_by_risk(risk_level: RiskLevel) -> List[OperationCatalogItem]:
    """
    Фильтрация операций по уровню риска.

    Args:
        risk_level: Уровень риска (SAFE, ADMIN, DANGEROUS, ADVANCED).

    Returns:
        Список операций соответствующего риска.
    """
    return [op for op in _OPERATIONS if op.risk_level == risk_level]


def search_catalog(query: str) -> List[OperationCatalogItem]:
    """
    Полнотекстовый поиск по операциям каталога.

    Args:
        query: Поисковая строка.

    Returns:
        Список найденных операций.
    """
    q = query.lower()
    return [
        op for op in _OPERATIONS
        if q in op.name_ru.lower()
        or q in op.description_ru.lower()
        or (op.win32_api and q in op.win32_api.lower())
        or (op.ps_or_cli and q in op.ps_or_cli.lower())
    ]
