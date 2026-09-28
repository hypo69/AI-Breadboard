"""Пакет нативных сенсоров дисков Windows."""
from apps.windows.storage_sensors.windows_storage_sensor import StorageDiskHealthInfo, WindowsStorageSensor, collect_storage_snapshot, save_snapshot
__all__ = ['StorageDiskHealthInfo', 'WindowsStorageSensor', 'collect_storage_snapshot', 'save_snapshot']