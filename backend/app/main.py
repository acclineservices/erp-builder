"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.database_health import router as database_health_router
from app.api.routes.auth import admin_router, router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.organization import router as organization_router
from app.api.routes.administration import router as administration_router
from app.api.routes.parties import router as parties_router
from app.api.routes.items import router as items_router
from app.api.routes.purchases import router as purchases_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the Pruvian API application."""
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Pruvian — Cloud Accounting & Business Management Platform.",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Content-Type", "X-Company-ID"],
    )
    application.include_router(health_router)
    application.include_router(database_health_router)
    application.include_router(auth_router)
    application.include_router(admin_router)
    application.include_router(organization_router)
    application.include_router(administration_router)
    application.include_router(parties_router)
    application.include_router(items_router)
    application.include_router(purchases_router)

    return application


app = create_app()
