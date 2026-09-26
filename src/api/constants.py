# -*- coding: utf-8 -*-
# =============================================================================
# Constants for API routing
# =============================================================================
# Description:
#   Centralized definition of the base API prefix used across all FastAPI routers.
#   This ensures a single source of truth and simplifies future versioning.
#
# NOTE: All routers must prepend this prefix to their own route prefixes.
# =============================================================================

BASE_API_PREFIX = "/api/v1"
