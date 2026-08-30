"""Structured logging setup (V9).

Single setup_logging() called from app startup. In `prod` the formatter
emits one JSON object per line; in `dev` it stays human-readable.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


class JsonFormatter(logging.Formatter):
    """Single-line JSON formatter for prod (suitable for log aggregators)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Surface structured fields (e.g. extra={"trace_id": ..., "user_id": ...})
        for k, v in record.__dict__.items():
            if k in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "asctime", "taskName",
            ):
                continue
            payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO", environment: str = "dev") -> None:
    """Configure the root logger once. Idempotent."""
    root = logging.getLogger()
    if root.handlers:
        # Already configured (uvicorn / reload)
        return

    handler = logging.StreamHandler(sys.stdout)
    if environment == "prod":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Tame chatty libraries
    for noisy in ("httpx", "httpcore", "multipart", "multipart.multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
