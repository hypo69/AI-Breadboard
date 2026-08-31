# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Cross-platform installation system for AI Breadboard
# Description: Sets up Python environment, dependencies, SSL certificates,
#   CLI configuration, and optional AI models for AI Breadboard across all
#   platforms.
# File: installer.py
# Project: ai-breadboard
# Package: scripts.cli
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Cross-platform installation system for AI Breadboard.

Ported from legacy install.ps1 to work on Windows, Linux, and macOS.

Usage:
    python scripts/cli/installer.py
    python scripts/cli/installer.py --lang en
    python scripts/cli/installer.py --skip-models
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cli.paths import get_paths, CrossPlatformPaths
from scripts.cli.config import get_config_manager
from scripts.cli.utils import which, run_command

class Language(Enum):
    """Supported languages"""
    EN = "en"
    RU = "ru"
    ES = "es"
    HE = "he"

# Messages in multiple languages
MESSAGES = {
    "en": {
        "welcome": "🎯 AI Breadboard Installation",
        "step_venv": "[1/6] Creating Python virtual environment...",
        "step_deps": "[2/6] Installing dependencies...",
        "step_certs": "[3/6] Setting up SSL certificates...",
        "step_cli": "[4/6] Configuring CLI assistant...",
        "step_verify": "[5/6] Verifying installation...",
        "step_models": "[6/6] Downloading AI models (optional)...",
        "success": "✅ Installation completed successfully!",
        "error": "❌ Installation failed:",
        "abort": "⚠️  Installation aborted by user",
    },
    "ru": {
        "welcome": "🎯 AI Breadboard Installation",
        "step_venv": "[1/6] Creating Python virtual environment...",
        "step_deps": "[2/6] Installing dependencies...",
        "step_certs": "[3/6] Setting up SSL certificates...",
        "step_cli": "[4/6] Configuring CLI assistant...",
        "step_verify": "[5/6] Verifying installation...",
        "step_models": "[6/6] Downloading AI models (optional)...",
        "success": "✅ Installation completed successfully!",
        "error": "❌ Installation failed:",
        "abort": "⚠️  Installation aborted by user",
    },
}

class Installer:
    """Main installer class"""
    
    def __init__(self, language: str = "en", install_dir: Optional[Path] = None):
        self.language = Language[language.upper()] if language.upper() in Language.__members__ else Language.EN
        self.messages = MESSAGES.get(self.language.value, MESSAGES["en"])
        self.install_dir = install_dir or self._get_default_install_dir()
        self.venv_dir = self.install_dir / "venv"
        self.config_mgr = get_config_manager()
    
    def msg(self, key: str) -> str:
        """Get message in current language"""
        return self.messages.get(key, key)
    
    @staticmethod
    def _get_default_install_dir() -> Path:
        """Get default installation directory"""
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\AI-Breadboard
            localappdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(localappdata) / "AI-Breadboard"
        else:
            # Linux/macOS: ~/AI-Breadboard or ~/.local/share/AI-Breadboard
            return Path.home() / "AI-Breadboard"
    
    def print_header(self):
        """Print installation header"""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + self.msg("welcome").center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(f"Installing to: {self.install_dir}")
        print()
    
    def create_venv(self) -> bool:
        """Create virtual environment"""
        print(self.msg("step_venv"))
        
        try:
            # Remove old venv if exists
            if self.venv_dir.exists():
                print(f"  Removing old venv...", end=" ", flush=True)
                shutil.rmtree(self.venv_dir)
                print("[OK]")
            
            # Create new venv
            print(f"  Creating venv...", end=" ", flush=True)
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_dir)],
                check=True,
                capture_output=True
            )
            print("[OK]")
            print()
            return True
        
        except Exception as e:
            print(f"[ERROR] {e}")
            print()
            return False
    
    def install_dependencies(self) -> bool:
        """Install dependencies"""
        print(self.msg("step_deps"))
        
        try:
            # Get pip path in venv
            if sys.platform == "win32":
                pip_exe = self.venv_dir / "Scripts" / "pip.exe"
            else:
                pip_exe = self.venv_dir / "bin" / "pip"
            
            if not pip_exe.exists():
                print(f"  [ERROR] pip not found in venv")
                print()
                return False
            
            # Requirements files
            req_files = [
                self.install_dir / "requirements.txt",
                self.install_dir / "install" / "req" / "requirements-core.txt",
                self.install_dir / "install" / "req" / "requirements-ai.txt",
            ]
            
            for req_file in req_files:
                if req_file.exists():
                    print(f"  Installing from {req_file.name}...", end=" ", flush=True)
                    result = subprocess.run(
                        [str(pip_exe), "install", "-r", str(req_file)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print("[OK]")
                    else:
                        print(f"[WARN]")
                        if result.stderr:
                            print(f"    {result.stderr[:100]}")
            
            print()
            return True
        
        except Exception as e:
            print(f"[ERROR] {e}")
            print()
            return False
    
    def setup_ssl_certificates(self) -> bool:
        """Setup SSL certificates"""
        print(self.msg("step_certs"))
        
        try:
            certs_dir = CrossPlatformPaths().certs_dir
            certs_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"  Certificates directory: {certs_dir}")
            
            # Check for mkcert
            if which("mkcert"):
                print(f"  mkcert found, generating certificates...", end=" ", flush=True)
                subprocess.run(
                    ["mkcert", "-install"],
                    cwd=str(certs_dir),
                    capture_output=True
                )
                subprocess.run(
                    ["mkcert", "-key-file", str(certs_dir / "localhost+2-key.pem"), 
                     "-cert-file", str(certs_dir / "localhost+2.pem"),
                     "localhost", "127.0.0.1", "::1"],
                    cwd=str(certs_dir),
                    capture_output=True
                )
                print("[OK]")
            else:
                print(f"  mkcert not installed (optional)")
                print(f"  Installation: https://github.com/FiloSottile/mkcert")
            
            print()
            return True
        
        except Exception as e:
            print(f"[WARN] Error setting up certificates: {e}")
            print()
            return True  # Not critical
    
    def configure_cli(self) -> bool:
        """Configure CLI assistant"""
        print(self.msg("step_cli"))
        
        try:
            from scripts.cli.utils import ensure_in_path, add_to_env_var
            
            # Add to PATH
            print(f"  Adding to PATH...", end=" ", flush=True)
            if ensure_in_path(self.install_dir / "assist"):
                print("[OK]")
            else:
                print("[WARN]")
            
            # Set environment variables
            print(f"  Setting environment variables...", end=" ", flush=True)
            add_to_env_var("AIBREADBOARD_DIR", str(self.install_dir))
            add_to_env_var("PYTHONPATH", str(self.install_dir))
            print("[OK]")
            
            print()
            return True
        
        except Exception as e:
            print(f"[WARN] {e}")
            print()
            return True  # Not critical
    
    def verify_installation(self) -> bool:
        """Verify installation"""
        print(self.msg("step_verify"))
        
        try:
            # Get Python in venv
            if sys.platform == "win32":
                python_exe = self.venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = self.venv_dir / "bin" / "python"
            
            if not python_exe.exists():
                print(f"  [ERROR] Python not found in venv")
                print()
                return False
            
            # Check core modules
            print(f"  Checking dependencies...", end=" ", flush=True)
            result = subprocess.run(
                [str(python_exe), "-c", "import fastapi, uvicorn, dotenv; print('OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "OK" in result.stdout:
                print("[OK]")
            else:
                print("[WARN] Some dependencies may not be installed")
            
            # Check assist
            assist_file = self.install_dir / "assist"
            if assist_file.exists() or (self.install_dir / "assist.cmd").exists():
                print(f"  Checking assist CLI...", end=" ", flush=True)
                print("[OK]")
            else:
                print(f"  [WARN] assist not found")
            
            print()
            return True
        
        except Exception as e:
            print(f"[WARN] {e}")
            print()
            return True  # Not critical
    
    def download_models(self, skip: bool = False) -> bool:
        """Download models (optional)"""
        if skip:
            print(self.msg("step_models"))
            print(f"  Skipping (used --skip-models)")
            print()
            return True
        
        print(self.msg("step_models"))
        
        # TODO: Implement model download
        print(f"  TODO: Implement model download")
        print()
        return True
    
    def run(self, skip_models: bool = False, skip_venv: bool = False, 
            skip_deps: bool = False, skip_certs: bool = False) -> int:
        """Run installation"""
        self.print_header()
        
        try:
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Installation steps
            steps = [
                (not skip_venv, self.create_venv, "venv"),
                (not skip_deps, self.install_dependencies, "dependencies"),
                (not skip_certs, self.setup_ssl_certificates, "SSL certificates"),
                (True, self.configure_cli, "CLI"),
                (True, self.verify_installation, "verification"),
                (True, lambda: self.download_models(skip=skip_models), "models"),
            ]
            
            for should_run, step_func, step_name in steps:
                if should_run:
                    if not step_func():
                        print(f"{self.msg('error')} {step_name}")
                        return 1
            
            # Success
            print("╔" + "═" * 68 + "╗")
            print("║" + self.msg("success").center(68) + "║")
            print("╚" + "═" * 68 + "╝")
            print()
            print(f"Next steps:")
            print(f"  1. Go to installation directory:")
            print(f"     cd {self.install_dir}")
            print(f"  2. Activate venv:")
            if sys.platform == "win32":
                print(f"     venv\\Scripts\\activate")
            else:
                print(f"     source venv/bin/activate")
            print(f"  3. Start the server:")
            print(f"     python run.py")
            print()
            return 0
        
        except KeyboardInterrupt:
            print()
            print(self.msg("abort"))
            print()
            return 1
        except Exception as e:
            print(f"{self.msg('error')} {e}")
            return 1

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="AI Breadboard installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cli/installer.py
  python scripts/cli/installer.py --lang en
  python scripts/cli/installer.py --install-dir /path/to/install
  python scripts/cli/installer.py --skip-models
        """
    )
    
    parser.add_argument(
        "--lang",
        choices=["en", "ru", "es", "he"],
        default="en",
        help="Installation language (default: en)"
    )
    
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=None,
        help="Installation directory"
    )
    
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip model download"
    )
    
    parser.add_argument(
        "--skip-venv",
        action="store_true",
        help="Skip venv creation"
    )
    
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency installation"
    )
    
    parser.add_argument(
        "--skip-certs",
        action="store_true",
        help="Skip certificate setup"
    )
    
    args = parser.parse_args()
    
    installer = Installer(
        language=args.lang,
        install_dir=args.install_dir
    )
    
    return installer.run(
        skip_models=args.skip_models,
        skip_venv=args.skip_venv,
        skip_deps=args.skip_deps,
        skip_certs=args.skip_certs,
    )

if __name__ == "__main__":
    sys.exit(main())
