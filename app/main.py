"""BillBot FastAPI application entry point (webhook mode)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.container import build_container
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application.

    Args:
        settings: The application settings. Loaded from the environment if
            omitted.

    Returns:
        The configured FastAPI application.
    """
    settings = settings or get_settings()
    configure_logging(settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Build dependencies on startup and release them on shutdown.

        Args:
            app: The FastAPI application instance.
        """
        container = await build_container(settings)
        await container.start()
        app.state.container = container
        try:
            yield
        finally:
            await container.aclose()

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

    return app


app = create_app()
