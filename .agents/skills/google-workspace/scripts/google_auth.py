## \file .agents/skills/google-workspace/scripts/google_auth.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Module for Google Workspace OAuth 2.0 authentication.
=====================================================

Handles user consent, token refresh, and credential retrieval for Google APIs.
"""

from pathlib import Path
from typing import Optional, List
import os

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    Request = None
    Credentials = None
    InstalledAppFlow = None

from src.logger.logger import logger

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly"
]

CREDENTIALS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "token.json"))


def get_credentials(
    credentials_path: Optional[Path] = None,
    token_path: Optional[Path] = None,
    scopes: Optional[List[str]] = None
):
    """Retrieve or generate valid Google OAuth 2.0 user credentials."""
    if InstalledAppFlow is None:
        logger.error("Google Auth libraries are not installed. Run 'pip install google-auth-oauthlib google-api-python-client'.")
        return None

    cred_file = credentials_path or CREDENTIALS_PATH
    tok_file = token_path or TOKEN_PATH
    active_scopes = scopes or DEFAULT_SCOPES

    creds = None

    if tok_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tok_file), active_scopes)
        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired Google OAuth token...")
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}. Re-authenticating...")
                creds = None

        if not creds:
            if not cred_file.exists():
                logger.error(
                    f"Google credentials file not found at: {cred_file.resolve()}. "
                    "Please download OAuth client credentials from Google Cloud Console."
                )
                return None

            try:
                logger.info("Starting local OAuth consent flow...")
                flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), active_scopes)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error during OAuth consent flow: {e}")
                return None

        try:
            tok_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tok_file, "w", encoding="utf-8") as token_out:
                token_out.write(creds.to_json())
            logger.info(f"Saved token to: {tok_file.resolve()}")
        except Exception as e:
            logger.error(f"Failed to save token file: {e}")

    return creds
