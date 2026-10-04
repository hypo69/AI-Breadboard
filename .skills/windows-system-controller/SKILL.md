---
name: windows-system-controller
description: Autonomous Windows OS diagnostics, management and telemetry controller
description_i18n:
  en: Autonomous Windows OS diagnostics, management and telemetry controller
  ru: Автономный контроллер диагностики, телеметрии и прямого управления Windows OS
---

# 🖥️ Навык: Windows System Controller

## 🎯 Назначение
Навык `windows-system-controller` наделяет модель и автономных агентов знаниями по прямому управлению операционной системой Windows через подсистемы `apps/windows/core` и `apps/windows/modules`.
Он охватывает аудит оборудования, контроль служб и процессов, проверку целостности (SFC/DISM), создание и откат точек восстановления (Windows Restore Points), безопасное изменение системных настроек и исполнение регламентированных утилит Windows.

---

## 🏗️ Архитектура подсистем Windows

```
apps/windows/
├── core/
│   ├── audits/               # 13 доменных коллекторов телеметрии
│   ├── atomic_capabilities.py # Реестр атомарных операций (diskpart, sc, bcdedit, dism...)
│   ├── system_restore.py     # Менеджер точек восстановления System Restore
│   ├── system_param_manager.py # SafeOps менеджер системных параметров
│   └── tools/                # WindowsCollectorTool & SafePowerShellProbeTool
└── modules/                  # 21 специализированный доменный модуль
    ├── services_manager/     # Управление системными службами
    ├── process_manager/      # Мониторинг и управление процессами
    ├── firewall_manager/     # Настройка правил сетевого экрана
    ├── defender/             # Мониторинг Windows Defender и угроз
    └── task_scheduler/       # Планировщик задач
```

---

## 🛠️ Набор доступных инструментов (Windows Native Tools)

| Инструмент | Назначение | Примеры параметров |
|---|---|---|
| `windows_collector_audit` | Сбор телеметрии по одному из 13 доменов | `collector_name: 'driver'` / `'storage'` / `'services'` / `'security'` |
| `windows_execute_atomic_op` | Выполнение каталожных атомарных операций | `operation_id: 'diskpart.disk.list'`, `dry_run: false` |
| `windows_manage_service` | Статус, запуск, остановка и перезапуск служб | `service_name: 'wuauserv'`, `action: 'status'` / `'restart'` |
| `windows_manage_process` | Список, инспекция по PID и завершение процессов | `action: 'list'`, `action: 'inspect'`, `pid: 1234` |
| `windows_manage_restore_point` | Проверка защиты, создание и откат точек восстановления | `action: 'status'`, `action: 'create'`, `description: 'Pre-update'` |
| `windows_manage_sys_param` | Управление параметрами системы (SafeOps) | `action: 'preview'`, `param_id: 'telemetry_level'`, `value: 0` |
| `windows_safe_probe` | Выполнение безопасных PowerShell/WMI запросов | `script: 'Get-PnpDevice \| Select-Object Status, Name \| ConvertTo-Json'` |
| `windows_execute_powershell` | Прямое выполнение любых PowerShell команд и скриптов | `script: 'Get-Volume \| Format-Table'`, `as_json: false` |

---

## 🔒 Протокол безопасности SafeOps (Обязателен к соблюдению)

1. **Принцип предварительного аудита (Diagnostic First)**:
   - Перед любым изменением конфигурации запустите соответствующий коллектор (`windows_collector_audit`) или проверьте текущий статус компонента.
2. **Точки восстановления перед чувствительными изменениями**:
   - При операциях уровня `HIGH` или `CRITICAL`, либо при изменении системных настроек, обязательно вызывайте создание точки восстановления:
     ```python
     await windows_manage_restore_point(action='create', description='Точка перед изменением конфигурации')
     ```
3. **Режим симуляции (Dry-Run)**:
   - Для незнакомых операций предварительно вызывайте `dry_run=True` или действие `preview` для оценки формируемой команды.
4. **Запрет деструктивных действий**:
   - Запрещено форматирование системных томов, удаление системных папок (`System32`, `WinSxS`) или отключение критических служб ядра (`RPCSS`, `DcomLaunch`, `EventLog`).
5. **Прозрачная отчетность**:
   - Формируйте результат в структурированном виде с фиксацией кодов возврата, затронутых компонентов и статуса стабильности системы.
