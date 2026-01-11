"""BillBot FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler.

    Initializes the database on startup.

    Args:
        app: The FastAPI application instance.
    """
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Telegram bot for processing bill documents.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A status message indicating the service is healthy.
    """
    return {"status": "healthy"}
