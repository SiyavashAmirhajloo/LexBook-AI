"""FastAPI application factory."""
from fastapi import FastAPI

from app.core.config import get_settings
from app.api.health import router as health_router
from app.api.documents import router as documents_router

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Include routers
app.include_router(health_router, prefix=settings.api_prefix, tags=["health"])
app.include_router(documents_router, prefix=settings.api_prefix, tags=["documents"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to LexBook AI Backend",
        "docs_url": "/docs",
        "health_check": f"{settings.api_prefix}/health",
    }