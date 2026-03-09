"""
Authentication middleware.

Simple API Key authentication to protect the system from unauthorized access.
When AUTH_API_KEY is configured, all API requests must include the key via:
  - Header: X-API-Key: <key>
  - Query param: ?api_key=<key>

Static file serving (CSS/JS/HTML) is exempt from auth.
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_settings

logger = logging.getLogger(__name__)

# Paths that don't require authentication
AUTH_EXEMPT_PATHS = {
    "/",
    "/ui",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Prefixes that don't require authentication
AUTH_EXEMPT_PREFIXES = (
    "/static/",
)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # If no auth key configured, skip authentication
        if not settings.auth_api_key:
            return await call_next(request)

        path = request.url.path

        # Skip auth for exempt paths
        if path in AUTH_EXEMPT_PATHS:
            return await call_next(request)

        # Skip auth for exempt prefixes (static files)
        if path.startswith(AUTH_EXEMPT_PREFIXES):
            return await call_next(request)

        # Extract API key from request
        api_key = (
            request.headers.get("X-API-Key")
            or request.query_params.get("api_key")
        )

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key. Provide via X-API-Key header or api_key query parameter."},
            )

        if api_key != settings.auth_api_key:
            logger.warning(f"Invalid API key attempt from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key."},
            )

        return await call_next(request)
