# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Extended Inspectors - Windows Sandbox Inspector
# =============================================================================
# Description:
#   Динамический запуск подозрительных исполняемых файлов в изолированной песочнице Windows Sandbox (.wsb).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.extended_inspectors.windows_sandbox_inspector import WindowsSandboxInspector
#
#     inspector = WindowsSandboxInspector()
#     status = inspector.launch_in_sandbox("C:/Path/To/binary.exe")
#
# File: windows_sandbox_inspector.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.extended_inspectors
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 05:04:00
# =============================================================================

from __future__ import annotations

"""Модуль генерации .wsb конфигураций и запуска бинарников в Windows Sandbox."""

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logger import logger


@dataclass
class SandboxLaunchResult:
    """Результат запуска приложения в песочнице."""
    target_path: str
    wsb_config_path: str
    sandbox_available: bool
    launched: bool
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat()) if 'field' in globals() else datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            'target_path': self.target_path,
            'wsb_config_path': self.wsb_config_path,
            'sandbox_available': self.sandbox_available,
            'launched': self.launched,
            'error': self.error,
        }


class WindowsSandboxInspector:
    """Инспектор динамического анализа в изолированной среде Windows Sandbox."""

    def is_sandbox_installed(self) -> bool:
        """Проверяет наличие файла WindowsSandbox.exe в системе."""
        sandbox_exe = Path('C:/Windows/System32/WindowsSandbox.exe')
        return sandbox_exe.exists()

    def generate_wsb_config(self, target_binary_path: str, enable_networking: bool = False) -> str:
        """Генерирует .wsb файлы конфигурации для вызова целевого исполняемого файла.

        Args:
            target_binary_path: Путь к бинарнику.
            enable_networking: Разрешить ли сетевой доступ в песочнице.

        Returns:
            str: Путь к сгенерированному файлу .wsb.
        """
        target = Path(target_binary_path)
        folder = target.parent if target.exists() else Path('C:/Temp')

        wsb_xml = f"""<Configuration>
  <VGpu>Disable</VGpu>
  <Networking>{'Default' if enable_networking else 'Disable'}</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>{folder}</HostFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>cmd.exe /c "C:\\Users\\WDAGUtilityAccount\\Desktop\\{folder.name}\\{target.name}"</Command>
  </LogonCommand>
</Configuration>"""

        wsb_path = folder / f"sandbox_analysis_{target.stem}.wsb"
        try:
            wsb_path.write_text(wsb_xml, encoding='utf-8')
        except Exception as ex:
            logger.error(f'[WindowsSandboxInspector] Ошибка записи .wsb конфига: {ex}')

        return str(wsb_path)

    def launch_in_sandbox(self, target_binary_path: str, enable_networking: bool = False) -> SandboxLaunchResult:
        """Запускает песочницу с монтированием папки целевого файла.

        Args:
            target_binary_path: Путь к анализируемому файлу.
            enable_networking: Разрешить сетевой доступ.

        Returns:
            SandboxLaunchResult: Результат вызова.
        """
        available = self.is_sandbox_installed()
        wsb_path = self.generate_wsb_config(target_binary_path, enable_networking=enable_networking)

        if not available or os.name != 'nt':
            return SandboxLaunchResult(
                target_path=target_binary_path,
                wsb_config_path=wsb_path,
                sandbox_available=False,
                launched=False,
                error='Windows Sandbox недоступен на данном хосте (требуется Windows 10/11 Pro/Enterprise)'
            )

        try:
            res = subprocess.Popen(['cmd.exe', '/c', 'start', '', wsb_path], shell=True)
            return SandboxLaunchResult(
                target_path=target_binary_path,
                wsb_config_path=wsb_path,
                sandbox_available=True,
                launched=True,
            )
        except Exception as ex:
            logger.error(f'[WindowsSandboxInspector] Ошибка запуска Windows Sandbox: {ex}')
            return SandboxLaunchResult(
                target_path=target_binary_path,
                wsb_config_path=wsb_path,
                sandbox_available=True,
                launched=False,
                error=str(ex)
            )
