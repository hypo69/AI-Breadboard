# -*- coding: utf-8 -*-
# =============================================================================
# Environment Manager Service
# =============================================================================
# Description: Manages Python virtual environments and package installation
#
# File: installer/services/environment_manager.py
# Project: AI Breadboard
# =============================================================================

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Manages Python virtual environments and packages."""
    
    def __init__(self):
        self._venv_created: bool = False
        self._pip_upgraded: bool = False
    
    def create_venv(self, install_dir: str, python_path: Optional[str] = None) -> str:
        """Create a new virtual environment."""
        install_path = Path(install_dir)
        venv_path = install_path / "venv"
        python_exe = venv_path / "Scripts" / "python.exe" if sys.platform == "win32" else venv_path / "bin" / "python"
        
        # Check if venv already exists and is valid
        if python_exe.exists():
            try:
                result = subprocess.run(
                    [str(python_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Virtual environment already exists: {venv_path}")
                    return str(python_exe)
            except:
                pass
        
        # Remove existing venv if corrupted
        if venv_path.exists():
            import shutil
            shutil.rmtree(venv_path)
        
        # Determine Python executable to use
        if python_path is None:
            python_path = sys.executable
        
        # Create virtual environment
        logger.info(f"Creating virtual environment at {venv_path}")
        subprocess.run(
            [python_path, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True
        )
        
        self._venv_created = True
        logger.info(f"Virtual environment created: {venv_path}")
        
        return str(python_exe)
    
    def upgrade_pip(self, python_path: str) -> bool:
        """Upgrade pip and build tools."""
        try:
            result = subprocess.run(
                [python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("pip, setuptools, wheel upgraded successfully")
                self._pip_upgraded = True
                return True
            else:
                logger.warning(f"Failed to upgrade pip: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"Error upgrading pip: {e}")
            return False
    
    def install_packages(self, install_dir: str, packages: List[str]) -> List[str]:
        """Install a list of packages."""
        venv_python = Path(install_dir) / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            raise FileNotFoundError(f"Virtual environment not found: {venv_python}")
        
        installed = []
        
        for package in packages:
            try:
                result = subprocess.run(
                    [str(venv_python), "-m", "pip", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    installed.append(package)
                    logger.info(f"Installed package: {package}")
                else:
                    logger.warning(f"Failed to install {package}: {result.stderr}")
                    
            except Exception as e:
                logger.warning(f"Error installing {package}: {e}")
        
        return installed
    
    def install_requirements(self, install_dir: str, requirements_file: str) -> int:
        """Install packages from a requirements file."""
        venv_python = Path(install_dir) / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            raise FileNotFoundError(f"Virtual environment not found: {venv_python}")
        
        req_file = Path(requirements_file)
        if not req_file.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
        
        try:
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info(f"Requirements installed from {requirements_file}")
                return 0
            else:
                logger.error(f"Failed to install requirements: {result.stderr}")
                return result.returncode
                
        except Exception as e:
            logger.error(f"Error installing requirements: {e}")
            return 1
    
    def is_venv_valid(self, install_dir: str) -> bool:
        """Check if virtual environment is valid."""
        venv_python = Path(install_dir) / "venv" / "Scripts" / "python.exe"
        
        if not venv_python.exists():
            return False
        
        try:
            result = subprocess.run(
                [str(venv_python), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def get_venv_python(self, install_dir: str) -> Optional[str]:
        """Get path to venv Python executable."""
        venv_python = Path(install_dir) / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return None
    
    async def async_install_packages(self, install_dir: str, packages: List[str]) -> List[str]:
        """Async version of install_packages."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.install_packages,
            install_dir,
            packages
        )
    
    async def async_install_requirements(self, install_dir: str, requirements_file: str) -> int:
        """Async version of install_requirements."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.install_requirements,
            install_dir,
            requirements_file
        )


# Singleton instance
_env_manager = None


def get_env_manager() -> EnvironmentManager:
    """Get singleton EnvironmentManager instance."""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentManager()
    return _env_manager