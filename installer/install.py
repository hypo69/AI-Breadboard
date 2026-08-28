#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# AI Breadboard Installer - Bootstrap Launcher
# =============================================================================
# Description: Launches the web-based installer server
#              This is the main entry point for the new installer.
#
# File: installer/install.py
# Project: AI Breadboard
# =============================================================================

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

# Add installer directory to path
installer_dir = Path(__file__).parent
sys.path.insert(0, str(installer_dir))


def check_python_version():
    """Check if Python version is compatible."""
    min_version = (3, 10)
    current = sys.version_info
    
    if current < min_version:
        print(f"ERROR: Python {min_version[0]}.{min_version[1]}+ required")
        print(f"       Your Python: {current.major}.{current.minor}.{current.micro}")
        return False
    
    return True


def install_dependencies():
    """Install required Python packages."""
    import subprocess
    
    packages = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "aiofiles>=23.2.0"
    ]
    
    print("Installing dependencies...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("Dependencies installed successfully")
            return True
        else:
            print(f"Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    required = ["fastapi", "uvicorn", "pydantic", "aiofiles"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    return missing


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Breadboard Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py                      # Start installer server
  python install.py --host 0.0.0.0       # Listen on all interfaces
  python install.py --port 8080          # Use custom port
  python install.py --no-open            # Don't open browser
        """
    )
    
    parser.add_argument(
        "--host", "-H",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't open browser after start"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install missing dependencies automatically"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        
        if args.install_deps:
            if not install_dependencies():
                print("Please install manually: pip install fastapi uvicorn pydantic aiofiles")
                sys.exit(1)
        else:
            print("Please install missing dependencies:")
            print(f"  pip install {' '.join(missing)}")
            sys.exit(1)
    
    # Import and start server
    try:
        import uvicorn
        
        print(f"\n{'=' * 60}")
        print(f"  AI Breadboard Installer v2.0.0")
        print(f"{'=' * 60}\n")
        print(f"Starting installer server...")
        print(f"  URL:      http://{args.host}:{args.port}")
        print(f"  Host:     {args.host}")
        print(f"  Port:     {args.port}")
        print(f"  Log:      {'verbose' if args.verbose else 'info'}")
        print()
        
        # Start server
        uvicorn.run(
            "server.main:app",
            host=args.host,
            port=args.port,
            log_level="debug" if args.verbose else "info",
            reload=False,
            access_log=args.verbose
        )
        
    except KeyboardInterrupt:
        print("\n\nInstaller stopped by user")
    except Exception as e:
        print(f"\nERROR: Failed to start installer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()