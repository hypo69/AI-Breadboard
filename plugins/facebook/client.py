# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Facebook Graph API Client Interface
# =============================================================================
# Description:
#   Provides an asynchronous HTTP client for interacting with Facebook Graph API,
#   supporting feed posts, link sharing, photo publishing, and account inspection.
#
# File: client.py
# Project: ai-breadboard
# Package: plugins.facebook
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Facebook Graph API client module.

Handles network requests to Facebook Graph API endpoints, providing typed methods
for posting messages, media, inspecting pages, and validating authentication tokens.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx

from src.logger import logger


class FacebookGraphClient:
    """Asynchronous client for interacting with the Facebook Graph API.

    Attributes:
        page_id (str): Default target Facebook Page ID.
        access_token (str): Facebook Page or User access token.
        api_version (str): Facebook Graph API version (e.g., 'v19.0').
        base_url (str): Computed base URL for the Graph API endpoints.
    """

    def __init__(
        self,
        page_id: str = "",
        access_token: str = "",
        api_version: str = "v19.0",
    ) -> None:
        """Initialize the Facebook Graph API client.

        Args:
            page_id (str): Target Facebook Page ID.
            access_token (str): Valid Page or User access token.
            api_version (str): Graph API version tag. Defaults to 'v19.0'.
        """
        self.page_id: str = str(page_id).strip()
        self.access_token: str = access_token.strip()
        self.api_version: str = api_version.strip() or "v19.0"
        self.base_url: str = f"https://graph.facebook.com/{self.api_version}"

    def is_configured(self) -> bool:
        """Check if minimum required credentials (token) are configured.

        Returns:
            bool: True if an access token is present, False otherwise.
        """
        return bool(self.access_token)

    async def publish_post(
        self,
        message: str,
        link: Optional[str] = None,
        page_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish a text message and optional URL link to a Facebook Page or feed.

        Args:
            message (str): Text body of the post.
            link (Optional[str]): Optional web URL to attach as a link preview.
            page_id (Optional[str]): Target Page ID. Falls back to self.page_id or 'me'.
            access_token (Optional[str]): Override access token. Falls back to self.access_token.

        Returns:
            Dict[str, Any]: API response containing 'id' or error details.
        """
        token = access_token or self.access_token
        if not token:
            return {"success": False, "error": "Access token is missing or not configured."}

        target_id = page_id or self.page_id or "me"
        url = f"{self.base_url}/{target_id}/feed"

        payload: Dict[str, Any] = {
            "message": message,
            "access_token": token,
        }
        if link:
            payload["link"] = link

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload)
                data = response.json()

                if response.is_success and "id" in data:
                    logger.info(f"Facebook post published successfully: ID={data['id']}")
                    return {"success": True, "id": data["id"], "data": data}

                error_msg = self._extract_error(data, response.status_code)
                logger.error(f"Facebook publish post failed: {error_msg}")
                return {"success": False, "error": error_msg, "status_code": response.status_code, "raw": data}

        except Exception as exc:
            logger.error(f"Network error during Facebook post publication: {exc}", exc_info=True)
            return {"success": False, "error": str(exc)}

    async def publish_photo(
        self,
        caption: str,
        photo_url: Optional[str] = None,
        photo_bytes: Optional[bytes] = None,
        filename: str = "photo.jpg",
        page_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish a photo with a caption to a Facebook Page or user albums.

        Args:
            caption (str): Description or caption text for the photo.
            photo_url (Optional[str]): Remote accessible URL of the image.
            photo_bytes (Optional[bytes]): Raw binary content of the photo file.
            filename (str): Name of the file when uploading raw bytes.
            page_id (Optional[str]): Target Page ID. Falls back to self.page_id or 'me'.
            access_token (Optional[str]): Override access token. Falls back to self.access_token.

        Returns:
            Dict[str, Any]: API response containing 'id' and 'post_id' or error details.
        """
        token = access_token or self.access_token
        if not token:
            return {"success": False, "error": "Access token is missing or not configured."}

        target_id = page_id or self.page_id or "me"
        url = f"{self.base_url}/{target_id}/photos"

        data_payload: Dict[str, Any] = {
            "caption": caption,
            "access_token": token,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                if photo_bytes:
                    files = {"source": (filename, photo_bytes, "image/jpeg")}
                    response = await client.post(url, data=data_payload, files=files)
                elif photo_url:
                    data_payload["url"] = photo_url
                    response = await client.post(url, data=data_payload)
                else:
                    return {"success": False, "error": "Neither photo_url nor photo_bytes was provided."}

                data = response.json()
                if response.is_success and "id" in data:
                    logger.info(f"Facebook photo published successfully: ID={data['id']}")
                    return {"success": True, "id": data["id"], "post_id": data.get("post_id"), "data": data}

                error_msg = self._extract_error(data, response.status_code)
                logger.error(f"Facebook publish photo failed: {error_msg}")
                return {"success": False, "error": error_msg, "status_code": response.status_code, "raw": data}

        except Exception as exc:
            logger.error(f"Network error during Facebook photo publication: {exc}", exc_info=True)
            return {"success": False, "error": str(exc)}

    async def get_page_info(
        self,
        page_id: Optional[str] = None,
        access_token: Optional[str] = None,
        fields: str = "id,name,fan_count,followers_count,link,about,is_published",
    ) -> Dict[str, Any]:
        """Fetch metadata and public stats for a target Facebook Page.

        Args:
            page_id (Optional[str]): Page ID or 'me'.
            access_token (Optional[str]): Override access token.
            fields (str): Comma-separated list of Graph API fields to request.

        Returns:
            Dict[str, Any]: Page details or error dictionary.
        """
        token = access_token or self.access_token
        if not token:
            return {"success": False, "error": "Access token is missing or not configured."}

        target_id = page_id or self.page_id or "me"
        url = f"{self.base_url}/{target_id}"
        params = {"fields": fields, "access_token": token}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params)
                data = response.json()

                if response.is_success and "id" in data:
                    return {"success": True, "data": data}

                error_msg = self._extract_error(data, response.status_code)
                return {"success": False, "error": error_msg, "status_code": response.status_code}

        except Exception as exc:
            logger.error(f"Error fetching Facebook page info: {exc}")
            return {"success": False, "error": str(exc)}

    async def get_accounts(
        self,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch list of Facebook Pages managed by the authenticated user.

        Args:
            access_token (Optional[str]): User access token with 'pages_show_list' permission.

        Returns:
            Dict[str, Any]: List of managed page accounts with Page IDs and tokens.
        """
        token = access_token or self.access_token
        if not token:
            return {"success": False, "error": "Access token is missing or not configured."}

        url = f"{self.base_url}/me/accounts"
        params = {"access_token": token}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params)
                data = response.json()

                if response.is_success and "data" in data:
                    return {"success": True, "accounts": data["data"]}

                error_msg = self._extract_error(data, response.status_code)
                return {"success": False, "error": error_msg, "status_code": response.status_code}

        except Exception as exc:
            logger.error(f"Error fetching Facebook accounts: {exc}")
            return {"success": False, "error": str(exc)}

    async def test_connection(self) -> Dict[str, Any]:
        """Verify API token validity and connectivity against the Graph API.

        Returns:
            Dict[str, Any]: Diagnostic verification result.
        """
        if not self.is_configured():
            return {
                "success": False,
                "configured": False,
                "error": "Facebook Access Token is not set.",
            }

        target_id = self.page_id or "me"
        info = await self.get_page_info(page_id=target_id, fields="id,name,is_published")
        if info.get("success"):
            page_data = info.get("data", {})
            return {
                "success": True,
                "configured": True,
                "target_id": target_id,
                "name": page_data.get("name", "Unknown"),
                "id": page_data.get("id"),
                "message": f"Successfully connected to Facebook target: {page_data.get('name', target_id)}",
            }

        return {
            "success": False,
            "configured": True,
            "error": info.get("error", "Unknown API error during connection test."),
        }

    def _extract_error(self, data: Dict[str, Any], status_code: int) -> str:
        """Extract user-friendly error message from Graph API error response.

        Args:
            data (Dict[str, Any]): Parsed JSON payload from Facebook.
            status_code (int): HTTP status code.

        Returns:
            str: Descriptive error string.
        """
        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            if isinstance(err, dict):
                msg = err.get("message", "Unknown Facebook API error")
                err_type = err.get("type", "")
                code = err.get("code", "")
                fbtrace_id = err.get("fbtrace_id", "")
                details = f"{msg} (code: {code}, type: {err_type})"
                if fbtrace_id:
                    details += f" [trace: {fbtrace_id}]"
                return details
            return str(err)
        return f"HTTP {status_code} request failed"
