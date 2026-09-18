---
name: folder-sharing-manager
description: Windows network folder sharing and SMB shares management toolkit.
description_i18n:
  en: Windows network folder sharing and SMB shares management toolkit.
  ru: Инструментарий управления общими сетевыми папками (SMB/CIFS) и правами доступа в Windows.
---

# Управление общими папками Windows (Folder Sharing & SMB Manager)

## 🎯 Назначение (Purpose)
Навык предназначен для инспекции существующих сетевых ресурсов (SMB Shares), предоставления общего доступа к локальным папкам (расшаривание), настройки прав доступа (NTFS и SMB) и управления сетевым обнаружением в Windows.

## 🚀 Триггеры и применение (When to Use & Triggers)
- Запросы пользователя: «как расшарить папку с файлами», «создай сетевую папку», «покажи общие папки», «открой доступ к папке», «настройка SMB share», «сетевой доступ к файлам».
- Работа в интерфейсе Test Computer (/tc), веб-чате и консоли.

## ⚙️ Протокол выполнения (Execution Protocol)

### 1. Инспекция текущих сетевых ресурсов (Read-Only)
Для получения списка всех активных общих ресурсов в Windows:
`powershell
Get-SmbShare | Select-Object Name, Path, Description, ScopeName | ConvertTo-Json
`

### 2. Расшаривание папки через PowerShell (SafeOps)
Создание нового сетевого ресурса с явным заданием прав доступа:
`powershell
# Создание общего ресурса для чтения (Read Access):
New-SmbShare -Name "<ИмяРесурса>" -Path "<ПутьКПпапке>" -ReadAccess "Everyone"

# Создание общего ресурса с полным доступом (Full Access):
New-SmbShare -Name "<ИмяРесурса>" -Path "<ПутьКПпапке>" -FullAccess "Authenticated Users"
`

### 3. Настройка прав безопасности NTFS (при необходимости)
`powershell
 = Get-Acl "<ПутьКПпапке>"
 = New-Object System.Security.AccessControl.FileSystemAccessRule("Authenticated Users", "ReadAndExecute, Synchronize", "ContainerInherit, ObjectInherit", "None", "Allow")
.AddAccessRule()
Set-Acl "<ПутьКПпапке>" 
`

### 4. Пошаговый алгоритм через графический интерфейс (GUI)
1. Открыть **Проводник (Explorer)** и перейти к целевой папке.
2. Кликнуть правой кнопкой мыши по папке и выбрать **Свойства (Properties)**.
3. Перейти на вкладку **Доступ (Sharing)** и нажать кнопку **Общий доступ... (Share...)** или **Расширенная настройка... (Advanced Sharing)**.
4. Установить флажок *«Открыть общий доступ к этой папке»*, указать имя ресурса и задать разрешения в кнопке **Разрешения (Permissions)**.
5. Нажать **Применить** и **ОК**.

### 5. Проверка сетевого обнаружения и брандмауэра
Убедиться, что в профиле сети включен общий доступ к файлам и принтерам:
`powershell
Get-NetFirewallRule -DisplayGroup "Общий доступ к файлам и принтерам" | Select-Object DisplayName, Enabled, Direction
`
