# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Standalone Messenger Microservice Runner
# =============================================================================
# Description:
#   Independent microservice runner allowing the Real-Time Messenger and WebRTC
#   hub to run as a dedicated, lightweight standalone service without loading
#   the entire AI-Breadboard monolithic environment.
#
# File: standalone.py
# Project: ai-breadboard
# Package: src.api.messenger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.api.messenger.router_messenger import init_router
from src.logger import logger

app = FastAPI(title="AI-Breadboard Standalone Messenger Hub", version="1.0.0")

# Allow all origins for standalone microservice
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register messenger router
app.include_router(init_router())

# Mount webinterface for web app and widget
webinterface_dir = Path(__file__).resolve().parents[1] / "webgui" / "messenger"
if webinterface_dir.exists():
    app.mount("/messenger", StaticFiles(directory=webinterface_dir, html=True), name="messenger_ui")

if __name__ == "__main__":
    port = int(os.getenv("MESSENGER_PORT", "8088"))
    host = os.getenv("MESSENGER_HOST", "0.0.0.0")
    logger.info(f"Starting standalone messenger service on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
