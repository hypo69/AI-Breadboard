# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Analytics 4 & Search Console Authentication Loader
# =============================================================================
# Description:
#   Resolves credentials for GA4 Data API, GA4 Admin API, and Google Search
#   Console across Service Account JSON, OAuth 2.0 User Tokens, and Mock/Demo mode.
#
# Examples:
#   >>> from apps.website_monitor.src.auth import WebsiteMonitorAuthManager
#   >>> auth_mgr = WebsiteMonitorAuthManager()
#   >>> status = auth_mgr.get_status()
#
# File: auth.py
# Project: ai-breadboard
# Package: apps.website_monitor.src
# Class: WebsiteMonitorAuthManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Authentication manager for GA4 and Search Console APIs."""

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

from logger import logger
from src.user_manager import user_manager


@dataclass
class AuthStatus:
    """Container for authentication diagnostic state."""

    authenticated: bool = False
    auth_type: str = 'none'
    property_id: str = ''
    site_url: str = ''
    client_email: str = ''
    source_file: str = ''
    is_mock: bool = False
    details: str = ''


class WebsiteMonitorAuthManager:
    """Manages credentials discovery, validation, and tokens for GA4 and GSC."""

    DEFAULT_SCOPES = [
        'https://www.googleapis.com/auth/analytics.readonly',
        'https://www.googleapis.com/auth/analytics.edit',
        'https://www.googleapis.com/auth/webmasters.readonly',
    ]

    def __init__(self, property_id_override: str = '', site_url_override: str = '') -> None:
        """Initialize authentication manager.

        Args:
            property_id_override (str): Optional GA4 property ID.
            site_url_override (str): Optional site URL for Search Console.
        """
        self.property_id_override: str = property_id_override
        self.site_url_override: str = site_url_override
        self._cached_credentials: Any = False
        self._cached_property_id: str = ''
        self._cached_site_url: str = ''
        self._auth_status: AuthStatus = AuthStatus()

    def _get_candidate_paths(self) -> List[Path]:
        """Collect candidate filepaths for Service Account JSON or credentials."""
        candidates: List[str] = [
            os.getenv('GA4_SERVICE_ACCOUNT_JSON', ''),
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''),
            os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', ''),
            'service_account.json',
            'ga4_service_account.json',
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

    def get_credentials(self) -> Tuple[Any, str, str]:
        """Discover and return valid credentials, property_id, and site_url.

        Returns:
            Tuple[Any, str, str]: (Credentials or False, property_id, site_url).
        """
        if self._auth_status.auth_type != 'none':
            return self._cached_credentials, self._cached_property_id, self._cached_site_url

        default_prop = self.property_id_override or os.getenv('GA4_PROPERTY_ID', 'properties/314159265')
        default_site = self.site_url_override or os.getenv('TARGET_SITE_URL', 'https://example.com')

        if not GOOGLE_AUTH_AVAILABLE:
            logger.info('Google Auth libraries not found. Website Monitor operating in Demo/Mock mode.')
            self._auth_status = AuthStatus(
                authenticated=False,
                auth_type='mock',
                property_id=default_prop,
                site_url=default_site,
                is_mock=True,
                details='google-auth not installed; running in high-fidelity mock mode',
            )
            return False, default_prop, default_site

        # 1. Candidate Service Account JSON files
        candidate_paths = self._get_candidate_paths()
        for path in candidate_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data.get('type') == 'service_account':
                    creds = service_account.Credentials.from_service_account_file(
                        str(path), scopes=self.DEFAULT_SCOPES
                    )
                    self._cached_credentials = creds
                    self._cached_property_id = default_prop
                    self._cached_site_url = default_site
                    self._auth_status = AuthStatus(
                        authenticated=True,
                        auth_type='service_account',
                        property_id=default_prop,
                        site_url=default_site,
                        client_email=data.get('client_email', ''),
                        source_file=str(path),
                        is_mock=False,
                        details='Authenticated via Service Account JSON key',
                    )
                    logger.info(f'Authenticated GA4 & GSC with service account: {self._auth_status.client_email}')
                    return creds, default_prop, default_site
            except Exception as exc:
                logger.warning(f'Failed parsing credentials from {path}: {exc}')

        # 2. Check user_manager OAuth token for default admin user (user_id=1)
        try:
            tokens = user_manager.get_google_tokens(1)
            access_token = tokens.get('access_token', '')
            if access_token:
                creds = Credentials(
                    token=access_token,
                    refresh_token=tokens.get('refresh_token', ''),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
                    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
                    scopes=self.DEFAULT_SCOPES,
                )
                self._cached_credentials = creds
                self._cached_property_id = default_prop
                self._cached_site_url = default_site
                self._auth_status = AuthStatus(
                    authenticated=True,
                    auth_type='oauth2',
                    property_id=default_prop,
                    site_url=default_site,
                    is_mock=False,
                    details='Authenticated via User OAuth 2.0 Token',
                )
                return creds, default_prop, default_site
        except Exception as exc:
            logger.debug(f'No OAuth tokens in user_manager: {exc}')

        # 3. Fallback to Demo / Mock mode
        self._cached_credentials = False
        self._cached_property_id = default_prop
        self._cached_site_url = default_site
        self._auth_status = AuthStatus(
            authenticated=False,
            auth_type='mock',
            property_id=default_prop,
            site_url=default_site,
            is_mock=True,
            details='No live Google credentials detected. Running in Demo/Mock Mode.',
        )
        return False, default_prop, default_site

    def get_status(self) -> AuthStatus:
        """Get current authentication state details."""
        if not self._auth_status.auth_type or self._auth_status.auth_type == 'none':
            self.get_credentials()
        return self._auth_status
