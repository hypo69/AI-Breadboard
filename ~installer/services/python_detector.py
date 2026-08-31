# -*- coding: utf-8 -*-
# =============================================================================
# Python Detector Service
# =============================================================================
# Description: Discovers available Python versions on the system
#              and manages Python installation for AI Breadboard.
#
# File: installer/services/python_detector.py
# Project: AI Breadboard
# =============================================================================

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class PythonDetector:
    """Detects and manages Python installations for AI Breadboard."""
    
    PREFERRED_VERSIONS = ["3.13", "3.12", "3.11", "3.10"]
    MIN_VERSION = "3.10"
    
    def __init__(self):
        self._cached_versions: List[Dict] = []
    
    def find_available_versions(self) -> List[Dict]:
        """Find all available Python versions on the system."""
        if self._cached_versions:
            return self._cached_versions
        
        versions = []
        
        # Try Python Launcher first (Windows)
        py_launcher = self._find_python_launcher()
        if py_launcher:
            for version in self.PREFERRED_VERSIONS:
                try:
                    result = subprocess.run(
                        [py_launcher, f"-{version}", "-c", "import sys; print(sys.executable)"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        python_path = result.stdout.strip()
                        ver = self._get_python_version(python_path)
                        versions.append({
                            "version": version,
                            "full_version": ver,
                            "path": python_path,
                            "available": True
                        })
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        
        # Try 'python' command
        python_cmd = self._which("python")
        if python_cmd:
            try:
                ver = self._get_python_version(python_cmd)
                if self._version_gte(ver, self.MIN_VERSION):
                    versions.append({
                        "version": ver.split('.')[:2],
                        "full_version": ver,
                        "path": python_cmd,
                        "available": True
                    })
            except:
                pass
        
        # Try 'python3' command (Linux/macOS)
        if sys.platform != "win32":
            python3_cmd = self._which("python3")
            if python3_cmd and python3_cmd != python_cmd:
                try:
                    ver = self._get_python_version(python3_cmd)
                    if self._version_gte(ver, self.MIN_VERSION):
                        versions.append({
                            "version": ver.split('.')[:2],
                            "full_version": ver,
                            "path": python3_cmd,
                            "available": True
                        })
                except:
                    pass
        
        self._cached_versions = versions
        return versions
    
    def _find_python_launcher(self) -> Optional[str]:
        """Find Python Launcher on Windows."""
        if sys.platform != "win32":
            return None
        
        # Try py launcher
        launcher_paths = [
            os.path.join(os.environ.get("SYSTEMROOT", ""), "py.exe"),
            os.path.join(os.environ.get("SYSTEMROOT", ""), "System32", "py.exe"),
            os.path.join(os.environ.get("SYSTEMROOT", ""), "SysWOW64", "py.exe"),
        ]
        
        for path in launcher_paths:
            if os.path.exists(path):
                return path
        
        # Try PATH
        return self._which("py")
    
    def _which(self, command: str) -> Optional[str]:
        """Find executable in PATH."""
        if sys.platform == "win32":
            command = f"{command}.exe"
        
        for path in os.environ.get("PATH", "").split(os.pathsep):
            full_path = os.path.join(path, command)
            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                return full_path
        
        return None
    
    def _get_python_version(self, python_path: str) -> str:
        """Get Python version from executable."""
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse version from output like "Python 3.13.7"
                match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
        except:
            pass
        
        return "0.0.0"
    
    def _version_gte(self, version: str, min_version: str) -> bool:
        """Check if version >= min_version."""
        try:
            v_parts = [int(x) for x in version.split('.')]
            m_parts = [int(x) for x in min_version.split('.')]
            
            for v, m in zip(v_parts, m_parts):
                if v > m:
                    return True
                if v < m:
                    return False
            return True
        except:
            return False
    
    async def find_or_install_python(self, target_version: str = "3.13") -> Optional[str]:
        """Find or install a specific Python version."""
        # First try to find existing installation
        versions = self.find_available_versions()
        
        for v in versions:
            if v["version"] == target_version:
                return v["path"]
        
        # If not found, try to download and install
        logger.info(f"Python {target_version} not found, will attempt download")
        return await self._download_python(target_version)
    
    async def _download_python(self, version: str) -> Optional[str]:
        """Download and install Python from python.org."""
        # TODO: Implement Python download and installation
        # For now, return None to indicate manual installation required
        # Future implementation would:
        # 1. Download installer from python.org
        # 2. Run installer silently
        # 3. Return path to new Python
        
        logger.warning(f"Automatic Python download not implemented yet for version {version}")
        return None
    
    def get_preferred_version(self) -> str:
        """Get the best available Python version."""
        versions = self.find_available_versions()
        
        for v in versions:
            if v["version"] in self.PREFERRED_VERSIONS:
                return v["version"]
        
        if versions:
            return versions[0]["version"]
        
        return self.PREFERRED_VERSIONS[0]


# Singleton instance
_python_detector = None


def get_python_detector() -> PythonDetector:
    """Get singleton PythonDetector instance."""
    global _python_detector
    if _python_detector is None:
        _python_detector = PythonDetector()
    return _python_detector