# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Configuration file management utilities
# =============================================================================
# Description:
#   Utilities for working with configuration files cross-platform.
#   Provides JSON loading/saving, environment variable management.
#
# File: config.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Cross-platform configuration management utilities.

Provides utilities for managing configuration files, JSON operations,
and environment variable handling."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.cli.paths import get_paths

class ConfigManager:
    """Configuration file management.
    
    Handles loading and saving of configuration files in JSON format
    with support for caching and environment variable integration.
    """
    
    def __init__(self):
        """Initialize config manager."""
        self.paths = get_paths()
        self._config_cache = {}
        self._env_vars = {}
    
    def load_json(self, filepath: Path) -> dict:
        """Load JSON file.
        
        Args:
            filepath: Path to JSON file.
            
        Returns:
            Dictionary with JSON content or empty dict if not found.
        """
        if not filepath.exists():
            return {}
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def save_json(self, filepath: Path, data: dict, pretty: bool = True) -> bool:
        """Save JSON file.
        
        Args:
            filepath: Path to save JSON to.
            data: Dictionary to save.
            pretty: Format output for readability.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2 if pretty else None
                )
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def load_env_file(self, filepath: Path) -> dict:
        """Load .env file.
        
        Args:
            filepath: Path to .env file.
            
        Returns:
            Dictionary of environment variables.
        """
        env_vars = {}
        
        if not filepath.exists():
            return env_vars
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
        
        return env_vars
    
    def save_env_file(self, filepath: Path, env_vars: dict) -> bool:
        """Save .env file.
        
        Args:
            filepath: Path to save .env to.
            env_vars: Dictionary of environment variables.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation like 'section.key').
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        # Load main config
        config = self.load_json(self.paths.config_file)
        
        # Navigate nested keys
        keys = key.split(".")
        current = config
        
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
            else:
                return default
        
        return current if current is not None else default
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation).
            value: Value to set.
            
        Returns:
            True if successful, False otherwise.
        """
        config = self.load_json(self.paths.config_file)
        
        # Navigate nested keys
        keys = key.split(".")
        current = config
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        return self.save_json(self.paths.config_file, config)
    
    def merge_env_to_config(self) -> None:
        """Merge environment variables into config."""
        env_file = self.paths.env_file
        env_vars = self.load_env_file(env_file)
        
        for key, value in env_vars.items():
            os.environ[key] = value
