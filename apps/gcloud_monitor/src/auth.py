# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Cloud Credentials and Authentication Loader
# =============================================================================
# Description:
#   Loads Google Cloud Platform credentials across multiple discovery vectors
#   including Service Account JSON, OAuth 2.0 User credentials, and Application
#   Default Credentials (ADC).
#
# Examples:
#   >>> from apps.gcloud_monitor.src.auth import GCloudAuthManager
#   >>> auth_mgr = GCloudAuthManager()
#   >>> creds, project_id = auth_mgr.get_credentials()
#
# File: auth.py
# Project: ai-breadboard
# Package: apps.gcloud_monitor.src
# Class: GCloudAuthManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Google Cloud Platform authentication and credential resolution."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    Request = None  # type: ignore
    service_account = None  # type: ignore
    Credentials = None  # type: ignore
    GOOGLE_AUTH_AVAILABLE = False

from src.logger import logger


@dataclass
class AuthStatus:
    """Container for authentication diagnostic state."""

    authenticated: bool = False
    auth_type: str = 'none'
    project_id: str = ''
    client_email: str = ''
    source_file: str = ''
    is_mock: bool = False
    details: str = ''


class GCloudAuthManager:
    """Manages credentials discovery, validation, and token lifecycle for GCP APIs."""

    DEFAULT_SCOPES = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/logging.read',
        'https://www.googleapis.com/auth/monitoring.read',
        'https://www.googleapis.com/auth/pubsub',
    ]

    def __init__(self, project_id_override: str = '') -> None:
        """Initialize authentication manager.

        Args:
            project_id_override (str): Optional GCP project ID to enforce.
        """
        self.project_id_override: str = project_id_override
        self._cached_credentials: Any = False
        self._cached_project_id: str = ''
        self._auth_status: AuthStatus = AuthStatus()

    def _get_candidate_paths(self) -> List[Path]:
        """Collect candidate filepaths for Service Account or OAuth credentials.

        Returns:
            List[Path]: Candidate paths in priority order.
        """
        candidates: List[str] = [
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''),
            os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', ''),
            os.getenv('GOOGLE_CREDENTIALS_PATH', ''),
            'service_account.json',
            'google_service_account.json',
            'src/secrets/service_account.json',
            'src/secrets/credentials.json',
            'credentials.json',
        ]
        resolved: List[Path] = []
        for p in candidates:
            if p and p.strip():
                path_obj = Path(p.strip())
                if path_obj.exists() and path_obj.is_file():
                    resolved.append(path_obj.resolve())
        return resolved

    def get_credentials(self) -> Tuple[Any, str]:
        """Discover and return valid GCP credentials with associated project ID.

        Returns:
            Tuple[Any, str]: (Credentials object or False, project_id string).
        """
        if self._auth_status.auth_type != 'none':
            return self._cached_credentials, self._cached_project_id

        if not GOOGLE_AUTH_AVAILABLE:
            logger.warning('Google Auth libraries not installed. Using offline mock mode.')
            self._auth_status = AuthStatus(
                authenticated=False,
                auth_type='mock',
                project_id=self.project_id_override or 'mock-gcp-project',
                is_mock=True,
                details='google-auth library not present; running mock telemetry',
            )
            return False, self._auth_status.project_id

        # 1. Search candidate JSON files
        candidate_paths = self._get_candidate_paths()
        for path in candidate_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data.get('type') == 'service_account':
                    creds = service_account.Credentials.from_service_account_file(
                        str(path), scopes=self.DEFAULT_SCOPES
                    )
                    proj_id = self.project_id_override or data.get('project_id', '')
                    self._cached_credentials = creds
                    self._cached_project_id = proj_id
                    self._auth_status = AuthStatus(
                        authenticated=True,
                        auth_type='service_account',
                        project_id=proj_id,
                        client_email=data.get('client_email', ''),
                        source_file=str(path),
                        is_mock=False,
                        details='Authenticated via Service Account JSON key',
                    )
                    logger.info(f'Authenticated GCP with service account: {self._auth_status.client_email}')
                    return creds, proj_id

                if 'installed' in data or 'web' in data:
                    token_path = Path('src/secrets/token.json')
                    if token_path.exists():
                        creds = Credentials.from_authorized_user_file(str(token_path), self.DEFAULT_SCOPES)
                        if creds and creds.expired and creds.refresh_token:
                            creds.refresh(Request())
                        proj_id = self.project_id_override or os.getenv('GOOGLE_CLOUD_PROJECT', '')
                        self._cached_credentials = creds
                        self._cached_project_id = proj_id
                        self._auth_status = AuthStatus(
                            authenticated=True,
                            auth_type='oauth2',
                            project_id=proj_id,
                            source_file=str(token_path),
                            is_mock=False,
                            details='Authenticated via OAuth 2.0 User Token',
                        )
                        return creds, proj_id
            except Exception as exc:
                logger.warning(f'Failed parsing credentials from {path}: {exc}')

        # 2. Fallback to Application Default Credentials (ADC)
        try:
            import google.auth
            creds, proj_id = google.auth.default(scopes=self.DEFAULT_SCOPES)
            final_proj_id = self.project_id_override or proj_id or os.getenv('GOOGLE_CLOUD_PROJECT', '')
            self._cached_credentials = creds
            self._cached_project_id = final_proj_id
            self._auth_status = AuthStatus(
                authenticated=True,
                auth_type='adc',
                project_id=final_proj_id,
                is_mock=False,
                details='Authenticated via Application Default Credentials (ADC)',
            )
            return creds, final_proj_id
        except Exception as exc:
            logger.info(f'ADC credentials not found: {exc}')

        # 3. Fallback to Mock / Offline Mode
        fallback_proj = self.project_id_override or os.getenv('GOOGLE_CLOUD_PROJECT', 'local-gcp-dev')
        self._cached_credentials = False
        self._cached_project_id = fallback_proj
        self._auth_status = AuthStatus(
            authenticated=False,
            auth_type='mock',
            project_id=fallback_proj,
            is_mock=True,
            details='No valid GCP credentials found. Running in simulated telemetry mode.',
        )
        return False, fallback_proj

    def get_status(self) -> AuthStatus:
        """Get current authentication state details.

        Returns:
            AuthStatus: Structured authentication state.
        """
        if not self._auth_status.auth_type or self._auth_status.auth_type == 'none':
            self.get_credentials()
        return self._auth_status
