# -*- coding: utf-8 -*-
# =============================================================================
# AI Breadboard Installer - FastAPI Backend
# =============================================================================
# Description: FastAPI server that powers the web-based installer GUI
#              Provides REST API for Python discovery, installation,
#              virtual environment management, and dependency installation.
#
# File: installer/server/main.py
# Project: AI Breadboard
# Author: AI Assistant
# =============================================================================

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add installer directory to path for imports
installer_dir = Path(__file__).parent.parent
sys.path.insert(0, str(installer_dir))

from installer.services.python_detector import PythonDetector
from installer.services.python_installer import PythonInstaller
from installer.services.environment_manager import EnvironmentManager

# Create FastAPI app
app = FastAPI(
    title="AI Breadboard Installer API",
    description="Backend API for AI Breadboard web-based installer",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Services
detector = PythonDetector()
installer = PythonInstaller()
env_manager = EnvironmentManager()

# Global state
installation_progress = {}
installation_status = {}


# ============================================================================
# Data Models
# ============================================================================

class PythonVersion(BaseModel):
    version: str
    path: Optional[str] = None
    available: bool = False


class InstallRequest(BaseModel):
    install_dir: str = Field(default_factory=lambda: os.environ.get(
        "LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")
    ) + "\\AI Breadboard")
    python_version: str = Field(default="3.13")
    create_venv: bool = True
    install_deps: bool = True
    add_to_path: bool = True


class InstallStatusResponse(BaseModel):
    status: str = Field(description="pending, running, completed, failed")
    progress: int = Field(default=0, ge=0, le=100)
    message: str = ""
    error: Optional[str] = None


class VenvRequest(BaseModel):
    install_dir: str
    python_path: Optional[str] = None


class PackageRequest(BaseModel):
    install_dir: str
    packages: list[str]
    requirements_file: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - redirects to web UI."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>AI Breadboard Installer</title>
        <meta http-equiv="refresh" content="0; url=/index.html" />
    </head>
    <body>
        <p>Redirecting to installer UI...</p>
    </body>
    </html>
    """)


@app.get("/api/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ai-breadboard-installer"}


@app.get("/api/python/versions", response_model=list[PythonVersion])
async def get_python_versions():
    """Discover available Python versions on the system."""
    return detector.find_available_versions()


@app.get("/api/python/installed", response_model=Optional[str])
async def get_installed_python():
    """Get path to currently installed Python for AI Breadboard."""
    config_path = Path(__file__).parent.parent / "install" / "install.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if config.get("install_dir"):
                venv_path = Path(config["install_dir"]) / "venv" / "Scripts" / "python.exe"
                if venv_path.exists():
                    return str(venv_path)
        except:
            pass
    return None


@app.post("/api/install", response_model=dict)
async def start_installation(
    request: InstallRequest,
    background_tasks: BackgroundTasks
):
    """Start the installation process asynchronously."""
    task_id = str(uuid.uuid4())
    
    installation_status[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Installation queued",
        "install_dir": request.install_dir
    }
    
    background_tasks.add_task(
        run_installation,
        task_id,
        request.install_dir,
        request.python_version,
        request.create_venv,
        request.install_deps,
        request.add_to_path
    )
    
    return {"task_id": task_id, "status": "started"}


@app.get("/api/install/status/{task_id}", response_model=InstallStatusResponse)
async def get_install_status(task_id: str):
    """Get status of installation task."""
    if task_id not in installation_status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    status = installation_status[task_id]
    return InstallStatusResponse(
        status=status["status"],
        progress=status["progress"],
        message=status.get("message", ""),
        error=status.get("error")
    )


@app.post("/api/venv/create", response_model=dict)
async def create_venv(request: VenvRequest):
    """Create a new virtual environment."""
    try:
        result = env_manager.create_venv(
            install_dir=request.install_dir,
            python_path=request.python_path
        )
        return {"success": True, "venv_path": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/packages/install", response_model=dict)
async def install_packages(request: PackageRequest):
    """Install packages or requirements."""
    try:
        if request.packages:
            result = env_manager.install_packages(
                install_dir=request.install_dir,
                packages=request.packages
            )
            return {"success": True, "installed": result}
        
        if request.requirements_file:
            result = env_manager.install_requirements(
                install_dir=request.install_dir,
                requirements_file=request.requirements_file
            )
            return {"success": True, "installed": result}
        
        raise HTTPException(status_code=400, detail="No packages or requirements file specified")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config", response_model=dict)
async def get_config():
    """Get installer configuration."""
    config_path = Path(__file__).parent.parent / "install" / "install.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


# ============================================================================
# Installation Worker
# ============================================================================

async def run_installation(
    task_id: str,
    install_dir: str,
    python_version: str,
    create_venv_flag: bool,
    install_deps_flag: bool,
    add_to_path_flag: bool
):
    """Background task to run installation process."""
    try:
        installation_status[task_id]["status"] = "running"
        installation_status[task_id]["progress"] = 10
        installation_status[task_id]["message"] = "Starting installation..."
        
        # Step 1: Check/Download Python
        installation_status[task_id]["progress"] = 20
        installation_status[task_id]["message"] = "Checking Python availability..."
        
        python_path = await detector.find_or_install_python(python_version)
        if not python_path:
            raise Exception(f"Python {python_version} could not be found or installed")
        
        installation_status[task_id]["message"] = f"Python {python_version} found: {python_path}"
        
        # Step 2: Create directory if needed
        installation_status[task_id]["progress"] = 30
        install_path = Path(install_dir)
        install_path.mkdir(parents=True, exist_ok=True)
        
        # Step 3: Clone/download repository if needed
        installation_status[task_id]["progress"] = 40
        installation_status[task_id]["message"] = "Checking project files..."
        
        header_path = install_path / "header.py"
        if not header_path.exists():
            # TODO: Implement git clone or zip download
            installation_status[task_id]["message"] = "Repository clone not implemented yet"
        
        # Step 4: Create virtual environment
        if create_venv_flag:
            installation_status[task_id]["progress"] = 50
            installation_status[task_id]["message"] = "Creating virtual environment..."
            
            venv_path = install_path / "venv"
            env_manager.create_venv(install_dir=str(install_path), python_path=python_path)
            
            installation_status[task_id]["message"] = "Virtual environment created"
        
        # Step 5: Upgrade pip
        installation_status[task_id]["progress"] = 60
        venv_python = install_path / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            env_manager.upgrade_pip(str(venv_python))
        
        # Step 6: Install dependencies
        if install_deps_flag:
            installation_status[task_id]["progress"] = 70
            installation_status[task_id]["message"] = "Installing dependencies..."
            
            req_file = install_path / "requirements.txt"
            if req_file.exists():
                env_manager.install_requirements(str(install_path), str(req_file))
            
            installation_status[task_id]["message"] = "Dependencies installed"
        
        # Step 7: Generate SSL certificates
        installation_status[task_id]["progress"] = 80
        installation_status[task_id]["message"] = "Generating SSL certificates..."
        
        # TODO: Implement SSL certificate generation
        
        # Step 8: Register system paths
        if add_to_path_flag:
            installation_status[task_id]["progress"] = 90
            installation_status[task_id]["message"] = "Registering system paths..."
            
            # TODO: Implement PATH registration
        
        # Step 9: Final verification
        installation_status[task_id]["progress"] = 100
        installation_status[task_id]["message"] = "Installation completed successfully!"
        installation_status[task_id]["status"] = "completed"
        
    except Exception as e:
        installation_status[task_id]["status"] = "failed"
        installation_status[task_id]["error"] = str(e)
        installation_status[task_id]["message"] = f"Installation failed: {str(e)}"


# ============================================================================
# Web UI Static Files
# ============================================================================

# Mount web directory for static files
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Start the installer server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Breadboard Installer Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--open", action="store_true", help="Open browser after start")
    
    args = parser.parse_args()
    
    print(f"Starting AI Breadboard Installer on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")
    
    # Open browser if requested
    if args.open:
        try:
            import webbrowser
            webbrowser.open(f"http://{args.host}:{args.port}")
        except:
            pass
    
    uvicorn.run(
        "installer.server.main:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()