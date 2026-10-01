# Windows Storage Sensor (Нативные сенсоры накопителей Windows)

## Описание
Модуль нативной диагностики накопителей (NVMe, SATA SSD, HDD, Storage Spaces, USB-накопителей) для Windows без зависимости от внешних утилит (таких как Smartmontools или AIDA64).

## Источники данных
1. **WMI / CIM (`root/cimv2`)**:
   - `Win32_DiskDrive`: физические устройства, размеры, интерфейсы, базовый статус.
   - `Win32_DiskPartition` и `Win32_LogicalDisk`: разделы и логические диски.
   - `Win32_Volume`: файловые тома.
2. **Microsoft Storage Management (`root/Microsoft/Windows/Storage`)**:
   - `MSFT_PhysicalDisk`: тип шины (BusType: NVMe, SATA, SAS, USB), тип носителя (MediaType: SSD, HDD), серийные номера, статус здоровья (`HealthStatus`, `OperationalStatus`).
   - `MSFT_VirtualDisk`, `MSFT_StoragePool`, `MSFT_Partition`: дисковые пулы и виртуальные диски.
   - `StorageReliabilityCounter`: процент износа (Wear), температура дисков в °C, общее время наработки (PowerOnHours), счетчики ошибок чтения/записи (`ReadErrorsTotal`, `WriteErrorsTotal`), максимальные задержки (`ReadLatencyMax`, `WriteLatencyMax`).
3. **Счетчики производительности Windows (`PhysicalDisk`)**:
   - Скорости чтения/записи (Bytes/sec), длина очереди (`Current Disk Queue Length`), среднее время отклика (`Avg. Disk sec/Read`, `Avg. Disk sec/Write`).
4. **Журнал событий Windows (Event Log)**:
   - События драйверов Storport, файловых систем NTFS/ReFS и разбиения разделов.

## Использование в коде

```python
from apps.windows.storage_sensors.windows_storage_sensor import WindowsStorageSensor

sensor = WindowsStorageSensor()
disks = sensor.get_physical_disks()

for disk in disks:
    print(f"Диск: {disk.friendly_name} ({disk.bus_type} {disk.media_type})")
    print(f"  Здоровье: {disk.health_status}, Износ: {disk.wear_percentage}%")
    print(f"  Температура: {disk.temperature_c}°C, Наработка: {disk.power_on_hours} ч.")
```

## CLI
```powershell
python apps/windows/storage_sensors/windows_storage_sensor.py --output storage_snapshot.json
```
