## \file .agents/skills/google-workspace/scripts/google_auth.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Module for Google Workspace OAuth 2.0 and Service Account authentication.
========================================================================

Handles project-level credentials (Service Account), user consent (OAuth 2.0),
token refresh, and credential retrieval for Google APIs (Drive, Gmail, Sheets, Docs).
"""

from pathlib import Path
from typing import Optional, List
import json
import os
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    Request = None
    Credentials = None
    service_account = None
    InstalledAppFlow = None

from src.logger.logger import logger

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

# Candidate paths for credentials
CREDENTIAL_CANDIDATES = [
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    os.getenv("GOOGLE_CREDENTIALS_PATH"),
    "src/secrets/credentials.json",
    "src/secrets/service_account.json",
    "credentials.json",
    "service_account.json",
    "google_credentials.json",
    "google_service_account.json",
    str(Path(__file__).parent / "credentials.json"),
]

TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "src/secrets/token.json"))


def find_credential_file(custom_path: Optional[Path] = None) -> Optional[Path]:
    """
    Locate the first available credential file in candidates.

    :param custom_path: Optional explicit path.
    :return: Resolved Path if found, else None.
    """
    if custom_path and Path(custom_path).exists():
        return Path(custom_path)

    for cand in CREDENTIAL_CANDIDATES:
        if not cand:
            continue
        p = Path(cand)
        if p.exists():
            return p
        # Also check relative to repo root
        root_p = _REPO_ROOT / cand
        if root_p.exists():
            return root_p

    return None


def get_credentials(
    credentials_path: Optional[Path] = None,
    token_path: Optional[Path] = None,
    scopes: Optional[List[str]] = None,
    account_name: Optional[str] = None,
):
    """
    Retrieve or generate valid Google credentials from secrets pool or local files.

    :param credentials_path: Explicit path to credentials/service account JSON.
    :param token_path: Explicit path to cached token JSON.
    :param scopes: List of requested OAuth/Service Account scopes.
    :param account_name: Specific account name from src/secrets/google_accounts.json pool.
    :return: Credentials instance or None.
    """
    if Request is None or Credentials is None:
        logger.error(
            "Google Auth libraries are not installed. Run 'pip install google-auth-oauthlib google-api-python-client'."
        )
        return None

    active_scopes = scopes or DEFAULT_SCOPES

    # 1. First try loading credentials from Google Accounts Pool in src/secrets
    try:
        from src.ai.google_accounts_state import load_account_credentials
        pool_creds = load_account_credentials(account_name=account_name, scopes=active_scopes)
        if pool_creds:
            return pool_creds
    except Exception as ex:
        logger.debug(f"Google accounts pool lookup skipped: {ex}")

    tok_file = token_path or TOKEN_PATH
    cred_file = find_credential_file(credentials_path)

    # 1. Check if Service Account JSON is provided in env var directly
    sa_json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json_env and service_account:
        try:
            info = json.loads(sa_json_env)
            logger.info("Loaded Google credentials from GOOGLE_SERVICE_ACCOUNT_JSON env var.")
            return service_account.Credentials.from_service_account_info(info, scopes=active_scopes)
        except Exception as e:
            logger.warning(f"Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # 2. Check if discovered file is a Service Account
    if cred_file and cred_file.exists() and service_account:
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("type") == "service_account":
                logger.info(f"Using Google Service Account credentials from: {cred_file.resolve()}")
                return service_account.Credentials.from_service_account_file(
                    str(cred_file), scopes=active_scopes
                )
        except Exception as e:
            logger.debug(f"File {cred_file} is not a valid Service Account JSON: {e}")

    # 3. Check for existing cached user OAuth token
    creds = None
    if tok_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tok_file), active_scopes)
        except Exception as e:
            logger.warning(f"Failed to load cached OAuth token: {e}")
            creds = None

    # 4. Refresh token or run local OAuth server
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired Google OAuth token...")
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}. Re-authenticating...")
                creds = None

        if not creds:
            if not cred_file or not cred_file.exists():
                logger.error(
                    f"No valid Google credentials found. Please place credentials.json or "
                    f"service_account.json in the project root or configure GOOGLE_APPLICATION_CREDENTIALS."
                )
                return None

            try:
                logger.info(f"Starting local OAuth consent flow with client secrets: {cred_file.resolve()}...")
                flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), active_scopes)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error during OAuth consent flow: {e}")
                return None

        # Cache refreshed/new token
        if creds:
            try:
                tok_file.parent.mkdir(parents=True, exist_ok=True)
                with open(tok_file, "w", encoding="utf-8") as token_out:
                    token_out.write(creds.to_json())
                logger.info(f"Saved token to: {tok_file.resolve()}")
            except Exception as e:
                logger.error(f"Failed to save token file: {e}")

    return creds
