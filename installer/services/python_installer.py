# -*- coding: utf-8 -*-
# =============================================================================
# Python Installer Service
# =============================================================================
# Description: Handles downloading and installing Python for AI Breadboard
#
# File: installer/services/python_installer.py
# Project: AI Breadboard
# =============================================================================

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import logging
import urllib.request

logger = logging.getLogger(__name__)


class PythonInstaller:
    """Handles Python installation for AI Breadboard."""
    
    PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python"
    WINDOWS_INSTALLER_SUFFIX = "/python-{version}-amd64.exe"
    WINDOWS_INSTALLER_ARM = "/python-{version}-arm64.exe"
    
    def __init__(self):
        self._download_dir = Path(tempfile.gettempdir()) / "aibreadboard_python"
        self._download_dir.mkdir(parents=True, exist_ok=True)
    
    async def install_python(self, version: str, target_dir: Optional[str] = None) -> Optional[str]:
        """Install a specific Python version."""
        logger.info(f"Starting Python {version} installation")
        
        # Determine installer URL based on platform
        if sys.platform == "win32":
            installer_url = self._get_windows_installer_url(version)
        elif sys.platform == "darwin":
            installer_url = self._get_macos_installer_url(version)
        else:
            logger.warning(f"Automatic Python installation not supported on {sys.platform}")
            return None
        
        if not installer_url:
            return None
        
        try:
            # Download installer
            installer_path = await self._download_installer(installer_url)
            if not installer_path:
                return None
            
            # Run installer silently
            python_path = await self._run_installer(installer_path, version, target_dir)
            
            # Clean up installer
            installer_path.unlink(missing_ok=True)
            
            return python_path
            
        except Exception as e:
            logger.error(f"Error installing Python {version}: {e}")
            return None
    
    def _get_windows_installer_url(self, version: str) -> Optional[str]:
        """Get Windows installer URL for Python version."""
        # Extract major.minor from version (e.g., "3.13.7" -> "3.13")
        parts = version.split('.')
        if len(parts) < 2:
            return None
        
        base_version = f"{parts[0]}.{parts[1]}"
        
        if sys.maxsize > 2**32:
            # 64-bit
            return f"{self.PYTHON_DOWNLOAD_URL}/{version}/python-{version}-amd64.exe"
        else:
            # 32-bit
            return f"{self.PYTHON_DOWNLOAD_URL}/{version}/python-{version}-win32.exe"
    
    def _get_macos_installer_url(self, version: str) -> Optional[str]:
        """Get macOS installer URL for Python version."""
        parts = version.split('.')
        if len(parts) < 2:
            return None
        
        base_version = f"{parts[0]}.{parts[1]}"
        
        # macOS installer URL format
        return f"{self.PYTHON_DOWNLOAD_URL}/{version}/python-{version}-macos11.pkg"
    
    async def _download_installer(self, url: str) -> Optional[Path]:
        """Download Python installer."""
        try:
            logger.info(f"Downloading Python installer from {url}")
            
            with urllib.request.urlopen(url) as response:
                filename = url.split('/')[-1]
                installer_path = self._download_dir / filename
                
                with open(installer_path, 'wb') as f:
                    f.write(response.read())
            
            logger.info(f"Downloaded to {installer_path}")
            return installer_path
            
        except Exception as e:
            logger.error(f"Error downloading installer: {e}")
            return None
    
    async def _run_installer(self, installer_path: Path, version: str, target_dir: Optional[str]) -> Optional[str]:
        """Run Python installer silently."""
        try:
            logger.info(f"Running installer: {installer_path}")
            
            if sys.platform == "win32":
                # Windows silent installation
                # /quiet installs Python without UI
                # InstallAllUsers=1 installs for all users
                # PrependPath=1 adds Python to PATH
                
                cmd = [
                    str(installer_path),
                    "/quiet",
                    "InstallAllUsers=0",
                    "PrependPath=1",
                    "Shortcuts=0",
                    "Include_pip=1",
                    "Include_test=0"
                ]
                
                if target_dir:
                    cmd.append(f"TargetDir={target_dir}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    python_path = self._find_python_after_install(version, target_dir)
                    logger.info(f"Python {version} installed at {python_path}")
                    return python_path
                else:
                    logger.error(f"Installer failed: {result.stderr}")
                    return None
                    
            elif sys.platform == "darwin":
                # macOS - use pkgutil
                cmd = [
                    "sudo", "installer", "-pkg", str(installer_path),
                    "-target", "/"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return "/usr/local/bin/python3"
                else:
                    logger.error(f"macOS installer failed: {result.stderr}")
                    return None
            else:
                logger.warning(f"Cannot run installer on {sys.platform}")
                return None
                
        except Exception as e:
            logger.error(f"Error running installer: {e}")
            return None
    
    def _find_python_after_install(self, version: str, target_dir: Optional[str]) -> Optional[str]:
        """Find Python executable after installation."""
        # Common Python installation paths
        common_paths = [
            Path(sys.executable),  # Current Python
            Path(sys.executable).parent / "python.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / f"Python{version.replace('.', '')}" / "python.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Python" / f"Python{version.replace('.', '')}" / "python.exe",
        ]
        
        if target_dir:
            common_paths.insert(0, Path(target_dir) / "python.exe")
        
        for path in common_paths:
            if path.exists() and path.is_file():
                try:
                    result = subprocess.run(
                        [str(path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and version in result.stdout:
                        return str(path)
                except:
                    continue
        
        return None
    
    async def download_python_only(self, version: str, destination: str) -> Optional[Path]:
        """Download Python installer without running it."""
        url = self._get_windows_installer_url(version)
        if not url:
            return None
        
        try:
            filename = url.split('/')[-1]
            dest_path = Path(destination) / filename
            
            with urllib.request.urlopen(url) as response:
                with open(dest_path, 'wb') as f:
                    f.write(response.read())
            
            return dest_path
            
        except Exception as e:
            logger.error(f"Error downloading Python: {e}")
            return None


# Singleton instance
_python_installer = None


def get_python_installer() -> PythonInstaller:
    """Get singleton PythonInstaller instance."""
    global _python_installer
    if _python_installer is None:
        _python_installer = PythonInstaller()
    return _python_installer