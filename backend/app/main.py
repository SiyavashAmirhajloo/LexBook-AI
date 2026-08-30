"""FastAPI application factory."""
from fastapi import FastAPI

from app.api.analytics import router as analytics_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.memory import router as memory_router
from app.api.personalization import router as personalization_router
from app.api.study_sessions import router as study_sessions_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Include routers
app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])
app.include_router(documents_router, prefix=settings.api_prefix, tags=["documents"])
app.include_router(chat_router, prefix=settings.api_prefix, tags=["chat"])
app.include_router(study_sessions_router, prefix=settings.api_prefix, tags=["study-sessions"])
app.include_router(personalization_router, prefix=settings.api_prefix, tags=["personalization"])
app.include_router(memory_router, prefix=settings.api_prefix, tags=["memory"])
app.include_router(analytics_router, prefix=settings.api_prefix, tags=["analytics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to LexBook AI Backend",
        "docs_url": "/docs",
        "health_check": f"{settings.api_prefix}/health",
    }
