# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cross-platform path management system
# =============================================================================
# Description:
#   Cross-platform path management that automatically determines correct paths
#   for Windows, Linux, and macOS systems using platform conventions.
#
# File: paths.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Cross-platform path management system.

Automatically determines correct paths for Windows, Linux, and macOS
using appropriate platform conventions and directory standards."""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import platformdirs
    HAS_PLATFORMDIRS = True
except ImportError:
    HAS_PLATFORMDIRS = False

class CrossPlatformPaths:
    """Centralized path system for all platforms.
    
    Uses:
    - Windows: %LOCALAPPDATA%, %USERPROFILE%
    - Linux/macOS: ~/.local/share, ~/.config, ~/.cache
    """
    
    def __init__(self, app_name: str = "AI-Breadboard", app_author: str = "hypo69"):
        """Initialize cross-platform paths.
        
        Args:
            app_name: Application name.
            app_author: Application author.
        """
        self.app_name = app_name
        self.app_author = app_author
        self._project_root = self._find_project_root()
        self._cache = {}
    
    @staticmethod
    def _find_project_root() -> Path:
        """Find project root by presence of main.py or config.json.
        
        Returns:
            Path to project root.
        """
        current = Path(__file__).parent
        for _ in range(10):  # Search up to 10 levels
            if (current / "main.py").exists() or (current / "config.json").exists():
                return current
            current = current.parent
        # Fallback to AIBREADBOARD_DIR or current directory
        return Path(os.environ.get("AIBREADBOARD_DIR", os.getcwd()))
    
    @property
    def project_root(self) -> Path:
        """Project root directory."""
        return self._project_root
    
    @property
    def data_dir(self) -> Path:
        """Application data directory.
        
        Windows: %LOCALAPPDATA%\AI-Breadboard
        Linux: ~/.local/share/AI-Breadboard
        macOS: ~/Library/Application Support/AI-Breadboard
        """
        if HAS_PLATFORMDIRS:
            return Path(platformdirs.user_data_dir(self.app_name, self.app_author))
        
        # Fallback for systems without platformdirs
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(base) / self.app_name
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / self.app_name
        else:
            return Path.home() / ".local" / "share" / self.app_name
    
    @property
    def config_dir(self) -> Path:
        """Configuration directory.
        
        Windows: %LOCALAPPDATA%\AI-Breadboard\config
        Linux: ~/.config/AI-Breadboard
        macOS: ~/Library/Preferences/AI-Breadboard
        """
        if HAS_PLATFORMDIRS:
            return Path(platformdirs.user_config_dir(self.app_name, self.app_author))
        
        if sys.platform == "win32":
            return self.data_dir / "config"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Preferences" / self.app_name
        else:
            return Path.home() / ".config" / self.app_name
    
    @property
    def cache_dir(self) -> Path:
        """Cache directory.
        
        Windows: %LOCALAPPDATA%\AI-Breadboard\Cache
        Linux: ~/.cache/AI-Breadboard
        macOS: ~/Library/Caches/AI-Breadboard
        """
        if HAS_PLATFORMDIRS:
            return Path(platformdirs.user_cache_dir(self.app_name, self.app_author))
        
        if sys.platform == "win32":
            return self.data_dir / "Cache"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Caches" / self.app_name
        else:
            return Path.home() / ".cache" / self.app_name
    
    @property
    def certs_dir(self) -> Path:
        """SSL certificates directory.
        
        Windows: %USERPROFILE%\.certs
        Linux: ~/.local/share/ca-certificates
        macOS: ~/Library/Certs
        """
        if sys.platform == "win32":
            return Path.home() / ".certs"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Certs"
        else:
            return Path.home() / ".local" / "share" / "ca-certificates"
    
    @property
    def certs_user_dir(self) -> Path:
        """Alternative user certificates directory."""
        return Path.home() / ".certs"
    
    @property
    def bin_dir(self) -> Path:
        """Executable files directory.
        
        Windows: %USERPROFILE%\.local\bin
        Linux/macOS: ~/.local/bin
        """
        return Path.home() / ".local" / "bin"
    
    @property
    def venv_dir(self) -> Path:
        """Python virtual environment directory."""
        return self.project_root / "venv"
    
    @property
    def venv_python(self) -> Path:
        """Python interpreter in virtual environment."""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"
    
    @property
    def secrets_dir(self) -> Path:
        """Secrets directory for API keys."""
        return self.project_root / "core" / "secrets"
    
    @property
    def env_file(self) -> Path:
        """.env file path."""
        return self.project_root / ".env"
    
    @property
    def config_file(self) -> Path:
        """config.json file path."""
        return self.project_root / "config.json"
    
    @property
    def requirements_main(self) -> Path:
        """Main requirements.txt file."""
        return self.project_root / "requirements.txt"
    
    @property
    def requirements_core(self) -> Path:
        """Core requirements file."""
        return self.project_root / "install" / "req" / "requirements-core.txt"
    
    @property
    def requirements_ai(self) -> Path:
        """AI requirements file."""
        return self.project_root / "install" / "req" / "requirements-ai.txt"
    
    @property
    def requirements_test(self) -> Path:
        """Test requirements file."""
        return self.project_root / "install" / "req" / "requirements-test.txt"
    
    @property
    def requirements_docs(self) -> Path:
        """Documentation requirements file."""
        return self.project_root / "install" / "req" / "requirements-docs.txt"
    
    def get_env_vars(self) -> dict:
        """Get required environment variables.
        
        Returns:
            Dictionary of environment variables.
        """
        return {
            "AIBREADBOARD_DIR": str(self.project_root),
            "ASSIST_DIR": str(self.project_root),
            "PYTHONUTF8": "1",
            "PYTHONPATH": f"{self.project_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}",
        }
    
    def setup_env(self) -> None:
        """Set environment variables."""
        for key, value in self.get_env_vars().items():
            if value:
                os.environ[key] = value
    
    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        dirs = [
            self.data_dir,
            self.config_dir,
            self.cache_dir,
            self.certs_dir,
            self.certs_user_dir,
            self.bin_dir,
            self.secrets_dir,
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

# Global instance
_paths_instance: Optional[CrossPlatformPaths] = None

def get_paths() -> CrossPlatformPaths:
    """Get global CrossPlatformPaths instance.
    
    Returns:
        Global paths instance.
    """
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = CrossPlatformPaths()
    return _paths_instance

def init_paths() -> CrossPlatformPaths:
    """Initialize paths and set environment variables.
    
    Returns:
        Initialized paths instance.
    """
    paths = get_paths()
    paths.setup_env()
    paths.ensure_dirs()
    return paths
