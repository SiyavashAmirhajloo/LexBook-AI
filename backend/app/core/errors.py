"""Centralized error handling (V9).

Custom exception hierarchy + a global FastAPI handler. All API errors
return the same shape: { detail, code, trace_id }. Stack traces never
leak to clients; they go to the logger (and JSON-formatted in prod).
"""
from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)


class AppError(Exception):
    """Base for all expected application errors."""

    status_code: int = 500
    code: str = "internal_error"
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, code: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    detail = "Resource not found"


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    detail = "Authentication required"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    detail = "Permission denied"


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"
    detail = "Invalid request"


class UpstreamError(AppError):
    """An external service (LLM, search, etc.) failed."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "upstream_error"
    detail = "Upstream service unavailable"


def _envelope(
    detail: str, code: str, status_code: int, trace_id: str
) -> dict[str, object]:
    return {
        "detail": detail,
        "code": code,
        "trace_id": trace_id,
        "status": status_code,
    }


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:  # noqa: ARG001
        trace_id = uuid.uuid4().hex[:12]
        log.info(
            "app_error",
            extra={
                "trace_id": trace_id,
                "code": exc.code,
                "path": str(request.url.path),
                "method": request.method,
                "status": exc.status_code,
                "detail": exc.detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.detail, exc.code, exc.status_code, trace_id),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        trace_id = uuid.uuid4().hex[:12]
        log.info(
            "validation_error",
            extra={
                "trace_id": trace_id,
                "path": str(request.url.path),
                "method": request.method,
                "errors": exc.errors(),
            },
        )
        return JSONResponse(
            status_code=422,
            content=_envelope(
                "Invalid request body", "validation_error", 422, trace_id
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def _db_error(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        trace_id = uuid.uuid4().hex[:12]
        log.exception(
            "db_error",
            extra={
                "trace_id": trace_id,
                "path": str(request.url.path),
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content=_envelope("Database error", "db_error", 500, trace_id),
        )

    @app.exception_handler(Exception)
    async def _unhandled(
        request: Request, exc: Exception
    ) -> JSONResponse:
        trace_id = uuid.uuid4().hex[:12]
        # Full stack only in the log, not the response.
        log.exception(
            "unhandled_exception",
            extra={
                "trace_id": trace_id,
                "path": str(request.url.path),
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content=_envelope("Internal server error", "internal_error", 500, trace_id),
        )
