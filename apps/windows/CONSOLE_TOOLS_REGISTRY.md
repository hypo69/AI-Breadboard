# 🛠️ Полный каталог атомарных возможностей Windows CLI и REST API

Данный документ представляет собой **исчерпывающий каталог возможностей Windows CLI и API**, декомпозированный на **атомарные операции («утилита → атомарные операции»)**, с указанием уровней риска SafeOps, требуемых системных привилегий, способов вызова (CLI, Win32 API, COM, WMI, PowerShell) и соответствующих эндпоинтов **FastAPI (`/api/v1/...`)**.

---

## 📑 17 Системных категорий и матрица атомарных операций

### 1. Диски, разделы и файловые системы (Storage & Filesystems)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **diskpart.exe** | `disk.list` | `READ_ONLY` | Admin | CLI / Win32 | `GET /api/v1/storage/disks` | Перечисление всех физических дисков и их номеров |
| | `disk.clean` | `CRITICAL` | Admin | CLI | `POST /api/v1/storage/disks/{disk}/clean` | Очистка разметки разделов диска |
| | `disk.convert` | `HIGH` | Admin | CLI | `POST /api/v1/storage/disks/{disk}/convert` | Конвертация MBR <-> GPT |
| | `partition.list` | `READ_ONLY` | Admin | CLI / WMI | `GET /api/v1/storage/disks/{disk}/partitions` | Список разделов на диске |
| | `partition.create`| `HIGH` | Admin | CLI | `POST /api/v1/storage/disks/{disk}/partitions` | Создание раздела (Primary/EFI/MSR) |
| | `partition.delete`| `CRITICAL` | Admin | CLI | `DELETE /api/v1/storage/disks/{disk}/partitions/{part}` | Удаление выбранного раздела |
| | `partition.extend`| `MEDIUM` | Admin | CLI | `POST /api/v1/storage/partitions/{part}/extend` | Расширение размера раздела |
| | `partition.shrink`| `MEDIUM` | Admin | CLI | `POST /api/v1/storage/partitions/{part}/shrink` | Уменьшение размера раздела |
| | `volume.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/storage/volumes` | Список всех томов с буквами и метками |
| | `volume.format` | `CRITICAL` | Admin | CLI | `POST /api/v1/storage/volumes/{vol}/format` | Форматирование тома в NTFS/FAT32/exFAT |
| | `volume.assign` | `MEDIUM` | Admin | CLI | `POST /api/v1/storage/volumes/{vol}/assign-letter` | Назначение буквы диску |
| **fsutil.exe** | `fs.info` | `READ_ONLY` | Standard | CLI | `GET /api/v1/storage/fs/info` | Получение информации о файловой системе |
| | `fs.trim_query` | `READ_ONLY` | Standard | CLI | `GET /api/v1/storage/fs/trim` | Проверка состояния команды TRIM для SSD |
| | `fs.trim_set` | `HIGH` | Admin | CLI | `POST /api/v1/storage/fs/trim` | Включение/отключение TRIM |
| | `fs.8dot3_query`| `READ_ONLY` | Standard | CLI | `GET /api/v1/storage/fs/8dot3` | Проверка генерации 8.3 коротких имен |
| | `fs.sparse_query`| `READ_ONLY`| Standard | CLI | `GET /api/v1/storage/fs/sparse` | Проверка поддержки sparse файлов |
| **mountvol.exe**| `mountvol.list` | `READ_ONLY` | Standard | CLI / Win32 | `GET /api/v1/storage/mountpoints` | Список точек монтирования и GUID томов |
| | `mountvol.mount`| `MEDIUM` | Admin | CLI | `POST /api/v1/storage/mountpoints` | Подключение тома к точке монтирования |
| **chkdsk.exe** | `chkdsk.scan` | `READ_ONLY` | Admin | CLI | `POST /api/v1/storage/volumes/{vol}/chkdsk-scan` | Анализ ошибок тома без блокировки |
| | `chkdsk.repair` | `HIGH` | Admin | CLI | `POST /api/v1/storage/volumes/{vol}/chkdsk-repair` | Исправление ошибок файловой системы (/F) |
| **format.com** | `format.quick` | `CRITICAL` | Admin | CLI | `POST /api/v1/storage/volumes/{vol}/quick-format` | Быстрое форматирование тома |

---

### 2. Загрузка и восстановление (Boot & Recovery)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **bcdedit.exe** | `bcd.list` | `READ_ONLY` | Admin | CLI / WMI | `GET /api/v1/boot/entries` | Чтение списка записей BCD и параметров |
| | `bcd.set_timeout` | `MEDIUM` | Admin | CLI | `POST /api/v1/boot/timeout` | Изменение таймаута меню загрузчика |
| | `bcd.safemode` | `HIGH` | Admin | CLI | `POST /api/v1/boot/safemode` | Включение безопасного режима Safe Mode |
| **bcdboot.exe** | `bcdboot.repair`| `CRITICAL` | Admin | CLI | `POST /api/v1/boot/repair-environment`| Восстановление загрузочных файлов EFI |
| **bootrec.exe** | `bootrec.fixmbr`| `CRITICAL` | Admin | CLI | `POST /api/v1/boot/fix-mbr` | Восстановление главной загрузочной записи |
| | `bootrec.rebuild`| `CRITICAL` | Admin | CLI | `POST /api/v1/boot/rebuild-bcd` | Перестроение хранилища BCD |
| **reagentc.exe**| `winre.info` | `READ_ONLY` | Admin | CLI | `GET /api/v1/recovery/winre/info` | Статус среды восстановления WinRE |
| | `winre.enable` | `MEDIUM` | Admin | CLI | `POST /api/v1/recovery/winre/enable` | Включение среды восстановления WinRE |

---

### 3. Системные файлы и компоненты (Servicing & Integrity)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **sfc.exe** | `sfc.scannow` | `HIGH` | Admin | CLI | `POST /api/v1/servicing/sfc/scannow` | Проверка и восстановление файлов WRP |
| | `sfc.verifyonly` | `READ_ONLY` | Admin | CLI | `POST /api/v1/servicing/sfc/verifyonly`| Проверка целостности без замены |
| **DISM.exe** | `dism.check_health` | `READ_ONLY` | Admin | CLI | `GET /api/v1/servicing/dism/check-health`| Проверка маркера повреждения Component Store |
| | `dism.restore_health`| `HIGH` | Admin | CLI | `POST /api/v1/servicing/dism/restore-health`| Восстановление образа Windows |
| | `dism.features_list` | `READ_ONLY` | Admin | CLI / PS | `GET /api/v1/servicing/features` | Список компонентов Windows Features |
| | `dism.cleanup` | `MEDIUM` | Admin | CLI | `POST /api/v1/servicing/dism/cleanup` | Очистка устаревших версий WinSxS |

---

### 4. Драйверы и устройства (Drivers & Devices)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **pnputil.exe** | `device.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/hardware/devices` | Список устройств PnP |
| | `device.problems` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/hardware/devices/problems`| Поиск устройств со сбоями (Code 10/43) |
| | `driver.packages` | `READ_ONLY` | Standard | CLI | `GET /api/v1/hardware/drivers/packages` | Список пакетов OEM .INF в DriverStore |
| | `driver.add` | `HIGH` | Admin | CLI | `POST /api/v1/hardware/drivers/packages`| Добавление и установка драйвера |
| | `driver.delete` | `HIGH` | Admin | CLI | `DELETE /api/v1/hardware/drivers/packages/{inf}` | Удаление пакета драйвера из хранилища |
| **driverquery.exe** | `driver.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/hardware/drivers/installed` | Список загруженных драйверов ядра |

---

### 5. Процессы (Processes)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **tasklist.exe**| `process.list` | `READ_ONLY` | Standard | Win32 / PS | `GET /api/v1/processes` | Список процессов, PID, память и сессии |
| | `process.modules` | `READ_ONLY` | Standard | Win32 | `GET /api/v1/processes/{pid}/modules` | Загруженные модули DLL процесса |
| **taskkill.exe**| `process.kill_pid` | `HIGH` | Standard | Win32 / CLI | `POST /api/v1/processes/{pid}/kill` | Принудительное завершение процесса |
| | `process.kill_tree`| `HIGH` | Standard | CLI | `POST /api/v1/processes/{pid}/kill-tree`| Завершение дерева дочерних процессов |

---

### 6. Планировщик (Task Scheduler)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **schtasks.exe**| `task.list` | `READ_ONLY` | Standard | COM / CLI | `GET /api/v1/scheduler/tasks` | Список заданий Task Scheduler |
| | `task.run` | `LOW` | Standard | COM / CLI | `POST /api/v1/scheduler/tasks/{task}/run` | Немедленный запуск задания |
| | `task.stop` | `LOW` | Standard | COM / CLI | `POST /api/v1/scheduler/tasks/{task}/stop` | Остановка выполняющегося задания |
| | `task.delete` | `HIGH` | Admin | COM / CLI | `DELETE /api/v1/scheduler/tasks/{task}` | Удаление запланированного задания |

---

### 7. Производительность и трассировка (Performance & Tracing)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **logman.exe** | `collector.list` | `READ_ONLY` | Admin | CLI | `GET /api/v1/tracing/collectors` | Список наборов сборщиков данных ETW |
| | `collector.start`| `LOW` | Admin | CLI | `POST /api/v1/tracing/collectors/{c}/start`| Запуск сессии трассировки |
| | `collector.stop` | `LOW` | Admin | CLI | `POST /api/v1/tracing/collectors/{c}/stop` | Остановка сессии трассировки |
| **typeperf.exe**| `counters.sample`| `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/tracing/counters/sample` | Чтение моментальных счетчиков CPU/RAM |

---

### 8. Службы (Service Control Manager)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **sc.exe** | `service.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/services` | Перечисление служб Windows и статусов |
| | `service.start` | `MEDIUM` | Admin | Win32 / CLI | `POST /api/v1/services/{name}/start` | Запуск системной службы |
| | `service.stop` | `MEDIUM` | Admin | Win32 / CLI | `POST /api/v1/services/{name}/stop` | Остановка службы |
| | `service.config_start`| `HIGH` | Admin | Win32 / CLI | `POST /api/v1/services/{name}/start-type` | Смена типа запуска (Auto/Manual/Disabled) |
| **net.exe** | `net.start_service` | `MEDIUM` | Admin | CLI | `POST /api/v1/services/{name}/net-start` | Запуск службы через NET START |

---

### 9. Event Log & Diagnostics

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **wevtutil.exe**| `log.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/events/logs` | Перечисление каналов журналов событий |
| | `log.clear` | `HIGH` | Admin | Win32 / CLI | `POST /api/v1/events/logs/{log}/clear` | Очистка журнала событий |
| | `log.export` | `LOW` | Admin | Win32 / CLI | `POST /api/v1/events/logs/{log}/export` | Бинарный экспорт канала в `.evtx` |
| **wecutil.exe** | `subscriptions.list`| `READ_ONLY` | Admin | CLI | `GET /api/v1/events/subscriptions` | Подписки пересылки событий (WEC) |

---

### 10. Сеть (Network Stack & Routing)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **ipconfig.exe**| `ip.all` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/network/ip-config` | Полная IP-конфигурация адаптеров |
| | `dns.flush` | `LOW` | Admin | CLI | `POST /api/v1/network/dns/flush` | Сброс кэша DNS резолвера |
| | `dhcp.renew` | `MEDIUM` | Admin | CLI | `POST /api/v1/network/dhcp/renew` | Обновление аренды DHCP |
| **netstat.exe** | `connections` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/network/connections` | Таблица TCP/UDP сокетов и PID |
| **route.exe** | `routes.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/network/routes` | Таблица маршрутизации IPv4/IPv6 |
| **netsh.exe** | `interfaces.list`| `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/network/interfaces` | Список интерфейсов и MTU |

---

### 11. Firewall (Windows Defender Firewall)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **netsh advfirewall** | `advfirewall.status` | `READ_ONLY` | Standard | CLI / PS | `GET /api/v1/firewall/status` | Статус профилей Domain, Private, Public |
| | `advfirewall.rules` | `READ_ONLY` | Standard | CLI / PS | `GET /api/v1/firewall/rules` | Список правил фильтрации |
| | `advfirewall.rule_add` | `MEDIUM` | Admin | CLI / PS | `POST /api/v1/firewall/rules` | Добавление правила брандмауэра |

---

### 12. Безопасность, ACL и шифрование (Security & ACL)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **icacls.exe** | `acl.get` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/security/acl` | Просмотр списков ACL для файла/папки |
| | `acl.grant` | `HIGH` | Admin | CLI | `POST /api/v1/security/acl/grant` | Выдача прав доступа субъекту |
| **manage-bde.exe** | `bitlocker.status` | `READ_ONLY` | Admin | CLI / WMI | `GET /api/v1/security/bitlocker/status` | Статус шифрования BitLocker и TPM |
| **cipher.exe** | `cipher.status` | `READ_ONLY` | Standard | CLI | `GET /api/v1/security/efs/status` | Состояние шифрования EFS |

---

### 13. Реестр и групповые политики (Registry & GPO)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **reg.exe** | `reg.query` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/registry/values` | Чтение параметров реестра HKLM/HKCU |
| | `reg.add` | `HIGH` | Admin | Win32 / CLI | `POST /api/v1/registry/values` | Запись параметра в реестр |
| **gpupdate.exe**| `gpo.update` | `MEDIUM` | Standard | CLI | `POST /api/v1/gpo/update` | Принудительное обновление политик GPO |
| **gpresult.exe**| `gpo.result` | `READ_ONLY` | Standard | CLI | `GET /api/v1/gpo/result` | Сводка примененных политик RSoP |

---

### 14. Пользователи и локальные группы (Identity & Users)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **net user** | `user.list` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/users` | Список локальных пользователей |
| | `user.create` | `HIGH` | Admin | Win32 / CLI | `POST /api/v1/users` | Создание новой учетной записи |
| **whoami.exe** | `whoami.all` | `READ_ONLY` | Standard | Win32 / CLI | `GET /api/v1/users/whoami` | Текущий SID, группы и Se-привилегии |

---

### 15. Резервное копирование и VSS (VSS & Backup)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **vssadmin.exe**| `shadows.list` | `READ_ONLY` | Admin | CLI / COM | `GET /api/v1/vss/shadows` | Список теневых копий томов VSS |
| | `storage.list` | `READ_ONLY` | Admin | CLI | `GET /api/v1/vss/storage` | Состояние хранилища теневых копий |
| **wbadmin.exe** | `backup.versions`| `READ_ONLY` | Admin | CLI | `GET /api/v1/backup/wbadmin/versions` | Список версий резервных копий |

---

### 16. Электропитание и жизненный цикл (Power & Lifecycle)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **powercfg.exe**| `power.schemes` | `READ_ONLY` | Standard | CLI / Win32 | `GET /api/v1/power/schemes` | Список доступных профилей питания |
| | `power.requests` | `READ_ONLY` | Standard | CLI | `GET /api/v1/power/requests` | Блокировки спящего режима (Sleep) |
| **shutdown.exe**| `shutdown.restart`| `HIGH` | Standard | Win32 / CLI | `POST /api/v1/lifecycle/restart` | Перезагрузка компьютера |
| **systeminfo.exe**| `system.info` | `READ_ONLY` | Standard | CLI / Win32 | `GET /api/v1/system/info` | Полная конфигурация ОС и хотфиксы |

---

### 17. Установка и управление пакетами (Software & Packages)

| Утилита | Атомарная операция | Риск | Привилегии | Метод | FastAPI Route & Метод | Описание |
|---|---|---|---|---|---|---|
| **winget.exe** | `winget.search` | `READ_ONLY` | Standard | CLI | `GET /api/v1/packages/winget/search` | Поиск пакетов в репозиториях WinGet |
| | `winget.list` | `READ_ONLY` | Standard | CLI | `GET /api/v1/packages/winget/installed`| Список установленных программ |
| | `winget.install` | `HIGH` | Admin | CLI | `POST /api/v1/packages/winget/install` | Установка выбранного пакета ПО |
| **msiexec.exe** | `msi.install` | `HIGH` | Admin | CLI | `POST /api/v1/packages/msi/install` | Тихая установка .MSI пакета |

---

## 2. Архитектура интеграции с SafeOps и FastAPI

```text
┌─────────────────────────────────────────────────────────────────────────┐
│              FastAPI Capabilities Router (/api/v1/capabilities)         │
├───────────────────────────────────┬─────────────────────────────────────┤
│ GET /capabilities/catalog         │ Плоский каталог всех 100+ операций  │
│ GET /capabilities/tree            │ Дерево («утилита -> операции»)      │
│ GET /capabilities/utilities/{u}   │ Операции конкретной утилиты         │
│ POST /capabilities/execute        │ SafeOps исполнение и Dry-Run        │
└───────────────────────────────────┴─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  WindowsAtomicCapabilitiesRegistry                      │
│ ├── Валидация аргументов и сопоставление CLI шаблонов                   │
│ ├── Проверка SafeOps уровней риска (READ_ONLY / LOW / HIGH / CRITICAL)  │
│ ├── Контроль прав доступа (STANDARD / ADMINISTRATOR / SYSTEM)           │
│ └── Потоковое протоколирование в CSV (AppCsvLogger)                     │
└─────────────────────────────────────────────────────────────────────────┘
```
