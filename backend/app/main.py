"""FastAPI application factory (V9)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.memory import router as memory_router
from app.api.personalization import router as personalization_router
from app.api.study_sessions import router as study_sessions_router
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(level=settings.log_level, environment=settings.environment)

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS — settings-driven allowlist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized error envelope + JSON logging in prod
install_exception_handlers(app)

# Auth: PUBLIC (no auth required) — must be included before the auth-required routers
app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])
app.include_router(auth_router, prefix=settings.api_prefix, tags=["auth"])

# Auth-required routers — wrapped by AuthMiddleware in app/middleware/auth.py
app.include_router(documents_router, prefix=settings.api_prefix, tags=["documents"])
app.include_router(chat_router, prefix=settings.api_prefix, tags=["chat"])
app.include_router(study_sessions_router, prefix=settings.api_prefix, tags=["study-sessions"])
app.include_router(personalization_router, prefix=settings.api_prefix, tags=["personalization"])
app.include_router(memory_router, prefix=settings.api_prefix, tags=["memory"])
app.include_router(analytics_router, prefix=settings.api_prefix, tags=["analytics"])

# Install the auth middleware AFTER routers (it sees all paths and lets
# the allowlist through).
from app.middleware.auth import install_auth_middleware  # noqa: E402

install_auth_middleware(app, settings)


@app.get("/")
async def root():
    return {
        "message": "Welcome to LexBook AI Backend",
        "docs_url": "/docs",
        "health_check": f"{settings.api_prefix}/health",
        "environment": settings.environment,
    }
