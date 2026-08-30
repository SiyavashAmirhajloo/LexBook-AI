"""Auth middleware (V9).

Validates the bearer token on every request under /api/v1 (except the
allowlisted public paths) and attaches the current `User` to request.state.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.db import AsyncSessionLocal as SessionLocal
from app.core.errors import AuthError
from app.models import User
from app.services.auth import decode_access

log = logging.getLogger(__name__)

# Paths that NEVER require auth (relative to API prefix).
PUBLIC_PREFIXES: tuple[str, ...] = (
    "/health",
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/guest",
    "/auth/google",
    "/docs",
    "/openapi.json",
    "/redoc",
)


def _is_public(path: str) -> bool:
    # API base is `/api/v1`; strip it for the comparison.
    if path.startswith("/api/v1"):
        path = path[len("/api/v1") :]
    return any(path.startswith(p) for p in PUBLIC_PREFIXES)


async def _resolve_user(settings: Settings, token: str) -> User | None:
    try:
        claims = decode_access(settings, token)
    except AuthError:
        return None
    sub = claims.get("sub")
    if not sub or sub == "guest":
        return None
    try:
        from uuid import UUID

        user_id = UUID(sub)
    except ValueError:
        return None
    async with SessionLocal() as db:  # type: AsyncSession
        return await db.get(User, user_id)


def current_user(request: Request) -> User:
    """FastAPI dependency: returns the user attached by the middleware."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise AuthError("Authentication required")
    return user


def install_auth_middleware(app: FastAPI, settings: Settings) -> None:
    @app.middleware("http")
    async def _auth_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not request.url.path.startswith("/api/v1") or _is_public(request.url.path):
            return await call_next(request)

        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required", "code": "unauthorized"},
            )
        token = header.split(" ", 1)[1].strip()
        user = await _resolve_user(settings, token)
        if user is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token", "code": "invalid_token"},
            )
        if not user.is_active:
            return JSONResponse(
                status_code=403,
                content={"detail": "Account disabled", "code": "forbidden"},
            )
        request.state.user = user
        return await call_next(request)
