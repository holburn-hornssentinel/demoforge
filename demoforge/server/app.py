"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from demoforge.cache import PipelineCache
from demoforge.config import Settings, get_settings
from demoforge.server.dependencies import set_app_settings
from demoforge.server.routes import analytics, health, pipeline, projects


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create FastAPI application.

    Args:
        settings: Application settings (loads from environment if None)

    Returns:
        Configured FastAPI app
    """
    if settings is None:
        settings = get_settings()

    # Set global settings for dependency injection
    set_app_settings(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for startup/shutdown events."""
        # Startup: cleanup expired cache entries
        cache = PipelineCache(
            cache_dir=settings.cache_dir,
            enabled=settings.enable_caching,
            ttl_hours=settings.cache_ttl_hours,
        )
        removed = cache.cleanup_expired()
        if removed > 0:
            print(f"Removed {removed} expired cache entries on startup")

        yield
        # Shutdown: nothing to do yet

    app = FastAPI(
        title="DemoForge API",
        description="Automated product demo video generator",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(pipeline.router)
    app.include_router(analytics.router)

    return app
