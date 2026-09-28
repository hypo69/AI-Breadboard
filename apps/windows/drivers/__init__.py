"""Пакет управления видеодрайверами GPU для Windows."""
from apps.windows.drivers.models import DriverBranch, DriverRelease, DownloadProgress, GpuDevice, GpuUpdateCheck, TaskStatus, VendorType
from apps.windows.drivers.hardware_detector import GpuHardwareDetector
from apps.windows.drivers.nvidia_catalog import NvidiaCatalogManager
from apps.windows.drivers.amd_catalog import AmdCatalogManager
from apps.windows.drivers.driver_downloader import DriverDownloader
__all__ = ['DriverBranch', 'DriverRelease', 'DownloadProgress', 'GpuDevice', 'GpuUpdateCheck', 'TaskStatus', 'VendorType', 'GpuHardwareDetector', 'NvidiaCatalogManager', 'AmdCatalogManager', 'DriverDownloader']