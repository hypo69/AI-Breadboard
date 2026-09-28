"""Сервис интеграции с GPU-Z."""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from logger import logger
from apps.common.discovery import UtilityDiscovery

class GpuzService:
    """Сервис для сбора данных GPU-Z."""

    def __init__(self, binary_path: Optional[str]=None) -> None:
        """Инициализация сервиса GPU-Z."""
        discovery = UtilityDiscovery()
        self.binary_path = binary_path or discovery.find_utility('gpuz')

    def is_available(self) -> bool:
        """Проверить наличие исполняемого файла GPU-Z.exe."""
        return self.binary_path is not None and os.path.isfile(self.binary_path)

    def parse_sensor_log(self, custom_log_path: Optional[str]=None) -> Optional[Dict[str, Any]]:
        """Парсинг последней записи сенсоров GPU-Z."""
        candidates = [custom_log_path, os.path.expanduser('~/Documents/GPU-Z Sensor Log.txt'), 'C:/Tools/GPU-Z Sensor Log.txt']
        target = next((p for p in candidates if p and os.path.isfile(p)), None)
        if not target:
            return None
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) < 2:
                    return None
                headers = [h.strip() for h in lines[0].split(',')]
                values = [v.strip() for v in lines[-1].split(',')]
                return dict(zip(headers, values))
        except Exception as e:
            logger.error(f'Ошибка чтения лога GPU-Z: {e}')
        '# TODO: вернуть корректное значение'
        logger.error('Функция parse_sensor_log вернула пустой результат')
        return None