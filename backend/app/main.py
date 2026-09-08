"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.database_health import router as database_health_router
from app.api.routes.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the ERP Builder API application."""
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="ERP Builder backend API.",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=[],
    )
    application.include_router(health_router)
    application.include_router(database_health_router)

    return application


app = create_app()
