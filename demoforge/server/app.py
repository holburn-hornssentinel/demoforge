"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from demoforge.config import Settings
from demoforge.server.routes import health, pipeline, projects


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create FastAPI application.

    Args:
        settings: Application settings (loads from environment if None)

    Returns:
        Configured FastAPI app
    """
    if settings is None:
        from demoforge.config import get_settings

        settings = get_settings()

    app = FastAPI(
        title="DemoForge API",
        description="Automated product demo video generator",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Dependency injection for settings
    def get_settings_dependency() -> Settings:
        return settings

    app.dependency_overrides[Settings] = get_settings_dependency

    # Register routes
    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(pipeline.router)

    return app
