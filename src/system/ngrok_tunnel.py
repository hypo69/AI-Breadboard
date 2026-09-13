# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Ngrok tunnel management and telemetry gateway
# =============================================================================
# Description:
#   Manages local ngrok tunnel lifecycle for exposing AI-Breadboard server
#   and receiving telemetry from distributed/local user instances.
#
# File: ngrok_tunnel.py
# Package: src.system
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from header import __root__
from src.logger import logger

load_dotenv(__root__ / '.env')


class NgrokTunnelManager:
    """Manages Ngrok tunnel processes and queries public endpoint information.

    Attributes:
        local_port (int): Local application port to expose.
        ngrok_api_url (str): Ngrok local inspector API URL.
        token (str): Ngrok authentication token.
    """

    def __init__(self, local_port: int = 8000) -> None:
        """Initialize NgrokTunnelManager.

        Args:
            local_port (int): Local HTTP port to tunnel. Defaults to 8000.
        """
        self.local_port: int = local_port
        self.ngrok_api_url: str = "http://127.0.0.1:4040/api/tunnels"
        self._cached_url: Optional[str] = None

    @property
    def authtoken(self) -> str:
        """Retrieve authtoken from environment variables with fallback keys.

        Returns:
            str: Resolved authtoken or empty string.
        """
        token = (
            os.getenv("NGROK_AUTHTOKEN")
            or os.getenv("NGROCK_AUTOTOKEN")
            or os.getenv("NGROK_TOKEN")
            or ""
        )
        if token in ("your_ngrok_authtoken_here", "None"):
            return ""
        return token.strip()

    def get_active_tunnel_url(self) -> Optional[str]:
        """Query active Ngrok tunnel URL from local Ngrok API or environment.

        Returns:
            Optional[str]: Active public HTTPS URL or None if not running.
        """
        # 1. First try querying local ngrok inspector API (http://127.0.0.1:4040/api/tunnels)
        try:
            resp = requests.get(self.ngrok_api_url, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                tunnels = data.get("tunnels", [])
                for t in tunnels:
                    public_url = t.get("public_url", "")
                    if public_url.startswith("https://"):
                        self._cached_url = public_url
                        return public_url
                if tunnels:
                    first_url = tunnels[0].get("public_url")
                    self._cached_url = first_url
                    return first_url
        except Exception:
            pass

        # 2. Check explicitly configured forward URL in .env
        env_url = (
            os.getenv("CENTRAL_TELEMETRY_URL")
            or os.getenv("NGROK_TUNNEL_URL")
            or os.getenv("REMOTE_TELEMETRY_URL")
        )
        if env_url and env_url.startswith("http"):
            return env_url.strip()

        return self._cached_url

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive tunnel status report.

        Returns:
            Dict[str, Any]: Dictionary containing active status, public URL, and port.
        """
        public_url = self.get_active_tunnel_url()
        is_active = bool(public_url)
        return {
            "is_active": is_active,
            "public_url": public_url,
            "local_port": self.local_port,
            "has_authtoken": bool(self.authtoken),
            "inspector_url": "http://127.0.0.1:4040" if is_active else None,
        }

    def start_tunnel(self) -> Dict[str, Any]:
        """Start Ngrok tunnel subprocess or via pyngrok if available.

        Returns:
            Dict[str, Any]: Status dictionary after starting attempt.
        """
        # Check if already running
        active_url = self.get_active_tunnel_url()
        if active_url:
            return {"status": "already_running", "public_url": active_url}

        # Try pyngrok if installed
        try:
            from pyngrok import ngrok
            token = self.authtoken
            if token:
                ngrok.set_auth_token(token)
            http_tunnel = ngrok.connect(self.local_port, "http")
            self._cached_url = str(http_tunnel.public_url)
            logger.info(f"Ngrok tunnel established via pyngrok: {self._cached_url}")
            return {"status": "started", "public_url": self._cached_url}
        except ImportError:
            pass
        except Exception as ex:
            logger.warning(f"pyngrok launch error: {ex}")

        # Fallback to ngrok CLI command
        try:
            token = self.authtoken
            if token:
                subprocess.run(
                    ["ngrok", "config", "add-authtoken", token],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

            logs_dir = __root__ / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / "ngrok.log"

            with open(log_file, "a", encoding="utf-8") as out:
                subprocess.Popen(
                    ["ngrok", "http", str(self.local_port), "--log=stdout"],
                    stdout=out,
                    stderr=out,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )

            time.sleep(2)
            url = self.get_active_tunnel_url()
            return {"status": "started" if url else "launching", "public_url": url}
        except Exception as ex:
            logger.error("Failed to start ngrok CLI process:", ex, False)
            return {"status": "error", "error": str(ex), "public_url": None}


ngrok_manager = NgrokTunnelManager()
